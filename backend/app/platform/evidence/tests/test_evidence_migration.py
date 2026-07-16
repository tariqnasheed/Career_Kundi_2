"""f0009 evidence foundation migration tests (0053-F2)."""

from __future__ import annotations

import ast
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect

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

F2_PREFIX = "ck_f2ev_"
F0008 = "f0008_passport_persistence"
F0009 = "f0009_evidence_foundation"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
    / "f0009_evidence_foundation.py"
)
EVIDENCE_TABLES = {"evidence_records", "claim_evidence_links"}
FORBIDDEN_TABLES = {
    "verifications",
    "verification_reviews",
    "claim_verifications",
    "public_evidence",
    "evidence_shares",
    "share_tokens",
    "evidence_items",
}


@require_disposable_postgres
def test_f0009_tables_exist_after_migration() -> None:
    with temporary_database(prefix=F2_PREFIX) as (_name, url):
        result = prepare_database(url)
        assert result.foundation_revisions == (foundation_heads()[0],)
        assert foundation_heads() == [F0009]
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert EVIDENCE_TABLES.issubset(tables)
            assert not (FORBIDDEN_TABLES & tables)
            idxs = {
                i["name"] for i in inspect(engine).get_indexes("evidence_records")
            }
            assert "ix_evidence_records_owner_user_id" in idxs
            assert "ix_evidence_records_subject_id" in idxs
            assert "ix_evidence_records_evidence_kind" in idxs
            assert "ix_evidence_records_privacy_class" in idxs
            assert "ix_evidence_records_source_id" in idxs
            assert "ix_evidence_records_snapshot_id" in idxs
            assert "ix_evidence_records_created_at" in idxs
            link_idxs = {
                i["name"] for i in inspect(engine).get_indexes("claim_evidence_links")
            }
            assert "ix_claim_evidence_links_claim_id" in link_idxs
            assert "ix_claim_evidence_links_evidence_id" in link_idxs
            assert "ix_claim_evidence_links_link_role" in link_idxs
            uniques = {
                u["name"]
                for u in inspect(engine).get_unique_constraints("claim_evidence_links")
            }
            assert "uq_claim_evidence_links_claim_evidence" in uniques
        finally:
            engine.dispose()


@require_disposable_postgres
def test_f0009_downgrade_upgrade() -> None:
    with temporary_database(prefix=F2_PREFIX) as (_name, url):
        prepare_database(url)
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0008)
            tables = set(inspect(engine).get_table_names())
            assert not (EVIDENCE_TABLES & tables)
            assert "career_passports" in tables
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            assert EVIDENCE_TABLES.issubset(set(inspect(engine).get_table_names()))
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (F0009,)
        finally:
            engine.dispose()


@require_disposable_postgres
def test_drift_zero_at_head() -> None:
    with temporary_database(prefix=F2_PREFIX) as (_name, url):
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


def test_f0009_no_create_all_or_orm_imports() -> None:
    tree = ast.parse(MIGRATION_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"create_all", "drop_all"}
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("app.db.models")
            assert mod != "app.db.base"
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("app.db.models")
