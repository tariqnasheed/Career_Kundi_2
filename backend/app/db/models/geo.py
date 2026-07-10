"""
Geo / jurisdiction / locale / work-authorization area models (0050-PF6-S1).

Domains stay separate: no geo↔jurisdiction/locale/auth FKs.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GeoArea(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "geo_areas"
    __table_args__ = (
        Index("ix_geo_areas_geo_kind", "geo_kind"),
        Index("ix_geo_areas_code", "code"),
        Index("ix_geo_areas_parent_geo_id", "parent_geo_id"),
    )

    geo_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parent_geo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("geo_areas.id", ondelete="RESTRICT"),
        nullable=True,
    )

    parent: Mapped[GeoArea | None] = relationship(
        "GeoArea",
        remote_side="GeoArea.id",
        foreign_keys=[parent_geo_id],
    )


class JurisdictionArea(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jurisdiction_areas"
    __table_args__ = (
        Index("ix_jurisdiction_areas_jurisdiction_kind", "jurisdiction_kind"),
        Index("ix_jurisdiction_areas_code", "code"),
        Index(
            "ix_jurisdiction_areas_parent_jurisdiction_id",
            "parent_jurisdiction_id",
        ),
    )

    jurisdiction_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parent_jurisdiction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jurisdiction_areas.id", ondelete="RESTRICT"),
        nullable=True,
    )

    parent: Mapped[JurisdictionArea | None] = relationship(
        "JurisdictionArea",
        remote_side="JurisdictionArea.id",
        foreign_keys=[parent_jurisdiction_id],
    )


class LocaleProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "locale_profiles"
    __table_args__ = (
        Index("ix_locale_profiles_locale_code", "locale_code"),
        Index("ix_locale_profiles_locale_kind", "locale_kind"),
    )

    locale_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    locale_code: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)


class WorkAuthorizationArea(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Area stub only — no candidate status, visa type, or eligibility."""

    __tablename__ = "work_authorization_areas"
    __table_args__ = (
        Index(
            "ix_work_authorization_areas_authorization_kind",
            "authorization_kind",
        ),
        Index("ix_work_authorization_areas_code", "code"),
    )

    authorization_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
