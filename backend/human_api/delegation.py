from __future__ import annotations

from datetime import datetime, timezone

from .models import DelegationPolicy, Employee, Question


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def classify_topic(question: str) -> str:
    text = question.lower()
    groups = {
        "deployment": ("deploy", "timeout", "probe", "release", "rollback", "startup"),
        "security": ("credential", "secret", "access", "sensitivity", "restricted"),
        "finance": ("budget", "forecast", "cost", "salary", "payroll"),
        "product": ("roadmap", "customer", "feature", "requirement"),
    }
    for label, words in groups.items():
        if any(word in text for word in words):
            return label
    return "general"


def policy_is_active(policy: DelegationPolicy, now: datetime | None = None) -> bool:
    now = now or utc_now()
    starts, ends = as_utc(policy.starts_at), as_utc(policy.ends_at)
    return bool(policy.enabled and policy.manager_approved
                and (starts is None or starts <= now) and (ends is None or ends >= now))


def eligible_reason(question: Question, owner: Employee, policy: DelegationPolicy | None,
                    now: datetime | None = None) -> tuple[bool, str]:
    now = now or utc_now()
    if not policy or not policy_is_active(policy, now):
        return False, "Owner has not enabled an active delegation policy."
    if question.project_id not in (policy.project_ids or []):
        return False, "Project is outside the owner's approved delegation scope."
    topic = question.topic
    if policy.topics and topic not in policy.topics and not (topic == "deployment" and "timeout" in policy.topics):
        return False, "Topic is outside the owner's approved delegation scope."
    if question.requester_id not in (policy.audience_ids or []):
        return False, "Requester is outside the owner's approved audience."
    starts, ends = as_utc(policy.starts_at), as_utc(policy.ends_at)
    if owner.availability == "out_of_office" and (starts is None or starts <= now) and (ends is None or ends >= now):
        return True, "Owner-enabled out-of-office delegation is active."
    deadline = as_utc(question.response_deadline)
    if deadline and now >= deadline:
        return True, "The explicit Human API response window elapsed."
    return False, "Waiting for a human response window or an enabled absence condition."
