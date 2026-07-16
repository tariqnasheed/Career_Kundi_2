# ruff: noqa: UP007,UP035
"""f0009_evidence_foundation — EvidenceRecord + ClaimEvidenceLink metadata.

Revision ID: f0009_evidence_foundation
Revises: f0008_passport_persistence
Create Date: 2026-07-16

Private evidence metadata only. No file blobs, no verification tables,
no public sharing tables. Linking evidence does not verify claims.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0009_evidence_foundation"
down_revision: Union[str, None] = "f0008_passport_persistence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence_records",
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("evidence_kind", sa.String(length=64), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("privacy_class", sa.String(length=64), nullable=False),
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
        "ix_evidence_records_owner_user_id",
        "evidence_records",
        ["owner_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_evidence_records_subject_id",
        "evidence_records",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        "ix_evidence_records_evidence_kind",
        "evidence_records",
        ["evidence_kind"],
        unique=False,
    )
    op.create_index(
        "ix_evidence_records_privacy_class",
        "evidence_records",
        ["privacy_class"],
        unique=False,
    )
    op.create_index(
        "ix_evidence_records_source_id",
        "evidence_records",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        "ix_evidence_records_snapshot_id",
        "evidence_records",
        ["snapshot_id"],
        unique=False,
    )
    op.create_index(
        "ix_evidence_records_created_at",
        "evidence_records",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "claim_evidence_links",
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("link_role", sa.String(length=64), nullable=False),
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
            ["claim_id"],
            ["career_claims.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence_records.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "claim_id",
            "evidence_id",
            name="uq_claim_evidence_links_claim_evidence",
        ),
    )
    op.create_index(
        "ix_claim_evidence_links_claim_id",
        "claim_evidence_links",
        ["claim_id"],
        unique=False,
    )
    op.create_index(
        "ix_claim_evidence_links_evidence_id",
        "claim_evidence_links",
        ["evidence_id"],
        unique=False,
    )
    op.create_index(
        "ix_claim_evidence_links_link_role",
        "claim_evidence_links",
        ["link_role"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_claim_evidence_links_link_role", table_name="claim_evidence_links"
    )
    op.drop_index(
        "ix_claim_evidence_links_evidence_id", table_name="claim_evidence_links"
    )
    op.drop_index(
        "ix_claim_evidence_links_claim_id", table_name="claim_evidence_links"
    )
    op.drop_table("claim_evidence_links")
    op.drop_index(
        "ix_evidence_records_created_at", table_name="evidence_records"
    )
    op.drop_index(
        "ix_evidence_records_snapshot_id", table_name="evidence_records"
    )
    op.drop_index("ix_evidence_records_source_id", table_name="evidence_records")
    op.drop_index(
        "ix_evidence_records_privacy_class", table_name="evidence_records"
    )
    op.drop_index(
        "ix_evidence_records_evidence_kind", table_name="evidence_records"
    )
    op.drop_index("ix_evidence_records_subject_id", table_name="evidence_records")
    op.drop_index(
        "ix_evidence_records_owner_user_id", table_name="evidence_records"
    )
    op.drop_table("evidence_records")
