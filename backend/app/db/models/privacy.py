"""
Privacy policy / consent / retention models (0050-PF9-S1).

Primitives only — not a legal compliance engine or deletion automation.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PrivacyPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "privacy_policies"
    __table_args__ = (
        Index("ix_privacy_policies_subject_id", "subject_id"),
        Index("ix_privacy_policies_data_classification", "data_classification"),
        Index("ix_privacy_policies_visibility_scope", "visibility_scope"),
        Index("ix_privacy_policies_processing_purpose", "processing_purpose"),
    )

    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=True,
    )
    data_classification: Mapped[str] = mapped_column(String(64), nullable=False)
    visibility_scope: Mapped[str] = mapped_column(String(64), nullable=False)
    processing_purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )


class ConsentRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consent_records"
    __table_args__ = (
        Index("ix_consent_records_subject_id", "subject_id"),
        Index("ix_consent_records_processing_purpose", "processing_purpose"),
        Index("ix_consent_records_consent_status", "consent_status"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    processing_purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    consent_status: Mapped[str] = mapped_column(String(64), nullable=False)
    granted_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    granted_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RetentionPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retention_policies"
    __table_args__ = (
        Index("ix_retention_policies_subject_id", "subject_id"),
        Index("ix_retention_policies_retention_category", "retention_category"),
        Index("ix_retention_policies_processing_purpose", "processing_purpose"),
    )

    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=True,
    )
    retention_category: Mapped[str] = mapped_column(String(64), nullable=False)
    processing_purpose: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retain_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
