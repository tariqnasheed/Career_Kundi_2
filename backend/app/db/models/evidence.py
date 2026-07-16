"""
EvidenceRecord + ClaimEvidenceLink — private evidence metadata (0053-F2).

Not verification. Not file storage. Not public sharing.
ClaimEvidenceLink is a join only and must not mutate claim status axes.
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class EvidenceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        Index("ix_evidence_records_owner_user_id", "owner_user_id"),
        Index("ix_evidence_records_subject_id", "subject_id"),
        Index("ix_evidence_records_evidence_kind", "evidence_kind"),
        Index("ix_evidence_records_privacy_class", "privacy_class"),
        Index("ix_evidence_records_source_id", "source_id"),
        Index("ix_evidence_records_snapshot_id", "snapshot_id"),
        Index("ix_evidence_records_created_at", "created_at"),
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    evidence_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
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
    privacy_class: Mapped[str] = mapped_column(String(64), nullable=False)

    created_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    owner: Mapped["User"] = relationship(  # noqa: F821, UP037
        "User",
        foreign_keys=[owner_user_id],
    )
    subject: Mapped["CareerSubject | None"] = relationship(  # noqa: F821, UP037
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


class ClaimEvidenceLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "claim_evidence_links"
    __table_args__ = (
        UniqueConstraint(
            "claim_id",
            "evidence_id",
            name="uq_claim_evidence_links_claim_evidence",
        ),
        Index("ix_claim_evidence_links_claim_id", "claim_id"),
        Index("ix_claim_evidence_links_evidence_id", "evidence_id"),
        Index("ix_claim_evidence_links_link_role", "link_role"),
    )

    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_claims.id", ondelete="RESTRICT"),
        nullable=False,
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_records.id", ondelete="RESTRICT"),
        nullable=False,
    )
    link_role: Mapped[str] = mapped_column(String(64), nullable=False)

    created_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    claim: Mapped["ClaimRecord"] = relationship(  # noqa: F821, UP037
        "ClaimRecord",
        foreign_keys=[claim_id],
    )
    evidence: Mapped["EvidenceRecord"] = relationship(
        "EvidenceRecord",
        foreign_keys=[evidence_id],
    )
