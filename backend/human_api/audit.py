from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from .models import AuditEvent


def record(session: Session, actor_id: str | None, action: str, resource_type: str,
           resource_id: str, decision: str, metadata: dict[str, Any] | None = None) -> None:
    # Audit metadata contains identifiers and policy decisions only, never prompt text or tokens.
    session.add(AuditEvent(actor_id=actor_id, action=action, resource_type=resource_type,
                           resource_id=resource_id, decision=decision,
                           metadata_json=metadata or {}, created_at=datetime.now(timezone.utc)))
