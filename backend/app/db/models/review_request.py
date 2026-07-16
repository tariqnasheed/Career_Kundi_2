"""
ReviewRequest — private review-request skeleton (0053-F10).

A review request is not verification. F10 supports user request/cancel only.
Does not mutate claim support_status or verification_status.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ReviewRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_requests"
    __table_args__ = (
        Index("ix_review_requests_owner_user_id", "owner_user_id"),
        Index("ix_review_requests_subject_id", "subject_id"),
        Index("ix_review_requests_claim_id", "claim_id"),
        Index("ix_review_requests_review_state", "review_state"),
        Index("ix_review_requests_created_at", "created_at"),
        # Partial unique: one active (requested) review per claim.
        Index(
            "uq_review_requests_active_claim",
            "claim_id",
            unique=True,
            postgresql_where=text("review_state = 'requested'"),
        ),
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_claims.id", ondelete="RESTRICT"),
        nullable=False,
    )
    review_state: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewer_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped["User"] = relationship(  # noqa: F821, UP037
        "User",
        foreign_keys=[owner_user_id],
    )
    subject: Mapped["CareerSubject"] = relationship(  # noqa: F821, UP037
        "CareerSubject",
        foreign_keys=[subject_id],
    )
    claim: Mapped["ClaimRecord"] = relationship(  # noqa: F821, UP037
        "ClaimRecord",
        foreign_keys=[claim_id],
    )
