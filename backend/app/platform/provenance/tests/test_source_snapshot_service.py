"""Provenance migration + source/snapshot service tests (0050-PF4-S1)."""

from __future__ import annotations

import ast
import asyncio
import inspect as pyinspect
import uuid
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.db.models  # noqa: F401
from app.db.base import Base
from app.db.migration_runner import (
    FOUNDATION_VERSION_TABLE,
    build_foundation_alembic_config,
    foundation_heads,
    prepare_database,
    read_foundation_revisions,
)
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.platform.provenance import ProvenanceRefError, SourceKind
from app.platform.provenance import service as provenance_service
from app.platform.provenance.service import (
    create_snapshot,
    create_source,
    get_snapshot,
    get_source,
    sha256_text,
)

PF4_PREFIX = "ck_pf4s1_"
F0002 = "f0002_identity_subject_stub"
F0003 = "f0003_provenance_source_snapshot"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
    / "f0003_provenance_source_snapshot.py"
)
FORBIDDEN_CLAIM_TABLES = {
    "claims",
    "evidence_items",
    "verifications",
    "subject_claims",
    "claim_sources",
}


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


@require_disposable_postgres
def test_f0003_migration_empty_to_head() -> None:
    with temporary_database(prefix=PF4_PREFIX) as (_name, url):
        result = prepare_database(url)
        assert result.foundation_revisions == (foundation_heads()[0],)
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert "provenance_sources" in tables
            assert "provenance_snapshots" in tables
            assert not (FORBIDDEN_CLAIM_TABLES & tables)
            fks = inspect(engine).get_foreign_keys("provenance_snapshots")
            assert any(
                fk["referred_table"] == "provenance_sources"
                and fk["constrained_columns"] == ["source_id"]
                for fk in fks
            )
            src_idxs = {
                i["name"] for i in inspect(engine).get_indexes("provenance_sources")
            }
            snap_idxs = {
                i["name"] for i in inspect(engine).get_indexes("provenance_snapshots")
            }
            assert "ix_provenance_sources_source_kind" in src_idxs
            assert "ix_provenance_snapshots_source_id" in snap_idxs
            assert "ix_provenance_snapshots_captured_at" in snap_idxs
        finally:
            engine.dispose()


@require_disposable_postgres
def test_f0003_downgrade_upgrade() -> None:
    with temporary_database(prefix=PF4_PREFIX) as (_name, url):
        prepare_database(url)
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0002)
            tables = set(inspect(engine).get_table_names())
            assert "provenance_sources" not in tables
            assert "provenance_snapshots" not in tables
            assert "career_subjects" in tables
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            tables = set(inspect(engine).get_table_names())
            assert "provenance_sources" in tables
            assert "provenance_snapshots" in tables
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (foundation_heads()[0],)
        finally:
            engine.dispose()


@require_disposable_postgres
def test_drift_zero_at_head() -> None:
    with temporary_database(prefix=PF4_PREFIX) as (_name, url):
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


def test_f0003_no_create_all_or_orm_imports() -> None:
    tree = ast.parse(MIGRATION_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"create_all", "drop_all"}
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("app.db.models")
            assert mod != "app.db.base"


def test_no_update_snapshot_service() -> None:
    assert not hasattr(provenance_service, "update_snapshot")
    names = {
        name
        for name, obj in pyinspect.getmembers(provenance_service)
        if pyinspect.isfunction(obj) and name.startswith("update_")
    }
    assert "update_snapshot" not in names


def test_sha256_text_pure() -> None:
    assert sha256_text("hello") == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


@require_disposable_postgres
def test_source_snapshot_service_semantics() -> None:
    with temporary_database(prefix=PF4_PREFIX) as (_name, url):
        prepare_database(url)
        async_engine = create_async_engine(_async_url(url), pool_pre_ping=True)
        SessionLocal = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )

        async def _run() -> None:
            async with SessionLocal() as db:
                created_kinds: list[str] = []
                for kind in SourceKind:
                    src = await create_source(
                        db,
                        source_kind=kind,
                        label=f"  Label {kind.value}  ",
                        uri=f"  ref://{kind.value}  ",
                    )
                    assert src.source_kind == kind.value
                    assert src.label == f"Label {kind.value}"
                    assert src.uri == f"ref://{kind.value}"
                    created_kinds.append(src.source_kind)
                    fetched = await get_source(db, src.id)
                    assert fetched is not None
                    assert fetched.id == src.id
                assert set(created_kinds) == {k.value for k in SourceKind}

                before = (
                    await db.execute(text("SELECT COUNT(*) FROM provenance_sources"))
                ).scalar_one()
                try:
                    await create_source(db, source_kind="not-a-real-kind")
                    raise AssertionError("expected bad kind rejection")
                except ProvenanceRefError:
                    pass
                after = (
                    await db.execute(text("SELECT COUNT(*) FROM provenance_sources"))
                ).scalar_one()
                assert after == before

                primary = await create_source(
                    db, source_kind=SourceKind.URL, label="primary", uri="https://ex"
                )
                snap = await create_snapshot(
                    db,
                    source_id=primary.id,
                    content_hash=sha256_text("body"),
                    hash_algorithm="sha256",
                    storage_uri="memory://unused",
                )
                assert snap.source_id == primary.id
                assert snap.captured_at is not None
                assert snap.content_hash == sha256_text("body")
                assert snap.hash_algorithm == "sha256"
                got = await get_snapshot(db, snap.id)
                assert got is not None
                assert got.id == snap.id

                missing_id = uuid.uuid4()
                try:
                    await create_snapshot(db, source_id=missing_id)
                    raise AssertionError("expected missing source failure")
                except ProvenanceRefError:
                    pass

                try:
                    await create_snapshot(
                        db, source_id=primary.id, content_hash="abc"
                    )
                    raise AssertionError("hash-only should fail")
                except ProvenanceRefError:
                    pass
                try:
                    await create_snapshot(
                        db, source_id=primary.id, hash_algorithm="sha256"
                    )
                    raise AssertionError("algo-only should fail")
                except ProvenanceRefError:
                    pass

                both = await create_snapshot(
                    db,
                    source_id=primary.id,
                    content_hash="deadbeef",
                    hash_algorithm="sha256",
                )
                neither = await create_snapshot(db, source_id=primary.id)
                assert both.id != neither.id
                assert both.source_id == primary.id == neither.source_id

        try:
            asyncio.run(_run())
        finally:
            asyncio.run(async_engine.dispose())
