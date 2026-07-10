"""
Lifecycle kind and status contracts (0050-PF7-S1).

No silent fallback to UNKNOWN. No auto-map to other.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypeVar

from app.platform.lifecycle.refs import LifecycleRefError

_E = TypeVar("_E", bound=StrEnum)


class GoalKind(StrEnum):
    CAREER = "career"
    EDUCATION = "education"
    JOB_SEARCH = "job_search"
    SKILL_DEVELOPMENT = "skill_development"
    MIGRATION = "migration"
    PUBLIC_SERVICE = "public_service"
    FINANCIAL = "financial"
    PERSONAL = "personal"
    OTHER = "other"
    UNKNOWN = "unknown"


class RecommendationKind(StrEnum):
    JOB = "job"
    COURSE = "course"
    SKILL = "skill"
    PRACTICE = "practice"
    DOCUMENT = "document"
    APPLICATION = "application"
    CAREER_PATH = "career_path"
    EDUCATION_PATH = "education_path"
    PUBLIC_SERVICE_PATH = "public_service_path"
    OTHER = "other"
    UNKNOWN = "unknown"


class AttemptKind(StrEnum):
    APPLICATION = "application"
    PRACTICE = "practice"
    ASSESSMENT = "assessment"
    COURSE = "course"
    INTERVIEW = "interview"
    DOCUMENT_PREPARATION = "document_preparation"
    RESEARCH = "research"
    OUTREACH = "outreach"
    OTHER = "other"
    UNKNOWN = "unknown"


class OutcomeKind(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class FeedbackKind(StrEnum):
    USER_FEEDBACK = "user_feedback"
    SYSTEM_OBSERVATION = "system_observation"
    EXTERNAL_RESPONSE = "external_response"
    ASSESSMENT_FEEDBACK = "assessment_feedback"
    EMPLOYER_RESPONSE = "employer_response"
    LEARNING_SIGNAL = "learning_signal"
    OTHER = "other"
    UNKNOWN = "unknown"


class LifecycleStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


def _parse_enum(enum_cls: type[_E], value: object, label: str) -> _E:
    if isinstance(value, enum_cls):
        return value
    if not isinstance(value, str):
        raise LifecycleRefError(
            f"{label} must be str or {enum_cls.__name__}; got {type(value).__name__}"
        )
    cleaned = value.strip()
    if not cleaned:
        raise LifecycleRefError(f"{label} must not be empty")
    try:
        return enum_cls(cleaned)
    except ValueError as exc:
        raise LifecycleRefError(f"unknown {label}: {value!r}") from exc


def parse_goal_kind(value: object) -> GoalKind:
    return _parse_enum(GoalKind, value, "goal_kind")


def parse_recommendation_kind(value: object) -> RecommendationKind:
    return _parse_enum(RecommendationKind, value, "recommendation_kind")


def parse_attempt_kind(value: object) -> AttemptKind:
    return _parse_enum(AttemptKind, value, "attempt_kind")


def parse_outcome_kind(value: object) -> OutcomeKind:
    return _parse_enum(OutcomeKind, value, "outcome_kind")


def parse_feedback_kind(value: object) -> FeedbackKind:
    return _parse_enum(FeedbackKind, value, "feedback_kind")


def parse_lifecycle_status(value: object) -> LifecycleStatus:
    return _parse_enum(LifecycleStatus, value, "status")
