"""
Review / verification state enums (0053-F9).

ReviewState is separate from ClaimRecord.verification_status.
No DB writes. No automatic claim upgrades.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypeVar

from app.platform.verification.refs import VerificationRefError

_E = TypeVar("_E", bound=StrEnum)


class ReviewState(StrEnum):
    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    UNDER_REVIEW = "under_review"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICTED = "conflicted"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ReviewerType(StrEnum):
    """Future reviewer organization kinds. Not auto-verification actors."""

    CAREERKUNDI_INTERNAL = "careerkundi_internal"
    ISSUER = "issuer"
    EMPLOYER = "employer"
    EDUCATION_PROVIDER = "education_provider"
    LICENSE_BODY = "license_body"
    SYSTEM_POLICY = "system_policy"


class ReviewActorType(StrEnum):
    """Who may attempt a review-state transition (capability, not org type)."""

    USER = "user"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    SYSTEM_POLICY = "system_policy"


# Forbidden self/AI/blockchain actor labels — never introduce as ReviewActorType.
FORBIDDEN_ACTOR_LABELS: frozenset[str] = frozenset(
    {
        "self_verified",
        "user_verified",
        "ai_verified",
        "blockchain_verified",
        "auto_verified",
    }
)


def _parse_enum(enum_cls: type[_E], value: object, label: str) -> _E:
    if isinstance(value, enum_cls):
        return value
    if not isinstance(value, str):
        raise VerificationRefError(
            f"{label} must be str or {enum_cls.__name__}; got {type(value).__name__}"
        )
    cleaned = value.strip()
    if not cleaned:
        raise VerificationRefError(f"{label} must not be empty")
    try:
        return enum_cls(cleaned)
    except ValueError as exc:
        raise VerificationRefError(f"unknown {label}: {value!r}") from exc


def parse_review_state(value: object) -> ReviewState:
    return _parse_enum(ReviewState, value, "review_state")


def parse_reviewer_type(value: object) -> ReviewerType:
    return _parse_enum(ReviewerType, value, "reviewer_type")


def parse_review_actor_type(value: object) -> ReviewActorType:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in FORBIDDEN_ACTOR_LABELS:
            raise VerificationRefError(
                f"forbidden review actor type: {value!r}"
            )
    return _parse_enum(ReviewActorType, value, "review_actor_type")
