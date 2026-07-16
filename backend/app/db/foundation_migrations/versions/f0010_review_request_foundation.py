# ruff: noqa: UP007,UP035
"""f0010_review_request_foundation — private review_requests skeleton.

Revision ID: f0010_review_request_foundation
Revises: f0009_evidence_foundation
Create Date: 2026-07-16

User request/cancel only. A review request is not verification.
No approval/rejection tables. No claim status mutation.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0010_review_request_foundation"
down_revision: Union[str, None] = "f0009_evidence_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_requests",
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_state", sa.String(length=64), nullable=False),
        sa.Column("reviewer_type", sa.String(length=64), nullable=True),
        sa.Column("request_note", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_by_actor_type", sa.String(length=64), nullable=True),
        sa.Column(
            "created_by_actor_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
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
            ["owner_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["career_subjects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["career_claims.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_review_requests_owner_user_id",
        "review_requests",
        ["owner_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_review_requests_subject_id",
        "review_requests",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        "ix_review_requests_claim_id",
        "review_requests",
        ["claim_id"],
        unique=False,
    )
    op.create_index(
        "ix_review_requests_review_state",
        "review_requests",
        ["review_state"],
        unique=False,
    )
    op.create_index(
        "ix_review_requests_created_at",
        "review_requests",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "uq_review_requests_active_claim",
        "review_requests",
        ["claim_id"],
        unique=True,
        postgresql_where=sa.text("review_state = 'requested'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_review_requests_active_claim",
        table_name="review_requests",
        postgresql_where=sa.text("review_state = 'requested'"),
    )
    op.drop_index("ix_review_requests_created_at", table_name="review_requests")
    op.drop_index("ix_review_requests_review_state", table_name="review_requests")
    op.drop_index("ix_review_requests_claim_id", table_name="review_requests")
    op.drop_index("ix_review_requests_subject_id", table_name="review_requests")
    op.drop_index("ix_review_requests_owner_user_id", table_name="review_requests")
    op.drop_table("review_requests")
