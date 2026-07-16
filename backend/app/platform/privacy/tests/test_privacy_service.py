"""Privacy migration + service tests (0050-PF9-S1)."""

from __future__ import annotations

import ast
import asyncio
import inspect as pyinspect
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
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
from app.db.models.career_subject import CareerSubject
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import new_entity_id
from app.platform.privacy import (
    ConsentStatus,
    DataClassification,
    PrivacyRefError,
    ProcessingPurpose,
    RetentionCategory,
    VisibilityScope,
)
from app.platform.privacy import service as privacy_service
from app.platform.privacy.service import (
    create_consent_record,
    create_privacy_policy,
    create_retention_policy,
    get_consent_record,
    get_privacy_policy,
    list_subject_consent_records,
    list_subject_privacy_policies,
)

PF9_PREFIX = "ck_pf9s1_"
F0006 = "f0006_lifecycle_loop_foundation"
F0007 = "f0007_privacy_foundation"
CURRENT_HEAD = "f0009_evidence_foundation"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
    / "f0007_privacy_foundation.py"
)
PRIVACY_TABLES = {"privacy_policies", "consent_records", "retention_policies"}
PASSPORT_TABLES = {"career_passports", "passport_targets"}
FORBIDDEN_TABLES = {
    "privacy_requests",
    "data_exports",
    "data_deletion_jobs",
    "rights_requests",
    "admin_privacy_reviews",
}
FORBIDDEN_FN_NAMES = {
    "delete_expired_data",
    "run_retention_job",
    "erase_subject_data",
    "export_personal_data",
    "process_rights_request",
}


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str) -> uuid.UUID:
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    uid = uuid.uuid4()
    try:
        with Session() as session:
            session.add(
                User(
                    id=uid,
                    email=f"pf9-{uid.hex[:8]}@example.com",
                    hashed_password=hash_password("test-password-ok"),
                    full_name="PF9 User",
                    role=UserRole.USER,
                    plan=SubscriptionPlan.FREE,
                    is_active=True,
                    is_email_verified=False,
                )
            )
            session.commit()
    finally:
        engine.dispose()
    return uid


@require_disposable_postgres
def test_f0007_migration_empty_to_f0007() -> None:
    """Historical F7 journey: upgrade explicitly to F7, not current head."""
    with temporary_database(prefix=PF9_PREFIX) as (_name, url):
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, F0007)
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (F0007,)
            tables = set(inspect(engine).get_table_names())
            assert PRIVACY_TABLES.issubset(tables)
            assert not (FORBIDDEN_TABLES & tables)
            # Passport tables belong to F8 — absent at historical F7.
            assert not (PASSPORT_TABLES & tables)
            for table in PRIVACY_TABLES:
                fks = inspect(engine).get_foreign_keys(table)
                assert any(fk["referred_table"] == "career_subjects" for fk in fks)
            assert "ix_privacy_policies_subject_id" in {
                i["name"] for i in inspect(engine).get_indexes("privacy_policies")
            }
            assert "ix_consent_records_consent_status" in {
                i["name"] for i in inspect(engine).get_indexes("consent_records")
            }
            assert "ix_retention_policies_retention_category" in {
                i["name"] for i in inspect(engine).get_indexes("retention_policies")
            }
        finally:
            engine.dispose()


@require_disposable_postgres
def test_f0007_downgrade_historical_upgrade_then_current_head() -> None:
    """Downgrade privacy, restore F7 historically, then advance to current head."""
    with temporary_database(prefix=PF9_PREFIX) as (_name, url):
        prepare_database(url)
        assert foundation_heads() == [CURRENT_HEAD]
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0006)
            tables = set(inspect(engine).get_table_names())
            assert not (PRIVACY_TABLES & tables)
            assert not (PASSPORT_TABLES & tables)
            assert "career_goals" in tables

            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, F0007)
            tables_f7 = set(inspect(engine).get_table_names())
            assert PRIVACY_TABLES.issubset(tables_f7)
            assert not (PASSPORT_TABLES & tables_f7)
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (F0007,)

            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            tables_head = set(inspect(engine).get_table_names())
            assert PRIVACY_TABLES.issubset(tables_head)
            assert PASSPORT_TABLES.issubset(tables_head)
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (CURRENT_HEAD,)
        finally:
            engine.dispose()


@require_disposable_postgres
def test_drift_zero_at_head() -> None:
    with temporary_database(prefix=PF9_PREFIX) as (_name, url):
        prepare_database(url)
        assert foundation_heads() == [CURRENT_HEAD]
        engine = create_engine(url)

        def _include_object(object, name, type_, reflected, compare_to):
            if type_ == "table" and name == FOUNDATION_VERSION_TABLE:
                return False
            return True

        try:
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (CURRENT_HEAD,)
                mc = MigrationContext.configure(
                    conn,
                    opts={
                        "version_table": FOUNDATION_VERSION_TABLE,
                        "version_table_schema": "public",
                        "include_object": _include_object,
                    },
                )
                diffs = compare_metadata(mc, Base.metadata)
            assert diffs == [], diffs
        finally:
            engine.dispose()

def test_f0007_no_create_all_or_orm_imports() -> None:
    tree = ast.parse(MIGRATION_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"create_all", "drop_all"}
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("app.db.models")
            assert mod != "app.db.base"


def test_no_deletion_automation_in_privacy_package() -> None:
    names = {
        name
        for name, obj in pyinspect.getmembers(privacy_service)
        if pyinspect.isfunction(obj) or pyinspect.isclass(obj)
    }
    assert not (FORBIDDEN_FN_NAMES & names)
    pkg = Path(__file__).resolve().parents[1]
    for path in pkg.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        src = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_FN_NAMES:
            assert f"def {forbidden}" not in src
            assert f"class {forbidden}" not in src


@require_disposable_postgres
def test_privacy_service_semantics() -> None:
    with temporary_database(prefix=PF9_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        async_engine = create_async_engine(_async_url(url), pool_pre_ping=True)
        SessionLocal = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )

        async def _count(db: AsyncSession, table: str) -> int:
            return int(
                (await db.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar_one()
            )

        async def _run() -> None:
            async with SessionLocal() as db:
                subject = CareerSubject(owner_user_id=user_id)
                db.add(subject)
                await db.commit()
                await db.refresh(subject)

                actor = ActorRef(actor_type=ActorType.USER, actor_id=new_entity_id())
                policy = await create_privacy_policy(
                    db,
                    subject_id=subject.id,
                    data_classification=DataClassification.PRIVATE,
                    visibility_scope=VisibilityScope.SUBJECT_OWNER,
                    processing_purpose=ProcessingPurpose.CAREER_PROFILE,
                    description="  profile private  ",
                    created_by_actor=actor,
                )
                assert policy.subject_id == subject.id
                assert policy.data_classification == DataClassification.PRIVATE.value
                assert policy.visibility_scope == VisibilityScope.SUBJECT_OWNER.value
                assert policy.description == "profile private"
                assert (await get_privacy_policy(db, policy.id)) is not None

                # Classification does not imply visibility
                sensitive = await create_privacy_policy(
                    db,
                    subject_id=subject.id,
                    data_classification=DataClassification.SENSITIVE,
                    visibility_scope=VisibilityScope.SYSTEM_ONLY,
                    processing_purpose=ProcessingPurpose.SAFETY_SECURITY,
                )
                assert (
                    sensitive.data_classification
                    == DataClassification.SENSITIVE.value
                )
                assert sensitive.visibility_scope == VisibilityScope.SYSTEM_ONLY.value

                # Visibility does not imply consent — no auto consent
                before_consent = await _count(db, "consent_records")
                assert before_consent == 0
                assert await list_subject_consent_records(db, subject.id) == []

                consent = await create_consent_record(
                    db,
                    subject_id=subject.id,
                    processing_purpose=ProcessingPurpose.CAREER_PROFILE,
                    consent_status=ConsentStatus.GRANTED,
                    granted_by_actor=actor,
                )
                assert consent.consent_status == ConsentStatus.GRANTED.value
                assert consent.granted_by_actor_id == uuid.UUID(str(actor.actor_id))
                assert (await get_consent_record(db, consent.id)) is not None

                # withdrawn_at validation
                now = datetime.now(UTC)
                try:
                    await create_consent_record(
                        db,
                        subject_id=subject.id,
                        processing_purpose=ProcessingPurpose.ANALYTICS,
                        consent_status=ConsentStatus.GRANTED,
                        withdrawn_at=now,
                    )
                    raise AssertionError("granted + withdrawn_at should fail")
                except PrivacyRefError:
                    pass
                try:
                    await create_consent_record(
                        db,
                        subject_id=subject.id,
                        processing_purpose=ProcessingPurpose.ANALYTICS,
                        consent_status=ConsentStatus.WITHDRAWN,
                    )
                    raise AssertionError("withdrawn without withdrawn_at should fail")
                except PrivacyRefError:
                    pass
                withdrawn = await create_consent_record(
                    db,
                    subject_id=subject.id,
                    processing_purpose=ProcessingPurpose.ANALYTICS,
                    consent_status=ConsentStatus.WITHDRAWN,
                    withdrawn_at=now,
                )
                assert withdrawn.withdrawn_at is not None

                # Retention validation
                try:
                    await create_retention_policy(
                        db,
                        subject_id=subject.id,
                        retention_category=RetentionCategory.FIXED_PERIOD,
                    )
                    raise AssertionError("fixed_period without retain_until should fail")
                except PrivacyRefError:
                    pass
                fixed = await create_retention_policy(
                    db,
                    subject_id=subject.id,
                    retention_category=RetentionCategory.FIXED_PERIOD,
                    retain_until=now + timedelta(days=30),
                    processing_purpose=ProcessingPurpose.LEGAL_OBLIGATION,
                )
                assert fixed.retain_until is not None
                active = await create_retention_policy(
                    db,
                    subject_id=subject.id,
                    retention_category=RetentionCategory.ACTIVE_ACCOUNT,
                )
                assert active.retain_until is None

                assert len(await list_subject_privacy_policies(db, subject.id)) == 2

        try:
            asyncio.run(_run())
        finally:
            asyncio.run(async_engine.dispose())
