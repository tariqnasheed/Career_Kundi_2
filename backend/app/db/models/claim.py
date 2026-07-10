"""
ClaimRecord — statement asserted about a career subject (0050-PF5-S1).

Not Evidence, Verification, or Passport. Optional source/snapshot FKs are
provenance links only and do not imply verification.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ClaimRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "career_claims"
    __table_args__ = (
        Index("ix_career_claims_subject_id", "subject_id"),
        Index("ix_career_claims_claim_kind", "claim_kind"),
        Index("ix_career_claims_claim_key", "claim_key"),
        Index("ix_career_claims_support_status", "support_status"),
        Index("ix_career_claims_verification_status", "verification_status"),
        Index("ix_career_claims_source_id", "source_id"),
        Index("ix_career_claims_snapshot_id", "snapshot_id"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    claim_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    claim_key: Mapped[str] = mapped_column(String(256), nullable=False)
    # Text (not JSONB): human-readable / JSON-compatible string; no schema framework.
    claim_value: Mapped[str] = mapped_column(Text, nullable=False)
    claim_origin: Mapped[str] = mapped_column(String(64), nullable=False)
    support_status: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(64), nullable=False)

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provenance_sources.id", ondelete="RESTRICT"),
        nullable=True,
    )
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provenance_snapshots.id", ondelete="RESTRICT"),
        nullable=True,
    )

    created_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    subject: Mapped["CareerSubject"] = relationship(  # noqa: F821, UP037
        "CareerSubject",
        foreign_keys=[subject_id],
    )
    source: Mapped["SourceRecord | None"] = relationship(  # noqa: F821, UP037
        "SourceRecord",
        foreign_keys=[source_id],
    )
    snapshot: Mapped["SourceSnapshot | None"] = relationship(  # noqa: F821, UP037
        "SourceSnapshot",
        foreign_keys=[snapshot_id],
    )
