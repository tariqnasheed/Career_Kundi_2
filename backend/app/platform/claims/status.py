"""
Claim kind and status axes (0050-PF5-S1).

Axes are independent: source_linked ≠ evidence_backed ≠ verified.
No silent upgrades between axes or values.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypeVar

from app.platform.claims.refs import ClaimRefError

_E = TypeVar("_E", bound=StrEnum)


class ClaimKind(StrEnum):
    SKILL = "skill"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CREDENTIAL = "credential"
    LANGUAGE = "language"
    WORK_AUTHORIZATION = "work_authorization"
    LOCATION_PREFERENCE = "location_preference"
    SALARY_PREFERENCE = "salary_preference"
    AVAILABILITY = "availability"
    CAREER_GOAL = "career_goal"
    PORTFOLIO = "portfolio"
    OTHER = "other"


class ClaimOrigin(StrEnum):
    USER_ASSERTED = "user_asserted"
    DOCUMENT_EXTRACTED = "document_extracted"
    MODEL_INFERRED = "model_inferred"
    SYSTEM_GENERATED = "system_generated"
    EXTERNAL_IMPORTED = "external_imported"
    UNKNOWN = "unknown"


class SupportStatus(StrEnum):
    NOT_PROVIDED = "not_provided"
    PROFILE_SUPPORTED = "profile_supported"
    SOURCE_LINKED = "source_linked"
    EVIDENCE_BACKED = "evidence_backed"
    ASSESSMENT_DEMONSTRATED = "assessment_demonstrated"
    UNKNOWN = "unknown"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"
    CONFLICTING = "conflicting"
    UNKNOWN = "unknown"


def _parse_enum(enum_cls: type[_E], value: object, label: str) -> _E:
    if isinstance(value, enum_cls):
        return value
    if not isinstance(value, str):
        raise ClaimRefError(
            f"{label} must be str or {enum_cls.__name__}; got {type(value).__name__}"
        )
    cleaned = value.strip()
    if not cleaned:
        raise ClaimRefError(f"{label} must not be empty")
    try:
        return enum_cls(cleaned)
    except ValueError as exc:
        raise ClaimRefError(f"unknown {label}: {value!r}") from exc


def parse_claim_kind(value: object) -> ClaimKind:
    """Accept known kinds only; never silently map to OTHER."""
    return _parse_enum(ClaimKind, value, "claim_kind")


def parse_claim_origin(value: object) -> ClaimOrigin:
    return _parse_enum(ClaimOrigin, value, "claim_origin")


def parse_support_status(value: object) -> SupportStatus:
    return _parse_enum(SupportStatus, value, "support_status")


def parse_verification_status(value: object) -> VerificationStatus:
    return _parse_enum(VerificationStatus, value, "verification_status")
