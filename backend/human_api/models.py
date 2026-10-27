from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    entra_oid: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    role: Mapped[str] = mapped_column(String(80))
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"))
    availability: Mapped[str] = mapped_column(String(40), default="available")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProjectMembership(Base):
    __tablename__ = "project_memberships"
    __table_args__ = (UniqueConstraint("employee_id", "project_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class DelegationPolicy(Base):
    __tablename__ = "delegation_policies"
    owner_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timeout_minutes: Mapped[int] = mapped_column(Integer, default=30)
    project_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    audience_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    backup_id: Mapped[str | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    manager_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    consented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    connector: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.id"), index=True)
    title: Mapped[str] = mapped_column(String(250))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    version: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    classification: Mapped[str] = mapped_column(String(80), default="Internal Team")
    allowed_user_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    owner_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    content: Mapped[str] = mapped_column(Text)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    requester_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(80), default="general")
    status: Mapped[str] = mapped_column(String(50), default="CREATED", index=True)
    mode: Mapped[str] = mapped_column(String(40), default="delayed_fallback")
    urgency: Mapped[str] = mapped_column(String(30), default="normal")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    response_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    policy_version: Mapped[int] = mapped_column(Integer, default=0)


class QuestionStatusHistory(Base):
    __tablename__ = "question_status_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    reason: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DurableJob(Base):
    __tablename__ = "durable_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    last_error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GeneratedAnswer(Base):
    __tablename__ = "generated_answers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), unique=True, index=True)
    answer_text: Mapped[str] = mapped_column(Text)
    answer_type: Mapped[str] = mapped_column(String(50))
    generation_mode: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(120), default="deterministic-evidence-demo")
    prompt_version: Mapped[str] = mapped_column(String(80), default="human-api-evidence-v1")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    human_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AnswerValidation(Base):
    __tablename__ = "answer_validations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), unique=True)
    outcome: Mapped[str] = mapped_column(String(50))
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    calibrated_score: Mapped[float | None] = mapped_column(nullable=True)


class EvidenceReference(Base):
    __tablename__ = "evidence_references"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    answer_id: Mapped[str] = mapped_column(ForeignKey("generated_answers.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    document_version: Mapped[str] = mapped_column(String(40))
    passage: Mapped[str] = mapped_column(Text)


class Escalation(Base):
    __tablename__ = "escalations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), unique=True)
    assignee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    reason: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(40), default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HumanReview(Base):
    __tablename__ = "human_reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    response_text: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ApprovedKnowledgeEntry(Base):
    __tablename__ = "approved_knowledge_entries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="PENDING_APPROVAL")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    rating: Mapped[str] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), index=True)
    question_id: Mapped[str | None] = mapped_column(ForeignKey("questions.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(500))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(100))
    decision: Mapped[str] = mapped_column(String(40))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
