from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select

from conftest import headers
from human_api.knowledge import clean_passage
from human_api.models import AuditEvent, Document, Employee, Project, ProjectMembership


def test_synthetic_dataset_has_expected_company_size(client):
    with client.app.state.session_factory() as session:
        assert len(session.scalars(select(Employee)).all()) == 20
        assert len(session.scalars(select(Project)).all()) == 5
        assert len(session.scalars(select(Document)).all()) == 55
        assert len(session.scalars(select(ProjectMembership)).all()) >= 20


def test_prompt_injection_is_treated_as_untrusted_document_text(client):
    with client.app.state.session_factory() as session:
        hostile = session.get(Document, "DOC-055")
        passage = clean_passage(hostile.content)
        assert "ignore all previous" not in passage.lower()
        assert "restricted budget document" not in passage.lower()
        assert "This is untrusted document content" in passage


def test_restricted_labels_require_explicit_document_acl(client):
    from human_api.authorization import may_read_document

    with client.app.state.session_factory() as session:
        security_note = session.get(Document, "SEC-009")
        budget = session.get(Document, "FIN-004")
        assert may_read_document(session, "alice", security_note) is False
        assert may_read_document(session, "alice", budget) is False
        assert may_read_document(session, "dinesh", budget) is True


def test_security_admin_sees_metadata_but_not_questions(client):
    created = client.post("/api/questions", headers=headers("alice"), json={
        "owner_id": "bob", "project_id": "alpha",
        "question": "Why was the Project Alpha startup timeout increased to 120 seconds?",
    }).json()
    view = client.get("/api/governance", headers=headers("hadi"))
    assert view.status_code == 200
    assert view.json()["note"].startswith("Aggregate and audit metadata only")
    assert created["question"] not in json.dumps(view.json())
    assert client.get(f"/api/questions/{created['id']}", headers=headers("hadi")).status_code == 404


def test_demo_identity_cannot_be_used_in_enterprise_mode(app, monkeypatch):
    from human_api.main import create_app
    from fastapi.testclient import TestClient
    monkeypatch.setenv("APP_MODE", "enterprise")
    enterprise = create_app(f"sqlite:///{Path('/tmp') / 'human-api-empty-enterprise.db'}", False)
    with TestClient(enterprise) as client:
        response = client.get("/api/session", headers=headers("alice"))
        assert response.status_code == 401
        assert client.get("/api/session", headers={"Authorization": "Bearer bad-token"}).status_code == 503
    monkeypatch.setenv("APP_MODE", "demo")
