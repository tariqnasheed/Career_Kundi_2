"""
CareerSubject — durable career-subject identity (0050-PF3-S1).

Not User, Profile, Actor, or Passport. Holds no biography/profile fields.
owner_user_id is the controlling account, not proof that User == Subject.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CareerSubject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "career_subjects"
    __table_args__ = (
        Index("ix_career_subjects_owner_user_id", "owner_user_id"),
    )

    # Controlling account. RESTRICT: do not silently delete subjects with the user.
    # Multi-subject: no UNIQUE(owner_user_id).
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    owner: Mapped["User"] = relationship(  # noqa: F821, UP037
        "User",
        foreign_keys=[owner_user_id],
    )
