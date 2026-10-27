from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class QuestionCreate(BaseModel):
    owner_id: str = Field(min_length=1, max_length=80)
    project_id: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=10, max_length=3000)
    urgency: str = Field(default="normal", pattern="^(low|normal|high)$")


class DelegationUpdate(BaseModel):
    enabled: bool
    starts_at: str | None = None
    ends_at: str | None = None
    timeout_minutes: int = Field(ge=5, le=1440)
    project_ids: list[str] = Field(max_length=12)
    topics: list[str] = Field(max_length=30)
    audience_ids: list[str] = Field(max_length=100)
    source_ids: list[str] = Field(max_length=250)
    backup_id: str | None = None

    @field_validator("starts_at", "ends_at")
    @classmethod
    def valid_iso_date(cls, value: str | None) -> str | None:
        if value is not None:
            from datetime import datetime
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class HumanAnswer(BaseModel):
    answer: str = Field(min_length=5, max_length=5000)


class FeedbackCreate(BaseModel):
    rating: str = Field(pattern="^(useful|incorrect|needs_context)$")
    note: str | None = Field(default=None, max_length=1000)


class Revocation(BaseModel):
    employee_id: str
    project_id: str
