from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .audit import record
from .authorization import (
    can_view_question, is_project_member, is_security_admin, is_team_manager,
    may_read_document,
)
from .db import initialize, make_engine, make_session_factory
from .delegation import as_utc, policy_is_active, utc_now
from .connectors.entra import EntraSettings, EntraTokenValidator, IdentityConfigurationError, TokenRejected
from .models import (
    ApprovedKnowledgeEntry, AnswerValidation, DelegationPolicy, Document, Employee,
    Escalation, EvidenceReference, Feedback, GeneratedAnswer, HumanReview, KnowledgeSource,
    Notification, Project, ProjectMembership, Question, QuestionStatusHistory, Team,
)
from .schemas import DelegationUpdate, FeedbackCreate, HumanAnswer, QuestionCreate, Revocation
from .seed import seed_demo
from .workflow import approve_knowledge, create_question, human_answer, process_due_questions, transition

DEFAULT_DB = "sqlite:///./backend/data/human_api_demo.db"
ACTIVE_QUESTION_STATES = {"CREATED", "WAITING_FOR_HUMAN", "DELEGATION_ELIGIBLE",
                          "AUTHORIZATION_CHECK", "KNOWLEDGE_RETRIEVAL", "EVIDENCE_VALIDATION"}
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def _session_user(session: Session, user_id: str) -> Employee:
    employee = session.get(Employee, user_id)
    if not employee or not employee.active:
        raise HTTPException(status_code=401, detail="Unknown or inactive demo identity.")
    return employee


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    normalized = as_utc(value)
    return normalized.isoformat() if normalized else None


def _question_dict(session: Session, question: Question, actor: Employee) -> dict:
    if not can_view_question(session, actor.id, question):
        raise HTTPException(status_code=404, detail="Question not found.")
    project = session.get(Project, question.project_id)
    owner = session.get(Employee, question.owner_id)
    requester = session.get(Employee, question.requester_id)
    answer = session.scalar(select(GeneratedAnswer).where(GeneratedAnswer.question_id == question.id))
    validation = session.scalar(select(AnswerValidation).where(AnswerValidation.question_id == question.id))
    human = session.scalars(select(HumanReview).where(
        HumanReview.question_id == question.id).order_by(HumanReview.created_at.desc())).first()
    entry = session.scalars(select(ApprovedKnowledgeEntry).where(
        ApprovedKnowledgeEntry.question_id == question.id).order_by(ApprovedKnowledgeEntry.created_at.desc())).first()
    citations = []
    answer_text = answer.answer_text if answer else None
    answer_type = answer.answer_type if answer else None
    answer_origin = ("Superseded by a human response" if answer and answer.answer_type == "SUPERSEDED"
                     else "AI-generated · deterministic evidence demo" if answer else None)
    evidence_refs = session.scalars(select(EvidenceReference).where(
        EvidenceReference.answer_id == answer.id)).all() if answer else []
    allowed_all = True
    for reference in evidence_refs:
        document = session.get(Document, reference.document_id)
        if not document or not may_read_document(session, actor.id, document):
            allowed_all = False
            continue
        citations.append({"document_id": document.id, "title": document.title,
                          "version": reference.document_version, "passage": reference.passage,
                          "updated_at": _iso(document.created_at)})
    if evidence_refs and not allowed_all:
        # Revalidation protects cached responses and citation metadata after access revocation.
        answer_text = "Access to one or more sources has changed. This earlier response is no longer available."
        answer_type = "ACCESS_DENIED"
        answer_origin = "Access revalidated"
        citations = []
    if question.status == "ACCESS_DENIED":
        answer_text = "I can't answer this request under the current access policy."
        answer_type = "ACCESS_DENIED"
        answer_origin = "Policy decision"
        citations = []
    return {
        "id": question.id, "question": question.question_text,
        "requester": {"id": requester.id, "name": requester.name} if requester else None,
        "owner": {"id": owner.id, "name": owner.name} if owner else None,
        "project": {"id": project.id, "name": project.name} if project else None,
        "topic": question.topic, "status": question.status, "mode": question.mode,
        "urgency": question.urgency, "created_at": _iso(question.created_at),
        "response_deadline": _iso(question.response_deadline),
        "answer": answer_text, "answer_type": answer_type, "answer_origin": answer_origin,
        "validation": {"outcome": validation.outcome, "reasons": validation.reasons}
        if validation else None,
        "evidence": citations,
        "human_answer": human.response_text if human else None,
        "knowledge_entry": {"id": entry.id, "status": entry.status} if entry else None,
        "feedback": [{"rating": f.rating, "note": f.note}
                     for f in session.scalars(select(Feedback).where(
                         Feedback.question_id == question.id, Feedback.actor_id == actor.id)).all()],
    }


def create_app(database_url: str | None = None, scheduler_enabled: bool | None = None) -> FastAPI:
    db_url = database_url or os.getenv("DATABASE_URL", DEFAULT_DB)
    mode = os.getenv("APP_MODE", "demo").lower()
    run_scheduler = scheduler_enabled if scheduler_enabled is not None else os.getenv("DISABLE_SCHEDULER") != "true"
    if db_url.startswith("sqlite:///") and not db_url.endswith(":memory:"):
        path_part = db_url.removeprefix("sqlite:///")
        Path(path_part).parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(db_url)
    factory = make_session_factory(engine)
    scheduler_task: asyncio.Task | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal scheduler_task
        initialize(engine)
        if app.state.mode == "demo":
            with factory() as session:
                seed_demo(session)
        if run_scheduler and app.state.mode == "demo":
            async def scan_due() -> None:
                while True:
                    try:
                        with factory() as session:
                            process_due_questions(session)
                    except Exception:
                        # The durable pending rows remain in the database and will be retried.
                        pass
                    await asyncio.sleep(3)
            scheduler_task = asyncio.create_task(scan_due())
        yield
        if scheduler_task:
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass
        engine.dispose()

    app = FastAPI(title="Human API", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    app.state.session_factory = factory
    app.state.mode = mode

    def get_session():
        with factory() as session:
            yield session

    def current_actor(request: Request, x_demo_user: Annotated[str | None, Header()] = None,
                      authorization: Annotated[str | None, Header()] = None,
                      session: Session = Depends(get_session)) -> Employee:
        if request.app.state.mode == "demo":
            if not x_demo_user:
                raise HTTPException(status_code=401, detail="Choose a synthetic demo identity to continue.")
            return _session_user(session, x_demo_user)
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="A validated Entra access token is required.")
        try:
            if not getattr(request.app.state, "entra_validator", None):
                settings = EntraSettings.from_env()
                request.app.state.entra_settings = settings
                request.app.state.entra_validator = EntraTokenValidator(settings)
            raw_token = authorization.split(None, 1)[1]
            claims = request.app.state.entra_validator.validate(raw_token)
        except IdentityConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except TokenRejected as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        employee = session.scalar(select(Employee).where(
            Employee.entra_oid == claims["oid"], Employee.active.is_(True)))
        if not employee:
            raise HTTPException(status_code=403, detail="This organization identity is not provisioned for Human API.")
        request.state.validated_user_assertion = raw_token
        return employee

    @app.get("/api/health")
    def health():
        return {"ok": True, "mode": app.state.mode, "connectors": "simulated"}

    @app.get("/api/session")
    def get_session_info(actor: Employee = Depends(current_actor)):
        return {"id": actor.id, "name": actor.name, "role": actor.role,
                "team_id": actor.team_id, "mode": app.state.mode,
                "identity_notice": ("Synthetic demo identity; this is not Entra authentication."
                                    if app.state.mode == "demo" else "Authenticated with a validated Entra access token.")}

    @app.get("/api/reference")
    def reference(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        project_ids = session.scalars(select(ProjectMembership.project_id).where(
            ProjectMembership.employee_id == actor.id, ProjectMembership.active.is_(True))).all()
        projects = session.scalars(select(Project).where(Project.id.in_(project_ids), Project.active.is_(True))).all() if project_ids else []
        return {"projects": [{"id": p.id, "name": p.name} for p in projects],
                "employees": [{"id": e.id, "name": e.name, "role": e.role,
                               "availability": e.availability, "availability_is_simulated": True}
                              for e in session.scalars(select(Employee).where(Employee.active.is_(True))).all()],
                "presence_notice": "Presence is fictional demo data. Busy status is never a delegation signal."}

    @app.get("/api/dashboard")
    def dashboard(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        if is_security_admin(actor):
            rows = session.execute(select(Question.status, func.count()).group_by(Question.status)).all()
            metrics = {status.lower(): count for status, count in rows}
            return {"scope": "organization aggregates only", "metrics": metrics,
                    "recent_questions": [], "pending_notifications": 0,
                    "delegation_enabled": None}
        own = session.scalars(select(Question).where(
            (Question.requester_id == actor.id) | (Question.owner_id == actor.id)
        ).order_by(Question.created_at.desc()).limit(8)).all()
        all_own = session.scalars(select(Question).where(
            (Question.requester_id == actor.id) | (Question.owner_id == actor.id))).all()
        counts: dict[str, int] = {}
        for item in all_own:
            counts[item.status] = counts.get(item.status, 0) + 1
        policy = session.get(DelegationPolicy, actor.id)
        notifications = session.scalar(select(func.count()).select_from(Notification).where(
            Notification.recipient_id == actor.id, Notification.delivered_at.is_(None))) or 0
        return {"scope": "your questions and direct delegations", "metrics": counts,
                "recent_questions": [_question_dict(session, q, actor) for q in own],
                "pending_notifications": notifications,
                "delegation_enabled": policy.enabled if policy else False,
                "simulated_presence": actor.availability}

    @app.get("/api/questions")
    def list_questions(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        questions = session.scalars(select(Question).where(
            (Question.requester_id == actor.id) | (Question.owner_id == actor.id)
        ).order_by(Question.created_at.desc()).limit(100)).all()
        return [_question_dict(session, q, actor) for q in questions]

    @app.post("/api/questions", status_code=201)
    def ask_question(body: QuestionCreate, request: Request,
                     actor: Employee = Depends(current_actor), session: Session = Depends(get_session),
                     idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None):
        if app.state.mode != "demo":
            raise HTTPException(status_code=503,
                                detail="Enterprise Graph retrieval is an adapter contract only in this MVP; use demo mode.")
        if len(idempotency_key or "") > 120:
            raise HTTPException(status_code=422, detail="Idempotency-Key is too long.")
        try:
            q = create_question(session, actor.id, body.owner_id, body.project_id,
                                body.question, body.urgency, idempotency_key)
        except PermissionError as exc:
            session.rollback()
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception:
            session.rollback()
            raise
        return _question_dict(session, q, actor)

    @app.get("/api/questions/{question_id}")
    def get_question(question_id: str, actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        question = session.get(Question, question_id)
        if not question or not can_view_question(session, actor.id, question):
            raise HTTPException(status_code=404, detail="Question not found.")
        return _question_dict(session, question, actor)

    @app.post("/api/questions/{question_id}/answer")
    def answer_question(question_id: str, body: HumanAnswer,
                        actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        question = session.get(Question, question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found.")
        try:
            human_answer(session, question, actor, body.answer)
            session.commit()
        except PermissionError as exc:
            session.rollback()
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _question_dict(session, question, actor)

    @app.post("/api/questions/{question_id}/feedback")
    def feedback(question_id: str, body: FeedbackCreate,
                 actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        question = session.get(Question, question_id)
        if not question or question.requester_id != actor.id:
            raise HTTPException(status_code=404, detail="Question not found.")
        session.add(Feedback(question_id=question.id, actor_id=actor.id, rating=body.rating,
                             note=body.note, created_at=utc_now()))
        record(session, actor.id, "answer.feedback", "question", question.id, "allow",
               {"rating": body.rating})
        session.commit()
        return {"saved": True}

    @app.get("/api/delegation")
    def get_delegation(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        policy = session.get(DelegationPolicy, actor.id)
        if not policy:
            raise HTTPException(status_code=404, detail="No delegation profile exists for this identity.")
        return _policy_dict(session, policy)

    def _policy_dict(session: Session, policy: DelegationPolicy) -> dict:
        return {"owner_id": policy.owner_id, "enabled": policy.enabled,
                "starts_at": _iso(policy.starts_at), "ends_at": _iso(policy.ends_at),
                "timeout_minutes": policy.timeout_minutes, "project_ids": policy.project_ids,
                "topics": policy.topics, "audience_ids": policy.audience_ids,
                "source_ids": policy.source_ids, "backup_id": policy.backup_id,
                "version": policy.version, "manager_approved": policy.manager_approved,
                "currently_active": policy_is_active(policy)}

    @app.get("/api/delegation/options")
    def delegation_options(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        own_projects = session.scalars(select(ProjectMembership.project_id).where(
            ProjectMembership.employee_id == actor.id, ProjectMembership.active.is_(True))).all()
        projects = session.scalars(select(Project).where(Project.id.in_(own_projects))).all() if own_projects else []
        people = session.scalars(select(Employee).where(Employee.id != actor.id,
                                                        Employee.active.is_(True))).all()
        memberships = {(m.employee_id, m.project_id) for m in session.scalars(select(ProjectMembership).where(
            ProjectMembership.active.is_(True))).all()}
        sources = session.scalars(select(KnowledgeSource).where(
            KnowledgeSource.project_id.in_(own_projects), KnowledgeSource.approved.is_(True),
            KnowledgeSource.active.is_(True))).all() if own_projects else []
        visible_sources = []
        for source in sources:
            docs = session.scalars(select(Document).where(Document.source_id == source.id,
                                                           Document.active.is_(True))).all()
            if any(may_read_document(session, actor.id, doc) for doc in docs):
                visible_sources.append({"id": source.id, "name": source.name,
                                        "project_id": source.project_id})
        return {"projects": [{"id": p.id, "name": p.name} for p in projects],
                "audiences": [{"id": e.id, "name": e.name, "role": e.role}
                              for e in people if any((e.id, pid) in memberships for pid in own_projects)],
                "backups": [{"id": e.id, "name": e.name, "role": e.role}
                            for e in people if any((e.id, pid) in memberships for pid in own_projects)],
                "sources": visible_sources}

    @app.put("/api/delegation")
    def update_delegation(body: DelegationUpdate,
                          actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        policy = session.get(DelegationPolicy, actor.id)
        if not policy:
            raise HTTPException(status_code=404, detail="No delegation profile exists for this identity.")
        owner_projects = set(session.scalars(select(ProjectMembership.project_id).where(
            ProjectMembership.employee_id == actor.id, ProjectMembership.active.is_(True))).all())
        if not set(body.project_ids) <= owner_projects:
            raise HTTPException(status_code=403, detail="A selected project is outside your active membership.")
        if body.backup_id and not any(is_project_member(session, body.backup_id, p) for p in body.project_ids):
            raise HTTPException(status_code=422, detail="The backup expert must be assigned to an approved project.")
        valid_audience = set()
        for user_id in body.audience_ids:
            if any(is_project_member(session, user_id, p) for p in body.project_ids):
                valid_audience.add(user_id)
        if len(valid_audience) != len(set(body.audience_ids)):
            raise HTTPException(status_code=403, detail="An audience member is outside the approved project scope.")
        permitted_sources = set()
        for source_id in body.source_ids:
            source = session.get(KnowledgeSource, source_id)
            if not source or not source.active or not source.approved or source.project_id not in body.project_ids:
                raise HTTPException(status_code=403, detail="A selected source is outside the approved project scope.")
            docs = session.scalars(select(Document).where(Document.source_id == source_id,
                                                           Document.active.is_(True))).all()
            if not any(may_read_document(session, actor.id, doc) for doc in docs):
                raise HTTPException(status_code=403, detail="A selected source is not accessible to you.")
            permitted_sources.add(source_id)
        scope_changed = (policy.enabled != body.enabled or policy.timeout_minutes != body.timeout_minutes
                         or policy.project_ids != body.project_ids or policy.topics != body.topics
                         or policy.audience_ids != sorted(valid_audience)
                         or policy.source_ids != sorted(permitted_sources) or policy.backup_id != body.backup_id)
        policy.enabled = body.enabled
        policy.starts_at = datetime.fromisoformat(body.starts_at.replace("Z", "+00:00")) if body.starts_at else None
        policy.ends_at = datetime.fromisoformat(body.ends_at.replace("Z", "+00:00")) if body.ends_at else None
        if policy.starts_at and policy.ends_at and as_utc(policy.ends_at) <= as_utc(policy.starts_at):
            raise HTTPException(status_code=422, detail="Delegation end must follow its start.")
        policy.timeout_minutes = body.timeout_minutes
        policy.project_ids = body.project_ids
        policy.topics = body.topics
        policy.audience_ids = sorted(valid_audience)
        policy.source_ids = sorted(permitted_sources)
        policy.backup_id = body.backup_id
        policy.version += 1
        if scope_changed:
            policy.manager_approved = False
        policy.consented_at = utc_now() if body.enabled else None
        record(session, actor.id, "delegation.policy_update", "delegation_policy", actor.id, "allow",
               {"version": policy.version, "enabled": policy.enabled,
                "project_count": len(policy.project_ids), "source_count": len(policy.source_ids)})
        session.commit()
        return _policy_dict(session, policy)

    @app.get("/api/delegation/pending")
    def pending_delegations(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        if not (is_team_manager(actor) or is_security_admin(actor)):
            raise HTTPException(status_code=403, detail="Manager or security administrator role required.")
        result = []
        for policy in session.scalars(select(DelegationPolicy).where(
            DelegationPolicy.enabled.is_(True), DelegationPolicy.manager_approved.is_(False)
        )).all():
            owner = session.get(Employee, policy.owner_id)
            if owner and (is_security_admin(actor) or actor.team_id == owner.team_id):
                result.append({"owner_id": owner.id, "owner_name": owner.name,
                               "version": policy.version, "project_count": len(policy.project_ids or []),
                               "source_count": len(policy.source_ids or []),
                               "audience_count": len(policy.audience_ids or []),
                               "timeout_minutes": policy.timeout_minutes})
        return result

    @app.post("/api/delegation/{owner_id}/approve")
    def approve_delegation(owner_id: str, actor: Employee = Depends(current_actor),
                           session: Session = Depends(get_session)):
        owner = session.get(Employee, owner_id)
        policy = session.get(DelegationPolicy, owner_id)
        if not owner or not policy:
            raise HTTPException(status_code=404, detail="Delegation policy not found.")
        if not (is_security_admin(actor) or (is_team_manager(actor) and actor.team_id == owner.team_id)):
            raise HTTPException(status_code=403, detail="Only the project team manager or security administrator can approve this policy.")
        if not policy.enabled:
            raise HTTPException(status_code=409, detail="A paused delegation policy cannot be approved.")
        policy.manager_approved = True
        record(session, actor.id, "delegation.policy_approve", "delegation_policy", owner_id,
               "allow", {"version": policy.version})
        session.flush()
        queued = session.scalars(select(Question).where(
            Question.owner_id == owner_id,
            Question.status.in_(["CREATED", "WAITING_FOR_HUMAN"]),
        ).order_by(Question.created_at).limit(100)).all()
        from .workflow import process_question
        for question in queued:
            process_question(session, question, actor_id=actor.id)
        session.commit()
        return _policy_dict(session, policy)

    @app.get("/api/escalations")
    def escalations(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        records = session.scalars(select(Escalation).where(
            (Escalation.assignee_id == actor.id) | (Escalation.question_id.in_(
                select(Question.id).where(Question.owner_id == actor.id)))
        ).order_by(Escalation.created_at.desc())).all()
        output = []
        for item in records:
            question = session.get(Question, item.question_id)
            output.append({"id": item.id, "question_id": item.question_id,
                           "reason": item.reason, "status": item.status,
                           "assignee_id": item.assignee_id,
                           "question": _question_dict(session, question, actor) if question else None})
        return output

    @app.get("/api/knowledge/pending")
    def pending_knowledge(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        entries = session.scalars(select(ApprovedKnowledgeEntry).where(
            ApprovedKnowledgeEntry.status == "PENDING_APPROVAL").order_by(
                ApprovedKnowledgeEntry.created_at.desc())).all()
        result = []
        for entry in entries:
            question = session.get(Question, entry.question_id)
            project = session.get(Project, entry.project_id)
            if not question or not project:
                continue
            allowed = actor.id == question.owner_id or (
                is_team_manager(actor) and actor.team_id == project.team_id
            )
            if allowed:
                result.append({"id": entry.id, "question_id": entry.question_id,
                               "project_id": entry.project_id, "project_name": project.name,
                               "content": entry.content, "created_by": entry.created_by,
                               "created_at": _iso(entry.created_at)})
        return result

    @app.post("/api/knowledge/{entry_id}/approve")
    def approve_entry(entry_id: str, actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        try:
            approve_knowledge(session, entry_id, actor)
            session.commit()
        except LookupError as exc:
            session.rollback()
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            session.rollback()
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"approved": True, "entry_id": entry_id}

    @app.get("/api/governance")
    def governance(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        if not is_security_admin(actor):
            raise HTTPException(status_code=403, detail="Security administrator role required.")
        rows = session.execute(select(Question.status, func.count()).group_by(Question.status)).all()
        events = session.scalars(select(QuestionStatusHistory).order_by(
            QuestionStatusHistory.created_at.desc()).limit(25)).all()
        return {"counts": {status: count for status, count in rows},
                "delegations": [{"owner_id": policy.owner_id, "enabled": policy.enabled,
                                 "version": policy.version,
                                 "project_count": len(policy.project_ids or []),
                                 "source_count": len(policy.source_ids or []),
                                 "manager_approved": policy.manager_approved}
                                for policy in session.scalars(select(DelegationPolicy)).all()],
                "audit_events": [{"action": e.to_status, "resource_type": "question",
                                  "resource_id": str(e.question_id), "actor_id": e.actor_id,
                                  "at": _iso(e.created_at)} for e in events],
                "note": "Aggregate and audit metadata only; this view does not grant question or document access."}

    @app.post("/api/governance/revoke")
    def revoke_access(body: Revocation,
                      actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        if not is_security_admin(actor):
            raise HTTPException(status_code=403, detail="Security administrator role required.")
        membership = session.scalar(select(ProjectMembership).where(
            ProjectMembership.employee_id == body.employee_id,
            ProjectMembership.project_id == body.project_id,
            ProjectMembership.active.is_(True)))
        if not membership:
            raise HTTPException(status_code=404, detail="Active project access was not found.")
        membership.active = False
        affected = session.scalars(select(Question).where(
            Question.requester_id == body.employee_id,
            Question.project_id == body.project_id,
            Question.status.in_(["AI_ANSWERED", "HUMAN_REVIEW_REQUIRED", "WAITING_FOR_HUMAN"])
        )).all()
        for question in affected:
            transition(session, question, "ACCESS_DENIED", "Requester access was revoked.", actor.id)
            answer = session.scalar(select(GeneratedAnswer).where(GeneratedAnswer.question_id == question.id))
            if answer:
                answer.answer_text = "I can't answer this request under the current access policy."
                answer.answer_type = "ACCESS_DENIED"
            escalation = session.scalar(select(Escalation).where(Escalation.question_id == question.id))
            if escalation and escalation.status == "OPEN":
                escalation.status = "CANCELED"
                escalation.resolved_at = utc_now()
        record(session, actor.id, "access.revoke", "project_membership",
               f"{body.employee_id}:{body.project_id}", "allow", {"affected_question_count": len(affected)})
        session.commit()
        return {"revoked": True, "affected_question_count": len(affected)}

    @app.get("/api/notifications")
    def notifications(actor: Employee = Depends(current_actor), session: Session = Depends(get_session)):
        items = session.scalars(select(Notification).where(
            Notification.recipient_id == actor.id).order_by(Notification.created_at.desc()).limit(20)).all()
        return [{"id": n.id, "kind": n.kind, "message": n.message,
                 "question_id": n.question_id, "created_at": _iso(n.created_at)} for n in items]

    @app.get("/")
    def frontend():
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(index)
        return {"name": "Human API", "message": "Run `make dev` to start the Vite frontend."}

    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    return app


app = create_app()
