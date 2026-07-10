"""
Provenance SourceRecord / SourceSnapshot (0050-PF4-S1).

Source = origin/channel. Snapshot = captured observation at a point in time.
No claim/evidence/verification fields.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SourceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provenance_sources"
    __table_args__ = (
        Index("ix_provenance_sources_source_kind", "source_kind"),
    )

    source_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str | None] = mapped_column(Text, nullable=True)
    uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    snapshots: Mapped[list[SourceSnapshot]] = relationship(
        "SourceSnapshot",
        back_populates="source",
        foreign_keys="SourceSnapshot.source_id",
    )


class SourceSnapshot(UUIDPrimaryKeyMixin, Base):
    """Append-only observation. No updated_at; no update service in PF4-S1."""

    __tablename__ = "provenance_snapshots"
    __table_args__ = (
        Index("ix_provenance_snapshots_source_id", "source_id"),
        Index("ix_provenance_snapshots_captured_at", "captured_at"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provenance_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hash_algorithm: Mapped[str | None] = mapped_column(String(64), nullable=True)
    storage_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source: Mapped[SourceRecord] = relationship(
        "SourceRecord",
        back_populates="snapshots",
        foreign_keys=[source_id],
    )
