"""
0053-F2 Evidence domain create/link contract validators.

Pure domain validation — no FastAPI, SQLAlchemy models, Passport, or feature
domains. Existence / ownership checks stay in service.py.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.platform.evidence.refs import EvidenceRefError
from app.platform.evidence.status import (
    ClaimEvidenceLinkRole,
    EvidenceKind,
    EvidencePrivacyClass,
    parse_claim_evidence_link_role,
    parse_evidence_kind,
    parse_evidence_privacy_class,
)


@dataclass(frozen=True, slots=True)
class ValidatedEvidenceCreate:
    title: str
    evidence_kind: EvidenceKind
    privacy_class: EvidencePrivacyClass
    source_id: uuid.UUID | None
    snapshot_id: uuid.UUID | None
    storage_uri: str | None
    content_hash: str | None
    mime_type: str | None
    size_bytes: int | None


@dataclass(frozen=True, slots=True)
class ValidatedClaimEvidenceLink:
    claim_id: uuid.UUID
    evidence_id: uuid.UUID
    link_role: ClaimEvidenceLinkRole


def _trim_required(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise EvidenceRefError(f"{label} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise EvidenceRefError(f"{label} must not be empty")
    return cleaned


def _trim_optional(value: object | None, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise EvidenceRefError(f"{label} must be a string or None")
    cleaned = value.strip()
    return cleaned if cleaned else None


def validate_evidence_source_snapshot_contract(
    *,
    source_id: uuid.UUID | None,
    snapshot_id: uuid.UUID | None,
) -> None:
    if snapshot_id is not None and source_id is None:
        raise EvidenceRefError("snapshot_id requires source_id")


def assert_no_evidence_verification_upgrade() -> None:
    """
    Evidence create/link must never imply verification outcomes.

    Kept as an explicit guard so callers cannot treat F2 as a verification API.
    """
    # No-op structural anchor: verification enums are intentionally absent here.
    return None


def validate_evidence_create_contract(
    *,
    title: object,
    evidence_kind: object,
    privacy_class: object | None = None,
    source_id: uuid.UUID | None = None,
    snapshot_id: uuid.UUID | None = None,
    storage_uri: object | None = None,
    content_hash: object | None = None,
    mime_type: object | None = None,
    size_bytes: object | None = None,
) -> ValidatedEvidenceCreate:
    cleaned_title = _trim_required(title, "title")
    kind = parse_evidence_kind(evidence_kind)
    privacy = (
        EvidencePrivacyClass.PRIVATE
        if privacy_class is None
        else parse_evidence_privacy_class(privacy_class)
    )

    validate_evidence_source_snapshot_contract(
        source_id=source_id, snapshot_id=snapshot_id
    )
    assert_no_evidence_verification_upgrade()

    uri = _trim_optional(storage_uri, "storage_uri")
    ch = _trim_optional(content_hash, "content_hash")
    mime = _trim_optional(mime_type, "mime_type")

    size: int | None
    if size_bytes is None:
        size = None
    elif isinstance(size_bytes, bool) or not isinstance(size_bytes, int):
        raise EvidenceRefError("size_bytes must be an int or None")
    elif size_bytes < 0:
        raise EvidenceRefError("size_bytes must not be negative")
    else:
        size = size_bytes

    return ValidatedEvidenceCreate(
        title=cleaned_title,
        evidence_kind=kind,
        privacy_class=privacy,
        source_id=source_id,
        snapshot_id=snapshot_id,
        storage_uri=uri,
        content_hash=ch,
        mime_type=mime,
        size_bytes=size,
    )


def validate_claim_evidence_link_contract(
    *,
    claim_id: uuid.UUID,
    evidence_id: uuid.UUID,
    link_role: object,
) -> ValidatedClaimEvidenceLink:
    role = parse_claim_evidence_link_role(link_role)
    assert_no_evidence_verification_upgrade()
    return ValidatedClaimEvidenceLink(
        claim_id=claim_id,
        evidence_id=evidence_id,
        link_role=role,
    )
