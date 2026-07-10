"""
Privacy kind contracts (0050-PF9-S1).

Classification, visibility, consent, and retention are independent axes.
No silent fallback to UNKNOWN.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypeVar

from app.platform.privacy.refs import PrivacyRefError

_E = TypeVar("_E", bound=StrEnum)


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class VisibilityScope(StrEnum):
    SUBJECT_OWNER = "subject_owner"
    SUBJECT_COLLABORATORS = "subject_collaborators"
    ORGANIZATION = "organization"
    SYSTEM_ONLY = "system_only"
    PUBLIC = "public"
    PRIVATE = "private"
    UNKNOWN = "unknown"


class ProcessingPurpose(StrEnum):
    ACCOUNT_OPERATION = "account_operation"
    CAREER_PROFILE = "career_profile"
    JOB_SEARCH = "job_search"
    EDUCATION_GUIDANCE = "education_guidance"
    APPLICATION_SUPPORT = "application_support"
    INTERVIEW_PREPARATION = "interview_preparation"
    ANALYTICS = "analytics"
    SAFETY_SECURITY = "safety_security"
    LEGAL_OBLIGATION = "legal_obligation"
    RESEARCH_DEVELOPMENT = "research_development"
    MARKETING = "marketing"
    UNKNOWN = "unknown"


class ConsentStatus(StrEnum):
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    NOT_REQUIRED = "not_required"
    UNKNOWN = "unknown"


class RetentionCategory(StrEnum):
    SESSION = "session"
    ACTIVE_ACCOUNT = "active_account"
    USER_CONTROLLED = "user_controlled"
    LEGAL_HOLD = "legal_hold"
    FIXED_PERIOD = "fixed_period"
    INDEFINITE_UNTIL_REVIEW = "indefinite_until_review"
    UNKNOWN = "unknown"


def _parse_enum(enum_cls: type[_E], value: object, label: str) -> _E:
    if isinstance(value, enum_cls):
        return value
    if not isinstance(value, str):
        raise PrivacyRefError(
            f"{label} must be str or {enum_cls.__name__}; got {type(value).__name__}"
        )
    cleaned = value.strip()
    if not cleaned:
        raise PrivacyRefError(f"{label} must not be empty")
    try:
        return enum_cls(cleaned)
    except ValueError as exc:
        raise PrivacyRefError(f"unknown {label}: {value!r}") from exc


def parse_data_classification(value: object) -> DataClassification:
    return _parse_enum(DataClassification, value, "data_classification")


def parse_visibility_scope(value: object) -> VisibilityScope:
    return _parse_enum(VisibilityScope, value, "visibility_scope")


def parse_processing_purpose(value: object) -> ProcessingPurpose:
    return _parse_enum(ProcessingPurpose, value, "processing_purpose")


def parse_consent_status(value: object) -> ConsentStatus:
    return _parse_enum(ConsentStatus, value, "consent_status")


def parse_retention_category(value: object) -> RetentionCategory:
    return _parse_enum(RetentionCategory, value, "retention_category")
