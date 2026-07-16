"""
Evidence kind, privacy, and claim-link role enums (0053-F2).

Evidence is not verification. No verified/official/public/wallet enums.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypeVar

from app.platform.evidence.refs import EvidenceRefError

_E = TypeVar("_E", bound=StrEnum)


class EvidenceKind(StrEnum):
    DOCUMENT = "document"
    CERTIFICATE = "certificate"
    TRANSCRIPT = "transcript"
    PORTFOLIO = "portfolio"
    ASSESSMENT = "assessment"
    REFERENCE = "reference"
    SOURCE_SNAPSHOT = "source_snapshot"
    OTHER = "other"


class EvidencePrivacyClass(StrEnum):
    PRIVATE = "private"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


class ClaimEvidenceLinkRole(StrEnum):
    SUPPORTS = "supports"
    CONTESTS = "contests"
    CONTEXT = "context"


# Explicitly rejected visibility tokens (not enum members).
REJECTED_PRIVACY_TOKENS: frozenset[str] = frozenset(
    {
        "public",
        "shared",
        "shareable",
        "world_readable",
        "anonymous_public",
    }
)


def _parse_enum(enum_cls: type[_E], value: object, label: str) -> _E:
    if isinstance(value, enum_cls):
        return value
    if not isinstance(value, str):
        raise EvidenceRefError(
            f"{label} must be str or {enum_cls.__name__}; got {type(value).__name__}"
        )
    cleaned = value.strip()
    if not cleaned:
        raise EvidenceRefError(f"{label} must not be empty")
    try:
        return enum_cls(cleaned)
    except ValueError as exc:
        raise EvidenceRefError(f"unknown {label}: {value!r}") from exc


def parse_evidence_kind(value: object) -> EvidenceKind:
    return _parse_enum(EvidenceKind, value, "evidence_kind")


def parse_evidence_privacy_class(value: object) -> EvidencePrivacyClass:
    if isinstance(value, str):
        token = value.strip().lower()
        if token in REJECTED_PRIVACY_TOKENS:
            raise EvidenceRefError(
                f"privacy_class={value!r} is rejected; evidence is private-only in F2 "
                "(no public/shared visibility)"
            )
    return _parse_enum(EvidencePrivacyClass, value, "privacy_class")


def parse_claim_evidence_link_role(value: object) -> ClaimEvidenceLinkRole:
    return _parse_enum(ClaimEvidenceLinkRole, value, "link_role")
