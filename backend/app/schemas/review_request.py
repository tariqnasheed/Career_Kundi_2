"""Private review-request API schemas (0053-F10 / F12). Request/cancel only — not verification."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Length/trim rules enforced in verification.service (product-safe messages).


class ApiListMeta(BaseModel):
    count: int


class ReviewRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: uuid.UUID
    request_note: str | None = Field(default=None)


class ReviewRequestCancel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cancellation_reason: str | None = Field(default=None)


class ReviewRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID
    claim_id: uuid.UUID
    review_state: str
    review_state_label: str
    review_state_help_text: str
    reviewer_type: str | None
    request_note: str | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None
    claim_verification_status: str
    claim_verification_label: str
    warning: str


class ReviewRequestEnvelope(BaseModel):
    data: ReviewRequestRead


class ReviewRequestListEnvelope(BaseModel):
    data: list[ReviewRequestRead]
    meta: ApiListMeta
