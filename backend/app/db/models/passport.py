"""
Passport persistence models (0052-F2).

Profile-wrapper strategy: CareerPassport aggregates one existing Profile;
section rows remain on Profile child tables. PassportTarget is Passport-owned.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import OrderableMixin, TimestampMixin, UUIDPrimaryKeyMixin


def _default_section_preferences() -> list[dict[str, Any]]:
    return [
        {"section": "profile", "order_index": 0, "enabled": True},
        {"section": "experience", "order_index": 1, "enabled": True},
        {"section": "education", "order_index": 2, "enabled": True},
        {"section": "projects", "order_index": 3, "enabled": True},
        {"section": "skills", "order_index": 4, "enabled": True},
        {"section": "credentials", "order_index": 5, "enabled": True},
        {"section": "targets", "order_index": 6, "enabled": True},
    ]


def _profile_backed_record_meta() -> dict[str, str]:
    """Metadata for Profile-backed / inherited records (not verified)."""
    return {
        "source_status": "user_asserted",
        "support_status": "profile_supported",
        "verification_status": "unverified",
    }


def _native_passport_record_meta() -> dict[str, str]:
    """Metadata for Passport-native rows such as targets."""
    return {
        "source_status": "user_asserted",
        "support_status": "not_provided",
        "verification_status": "unverified",
    }


_DEFAULT_SECTION_PREFS_SQL = (
    "'["
    '{"section": "profile", "order_index": 0, "enabled": true}, '
    '{"section": "experience", "order_index": 1, "enabled": true}, '
    '{"section": "education", "order_index": 2, "enabled": true}, '
    '{"section": "projects", "order_index": 3, "enabled": true}, '
    '{"section": "skills", "order_index": 4, "enabled": true}, '
    '{"section": "credentials", "order_index": 5, "enabled": true}, '
    '{"section": "targets", "order_index": 6, "enabled": true}'
    "]'::jsonb"
)

_PROFILE_BACKED_META_SQL = (
    "'{"
    '"source_status": "user_asserted", '
    '"support_status": "profile_supported", '
    '"verification_status": "unverified"'
    "}'::jsonb"
)

_NATIVE_META_SQL = (
    "'{"
    '"source_status": "user_asserted", '
    '"support_status": "not_provided", '
    '"verification_status": "unverified"'
    "}'::jsonb"
)


class CareerPassport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One Passport per user, wrapping exactly one existing Profile."""

    __tablename__ = "career_passports"
    __table_args__ = (
        CheckConstraint(
            "visibility = 'private'",
            name="ck_career_passports_visibility_private",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_career_passports_version_positive",
        ),
        CheckConstraint(
            "jsonb_typeof(section_preferences) = 'array'",
            name="ck_career_passports_section_preferences_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(profile_record_meta) = 'object'",
            name="ck_career_passports_profile_record_meta_is_object",
        ),
        Index("ix_career_passports_subject_id", "subject_id"),
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    visibility: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="private",
        server_default="private",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    section_preferences: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=_default_section_preferences,
        server_default=text(_DEFAULT_SECTION_PREFS_SQL),
    )
    profile_record_meta: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=_profile_backed_record_meta,
        server_default=text(_PROFILE_BACKED_META_SQL),
    )

    owner: Mapped[User] = relationship(  # noqa: F821
        "User",
        back_populates="passport",
        foreign_keys=[owner_user_id],
    )
    profile: Mapped[Profile] = relationship(  # noqa: F821
        "Profile",
        back_populates="passport",
        foreign_keys=[profile_id],
    )
    subject: Mapped[CareerSubject | None] = relationship(  # noqa: F821
        "CareerSubject",
        foreign_keys=[subject_id],
    )
    targets: Mapped[list[PassportTarget]] = relationship(
        back_populates="passport",
        cascade="all, delete-orphan",
        order_by="PassportTarget.order_index",
    )


class PassportTarget(UUIDPrimaryKeyMixin, TimestampMixin, OrderableMixin, Base):
    """Passport-owned career target rows (not Platform goals)."""

    __tablename__ = "passport_targets"
    __table_args__ = (
        CheckConstraint(
            "priority >= 1 AND priority <= 5",
            name="ck_passport_targets_priority_range",
        ),
        CheckConstraint(
            "order_index >= 0",
            name="ck_passport_targets_order_index_nonnegative",
        ),
        CheckConstraint(
            "role_taxonomy IS NULL OR jsonb_typeof(role_taxonomy) = 'object'",
            name="ck_passport_targets_role_taxonomy_object",
        ),
        CheckConstraint(
            "jsonb_typeof(passport_record_meta) = 'object'",
            name="ck_passport_targets_record_meta_is_object",
        ),
        Index("ix_passport_targets_passport_id", "passport_id"),
    )

    passport_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_passports.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_role_text: Mapped[str] = mapped_column(String(255), nullable=False)
    role_taxonomy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pathway_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_industry: Mapped[str | None] = mapped_column(String(160), nullable=True)
    target_seniority: Mapped[str | None] = mapped_column(String(64), nullable=True)
    time_horizon: Mapped[str | None] = mapped_column(String(120), nullable=True)
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        server_default="3",
    )
    # Override mixin so DB default matches migration (OrderableMixin has Python-only default).
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    passport_record_meta: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=_native_passport_record_meta,
        server_default=text(_NATIVE_META_SQL),
    )

    passport: Mapped[CareerPassport] = relationship(back_populates="targets")
