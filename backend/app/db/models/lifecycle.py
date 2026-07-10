"""
Lifecycle loop models (0050-PF7-S1).

Thin Goal → Recommendation → Attempt → Outcome → Feedback records.
No workflow, scoring, or claim coupling.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CareerGoal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "career_goals"
    __table_args__ = (
        Index("ix_career_goals_subject_id", "subject_id"),
        Index("ix_career_goals_goal_kind", "goal_kind"),
        Index("ix_career_goals_status", "status"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    goal_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )


class CareerRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "career_recommendations"
    __table_args__ = (
        Index("ix_career_recommendations_subject_id", "subject_id"),
        Index("ix_career_recommendations_goal_id", "goal_id"),
        Index("ix_career_recommendations_recommendation_kind", "recommendation_kind"),
        Index("ix_career_recommendations_status", "status"),
        Index("ix_career_recommendations_source_id", "source_id"),
        Index("ix_career_recommendations_snapshot_id", "snapshot_id"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_goals.id", ondelete="RESTRICT"),
        nullable=True,
    )
    recommendation_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
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


class CareerAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "career_attempts"
    __table_args__ = (
        Index("ix_career_attempts_subject_id", "subject_id"),
        Index("ix_career_attempts_goal_id", "goal_id"),
        Index("ix_career_attempts_recommendation_id", "recommendation_id"),
        Index("ix_career_attempts_attempt_kind", "attempt_kind"),
        Index("ix_career_attempts_status", "status"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_goals.id", ondelete="RESTRICT"),
        nullable=True,
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_recommendations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    attempt_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )


class CareerOutcome(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "career_outcomes"
    __table_args__ = (
        Index("ix_career_outcomes_subject_id", "subject_id"),
        Index("ix_career_outcomes_attempt_id", "attempt_id"),
        Index("ix_career_outcomes_outcome_kind", "outcome_kind"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_attempts.id", ondelete="RESTRICT"),
        nullable=True,
    )
    outcome_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CareerFeedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Lifecycle feedback signal — distinct from audit FeedbackRecord."""

    __tablename__ = "career_feedback"
    __table_args__ = (
        Index("ix_career_feedback_subject_id", "subject_id"),
        Index("ix_career_feedback_goal_id", "goal_id"),
        Index("ix_career_feedback_recommendation_id", "recommendation_id"),
        Index("ix_career_feedback_attempt_id", "attempt_id"),
        Index("ix_career_feedback_outcome_id", "outcome_id"),
        Index("ix_career_feedback_feedback_kind", "feedback_kind"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_goals.id", ondelete="RESTRICT"),
        nullable=True,
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_recommendations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_attempts.id", ondelete="RESTRICT"),
        nullable=True,
    )
    outcome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_outcomes.id", ondelete="RESTRICT"),
        nullable=True,
    )
    feedback_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
