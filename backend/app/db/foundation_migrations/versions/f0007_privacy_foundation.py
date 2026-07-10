# ruff: noqa: UP007,UP035
"""f0007_privacy_foundation — privacy policy / consent / retention stubs.

Revision ID: f0007_privacy_foundation
Revises: f0006_lifecycle_loop_foundation
Create Date: 2026-07-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0007_privacy_foundation"
down_revision: Union[str, None] = "f0006_lifecycle_loop_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "privacy_policies",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("data_classification", sa.String(length=64), nullable=False),
        sa.Column("visibility_scope", sa.String(length=64), nullable=False),
        sa.Column("processing_purpose", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
    op.create_index("ix_privacy_policies_subject_id", "privacy_policies", ["subject_id"])
    op.create_index(
        "ix_privacy_policies_data_classification",
        "privacy_policies",
        ["data_classification"],
    )
    op.create_index(
        "ix_privacy_policies_visibility_scope",
        "privacy_policies",
        ["visibility_scope"],
    )
    op.create_index(
        "ix_privacy_policies_processing_purpose",
        "privacy_policies",
        ["processing_purpose"],
    )

    op.create_table(
        "consent_records",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("processing_purpose", sa.String(length=64), nullable=False),
        sa.Column("consent_status", sa.String(length=64), nullable=False),
        sa.Column("granted_by_actor_type", sa.String(length=64), nullable=True),
        sa.Column(
            "granted_by_actor_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index("ix_consent_records_subject_id", "consent_records", ["subject_id"])
    op.create_index(
        "ix_consent_records_processing_purpose",
        "consent_records",
        ["processing_purpose"],
    )
    op.create_index(
        "ix_consent_records_consent_status", "consent_records", ["consent_status"]
    )

    op.create_table(
        "retention_policies",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("retention_category", sa.String(length=64), nullable=False),
        sa.Column("processing_purpose", sa.String(length=64), nullable=True),
        sa.Column("retain_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
    op.create_index(
        "ix_retention_policies_subject_id", "retention_policies", ["subject_id"]
    )
    op.create_index(
        "ix_retention_policies_retention_category",
        "retention_policies",
        ["retention_category"],
    )
    op.create_index(
        "ix_retention_policies_processing_purpose",
        "retention_policies",
        ["processing_purpose"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_retention_policies_processing_purpose",
        table_name="retention_policies",
    )
    op.drop_index(
        "ix_retention_policies_retention_category",
        table_name="retention_policies",
    )
    op.drop_index("ix_retention_policies_subject_id", table_name="retention_policies")
    op.drop_table("retention_policies")

    op.drop_index("ix_consent_records_consent_status", table_name="consent_records")
    op.drop_index(
        "ix_consent_records_processing_purpose", table_name="consent_records"
    )
    op.drop_index("ix_consent_records_subject_id", table_name="consent_records")
    op.drop_table("consent_records")

    op.drop_index(
        "ix_privacy_policies_processing_purpose", table_name="privacy_policies"
    )
    op.drop_index(
        "ix_privacy_policies_visibility_scope", table_name="privacy_policies"
    )
    op.drop_index(
        "ix_privacy_policies_data_classification", table_name="privacy_policies"
    )
    op.drop_index("ix_privacy_policies_subject_id", table_name="privacy_policies")
    op.drop_table("privacy_policies")
