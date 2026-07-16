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
    evidence_kind_label: str
    privacy_label: str
    truth_warning: str
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
