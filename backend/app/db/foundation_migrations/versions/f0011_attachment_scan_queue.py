# ruff: noqa: UP007,UP035
"""f0011_attachment_scan_queue — private attachment scan jobs.

Revision ID: f0011_attachment_scan_queue
Revises: f0010_review_request_foundation
Create Date: 2026-07-17

Queue skeleton only. A queued scan job is not a completed scan and is not
verification. No scanner engine, quarantine storage, or public sharing.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0011_attachment_scan_queue"
down_revision: Union[str, None] = "f0010_review_request_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attachment_scan_jobs",
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_hash_snapshot", sa.String(length=128), nullable=False),
        sa.Column("mime_type_snapshot", sa.String(length=128), nullable=True),
        sa.Column("size_bytes_snapshot", sa.BigInteger(), nullable=True),
        sa.Column("job_status", sa.String(length=64), nullable=False),
        sa.Column("attachment_safety_status", sa.String(length=64), nullable=False),
        sa.Column("engine_name", sa.String(length=128), nullable=True),
        sa.Column("engine_version", sa.String(length=128), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("safe_error_code", sa.String(length=128), nullable=True),
        sa.Column("safe_error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            ["evidence_id"],
            ["evidence_records.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_attachment_scan_jobs_owner_user_id",
        "attachment_scan_jobs",
        ["owner_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_attachment_scan_jobs_evidence_id",
        "attachment_scan_jobs",
        ["evidence_id"],
        unique=False,
    )
    op.create_index(
        "ix_attachment_scan_jobs_job_status",
        "attachment_scan_jobs",
        ["job_status"],
        unique=False,
    )
    op.create_index(
        "ix_attachment_scan_jobs_attachment_safety_status",
        "attachment_scan_jobs",
        ["attachment_safety_status"],
        unique=False,
    )
    op.create_index(
        "ix_attachment_scan_jobs_created_at",
        "attachment_scan_jobs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_attachment_scan_jobs_evidence_content_hash",
        "attachment_scan_jobs",
        ["evidence_id", "content_hash_snapshot"],
        unique=False,
    )
    op.create_index(
        "uq_attachment_scan_jobs_active_evidence_hash",
        "attachment_scan_jobs",
        ["evidence_id", "content_hash_snapshot"],
        unique=True,
        postgresql_where=sa.text("job_status IN ('queued', 'reserved')"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_attachment_scan_jobs_active_evidence_hash",
        table_name="attachment_scan_jobs",
        postgresql_where=sa.text("job_status IN ('queued', 'reserved')"),
    )
    op.drop_index(
        "ix_attachment_scan_jobs_evidence_content_hash",
        table_name="attachment_scan_jobs",
    )
    op.drop_index(
        "ix_attachment_scan_jobs_created_at",
        table_name="attachment_scan_jobs",
    )
    op.drop_index(
        "ix_attachment_scan_jobs_attachment_safety_status",
        table_name="attachment_scan_jobs",
    )
    op.drop_index(
        "ix_attachment_scan_jobs_job_status",
        table_name="attachment_scan_jobs",
    )
    op.drop_index(
        "ix_attachment_scan_jobs_evidence_id",
        table_name="attachment_scan_jobs",
    )
    op.drop_index(
        "ix_attachment_scan_jobs_owner_user_id",
        table_name="attachment_scan_jobs",
    )
    op.drop_table("attachment_scan_jobs")
