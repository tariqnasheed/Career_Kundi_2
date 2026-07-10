# ruff: noqa: UP007,UP035
"""f0004_claim_foundation — ClaimRecord storage stub.

Revision ID: f0004_claim_foundation
Revises: f0003_provenance_source_snapshot
Create Date: 2026-07-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0004_claim_foundation"
down_revision: Union[str, None] = "f0003_provenance_source_snapshot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_claims",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_kind", sa.String(length=64), nullable=False),
        sa.Column("claim_key", sa.String(length=256), nullable=False),
        sa.Column("claim_value", sa.Text(), nullable=False),
        sa.Column("claim_origin", sa.String(length=64), nullable=False),
        sa.Column("support_status", sa.String(length=64), nullable=False),
        sa.Column("verification_status", sa.String(length=64), nullable=False),
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
            ["subject_id"],
            ["career_subjects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["provenance_sources.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["provenance_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_career_claims_subject_id", "career_claims", ["subject_id"], unique=False
    )
    op.create_index(
        "ix_career_claims_claim_kind", "career_claims", ["claim_kind"], unique=False
    )
    op.create_index(
        "ix_career_claims_claim_key", "career_claims", ["claim_key"], unique=False
    )
    op.create_index(
        "ix_career_claims_support_status",
        "career_claims",
        ["support_status"],
        unique=False,
    )
    op.create_index(
        "ix_career_claims_verification_status",
        "career_claims",
        ["verification_status"],
        unique=False,
    )
    op.create_index(
        "ix_career_claims_source_id", "career_claims", ["source_id"], unique=False
    )
    op.create_index(
        "ix_career_claims_snapshot_id",
        "career_claims",
        ["snapshot_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_career_claims_snapshot_id", table_name="career_claims")
    op.drop_index("ix_career_claims_source_id", table_name="career_claims")
    op.drop_index("ix_career_claims_verification_status", table_name="career_claims")
    op.drop_index("ix_career_claims_support_status", table_name="career_claims")
    op.drop_index("ix_career_claims_claim_key", table_name="career_claims")
    op.drop_index("ix_career_claims_claim_kind", table_name="career_claims")
    op.drop_index("ix_career_claims_subject_id", table_name="career_claims")
    op.drop_table("career_claims")
