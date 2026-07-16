"""
AttachmentScanJob — private attachment scan queue skeleton (0053-F16).

A queued scan job is not a completed scan and is not verification.
No scanner engine, quarantine storage, or public sharing in F16.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AttachmentScanJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attachment_scan_jobs"
    __table_args__ = (
        Index("ix_attachment_scan_jobs_owner_user_id", "owner_user_id"),
        Index("ix_attachment_scan_jobs_evidence_id", "evidence_id"),
        Index("ix_attachment_scan_jobs_job_status", "job_status"),
        Index(
            "ix_attachment_scan_jobs_attachment_safety_status",
            "attachment_safety_status",
        ),
        Index("ix_attachment_scan_jobs_created_at", "created_at"),
        Index(
            "ix_attachment_scan_jobs_evidence_content_hash",
            "evidence_id",
            "content_hash_snapshot",
        ),
        # One active (queued/reserved) job per evidence + content hash.
        Index(
            "uq_attachment_scan_jobs_active_evidence_hash",
            "evidence_id",
            "content_hash_snapshot",
            unique=True,
            postgresql_where=text("job_status IN ('queued', 'reserved')"),
        ),
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_records.id", ondelete="RESTRICT"),
        nullable=False,
    )
    content_hash_snapshot: Mapped[str] = mapped_column(String(128), nullable=False)
    mime_type_snapshot: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes_snapshot: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    job_status: Mapped[str] = mapped_column(String(64), nullable=False)
    attachment_safety_status: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    engine_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    safe_error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    safe_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped["User"] = relationship(  # noqa: F821, UP037
        "User",
        foreign_keys=[owner_user_id],
    )
    evidence: Mapped["EvidenceRecord"] = relationship(  # noqa: F821, UP037
        "EvidenceRecord",
        foreign_keys=[evidence_id],
    )
