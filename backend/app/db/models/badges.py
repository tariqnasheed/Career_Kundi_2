"""
db/models/badges.py
====================
Two-table badge system:

  BadgeDefinition   — static registry of every badge in the system (seeded at
                      startup from BADGE_DEFINITIONS in data/badges_seed.py)
  UserBadge         — per-user progress record; `earned_at` is set when the
                      user crosses `condition_target`

Badge categories (8):
  skill_mastery        | roadmap_progress    | interview_prep
  job_applications     | cv_builder          | consistency
  profile_completion   | learning_challenge

Rarity levels:
  common | uncommon | rare | epic | legendary

Condition types:
  boolean   Earned once when a specific action is performed (e.g. "first CV")
  count     Earned after N cumulative actions (e.g. "saved 10 jobs")
  streak    Earned after N consecutive days of platform activity
  score     Earned when a quiz/practice score exceeds a threshold
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class BadgeDefinition(Base):
    """Static badge catalogue — one row per badge type in the system."""
    __tablename__ = "badge_definitions"

    # String slug primary key so the badge ID is human-readable in logs / API.
    id: Mapped[str] = mapped_column(String(80), primary_key=True)

    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)

    category: Mapped[str] = mapped_column(String(40), index=True)
    # Lucide icon name to render in the badge gallery
    icon: Mapped[str] = mapped_column(String(60), default="trophy")
    # Visual gradient swatch: "violet", "cyan", "emerald", "amber", "rose", "gold"
    color_swatch: Mapped[str] = mapped_column(String(20), default="violet")

    rarity: Mapped[str] = mapped_column(String(20), default="common")  # common|uncommon|rare|epic|legendary

    # --- Condition -----------------------------------------------------------
    condition_type: Mapped[str] = mapped_column(String(20))  # boolean|count|streak|score
    condition_metric: Mapped[str] = mapped_column(String(60))  # the tracked metric name
    condition_target: Mapped[int] = mapped_column(Integer, default=1)
    # For `score` type: minimum passing score (0-100)
    condition_score_min: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Display order in the gallery (lower = appears first)
    display_order: Mapped[int] = mapped_column(Integer, default=100)

    user_badges: Mapped[list["UserBadge"]] = relationship(back_populates="badge_definition")


class UserBadge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-user progress toward each badge."""
    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
        Index("ix_user_badge_user", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    badge_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("badge_definitions.id", ondelete="CASCADE")
    )

    # Current progress count (for `count` and `streak` types)
    progress: Mapped[int] = mapped_column(Integer, default=0)

    # Whether the badge has been awarded
    is_earned: Mapped[bool] = mapped_column(Boolean, default=False)
    earned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # For streak badges: date of the last qualifying action
    last_activity_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Whether a celebration animation has been triggered/shown (so we don't
    # re-animate on page refresh)
    celebration_shown: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="user_badges")  # noqa: F821
    badge_definition: Mapped["BadgeDefinition"] = relationship(back_populates="user_badges")

    @property
    def pct_complete(self) -> float:
        """0-100 progress percentage toward earning this badge."""
        target = self.badge_definition.condition_target if self.badge_definition else 1
        if target <= 0:
            return 100.0
        return min(100.0, (self.progress / target) * 100.0)
