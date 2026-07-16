"""Private evidence API schemas (0053-F3). Metadata/links only — not verification."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiListMeta(BaseModel):
    count: int


class EvidenceCreate(BaseModel):
    """Create evidence metadata. owner_user_id is never accepted from the client."""

    model_config = ConfigDict(extra="forbid")

    title: str
    evidence_kind: str
    subject_id: uuid.UUID | None = None
    privacy_class: str | None = Field(default=None)
    storage_uri: str | None = None
    content_hash: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    source_id: uuid.UUID | None = None
    snapshot_id: uuid.UUID | None = None


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID | None
    title: str
    evidence_kind: str
    privacy_class: str
    storage_uri: str | None
    content_hash: str | None
    mime_type: str | None
    size_bytes: int | None
    source_id: uuid.UUID | None
    snapshot_id: uuid.UUID | None
    has_attachment: bool = False
    evidence_kind_label: str
    privacy_label: str
    truth_warning: str
    # 0053-F13: derived only; no scanner / no DB column.
    attachment_safety_status: str = "scan_not_available"
    attachment_safety_label: str = "Scan not available"
    attachment_safety_warning: str = (
        "Private attachments are stored but not malware-scanned, parsed, "
        "reviewed, or verified in this version."
    )
    created_at: datetime
    updated_at: datetime


class EvidenceEnvelope(BaseModel):
    data: EvidenceRead


class EvidenceListEnvelope(BaseModel):
    data: list[EvidenceRead]
    meta: ApiListMeta


class ClaimEvidenceLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: uuid.UUID
    evidence_id: uuid.UUID
    link_role: str


class EvidenceSummary(BaseModel):
    id: uuid.UUID
    title: str
    evidence_kind: str
    evidence_kind_label: str
    privacy_class: str


class ClaimEvidenceLinkRead(BaseModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    evidence_id: uuid.UUID
    link_role: str
    link_role_label: str
    created_at: datetime
    evidence: EvidenceSummary
    truth_warning: str
    claim_support_status: str
    claim_verification_status: str
    claim_support_label: str
    claim_verification_label: str


class ClaimEvidenceLinkEnvelope(BaseModel):
    data: ClaimEvidenceLinkRead


class ClaimEvidenceLinkListEnvelope(BaseModel):
    data: list[ClaimEvidenceLinkRead]
    meta: ApiListMeta


class LinkableClaimRead(BaseModel):
    """Private claim row for Evidence Library selector (0053-F7). Not verification."""

    id: uuid.UUID
    subject_id: uuid.UUID
    claim_kind: str
    claim_key: str
    claim_value: str
    claim_origin: str
    support_status: str
    support_label: str
    verification_status: str
    verification_label: str
    truth_warning: str
    created_at: datetime


class LinkableClaimListEnvelope(BaseModel):
    data: list[LinkableClaimRead]
    meta: ApiListMeta


class EvidenceClaimLinkRead(BaseModel):
    """Evidence-centric private claim link row (0053-F7)."""

    id: uuid.UUID
    claim_id: uuid.UUID
    evidence_id: uuid.UUID
    link_role: str
    link_role_label: str
    created_at: datetime
    claim_kind: str
    claim_key: str
    claim_value: str
    claim_support_status: str
    claim_support_label: str
    claim_verification_status: str
    claim_verification_label: str
    truth_warning: str


class EvidenceClaimLinkListEnvelope(BaseModel):
    data: list[EvidenceClaimLinkRead]
    meta: ApiListMeta


class PassportEvidenceSummaryItem(BaseModel):
    """One private evidence↔claim link row for Passport read-only awareness (0053-F8)."""

    claim_id: uuid.UUID
    subject_id: uuid.UUID
    claim_kind: str
    claim_value: str
    claim_support_status: str
    claim_support_label: str
    claim_verification_status: str
    claim_verification_label: str
    link_role: str
    link_role_label: str
    evidence_id: uuid.UUID
    evidence_title: str
    evidence_kind: str
    evidence_kind_label: str
    has_attachment: bool
    truth_warning: str
    # 0053-F13: derived only; no scanner / no DB column.
    attachment_safety_status: str = "scan_not_available"
    attachment_safety_label: str = "Scan not available"
    attachment_safety_warning: str = (
        "Private attachments are stored but not malware-scanned, parsed, "
        "reviewed, or verified in this version."
    )
    created_at: datetime


class PassportEvidenceSummaryRead(BaseModel):
    """Read-only current-user evidence-linked claim summary for Passport (0053-F8)."""

    linked_claims_count: int
    evidence_records_count: int
    items: list[PassportEvidenceSummaryItem]
    truth_warning: str


class PassportEvidenceSummaryEnvelope(BaseModel):
    data: PassportEvidenceSummaryRead
