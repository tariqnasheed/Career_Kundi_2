"""Passport persistence + migration journey tests (0052-F2)."""

from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401
from app.core.security import hash_password
from app.db.base import Base
from app.db.migration_runner import (
    FOUNDATION_VERSION_TABLE,
    build_foundation_alembic_config,
    foundation_heads,
    prepare_database,
    read_foundation_revisions,
)
from app.db.models.passport import CareerPassport, PassportTarget
from app.db.models.profile import (
    Certification,
    Education,
    Profile,
    Project,
    Skill,
    WorkExperience,
)
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.schemas.profile import (
    CertificationIn,
    EducationIn,
    ProfileRead,
    ProjectIn,
    SkillIn,
    WorkExperienceIn,
)

F2_PREFIX = "ck_pf1r1a_"
F0007 = "f0007_privacy_foundation"
F0008 = "f0008_passport_persistence"
FORBIDDEN_PASSPORT_SECTION_TABLES = {
    "passport_profiles",
    "passport_experiences",
    "passport_educations",
    "passport_projects",
    "passport_skills",
    "passport_credentials",
}
PROFILE_BACKED_META = {
    "source_status": "user_asserted",
    "support_status": "profile_supported",
    "verification_status": "unverified",
}
NATIVE_META = {
    "source_status": "user_asserted",
    "support_status": "not_provided",
    "verification_status": "unverified",
}


def _include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name == FOUNDATION_VERSION_TABLE:
        return False
    return True


def _drift(engine) -> list:
    with engine.connect() as conn:
        mc = MigrationContext.configure(
            conn,
            opts={
                "version_table": FOUNDATION_VERSION_TABLE,
                "version_table_schema": "public",
                "include_object": _include_object,
            },
        )
        return compare_metadata(mc, Base.metadata)


def _insert_legacy_user_profile_sections(sync_url: str) -> dict:
    """Insert legacy Profile data while DB is at F7 (no Passport columns yet)."""
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    uid = uuid.uuid4()
    pid = uuid.uuid4()
    we_id = uuid.uuid4()
    ed_id = uuid.uuid4()
    pr_id = uuid.uuid4()
    sk_id = uuid.uuid4()
    cert_id = uuid.uuid4()
    try:
        with Session() as session:
            session.add(
                User(
                    id=uid,
                    email=f"f2-{uid.hex[:8]}@example.com",
                    hashed_password=hash_password("test-password-ok"),
                    full_name="F2 Legacy User",
                    role=UserRole.USER,
                    plan=SubscriptionPlan.FREE,
                    is_active=True,
                    is_email_verified=False,
                )
            )
            session.flush()
            session.add(
                Profile(
                    id=pid,
                    user_id=uid,
                    professional_headline="Legacy headline",
                    bio_summary="Legacy bio",
                )
            )
            session.flush()
            # Insert section rows via raw SQL so F7 schema (pre-Passport columns) works
            # even when ORM metadata already includes F8 columns.
            session.execute(
                text(
                    """
                    INSERT INTO work_experiences
                      (id, profile_id, job_title, company_name, is_current,
                       description_bullets, order_index)
                    VALUES
                      (:id, :profile_id, :job_title, :company_name, false,
                       CAST(:bullets AS json), 0)
                    """
                ),
                {
                    "id": we_id,
                    "profile_id": pid,
                    "job_title": "Engineer",
                    "company_name": "Acme",
                    "bullets": "[]",
                },
            )
            session.execute(
                text(
                    """
                    INSERT INTO educations
                      (id, profile_id, degree, institution, is_current,
                       description_bullets, relevant_coursework, order_index)
                    VALUES
                      (:id, :profile_id, :degree, :institution, false,
                       CAST(:bullets AS json), CAST(:coursework AS json), 0)
                    """
                ),
                {
                    "id": ed_id,
                    "profile_id": pid,
                    "degree": "BSc",
                    "institution": "State U",
                    "bullets": "[]",
                    "coursework": "[]",
                },
            )
            session.execute(
                text(
                    """
                    INSERT INTO projects
                      (id, profile_id, title, technologies, key_achievements, order_index)
                    VALUES
                      (:id, :profile_id, :title, CAST(:tech AS json),
                       CAST(:achievements AS json), 0)
                    """
                ),
                {
                    "id": pr_id,
                    "profile_id": pid,
                    "title": "Portfolio Site",
                    "tech": '["Python"]',
                    "achievements": "[]",
                },
            )
            session.execute(
                text(
                    """
                    INSERT INTO skills
                      (id, profile_id, name, skill_type, order_index)
                    VALUES
                      (:id, :profile_id, :name, :skill_type, 0)
                    """
                ),
                {
                    "id": sk_id,
                    "profile_id": pid,
                    "name": "Python",
                    "skill_type": "technical",
                },
            )
            session.execute(
                text(
                    """
                    INSERT INTO certifications
                      (id, profile_id, name, issuing_organization, order_index)
                    VALUES
                      (:id, :profile_id, :name, :org, 0)
                    """
                ),
                {
                    "id": cert_id,
                    "profile_id": pid,
                    "name": "AWS CCP",
                    "org": "Amazon",
                },
            )
            session.commit()
    finally:
        engine.dispose()
    return {
        "user_id": uid,
        "profile_id": pid,
        "work_experience_id": we_id,
        "education_id": ed_id,
        "project_id": pr_id,
        "skill_id": sk_id,
        "certification_id": cert_id,
        "headline": "Legacy headline",
        "bio": "Legacy bio",
        "job_title": "Engineer",
        "company_name": "Acme",
        "degree": "BSc",
        "institution": "State U",
        "project_title": "Portfolio Site",
        "skill_name": "Python",
        "cert_name": "AWS CCP",
        "cert_org": "Amazon",
    }


def test_orm_metadata_contains_passport_tables() -> None:
    tables = set(Base.metadata.tables)
    assert "career_passports" in tables
    assert "passport_targets" in tables
    for forbidden in FORBIDDEN_PASSPORT_SECTION_TABLES:
        assert forbidden not in tables


def test_no_taxonomy_id_foreign_keys() -> None:
    for table_name in ("career_passports", "passport_targets"):
        table = Base.metadata.tables[table_name]
        for fk in table.foreign_keys:
            referred = fk.column.table.name
            assert referred in {
                "users",
                "profiles",
                "career_subjects",
                "career_passports",
            }


def test_subject_nullable_and_fk_delete_rules() -> None:
    cp = Base.metadata.tables["career_passports"]
    assert cp.c.subject_id.nullable is True
    owner_fk = next(fk for fk in cp.foreign_keys if fk.parent.name == "owner_user_id")
    profile_fk = next(fk for fk in cp.foreign_keys if fk.parent.name == "profile_id")
    subject_fk = next(fk for fk in cp.foreign_keys if fk.parent.name == "subject_id")
    assert owner_fk.ondelete == "CASCADE"
    assert profile_fk.ondelete == "CASCADE"
    assert subject_fk.ondelete == "SET NULL"
    targets = Base.metadata.tables["passport_targets"]
    target_fk = next(fk for fk in targets.foreign_keys if fk.parent.name == "passport_id")
    assert target_fk.ondelete == "CASCADE"


def test_visibility_and_version_defaults_and_checks() -> None:
    cp = Base.metadata.tables["career_passports"]
    assert str(cp.c.visibility.server_default.arg) == "private"
    assert str(cp.c.version.server_default.arg) == "1"
    check_names = {c.name for c in cp.constraints if c.name}
    assert "ck_career_passports_visibility_private" in check_names
    assert "ck_career_passports_version_positive" in check_names
    assert cp.c.section_preferences.type.__class__.__name__ == "JSONB"
    assert cp.c.profile_record_meta.type.__class__.__name__ == "JSONB"


def test_section_metadata_uses_jsonb() -> None:
    assert Base.metadata.tables["work_experiences"].c.passport_record_meta.type.__class__.__name__ == "JSONB"
    assert Base.metadata.tables["educations"].c.passport_record_meta.type.__class__.__name__ == "JSONB"
    assert Base.metadata.tables["projects"].c.passport_skill_taxonomy.type.__class__.__name__ == "JSONB"
    assert Base.metadata.tables["skills"].c.passport_record_meta.type.__class__.__name__ == "JSONB"
    assert Base.metadata.tables["certifications"].c.passport_record_meta.type.__class__.__name__ == "JSONB"


def test_passport_not_exported_from_contracts_package() -> None:
    import app.career_passport as pkg

    assert not hasattr(pkg, "CareerPassport") or not hasattr(
        getattr(pkg, "CareerPassport", None), "__tablename__"
    )
    assert "CareerPassport" not in getattr(pkg, "__all__", [])
    assert CareerPassport.__tablename__ == "career_passports"
    assert PassportTarget.__tablename__ == "passport_targets"


def test_profile_schemas_ignore_passport_fields() -> None:
    we = WorkExperienceIn(job_title="Eng", company_name="Acme")
    assert "passport_record_meta" not in WorkExperienceIn.model_fields
    assert "passport_record_meta" not in EducationIn.model_fields
    assert "passport_skill_taxonomy" not in ProjectIn.model_fields
    assert "passport_taxonomy" not in SkillIn.model_fields
    assert "passport_credential_type" not in CertificationIn.model_fields
    assert we.job_title == "Eng"


@require_disposable_postgres
def test_passport_persistence_migration_journey() -> None:
    with temporary_database(prefix=F2_PREFIX) as (_name, url):
        # A. Empty upgrade to head
        result = prepare_database(url)
        assert result.foundation_revisions == (F0008,)
        assert foundation_heads() == [F0008]
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert "career_passports" in tables
            assert "passport_targets" in tables
            assert not (FORBIDDEN_PASSPORT_SECTION_TABLES & tables)
            we_cols = {c["name"] for c in inspect(engine).get_columns("work_experiences")}
            assert "passport_role_taxonomy" in we_cols
            assert "passport_record_meta" in we_cols
            proj_cols = {c["name"] for c in inspect(engine).get_columns("projects")}
            assert "passport_skill_taxonomy" in proj_cols
            cert_cols = {c["name"] for c in inspect(engine).get_columns("certifications")}
            assert "passport_credential_type" in cert_cols
            idxs = {i["name"] for i in inspect(engine).get_indexes("career_passports")}
            assert "ix_career_passports_subject_id" in idxs
            with engine.connect() as conn:
                assert (
                    conn.execute(text("SELECT COUNT(*) FROM career_passports")).scalar()
                    == 0
                )
                assert (
                    conn.execute(text("SELECT COUNT(*) FROM passport_targets")).scalar()
                    == 0
                )

            # B. Legacy-data upgrade path
            cfg = build_foundation_alembic_config()
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0007)
            assert "career_passports" not in set(inspect(engine).get_table_names())
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (F0007,)

            legacy = _insert_legacy_user_profile_sections(url)

            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (F0008,)
                row = conn.execute(
                    text(
                        "SELECT job_title, company_name, passport_record_meta "
                        "FROM work_experiences WHERE id = :id"
                    ),
                    {"id": legacy["work_experience_id"]},
                ).mappings().one()
                assert row["job_title"] == legacy["job_title"]
                assert row["company_name"] == legacy["company_name"]
                assert row["passport_record_meta"] == PROFILE_BACKED_META

                edu = conn.execute(
                    text(
                        "SELECT degree, institution, passport_record_meta "
                        "FROM educations WHERE id = :id"
                    ),
                    {"id": legacy["education_id"]},
                ).mappings().one()
                assert edu["degree"] == legacy["degree"]
                assert edu["passport_record_meta"] == PROFILE_BACKED_META

                proj = conn.execute(
                    text(
                        "SELECT title, passport_skill_taxonomy, passport_record_meta "
                        "FROM projects WHERE id = :id"
                    ),
                    {"id": legacy["project_id"]},
                ).mappings().one()
                assert proj["title"] == legacy["project_title"]
                assert proj["passport_skill_taxonomy"] == []
                assert proj["passport_record_meta"] == PROFILE_BACKED_META

                skill = conn.execute(
                    text(
                        "SELECT name, passport_record_meta FROM skills WHERE id = :id"
                    ),
                    {"id": legacy["skill_id"]},
                ).mappings().one()
                assert skill["name"] == legacy["skill_name"]
                assert skill["passport_record_meta"] == PROFILE_BACKED_META

                cert = conn.execute(
                    text(
                        "SELECT name, issuing_organization, passport_credential_type, "
                        "passport_record_meta FROM certifications WHERE id = :id"
                    ),
                    {"id": legacy["certification_id"]},
                ).mappings().one()
                assert cert["name"] == legacy["cert_name"]
                assert cert["issuing_organization"] == legacy["cert_org"]
                assert cert["passport_credential_type"] == "certification"
                assert cert["passport_record_meta"] == PROFILE_BACKED_META

                assert (
                    conn.execute(text("SELECT COUNT(*) FROM career_passports")).scalar()
                    == 0
                )

            # C. Persistence
            Session = sessionmaker(bind=engine)
            passport_id = uuid.uuid4()
            target_id = uuid.uuid4()
            with Session() as session:
                passport = CareerPassport(
                    id=passport_id,
                    owner_user_id=legacy["user_id"],
                    profile_id=legacy["profile_id"],
                    subject_id=None,
                )
                session.add(passport)
                session.flush()
                assert passport.visibility == "private"
                assert passport.version == 1
                assert isinstance(passport.section_preferences, list)
                assert len(passport.section_preferences) == 7
                assert passport.profile_record_meta == PROFILE_BACKED_META
                session.add(
                    PassportTarget(
                        id=target_id,
                        passport_id=passport_id,
                        target_role_text="Staff Engineer",
                        order_index=0,
                        priority=3,
                    )
                )
                session.commit()

            with Session() as session:
                target = session.get(PassportTarget, target_id)
                assert target is not None
                assert target.order_index == 0
                assert target.passport_record_meta == NATIVE_META

                other_user = User(
                    id=uuid.uuid4(),
                    email=f"f2b-{uuid.uuid4().hex[:8]}@example.com",
                    hashed_password=hash_password("test-password-ok"),
                    full_name="Other",
                    role=UserRole.USER,
                    plan=SubscriptionPlan.FREE,
                    is_active=True,
                    is_email_verified=False,
                )
                session.add(other_user)
                session.flush()
                other_profile = Profile(
                    id=uuid.uuid4(),
                    user_id=other_user.id,
                    professional_headline="other",
                )
                session.add(other_profile)
                session.flush()

                # Unique owner_user_id
                with pytest.raises(IntegrityError):
                    session.add(
                        CareerPassport(
                            id=uuid.uuid4(),
                            owner_user_id=legacy["user_id"],
                            profile_id=other_profile.id,
                            subject_id=None,
                        )
                    )
                    session.flush()
                session.rollback()

                # Unique profile_id
                with pytest.raises(IntegrityError):
                    session.add(
                        CareerPassport(
                            id=uuid.uuid4(),
                            owner_user_id=other_user.id,
                            profile_id=legacy["profile_id"],
                            subject_id=None,
                        )
                    )
                    session.flush()
                session.rollback()

                # Cascade: delete passport removes targets, keeps profile
                session.delete(session.get(CareerPassport, passport_id))
                session.commit()
                assert session.get(PassportTarget, target_id) is None
                assert session.get(Profile, legacy["profile_id"]) is not None
                assert session.get(User, legacy["user_id"]) is not None

            # Recreate for subject nullability + downgrade
            with Session() as session:
                passport = CareerPassport(
                    id=passport_id,
                    owner_user_id=legacy["user_id"],
                    profile_id=legacy["profile_id"],
                    subject_id=None,
                )
                session.add(passport)
                session.add(
                    PassportTarget(
                        id=target_id,
                        passport_id=passport_id,
                        target_role_text="Staff Engineer",
                    )
                )
                session.commit()

            # Constraint: visibility and version
            with engine.begin() as conn:
                with pytest.raises(Exception):
                    conn.execute(
                        text(
                            "UPDATE career_passports SET visibility = 'public' "
                            "WHERE id = :id"
                        ),
                        {"id": passport_id},
                    )
            with engine.begin() as conn:
                with pytest.raises(Exception):
                    conn.execute(
                        text(
                            "UPDATE career_passports SET version = 0 WHERE id = :id"
                        ),
                        {"id": passport_id},
                    )

            # D. Downgrade preserves legacy Profile values
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0007)
            tables_after = set(inspect(engine).get_table_names())
            assert "career_passports" not in tables_after
            assert "passport_targets" not in tables_after
            assert "profiles" in tables_after
            assert "work_experiences" in tables_after
            we_cols_d = {c["name"] for c in inspect(engine).get_columns("work_experiences")}
            assert "passport_record_meta" not in we_cols_d
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (F0007,)
                preserved = conn.execute(
                    text(
                        "SELECT job_title, company_name FROM work_experiences "
                        "WHERE id = :id"
                    ),
                    {"id": legacy["work_experience_id"]},
                ).mappings().one()
                assert preserved["job_title"] == legacy["job_title"]
                assert preserved["company_name"] == legacy["company_name"]
                profile_row = conn.execute(
                    text(
                        "SELECT professional_headline, bio_summary FROM profiles "
                        "WHERE id = :id"
                    ),
                    {"id": legacy["profile_id"]},
                ).mappings().one()
                assert profile_row["professional_headline"] == legacy["headline"]
                assert profile_row["bio_summary"] == legacy["bio"]

            # E. Re-upgrade
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (F0008,)
                meta = conn.execute(
                    text(
                        "SELECT passport_record_meta, passport_skill_taxonomy "
                        "FROM projects WHERE id = :id"
                    ),
                    {"id": legacy["project_id"]},
                ).mappings().one()
                assert meta["passport_record_meta"] == PROFILE_BACKED_META
                assert meta["passport_skill_taxonomy"] == []
                assert (
                    conn.execute(
                        text(
                            "SELECT passport_credential_type FROM certifications "
                            "WHERE id = :id"
                        ),
                        {"id": legacy["certification_id"]},
                    ).scalar()
                    == "certification"
                )

            diffs = _drift(engine)
            assert diffs == [], diffs

            # Profile schema compatibility: ORM defaults + ProfileRead serialization
            with Session() as session:
                we = WorkExperience(
                    profile_id=legacy["profile_id"],
                    job_title="Compat Eng",
                    company_name="Compat Co",
                    order_index=1,
                )
                session.add(we)
                session.flush()
                assert we.passport_record_meta == PROFILE_BACKED_META
                profile = session.get(Profile, legacy["profile_id"])
                assert profile is not None
                # Ensure relationship load works for CV-style snapshot fields
                _ = profile.work_experiences
                _ = profile.educations
                _ = profile.projects
                _ = profile.skills
                _ = profile.certifications
                read = ProfileRead.model_validate(profile)
                assert read.professional_headline == legacy["headline"]
                assert read.bio_summary == legacy["bio"]
                assert all(
                    not hasattr(item, "passport_record_meta")
                    for item in read.work_experiences
                )
                session.commit()
        finally:
            engine.dispose()


def test_f0008_migration_ast_guards() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "foundation_migrations"
        / "versions"
        / "f0008_passport_persistence.py"
    )
    import ast

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"create_all", "drop_all"}
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("app.db.models")
            assert mod != "app.db.base"
