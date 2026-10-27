from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    DelegationPolicy, Document, Employee, KnowledgeSource, Project, ProjectMembership,
    Team,
)

SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "seed.json"


def parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value).astimezone(timezone.utc) if value else None


def seed_demo(session: Session, seed_path: Path = SEED_PATH) -> None:
    """Idempotently insert synthetic reference data into an empty demo database."""
    if session.scalar(select(Employee.id).limit(1)):
        return
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    session.add_all([Team(**row) for row in data["teams"]])
    session.flush()
    session.add_all([Employee(**row) for row in data["employees"]])
    session.add_all([Project(**row) for row in data["projects"]])
    session.flush()
    session.add_all([ProjectMembership(**row) for row in data["memberships"]])
    session.add_all([KnowledgeSource(**row) for row in data["sources"]])
    session.flush()
    session.add_all([
        Document(
            id=row["id"], source_id=row["source_id"], title=row["title"],
            project_id=row["project_id"], owner_id=row["owner_id"], version=row["version"],
            created_at=parse_dt(row["created_at"]), classification=row["classification"],
            allowed_user_ids=row["allowed_user_ids"], owner_approved=row["approved"],
            active=row["active"], content=row["content"],
        ) for row in data["documents"]
    ])
    for row in data["policies"]:
        session.add(DelegationPolicy(
            owner_id=row["owner_id"], enabled=row["enabled"], starts_at=parse_dt(row["starts_at"]),
            ends_at=parse_dt(row["ends_at"]), timeout_minutes=row["timeout_minutes"],
            project_ids=row["project_ids"], topics=row["topics"], audience_ids=row["audience_ids"],
            source_ids=row["source_ids"], backup_id=row["backup_id"], version=row["version"],
            manager_approved=row["manager_approved"], consented_at=parse_dt(row["starts_at"]),
        ))
    session.commit()
