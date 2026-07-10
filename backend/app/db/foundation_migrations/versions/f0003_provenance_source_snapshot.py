# ruff: noqa: UP007,UP035
"""f0003_provenance_source_snapshot — SourceRecord / SourceSnapshot tables.

Revision ID: f0003_provenance_source_snapshot
Revises: f0002_identity_subject_stub
Create Date: 2026-07-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0003_provenance_source_snapshot"
down_revision: Union[str, None] = "f0002_identity_subject_stub"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "provenance_sources",
        sa.Column("source_kind", sa.String(length=64), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("uri", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_provenance_sources_source_kind",
        "provenance_sources",
        ["source_kind"],
        unique=False,
    )

    op.create_table(
        "provenance_snapshots",
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("hash_algorithm", sa.String(length=64), nullable=True),
        sa.Column("storage_uri", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["provenance_sources.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_provenance_snapshots_source_id",
        "provenance_snapshots",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        "ix_provenance_snapshots_captured_at",
        "provenance_snapshots",
        ["captured_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_provenance_snapshots_captured_at", table_name="provenance_snapshots"
    )
    op.drop_index(
        "ix_provenance_snapshots_source_id", table_name="provenance_snapshots"
    )
    op.drop_table("provenance_snapshots")
    op.drop_index(
        "ix_provenance_sources_source_kind", table_name="provenance_sources"
    )
    op.drop_table("provenance_sources")
