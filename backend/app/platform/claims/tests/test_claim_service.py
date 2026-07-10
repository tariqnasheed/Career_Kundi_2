"""Claim migration + service tests (0050-PF5-S1)."""

from __future__ import annotations

import ast
import asyncio
import uuid
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
from app.platform.claims import (
    ClaimKind,
    ClaimOrigin,
    ClaimRefError,
    SupportStatus,
    VerificationStatus,
)
from app.platform.claims.service import create_claim, get_claim, list_subject_claims
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import new_entity_id
from app.platform.provenance import SourceKind
from app.platform.provenance.service import create_snapshot, create_source

PF5_PREFIX = "ck_pf5s1_"
F0003 = "f0003_provenance_source_snapshot"
F0004 = "f0004_claim_foundation"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
    / "f0004_claim_foundation.py"
)
FORBIDDEN_EVIDENCE_TABLES = {
    "evidence_items",
    "verifications",
    "claim_evidence",
    "claim_verifications",
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
                    email=f"pf5-{uid.hex[:8]}@example.com",
                    hashed_password=hash_password("test-password-ok"),
                    full_name="PF5 User",
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
def test_f0004_migration_empty_to_head() -> None:
    with temporary_database(prefix=PF5_PREFIX) as (_name, url):
        result = prepare_database(url)
        assert result.foundation_revisions == (foundation_heads()[0],)
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert "career_claims" in tables
            assert not (FORBIDDEN_EVIDENCE_TABLES & tables)
            fks = inspect(engine).get_foreign_keys("career_claims")
            referred = {fk["referred_table"] for fk in fks}
            assert "career_subjects" in referred
            assert "provenance_sources" in referred
            assert "provenance_snapshots" in referred
            idxs = {i["name"] for i in inspect(engine).get_indexes("career_claims")}
            assert "ix_career_claims_subject_id" in idxs
            assert "ix_career_claims_claim_kind" in idxs
            assert "ix_career_claims_claim_key" in idxs
            assert "ix_career_claims_support_status" in idxs
            assert "ix_career_claims_verification_status" in idxs
            assert "ix_career_claims_source_id" in idxs
            assert "ix_career_claims_snapshot_id" in idxs
        finally:
            engine.dispose()


@require_disposable_postgres
def test_f0004_downgrade_upgrade() -> None:
    with temporary_database(prefix=PF5_PREFIX) as (_name, url):
        prepare_database(url)
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0003)
            tables = set(inspect(engine).get_table_names())
            assert "career_claims" not in tables
            assert "provenance_sources" in tables
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            assert "career_claims" in inspect(engine).get_table_names()
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (foundation_heads()[0],)
        finally:
            engine.dispose()


@require_disposable_postgres
def test_drift_zero_at_head() -> None:
    with temporary_database(prefix=PF5_PREFIX) as (_name, url):
        prepare_database(url)
        engine = create_engine(url)

        def _include_object(object, name, type_, reflected, compare_to):
            if type_ == "table" and name == FOUNDATION_VERSION_TABLE:
                return False
            return True

        try:
            with engine.connect() as conn:
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


def test_f0004_no_create_all_or_orm_imports() -> None:
    tree = ast.parse(MIGRATION_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"create_all", "drop_all"}
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("app.db.models")
            assert mod != "app.db.base"


@require_disposable_postgres
def test_claim_service_semantics() -> None:
    with temporary_database(prefix=PF5_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        async_engine = create_async_engine(_async_url(url), pool_pre_ping=True)
        SessionLocal = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )

        async def _count_claims(db: AsyncSession) -> int:
            return int(
                (await db.execute(text("SELECT COUNT(*) FROM career_claims"))).scalar_one()
            )

        async def _run() -> None:
            async with SessionLocal() as db:
                subject_a = CareerSubject(owner_user_id=user_id)
                subject_b = CareerSubject(owner_user_id=user_id)
                db.add_all([subject_a, subject_b])
                await db.commit()
                await db.refresh(subject_a)
                await db.refresh(subject_b)

                actor = ActorRef(actor_type=ActorType.USER, actor_id=new_entity_id())
                claim_plain = await create_claim(
                    db,
                    subject_id=subject_a.id,
                    claim_kind=ClaimKind.SKILL,
                    claim_key="  python  ",
                    claim_value="  Python  ",
                    claim_origin=ClaimOrigin.USER_ASSERTED,
                    support_status=SupportStatus.NOT_PROVIDED,
                    verification_status=VerificationStatus.UNVERIFIED,
                    created_by_actor=actor,
                )
                assert claim_plain.claim_key == "python"
                assert claim_plain.claim_value == "Python"
                assert claim_plain.source_id is None
                assert claim_plain.snapshot_id is None
                assert claim_plain.support_status == SupportStatus.NOT_PROVIDED.value
                assert (
                    claim_plain.verification_status
                    == VerificationStatus.UNVERIFIED.value
                )
                assert claim_plain.created_by_actor_type == ActorType.USER.value
                assert claim_plain.created_by_actor_id == uuid.UUID(str(actor.actor_id))
                assert (await get_claim(db, claim_plain.id)) is not None

                source_a = await create_source(
                    db, source_kind=SourceKind.URL, uri="https://a.example"
                )
                claim_src = await create_claim(
                    db,
                    subject_id=subject_a.id,
                    claim_kind=ClaimKind.EXPERIENCE,
                    claim_key="backend_engineer",
                    claim_value="Backend Engineer",
                    claim_origin=ClaimOrigin.DOCUMENT_EXTRACTED,
                    support_status=SupportStatus.SOURCE_LINKED,
                    verification_status=VerificationStatus.UNVERIFIED,
                    source_id=source_a.id,
                )
                assert claim_src.source_id == source_a.id
                assert claim_src.snapshot_id is None
                assert claim_src.support_status == SupportStatus.SOURCE_LINKED.value
                assert (
                    claim_src.verification_status
                    == VerificationStatus.UNVERIFIED.value
                )
                assert claim_src.verification_status != VerificationStatus.VERIFIED.value

                snap_a = await create_snapshot(db, source_id=source_a.id)
                claim_both = await create_claim(
                    db,
                    subject_id=subject_a.id,
                    claim_kind=ClaimKind.EDUCATION,
                    claim_key="msc_power",
                    claim_value="MSc Electrical Power",
                    claim_origin=ClaimOrigin.EXTERNAL_IMPORTED,
                    support_status=SupportStatus.SOURCE_LINKED,
                    verification_status=VerificationStatus.UNKNOWN,
                    source_id=source_a.id,
                    snapshot_id=snap_a.id,
                )
                assert claim_both.source_id == source_a.id
                assert claim_both.snapshot_id == snap_a.id

                before = await _count_claims(db)
                try:
                    await create_claim(
                        db,
                        subject_id=subject_a.id,
                        claim_kind=ClaimKind.SKILL,
                        claim_key="x",
                        claim_value="x",
                        claim_origin=ClaimOrigin.USER_ASSERTED,
                        support_status=SupportStatus.SOURCE_LINKED,
                        verification_status=VerificationStatus.UNVERIFIED,
                        snapshot_id=snap_a.id,
                    )
                    raise AssertionError("snapshot without source should fail")
                except ClaimRefError:
                    pass
                assert await _count_claims(db) == before

                source_b = await create_source(
                    db, source_kind=SourceKind.DOCUMENT, uri="doc://b"
                )
                snap_b = await create_snapshot(db, source_id=source_b.id)
                try:
                    await create_claim(
                        db,
                        subject_id=subject_a.id,
                        claim_kind=ClaimKind.SKILL,
                        claim_key="y",
                        claim_value="y",
                        claim_origin=ClaimOrigin.USER_ASSERTED,
                        support_status=SupportStatus.SOURCE_LINKED,
                        verification_status=VerificationStatus.UNVERIFIED,
                        source_id=source_a.id,
                        snapshot_id=snap_b.id,
                    )
                    raise AssertionError("source/snapshot mismatch should fail")
                except ClaimRefError:
                    pass
                assert await _count_claims(db) == before

                try:
                    await create_claim(
                        db,
                        subject_id=uuid.uuid4(),
                        claim_kind=ClaimKind.SKILL,
                        claim_key="z",
                        claim_value="z",
                        claim_origin=ClaimOrigin.USER_ASSERTED,
                        support_status=SupportStatus.NOT_PROVIDED,
                        verification_status=VerificationStatus.UNVERIFIED,
                    )
                    raise AssertionError("missing subject should fail")
                except ClaimRefError:
                    pass
                assert await _count_claims(db) == before

                claim_b = await create_claim(
                    db,
                    subject_id=subject_b.id,
                    claim_kind=ClaimKind.LANGUAGE,
                    claim_key="english",
                    claim_value="English",
                    claim_origin=ClaimOrigin.USER_ASSERTED,
                    support_status=SupportStatus.PROFILE_SUPPORTED,
                    verification_status=VerificationStatus.UNVERIFIED,
                )
                listed_a = await list_subject_claims(db, subject_a.id)
                listed_b = await list_subject_claims(db, subject_b.id)
                assert {c.id for c in listed_a} == {
                    claim_plain.id,
                    claim_src.id,
                    claim_both.id,
                }
                assert {c.id for c in listed_b} == {claim_b.id}

        try:
            asyncio.run(_run())
        finally:
            asyncio.run(async_engine.dispose())
