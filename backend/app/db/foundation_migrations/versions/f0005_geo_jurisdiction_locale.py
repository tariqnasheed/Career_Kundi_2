# ruff: noqa: UP007,UP035
"""f0005_geo_jurisdiction_locale — geo/jurisdiction/locale/auth-area stubs.

Revision ID: f0005_geo_jurisdiction_locale
Revises: f0004_claim_foundation
Create Date: 2026-07-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0005_geo_jurisdiction_locale"
down_revision: Union[str, None] = "f0004_claim_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "geo_areas",
        sa.Column("geo_kind", sa.String(length=64), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("parent_geo_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["parent_geo_id"],
            ["geo_areas.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_geo_areas_geo_kind", "geo_areas", ["geo_kind"], unique=False)
    op.create_index("ix_geo_areas_code", "geo_areas", ["code"], unique=False)
    op.create_index(
        "ix_geo_areas_parent_geo_id", "geo_areas", ["parent_geo_id"], unique=False
    )

    op.create_table(
        "jurisdiction_areas",
        sa.Column("jurisdiction_kind", sa.String(length=64), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column(
            "parent_jurisdiction_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
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
            ["parent_jurisdiction_id"],
            ["jurisdiction_areas.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_jurisdiction_areas_jurisdiction_kind",
        "jurisdiction_areas",
        ["jurisdiction_kind"],
        unique=False,
    )
    op.create_index(
        "ix_jurisdiction_areas_code", "jurisdiction_areas", ["code"], unique=False
    )
    op.create_index(
        "ix_jurisdiction_areas_parent_jurisdiction_id",
        "jurisdiction_areas",
        ["parent_jurisdiction_id"],
        unique=False,
    )

    op.create_table(
        "locale_profiles",
        sa.Column("locale_kind", sa.String(length=64), nullable=False),
        sa.Column("locale_code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
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
        "ix_locale_profiles_locale_code",
        "locale_profiles",
        ["locale_code"],
        unique=False,
    )
    op.create_index(
        "ix_locale_profiles_locale_kind",
        "locale_profiles",
        ["locale_kind"],
        unique=False,
    )

    op.create_table(
        "work_authorization_areas",
        sa.Column("authorization_kind", sa.String(length=64), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
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
        "ix_work_authorization_areas_authorization_kind",
        "work_authorization_areas",
        ["authorization_kind"],
        unique=False,
    )
    op.create_index(
        "ix_work_authorization_areas_code",
        "work_authorization_areas",
        ["code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_work_authorization_areas_code",
        table_name="work_authorization_areas",
    )
    op.drop_index(
        "ix_work_authorization_areas_authorization_kind",
        table_name="work_authorization_areas",
    )
    op.drop_table("work_authorization_areas")

    op.drop_index("ix_locale_profiles_locale_kind", table_name="locale_profiles")
    op.drop_index("ix_locale_profiles_locale_code", table_name="locale_profiles")
    op.drop_table("locale_profiles")

    op.drop_index(
        "ix_jurisdiction_areas_parent_jurisdiction_id",
        table_name="jurisdiction_areas",
    )
    op.drop_index("ix_jurisdiction_areas_code", table_name="jurisdiction_areas")
    op.drop_index(
        "ix_jurisdiction_areas_jurisdiction_kind",
        table_name="jurisdiction_areas",
    )
    op.drop_table("jurisdiction_areas")

    op.drop_index("ix_geo_areas_parent_geo_id", table_name="geo_areas")
    op.drop_index("ix_geo_areas_code", table_name="geo_areas")
    op.drop_index("ix_geo_areas_geo_kind", table_name="geo_areas")
    op.drop_table("geo_areas")
