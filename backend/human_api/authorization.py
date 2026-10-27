from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import DelegationPolicy, Document, Employee, Escalation, KnowledgeSource, ProjectMembership


def is_project_member(session: Session, employee_id: str, project_id: str) -> bool:
    return session.scalar(select(ProjectMembership.id).where(
        ProjectMembership.employee_id == employee_id,
        ProjectMembership.project_id == project_id,
        ProjectMembership.active.is_(True),
    )) is not None


def may_read_document(session: Session, employee_id: str, document: Document) -> bool:
    """Deny first, then check current membership and document-specific ACLs."""
    employee = session.get(Employee, employee_id)
    if not employee or not employee.active or not document.active or not document.owner_approved:
        return False
    if not is_project_member(session, employee_id, document.project_id):
        return False
    # High-sensitivity labels require an explicit document ACL. A project
    # membership alone must not turn Restricted content into team knowledge.
    if document.classification in {"Restricted", "Highly Restricted"}:
        if document.allowed_user_ids is None or employee_id not in document.allowed_user_ids:
            return False
    if document.allowed_user_ids is not None and employee_id not in document.allowed_user_ids:
        return False
    return True


def may_use_document_for_policy(
    session: Session, requester_id: str, owner_id: str, document: Document,
    policy: DelegationPolicy,
) -> bool:
    """Consent scopes the source; it never replaces the requester's source ACL."""
    if not policy.enabled or document.source_id not in (policy.source_ids or []):
        return False
    source = session.get(KnowledgeSource, document.source_id)
    if not source or not source.active or not source.approved:
        return False
    if not may_read_document(session, requester_id, document):
        return False
    return True


def can_view_question(session: Session, actor_id: str, question) -> bool:
    if actor_id in {question.requester_id, question.owner_id}:
        return True
    escalation = session.scalar(select(Escalation).where(Escalation.question_id == question.id))
    return bool(escalation and escalation.assignee_id == actor_id)


def is_security_admin(employee: Employee) -> bool:
    return employee.role == "Security Administrator"


def is_team_manager(employee: Employee) -> bool:
    return employee.role == "Team Manager"
