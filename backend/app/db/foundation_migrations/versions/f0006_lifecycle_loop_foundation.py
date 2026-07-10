# ruff: noqa: UP007,UP035
"""f0006_lifecycle_loop_foundation — Goal/Recommendation/Attempt/Outcome/Feedback stubs.

Revision ID: f0006_lifecycle_loop_foundation
Revises: f0005_geo_jurisdiction_locale
Create Date: 2026-07-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0006_lifecycle_loop_foundation"
down_revision: Union[str, None] = "f0005_geo_jurisdiction_locale"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_goals",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("goal_kind", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_by_actor_type", sa.String(length=64), nullable=True),
        sa.Column(
            "created_by_actor_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["career_subjects.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_goals_subject_id", "career_goals", ["subject_id"])
    op.create_index("ix_career_goals_goal_kind", "career_goals", ["goal_kind"])
    op.create_index("ix_career_goals_status", "career_goals", ["status"])

    op.create_table(
        "career_recommendations",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation_kind", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_actor_type", sa.String(length=64), nullable=True),
        sa.Column(
            "created_by_actor_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["career_subjects.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["goal_id"], ["career_goals.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["provenance_sources.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"], ["provenance_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_career_recommendations_subject_id",
        "career_recommendations",
        ["subject_id"],
    )
    op.create_index(
        "ix_career_recommendations_goal_id", "career_recommendations", ["goal_id"]
    )
    op.create_index(
        "ix_career_recommendations_recommendation_kind",
        "career_recommendations",
        ["recommendation_kind"],
    )
    op.create_index(
        "ix_career_recommendations_status", "career_recommendations", ["status"]
    )
    op.create_index(
        "ix_career_recommendations_source_id",
        "career_recommendations",
        ["source_id"],
    )
    op.create_index(
        "ix_career_recommendations_snapshot_id",
        "career_recommendations",
        ["snapshot_id"],
    )

    op.create_table(
        "career_attempts",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attempt_kind", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_actor_type", sa.String(length=64), nullable=True),
        sa.Column(
            "created_by_actor_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["career_subjects.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["goal_id"], ["career_goals.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["career_recommendations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_attempts_subject_id", "career_attempts", ["subject_id"])
    op.create_index("ix_career_attempts_goal_id", "career_attempts", ["goal_id"])
    op.create_index(
        "ix_career_attempts_recommendation_id",
        "career_attempts",
        ["recommendation_id"],
    )
    op.create_index(
        "ix_career_attempts_attempt_kind", "career_attempts", ["attempt_kind"]
    )
    op.create_index("ix_career_attempts_status", "career_attempts", ["status"])

    op.create_table(
        "career_outcomes",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome_kind", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["career_subjects.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["career_attempts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_outcomes_subject_id", "career_outcomes", ["subject_id"])
    op.create_index("ix_career_outcomes_attempt_id", "career_outcomes", ["attempt_id"])
    op.create_index(
        "ix_career_outcomes_outcome_kind", "career_outcomes", ["outcome_kind"]
    )

    op.create_table(
        "career_feedback",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("feedback_kind", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_by_actor_type", sa.String(length=64), nullable=True),
        sa.Column(
            "created_by_actor_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["career_subjects.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["goal_id"], ["career_goals.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["career_recommendations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["career_attempts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["outcome_id"], ["career_outcomes.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_feedback_subject_id", "career_feedback", ["subject_id"])
    op.create_index("ix_career_feedback_goal_id", "career_feedback", ["goal_id"])
    op.create_index(
        "ix_career_feedback_recommendation_id",
        "career_feedback",
        ["recommendation_id"],
    )
    op.create_index("ix_career_feedback_attempt_id", "career_feedback", ["attempt_id"])
    op.create_index("ix_career_feedback_outcome_id", "career_feedback", ["outcome_id"])
    op.create_index(
        "ix_career_feedback_feedback_kind", "career_feedback", ["feedback_kind"]
    )


def downgrade() -> None:
    op.drop_index("ix_career_feedback_feedback_kind", table_name="career_feedback")
    op.drop_index("ix_career_feedback_outcome_id", table_name="career_feedback")
    op.drop_index("ix_career_feedback_attempt_id", table_name="career_feedback")
    op.drop_index(
        "ix_career_feedback_recommendation_id", table_name="career_feedback"
    )
    op.drop_index("ix_career_feedback_goal_id", table_name="career_feedback")
    op.drop_index("ix_career_feedback_subject_id", table_name="career_feedback")
    op.drop_table("career_feedback")

    op.drop_index("ix_career_outcomes_outcome_kind", table_name="career_outcomes")
    op.drop_index("ix_career_outcomes_attempt_id", table_name="career_outcomes")
    op.drop_index("ix_career_outcomes_subject_id", table_name="career_outcomes")
    op.drop_table("career_outcomes")

    op.drop_index("ix_career_attempts_status", table_name="career_attempts")
    op.drop_index("ix_career_attempts_attempt_kind", table_name="career_attempts")
    op.drop_index(
        "ix_career_attempts_recommendation_id", table_name="career_attempts"
    )
    op.drop_index("ix_career_attempts_goal_id", table_name="career_attempts")
    op.drop_index("ix_career_attempts_subject_id", table_name="career_attempts")
    op.drop_table("career_attempts")

    op.drop_index(
        "ix_career_recommendations_snapshot_id",
        table_name="career_recommendations",
    )
    op.drop_index(
        "ix_career_recommendations_source_id",
        table_name="career_recommendations",
    )
    op.drop_index(
        "ix_career_recommendations_status", table_name="career_recommendations"
    )
    op.drop_index(
        "ix_career_recommendations_recommendation_kind",
        table_name="career_recommendations",
    )
    op.drop_index(
        "ix_career_recommendations_goal_id", table_name="career_recommendations"
    )
    op.drop_index(
        "ix_career_recommendations_subject_id",
        table_name="career_recommendations",
    )
    op.drop_table("career_recommendations")

    op.drop_index("ix_career_goals_status", table_name="career_goals")
    op.drop_index("ix_career_goals_goal_kind", table_name="career_goals")
    op.drop_index("ix_career_goals_subject_id", table_name="career_goals")
    op.drop_table("career_goals")
