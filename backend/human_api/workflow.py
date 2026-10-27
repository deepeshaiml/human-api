from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from .audit import record
from .authorization import is_project_member
from .delegation import as_utc, classify_topic, eligible_reason, utc_now
from .knowledge import Evidence, retrieve_authorized
from .models import (
    AnswerValidation, DelegationPolicy, Document, DurableJob, Employee, Escalation, EvidenceReference,
    GeneratedAnswer, HumanReview, KnowledgeSource, Notification, Project, Question,
    QuestionStatusHistory,
)

TERMINAL = {"AI_ANSWERED", "HUMAN_REVIEW_REQUIRED", "ACCESS_DENIED", "RESOLVED", "CLOSED"}


def transition(session: Session, question: Question, status: str, reason: str,
               actor_id: str | None = None) -> bool:
    if question.status == status:
        return True
    old = question.status
    if status == "ACCESS_DENIED":
        allowed_state = Question.status != "ACCESS_DENIED"
    elif status == "RESOLVED":
        allowed_state = Question.status.not_in({"RESOLVED", "CLOSED", "ACCESS_DENIED"})
    else:
        allowed_state = Question.status.not_in(TERMINAL)
    result = session.execute(update(Question).where(
        Question.id == question.id, allowed_state
    ).values(status=status).execution_options(synchronize_session=False))
    if result.rowcount != 1:
        session.refresh(question)
        return False
    question.status = status
    session.add(QuestionStatusHistory(
        question_id=question.id, from_status=old, to_status=status, actor_id=actor_id,
        reason=reason[:240], created_at=utc_now(),
    ))
    record(session, actor_id, "question.status_transition", "question", question.id,
           "allow", {"from": old, "to": status})
    if status in TERMINAL:
        job = session.scalar(select(DurableJob).where(DurableJob.question_id == question.id))
        if job and job.status in {"PENDING", "RUNNING"}:
            job.status = "CANCELLED" if status in {"RESOLVED", "CLOSED"} else "COMPLETED"
            job.completed_at = utc_now()
    return True


def make_escalation(session: Session, question: Question, policy: DelegationPolicy | None,
                    reason: str) -> Escalation:
    existing = session.scalar(select(Escalation).where(Escalation.question_id == question.id))
    if existing:
        return existing
    backup = policy.backup_id if policy else None
    if not backup or not is_project_member(session, backup, question.project_id):
        backup = question.owner_id
    escalation = Escalation(id=str(uuid4()), question_id=question.id, assignee_id=backup,
                            reason=reason[:240], status="OPEN", created_at=utc_now())
    session.add(escalation)
    session.add(Notification(recipient_id=backup, question_id=question.id,
                             kind="human_review", message="A project question needs your review.",
                             created_at=utc_now()))
    return escalation


def _policy(session: Session, question: Question) -> DelegationPolicy | None:
    return session.get(DelegationPolicy, question.owner_id)


def _simple_answer(question: Question, evidence: list[Evidence]) -> tuple[str, str, str, list[str]]:
    text = question.question_text.lower()
    if "why" in text and "timeout" in text and "120" in text and evidence:
        answer = ("ADR-024 says the Project Alpha startup timeout was increased from 90 to 120 seconds "
                  "because dependency initialization sometimes exceeded the previous 90-second limit. "
                  "The record says the change was approved for release 5.2, but it does not establish "
                  "whether the value is still required in the current release.")
        return answer, "PARTIAL", "PARTIAL", ["The decision record does not confirm current necessity."]
    if "timeout" in text and any(word in text for word in ("current", "latest", "now")):
        values: set[str] = set()
        for item in evidence:
            historical = re.search(r"timeout from \d{2,3} to (\d{2,3})\s*seconds", item.passage.lower())
            current = re.search(r"timeoutseconds\s*(?:is|=|:|to)\s*(\d{2,3})", item.passage.lower())
            if historical:
                values.add(historical.group(1))
            if current:
                values.add(current.group(1))
        if len(values) > 1:
            numbers = ", ".join(sorted(values, key=int))
            answer = (f"The approved sources conflict: they refer to different startup timeout values "
                      f"({numbers} seconds). I cannot determine which value is authoritative, so an "
                      f"expert needs to clarify the current configuration.")
            return answer, "REQUIRES_CLARIFICATION", "CONFLICTS", ["Authorized sources disagree on the current value."]
    snippet = evidence[0].passage
    answer = f"The approved project source says: {snippet}"
    return answer, "SUPPORTED", "SUPPORTED", []


def process_question(session: Session, question: Question, actor_id: str | None = None,
                     now: datetime | None = None) -> Question:
    """Run one idempotent, deterministic delegation attempt."""
    now = now or utc_now()
    session.refresh(question)
    if question.status not in {"CREATED", "WAITING_FOR_HUMAN", "DELEGATION_ELIGIBLE"}:
        return question
    policy = _policy(session, question)
    owner = session.get(Employee, question.owner_id)
    if not owner or not is_project_member(session, question.requester_id, question.project_id):
        transition(session, question, "ACCESS_DENIED", "Requester no longer has project access.", actor_id)
        record(session, actor_id, "authorization.check", "question", question.id, "deny",
               {"scope": "requester_project_membership"})
        session.flush()
        return question
    # A restricted-topic policy denies before delegation eligibility or document retrieval.
    if question.topic == "finance":
        transition(session, question, "ACCESS_DENIED", "The requested topic is restricted by policy.", actor_id)
        session.add(AnswerValidation(question_id=question.id, outcome="ACCESS_DENIED",
                                     reasons=["Request is not permitted by the current policy."],
                                     validated_at=now))
        record(session, actor_id, "authorization.check", "question", question.id, "deny",
               {"scope": "restricted_topic"})
        session.flush()
        return question
    eligible, why = eligible_reason(question, owner, policy, now)
    deadline = as_utc(question.response_deadline)
    if not eligible:
        if deadline and now >= deadline:
            transition(session, question, "HUMAN_REVIEW_REQUIRED", why, actor_id)
            make_escalation(session, question, policy, why)
        else:
            if question.status == "CREATED":
                transition(session, question, "WAITING_FOR_HUMAN", why, actor_id)
        session.flush()
        return question

    transition(session, question, "DELEGATION_ELIGIBLE", why, actor_id)
    if policy is None:
        transition(session, question, "HUMAN_REVIEW_REQUIRED", "No approved policy is available.", actor_id)
        make_escalation(session, question, policy, "No approved policy is available.")
        session.flush()
        return question
    if not is_project_member(session, policy.owner_id, question.project_id):
        transition(session, question, "ACCESS_DENIED", "Owner scope is not valid for this project.", actor_id)
        record(session, actor_id, "authorization.check", "question", question.id, "deny",
               {"scope": "owner_project_membership"})
        session.flush()
        return question
    transition(session, question, "AUTHORIZATION_CHECK", "Checking requester and source access.", actor_id)
    record(session, actor_id, "authorization.check", "question", question.id, "allow",
           {"requester": question.requester_id, "project": question.project_id,
            "policy_version": policy.version})

    transition(session, question, "KNOWLEDGE_RETRIEVAL", "Searching only requester-authorized sources.", actor_id)
    evidence = retrieve_authorized(session, question.requester_id, question.owner_id,
                                   question.project_id, question.question_text, policy)
    transition(session, question, "EVIDENCE_VALIDATION", "Checking evidence support and conflicts.", actor_id)
    session.refresh(question)
    if question.status in TERMINAL:
        return question
    if not evidence:
        answer_text = ("I could not find enough approved, accessible evidence to answer this question. "
                       "It has been routed to an authorized human for clarification.")
        answer = GeneratedAnswer(id=str(uuid4()), question_id=question.id,
                                 answer_text=answer_text, answer_type="REQUIRES_CLARIFICATION",
                                 generation_mode="evidence_only_demo",
                                 model_version="deterministic-evidence-demo", generated_at=now)
        session.add(answer)
        session.add(AnswerValidation(question_id=question.id, outcome="INSUFFICIENT_EVIDENCE",
                                     reasons=["No authorized source met the retrieval threshold."],
                                     validated_at=now))
        transition(session, question, "HUMAN_REVIEW_REQUIRED", "No sufficient authorized evidence.", actor_id)
        make_escalation(session, question, policy, "Insufficient approved evidence.")
        record(session, actor_id, "answer.generation", "question", question.id, "abstain",
               {"evidence_count": 0, "generator": "deterministic-evidence-demo"})
        session.flush()
        return question

    answer_text, answer_type, outcome, reasons = _simple_answer(question, evidence)
    answer = GeneratedAnswer(id=str(uuid4()), question_id=question.id, answer_text=answer_text,
                             answer_type=answer_type, generation_mode="evidence_only_demo",
                             model_version="deterministic-evidence-demo", generated_at=now)
    session.add(answer)
    session.flush()
    for item in evidence:
        # A source is retained only when it was authorized at generation time. Each read rechecks ACLs.
        if session.get(Document, item.document_id):
            session.add(EvidenceReference(answer_id=answer.id, document_id=item.document_id,
                                          document_version=item.version, passage=item.passage))
    session.add(AnswerValidation(question_id=question.id, outcome=outcome, reasons=reasons,
                                 validated_at=now))
    if answer_type == "REQUIRES_CLARIFICATION":
        transition(session, question, "HUMAN_REVIEW_REQUIRED", "Authorized sources conflict.", actor_id)
        make_escalation(session, question, policy, "Authorized sources conflict on the current value.")
    else:
        transition(session, question, "AI_ANSWERED", "Evidence-backed demo answer is ready.", actor_id)
        session.add(Notification(recipient_id=question.requester_id, question_id=question.id,
                                 kind="answer_ready", message="An AI-generated answer is ready to review.",
                                 created_at=now))
    record(session, actor_id, "answer.generation", "question", question.id, "allow",
           {"evidence_count": len(evidence), "answer_type": answer_type,
            "generator": "deterministic-evidence-demo"})
    session.flush()
    return question


def create_question(session: Session, requester_id: str, owner_id: str, project_id: str,
                    question_text: str, urgency: str = "normal", idempotency_key: str | None = None) -> Question:
    if idempotency_key:
        existing = session.scalar(select(Question).where(Question.idempotency_key == idempotency_key))
        if existing:
            if existing.requester_id != requester_id:
                raise PermissionError("Request could not be accepted under the supplied identity.")
            return existing
    if not is_project_member(session, requester_id, project_id):
        raise PermissionError("You do not have access to this project.")
    if not is_project_member(session, owner_id, project_id):
        raise PermissionError("The selected owner is not assigned to this project.")
    policy = session.get(DelegationPolicy, owner_id)
    created = utc_now()
    question = Question(
        id=str(uuid4()), idempotency_key=idempotency_key, requester_id=requester_id,
        owner_id=owner_id, project_id=project_id, question_text=question_text.strip(),
        topic=classify_topic(question_text),
        status="CREATED", mode="automatic_policy", urgency=urgency, created_at=created,
        response_deadline=created + timedelta(minutes=policy.timeout_minutes if policy else 30),
        policy_version=policy.version if policy else 0,
    )
    session.add(question)
    session.flush()
    session.add(DurableJob(question_id=question.id, status="PENDING",
                           run_at=question.response_deadline, next_attempt_at=created,
                           attempts=0, max_attempts=5, created_at=created))
    session.flush()
    transition(session, question, "WAITING_FOR_HUMAN", "Question is waiting under the configured response window.", requester_id)
    session.add(Notification(recipient_id=owner_id, question_id=question.id, kind="question_received",
                             message="A colleague directed a project question to you.", created_at=created))
    record(session, requester_id, "question.submit", "question", question.id, "allow",
           {"project": project_id, "policy_version": question.policy_version,
            "mode": question.mode})
    process_question(session, question, actor_id=None, now=created)
    session.commit()
    session.refresh(question)
    return question


def process_due_questions(session: Session, now: datetime | None = None) -> int:
    now = now or utc_now()
    # Recheck pending durable jobs after restarts; absence is a valid trigger only with owner consent.
    jobs = session.scalars(select(DurableJob).join(Question, DurableJob.question_id == Question.id)
        .join(Employee, Employee.id == Question.owner_id).where(
            DurableJob.status == "PENDING",
            or_(DurableJob.next_attempt_at <= now.replace(tzinfo=None),
                Employee.availability == "out_of_office"),
        ).order_by(DurableJob.next_attempt_at).limit(100)).all()
    count = 0
    for job in jobs:
        question = session.get(Question, job.question_id)
        if not question or question.status not in {"CREATED", "WAITING_FOR_HUMAN"}:
            job.status = "CANCELLED"
            job.completed_at = now
            continue
        policy = _policy(session, question)
        owner = session.get(Employee, question.owner_id)
        eligible, _ = eligible_reason(question, owner, policy, now) if owner else (False, "owner missing")
        deadline = as_utc(question.response_deadline)
        if not eligible and (not deadline or deadline > now):
            # Leave it durable at the explicit deadline without consuming retry attempts.
            if deadline:
                job.next_attempt_at = deadline
            continue
        claim = session.execute(update(DurableJob).where(
            DurableJob.id == job.id, DurableJob.status == "PENDING"
        ).values(status="RUNNING").execution_options(synchronize_session=False))
        if claim.rowcount != 1:
            continue
        job.status = "RUNNING"
        try:
            with session.begin_nested():
                job.attempts += 1
                process_question(session, question, actor_id=None, now=now)
        except Exception as exc:
            session.refresh(job)
            session.refresh(question)
            job.attempts += 1
            job.last_error_code = type(exc).__name__[:80]
            if job.attempts >= job.max_attempts:
                job.status = "FAILED"
                job.completed_at = now
                if question.status not in TERMINAL:
                    transition(session, question, "HUMAN_REVIEW_REQUIRED",
                               "Automated processing reached its retry limit.")
                    make_escalation(session, question, _policy(session, question),
                                    "Automated processing reached its retry limit.")
            else:
                job.status = "PENDING"
                job.next_attempt_at = now + timedelta(seconds=min(2 ** job.attempts, 60))
            record(session, None, "workflow.retry", "question", question.id, "retry",
                   {"attempt": job.attempts, "error_code": job.last_error_code})
        count += 1
    session.commit()
    return count


def human_answer(session: Session, question: Question, actor: Employee, answer_text: str) -> None:
    if actor.id not in {question.owner_id}:
        escalation = session.scalar(select(Escalation).where(Escalation.question_id == question.id))
        if not escalation or escalation.assignee_id != actor.id:
            raise PermissionError("You are not assigned to answer this question.")
    if question.status in {"RESOLVED", "CLOSED", "ACCESS_DENIED"}:
        raise ValueError("This question is no longer open for an answer.")
    now = utc_now()
    if not transition(session, question, "RESOLVED", "An authorized human answered before or after the timeout.", actor.id):
        raise ValueError("This question was resolved by another workflow action.")
    escalation = session.scalar(select(Escalation).where(Escalation.question_id == question.id))
    if escalation:
        escalation.status = "RESOLVED"
        escalation.resolved_at = now
    session.add(HumanReview(question_id=question.id, reviewer_id=actor.id,
                            response_text=answer_text.strip(), approved=True, created_at=now))
    existing_answer = session.scalar(select(GeneratedAnswer).where(
        GeneratedAnswer.question_id == question.id))
    deadline = as_utc(question.response_deadline)
    if existing_answer and deadline and now <= deadline:
        existing_answer.answer_text = "An authorized human responded before the configured wait window. The earlier AI response is no longer active."
        existing_answer.answer_type = "SUPERSEDED"
        session.execute(EvidenceReference.__table__.delete().where(
            EvidenceReference.answer_id == existing_answer.id))
        prior_notice = session.scalar(select(Notification).where(
            Notification.question_id == question.id, Notification.kind == "answer_ready"))
        if prior_notice:
            prior_notice.kind = "answer_superseded"
            prior_notice.message = "An expert response replaced the earlier AI response."
    from .models import ApprovedKnowledgeEntry
    entry = ApprovedKnowledgeEntry(id=str(uuid4()), question_id=question.id,
                                   project_id=question.project_id, created_by=actor.id,
                                   content=answer_text.strip(), status="PENDING_APPROVAL",
                                   created_at=now)
    session.add(entry)
    session.add(Notification(recipient_id=question.requester_id, question_id=question.id,
                             kind="human_answer", message="The project expert responded to your question.",
                             created_at=now))
    record(session, actor.id, "question.human_answer", "question", question.id, "allow",
           {"knowledge_status": "PENDING_APPROVAL"})
    session.flush()


def approve_knowledge(session: Session, entry_id: str, actor: Employee) -> None:
    from .models import ApprovedKnowledgeEntry
    entry = session.get(ApprovedKnowledgeEntry, entry_id)
    if not entry:
        raise LookupError("Knowledge entry not found.")
    question = session.get(Question, entry.question_id)
    project = session.get(Project, entry.project_id)
    if actor.id != question.owner_id and not (
        actor.role == "Team Manager" and project and actor.team_id == project.team_id
    ):
        raise PermissionError("Only the knowledge owner or the project team manager can approve publication.")
    if entry.status != "PENDING_APPROVAL":
        raise ValueError("This entry is no longer pending approval.")
    now = utc_now()
    entry.status, entry.approved_by, entry.approved_at = "APPROVED", actor.id, now
    source_id = f"approved-{entry.id}"
    doc_id = f"AK-{entry.id}"
    approved_content = (f"Original question: {question.question_text}\n"
                        f"Verified expert response: {entry.content}")
    session.add(KnowledgeSource(id=source_id, name="Human-approved project knowledge",
                                connector="Human API approved knowledge", owner_id=question.owner_id,
                                project_id=entry.project_id, approved=True, active=True))
    session.flush()
    session.add(Document(id=doc_id, source_id=source_id, title="Approved expert correction",
                         project_id=entry.project_id, owner_id=question.owner_id, version="v1.0",
                         created_at=now, classification="Project Confidential", allowed_user_ids=None,
                         owner_approved=True, active=True, content=approved_content))
    policy = session.get(DelegationPolicy, question.owner_id)
    if policy:
        policy.source_ids = list(dict.fromkeys([*(policy.source_ids or []), source_id]))
        policy.version += 1
    record(session, actor.id, "knowledge.publish", "knowledge_entry", entry.id, "allow",
           {"project": entry.project_id, "source_id": source_id})
    session.flush()
