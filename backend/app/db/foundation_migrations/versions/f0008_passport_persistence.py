# ruff: noqa: UP007,UP035
"""f0008_passport_persistence — CareerPassport + PassportTarget + Profile section extensions.

Revision ID: f0008_passport_persistence
Revises: f0007_privacy_foundation
Create Date: 2026-07-13

Profile-wrapper strategy: new tables are career_passports and passport_targets only.
Existing Profile section tables are extended in place (no parallel Passport section tables).
No automatic CareerPassport / PassportTarget rows are created.
Downgrade drops Passport tables/columns only; legacy Profile data is preserved.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0008_passport_persistence"
down_revision: Union[str, None] = "f0007_privacy_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PROFILE_BACKED_META = (
    "'{"
    '"source_status": "user_asserted", '
    '"support_status": "profile_supported", '
    '"verification_status": "unverified"'
    "}'::jsonb"
)

_NATIVE_META = (
    "'{"
    '"source_status": "user_asserted", '
    '"support_status": "not_provided", '
    '"verification_status": "unverified"'
    "}'::jsonb"
)

_DEFAULT_SECTION_PREFS = (
    "'["
    '{"section": "profile", "order_index": 0, "enabled": true}, '
    '{"section": "experience", "order_index": 1, "enabled": true}, '
    '{"section": "education", "order_index": 2, "enabled": true}, '
    '{"section": "projects", "order_index": 3, "enabled": true}, '
    '{"section": "skills", "order_index": 4, "enabled": true}, '
    '{"section": "credentials", "order_index": 5, "enabled": true}, '
    '{"section": "targets", "order_index": 6, "enabled": true}'
    "]'::jsonb"
)


def upgrade() -> None:
    op.create_table(
        "career_passports",
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "visibility",
            sa.String(length=32),
            server_default="private",
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "section_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(_DEFAULT_SECTION_PREFS),
            nullable=False,
        ),
        sa.Column(
            "profile_record_meta",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(_PROFILE_BACKED_META),
            nullable=False,
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
        sa.CheckConstraint(
            "visibility = 'private'",
            name="ck_career_passports_visibility_private",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_career_passports_version_positive",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(section_preferences) = 'array'",
            name="ck_career_passports_section_preferences_is_array",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(profile_record_meta) = 'object'",
            name="ck_career_passports_profile_record_meta_is_object",
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["career_subjects.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id"),
        sa.UniqueConstraint("profile_id"),
    )
    op.create_index(
        "ix_career_passports_subject_id", "career_passports", ["subject_id"]
    )

    op.create_table(
        "passport_targets",
        sa.Column("passport_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_role_text", sa.String(length=255), nullable=False),
        sa.Column(
            "role_taxonomy",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("pathway_type", sa.String(length=64), nullable=True),
        sa.Column("target_country", sa.String(length=120), nullable=True),
        sa.Column("target_region", sa.String(length=120), nullable=True),
        sa.Column("target_industry", sa.String(length=160), nullable=True),
        sa.Column("target_seniority", sa.String(length=64), nullable=True),
        sa.Column("time_horizon", sa.String(length=120), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="3", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "passport_record_meta",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(_NATIVE_META),
            nullable=False,
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
        sa.CheckConstraint(
            "priority >= 1 AND priority <= 5",
            name="ck_passport_targets_priority_range",
        ),
        sa.CheckConstraint(
            "order_index >= 0",
            name="ck_passport_targets_order_index_nonnegative",
        ),
        sa.CheckConstraint(
            "role_taxonomy IS NULL OR jsonb_typeof(role_taxonomy) = 'object'",
            name="ck_passport_targets_role_taxonomy_object",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(passport_record_meta) = 'object'",
            name="ck_passport_targets_record_meta_is_object",
        ),
        sa.ForeignKeyConstraint(
            ["passport_id"], ["career_passports.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_passport_targets_passport_id", "passport_targets", ["passport_id"]
    )

    # --- Extend existing Profile section tables (nullable → backfill → NOT NULL) ---
    op.add_column(
        "work_experiences",
        sa.Column(
            "passport_role_taxonomy",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "work_experiences",
        sa.Column(
            "passport_record_meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE work_experiences SET passport_record_meta = "
            f"{_PROFILE_BACKED_META} WHERE passport_record_meta IS NULL"
        )
    )
    op.alter_column(
        "work_experiences",
        "passport_record_meta",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text(_PROFILE_BACKED_META),
    )
    op.create_check_constraint(
        "ck_work_experiences_passport_role_taxonomy_object",
        "work_experiences",
        "passport_role_taxonomy IS NULL OR jsonb_typeof(passport_role_taxonomy) = 'object'",
    )
    op.create_check_constraint(
        "ck_work_experiences_passport_record_meta_is_object",
        "work_experiences",
        "jsonb_typeof(passport_record_meta) = 'object'",
    )

    op.add_column(
        "educations",
        sa.Column(
            "passport_record_meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE educations SET passport_record_meta = "
            f"{_PROFILE_BACKED_META} WHERE passport_record_meta IS NULL"
        )
    )
    op.alter_column(
        "educations",
        "passport_record_meta",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text(_PROFILE_BACKED_META),
    )
    op.create_check_constraint(
        "ck_educations_passport_record_meta_is_object",
        "educations",
        "jsonb_typeof(passport_record_meta) = 'object'",
    )

    op.add_column(
        "projects",
        sa.Column(
            "passport_skill_taxonomy",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "passport_record_meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE projects SET passport_skill_taxonomy = '[]'::jsonb "
            "WHERE passport_skill_taxonomy IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE projects SET passport_record_meta = "
            f"{_PROFILE_BACKED_META} WHERE passport_record_meta IS NULL"
        )
    )
    op.alter_column(
        "projects",
        "passport_skill_taxonomy",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    )
    op.alter_column(
        "projects",
        "passport_record_meta",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text(_PROFILE_BACKED_META),
    )
    op.create_check_constraint(
        "ck_projects_passport_skill_taxonomy_is_array",
        "projects",
        "jsonb_typeof(passport_skill_taxonomy) = 'array'",
    )
    op.create_check_constraint(
        "ck_projects_passport_record_meta_is_object",
        "projects",
        "jsonb_typeof(passport_record_meta) = 'object'",
    )

    op.add_column(
        "skills",
        sa.Column(
            "passport_taxonomy",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "skills",
        sa.Column(
            "passport_record_meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE skills SET passport_record_meta = "
            f"{_PROFILE_BACKED_META} WHERE passport_record_meta IS NULL"
        )
    )
    op.alter_column(
        "skills",
        "passport_record_meta",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text(_PROFILE_BACKED_META),
    )
    op.create_check_constraint(
        "ck_skills_passport_taxonomy_object",
        "skills",
        "passport_taxonomy IS NULL OR jsonb_typeof(passport_taxonomy) = 'object'",
    )
    op.create_check_constraint(
        "ck_skills_passport_record_meta_is_object",
        "skills",
        "jsonb_typeof(passport_record_meta) = 'object'",
    )

    op.add_column(
        "certifications",
        sa.Column(
            "passport_credential_type",
            sa.String(length=64),
            nullable=True,
        ),
    )
    op.add_column(
        "certifications",
        sa.Column(
            "passport_record_meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE certifications SET passport_credential_type = 'certification' "
            "WHERE passport_credential_type IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE certifications SET passport_record_meta = "
            f"{_PROFILE_BACKED_META} WHERE passport_record_meta IS NULL"
        )
    )
    op.alter_column(
        "certifications",
        "passport_credential_type",
        existing_type=sa.String(length=64),
        nullable=False,
        server_default="certification",
    )
    op.alter_column(
        "certifications",
        "passport_record_meta",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text(_PROFILE_BACKED_META),
    )
    op.create_check_constraint(
        "ck_certifications_passport_credential_type",
        "certifications",
        "passport_credential_type IN ("
        "'certification', 'license', 'course_certificate', "
        "'education_award', 'professional_membership', 'other')",
    )
    op.create_check_constraint(
        "ck_certifications_passport_record_meta_is_object",
        "certifications",
        "jsonb_typeof(passport_record_meta) = 'object'",
    )


def downgrade() -> None:
    """Drop Passport persistence only. Legacy Profile tables and values remain."""

    op.drop_constraint(
        "ck_certifications_passport_record_meta_is_object",
        "certifications",
        type_="check",
    )
    op.drop_constraint(
        "ck_certifications_passport_credential_type",
        "certifications",
        type_="check",
    )
    op.drop_column("certifications", "passport_record_meta")
    op.drop_column("certifications", "passport_credential_type")

    op.drop_constraint(
        "ck_skills_passport_record_meta_is_object", "skills", type_="check"
    )
    op.drop_constraint(
        "ck_skills_passport_taxonomy_object", "skills", type_="check"
    )
    op.drop_column("skills", "passport_record_meta")
    op.drop_column("skills", "passport_taxonomy")

    op.drop_constraint(
        "ck_projects_passport_record_meta_is_object", "projects", type_="check"
    )
    op.drop_constraint(
        "ck_projects_passport_skill_taxonomy_is_array", "projects", type_="check"
    )
    op.drop_column("projects", "passport_record_meta")
    op.drop_column("projects", "passport_skill_taxonomy")

    op.drop_constraint(
        "ck_educations_passport_record_meta_is_object",
        "educations",
        type_="check",
    )
    op.drop_column("educations", "passport_record_meta")

    op.drop_constraint(
        "ck_work_experiences_passport_record_meta_is_object",
        "work_experiences",
        type_="check",
    )
    op.drop_constraint(
        "ck_work_experiences_passport_role_taxonomy_object",
        "work_experiences",
        type_="check",
    )
    op.drop_column("work_experiences", "passport_record_meta")
    op.drop_column("work_experiences", "passport_role_taxonomy")

    op.drop_index("ix_passport_targets_passport_id", table_name="passport_targets")
    op.drop_table("passport_targets")

    op.drop_index("ix_career_passports_subject_id", table_name="career_passports")
    op.drop_table("career_passports")
