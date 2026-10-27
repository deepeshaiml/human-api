from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from human_api.delegation import utc_now
from human_api.models import (
    ApprovedKnowledgeEntry, Document, DurableJob, EvidenceReference, GeneratedAnswer,
    Question, QuestionStatusHistory,
)
from human_api.workflow import process_due_questions
from conftest import headers


TIMEOUT_QUESTION = "Why was the Project Alpha startup timeout increased to 120 seconds, and is it still required?"


def ask(client, question: str = TIMEOUT_QUESTION, owner: str = "bob"):
    return client.post("/api/questions", headers=headers("alice"), json={
        "owner_id": owner, "project_id": "alpha", "question": question,
    })


def test_idempotency_key_returns_the_original_question(client):
    payload = {"owner_id": "bob", "project_id": "alpha", "question": TIMEOUT_QUESTION}
    first = client.post("/api/questions", headers={**headers("alice"), "Idempotency-Key": "demo-once"},
                        json=payload)
    second = client.post("/api/questions", headers={**headers("alice"), "Idempotency-Key": "demo-once"},
                         json=payload)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_pending_deadline_job_survives_application_restart(tmp_path):
    from fastapi.testclient import TestClient
    from human_api.main import create_app
    from human_api.models import Employee

    database_url = f"sqlite:///{tmp_path / 'restart_demo.db'}"
    first_app = create_app(database_url, scheduler_enabled=False)
    with TestClient(first_app) as first_client:
        with first_app.state.session_factory() as session:
            session.get(Employee, "bob").availability = "available"
            session.commit()
        created = ask(first_client).json()
        assert created["status"] == "WAITING_FOR_HUMAN"

    restarted_app = create_app(database_url, scheduler_enabled=False)
    with TestClient(restarted_app) as restarted_client:
        with restarted_app.state.session_factory() as session:
            bob = session.get(Employee, "bob")
            bob.availability = "out_of_office"
            session.commit()
            assert process_due_questions(session, utc_now()) == 1
        result = restarted_client.get(f"/api/questions/{created['id']}", headers=headers("alice"))
        assert result.status_code == 200
        assert result.json()["status"] == "AI_ANSWERED"


def test_out_of_office_answer_is_partial_and_cites_authorized_adr(client):
    response = ask(client)
    assert response.status_code == 201
    item = response.json()
    assert item["status"] == "AI_ANSWERED"
    assert item["answer_type"] == "PARTIAL"
    assert "not establish whether the value is still required" in item["answer"]
    assert item["answer_origin"].startswith("AI-generated")
    assert [source["document_id"] for source in item["evidence"]] == ["ADR-024"]
    assert "written by Bob" not in item["answer"]


def test_restricted_finance_question_denies_without_titles_or_snippets(client):
    response = ask(client, "What is the confidential budget for Project Alpha?")
    assert response.status_code == 201
    item = response.json()
    assert item["status"] == "ACCESS_DENIED"
    assert item["evidence"] == []
    assert item["answer_type"] == "ACCESS_DENIED"
    assert "AED" not in item["answer"]
    assert "FIN-004" not in str(item)
    assert "1,250,000" not in str(item)


def test_insufficient_evidence_routes_to_backup(client):
    response = ask(client, "Why was the undocumented blue deployment approval skipped?")
    item = response.json()
    assert item["status"] == "HUMAN_REVIEW_REQUIRED"
    assert item["answer_type"] == "REQUIRES_CLARIFICATION"
    assert item["evidence"] == []
    inbox = client.get("/api/escalations", headers=headers("carla"))
    assert inbox.status_code == 200
    assert any(row["question_id"] == item["id"] and row["assignee_id"] == "carla"
               for row in inbox.json())


def test_conflicting_sources_require_human_clarification(client):
    response = ask(client, "What is the current Project Alpha startup timeout value?")
    item = response.json()
    assert item["status"] == "HUMAN_REVIEW_REQUIRED"
    assert item["validation"]["outcome"] == "CONFLICTS"
    assert "120, 180 seconds" in item["answer"]
    assert {source["document_id"] for source in item["evidence"]} == {"ADR-024", "RUN-018"}


def test_human_answer_before_deadline_cancels_durable_ai_job(client, app):
    created = ask(client, "Can you verify the release handover path for this service?", owner="carla").json()
    assert created["status"] == "WAITING_FOR_HUMAN"
    answer = client.post(f"/api/questions/{created['id']}/answer", headers=headers("carla"),
                         json={"answer": "Carla confirms the platform backup owns release handover."})
    assert answer.status_code == 200
    assert answer.json()["status"] == "RESOLVED"
    with app.state.session_factory() as session:
        job = session.scalar(select(DurableJob).where(DurableJob.question_id == created["id"]))
        question = session.get(Question, created["id"])
        assert job.status == "CANCELLED"
        question.response_deadline = utc_now() - timedelta(seconds=1)
        session.commit()
        assert process_due_questions(session, utc_now()) == 0
        assert session.scalar(select(GeneratedAnswer).where(
            GeneratedAnswer.question_id == created["id"])) is None
        assert question.status == "RESOLVED"


def test_expert_correction_is_not_retrievable_until_owner_approves(client):
    unsupported = ask(client, "Why was the undocumented blue deployment approval skipped?").json()
    reply = client.post(f"/api/questions/{unsupported['id']}/answer", headers=headers("carla"),
                        json={"answer": "The approval was skipped because the staging credential expired; Bob approved a retry after the credential was rotated."})
    assert reply.status_code == 200
    entry = reply.json()["knowledge_entry"]
    assert entry["status"] == "PENDING_APPROVAL"
    assert client.post(f"/api/knowledge/{entry['id']}/approve", headers=headers("carla")).status_code == 403

    before = ask(client, "Why was the undocumented blue deployment approval skipped?")
    assert before.json()["status"] == "HUMAN_REVIEW_REQUIRED"
    published = client.post(f"/api/knowledge/{entry['id']}/approve", headers=headers("bob"))
    assert published.status_code == 200
    after = ask(client, "Why was the undocumented blue deployment approval skipped?")
    assert after.json()["status"] == "AI_ANSWERED"
    assert "staging credential expired" in after.json()["answer"]
    assert after.json()["evidence"][0]["title"] == "Approved expert correction"


def test_project_revocation_invalidates_cached_answer_and_admin_cannot_read_content(client):
    item = ask(client).json()
    denied = client.get(f"/api/questions/{item['id']}", headers=headers("hadi"))
    assert denied.status_code == 404
    result = client.post("/api/governance/revoke", headers=headers("hadi"),
                         json={"employee_id": "alice", "project_id": "alpha"})
    assert result.status_code == 200
    updated = client.get(f"/api/questions/{item['id']}", headers=headers("alice")).json()
    assert updated["status"] == "ACCESS_DENIED"
    assert updated["evidence"] == []
    assert updated["answer_type"] == "ACCESS_DENIED"
    assert "ADR-024" not in str(updated)


def test_user_cannot_read_another_requesters_question(client):
    item = ask(client).json()
    response = client.get(f"/api/questions/{item['id']}", headers=headers("george"))
    assert response.status_code == 404


def test_delegation_scope_change_waits_for_manager_approval(client):
    policy = client.get("/api/delegation", headers=headers("bob")).json()
    options = client.get("/api/delegation/options", headers=headers("bob")).json()
    changed = {
        **policy,
        "enabled": True,
        "project_ids": ["alpha"],
        "source_ids": [item["id"] for item in options["sources"] if item["project_id"] == "alpha"],
        "audience_ids": ["alice"],
        "topics": ["deployment", "release", "timeout"],
        "timeout_minutes": 30,
        "backup_id": "carla",
    }
    response = client.put("/api/delegation", headers=headers("bob"), json=changed)
    assert response.status_code == 200
    assert response.json()["manager_approved"] is False
    waiting = ask(client).json()
    assert waiting["status"] == "WAITING_FOR_HUMAN"
    assert client.get("/api/delegation/pending", headers=headers("alice")).status_code == 403
    pending = client.get("/api/delegation/pending", headers=headers("dinesh")).json()
    assert any(item["owner_id"] == "bob" for item in pending)
    approved = client.post("/api/delegation/bob/approve", headers=headers("dinesh"))
    assert approved.status_code == 200
    assert approved.json()["manager_approved"] is True
    resolved = client.get(f"/api/questions/{waiting['id']}", headers=headers("alice")).json()
    assert resolved["status"] == "AI_ANSWERED"


def test_durable_retry_limit_escalates_without_infinite_retries(client, app, monkeypatch):
    created = ask(client, "Can you confirm who owns the release handover?", owner="carla").json()
    with app.state.session_factory() as session:
        question = session.get(Question, created["id"])
        job = session.scalar(select(DurableJob).where(DurableJob.question_id == created["id"]))
        question.response_deadline = utc_now() - timedelta(seconds=1)
        job.run_at = question.response_deadline
        job.next_attempt_at = question.response_deadline
        session.commit()

    import human_api.workflow as workflow
    def fail(*_args, **_kwargs):
        raise RuntimeError("synthetic downstream failure")
    monkeypatch.setattr(workflow, "process_question", fail)
    with app.state.session_factory() as session:
        now = utc_now()
        for _ in range(5):
            workflow.process_due_questions(session, now)
            now += timedelta(minutes=5)
        job = session.scalar(select(DurableJob).where(DurableJob.question_id == created["id"]))
        assert job.attempts == job.max_attempts == 5
        assert job.status == "FAILED"
        assert job.last_error_code == "RuntimeError"
        question = session.get(Question, created["id"])
        assert question.status == "HUMAN_REVIEW_REQUIRED"
