"""f0010 review request foundation migration tests (0053-F10)."""

from __future__ import annotations

import ast
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, inspect, text

from app.db.migration_runner import (
    build_foundation_alembic_config,
    foundation_heads,
    prepare_database,
    read_foundation_revisions,
)
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database

F10_PREFIX = "ck_f2svc_"
F0009 = "f0009_evidence_foundation"
F0010 = "f0010_review_request_foundation"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
    / "f0010_review_request_foundation.py"
)


@require_disposable_postgres
def test_f0010_review_requests_table_exists() -> None:
    with temporary_database(prefix=F10_PREFIX) as (_name, url):
        result = prepare_database(url)
        assert foundation_heads() == [F0010]
        assert result.foundation_revisions == (F0010,)
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert "review_requests" in tables
            assert "verification_reviews" not in tables
            idxs = {
                i["name"] for i in inspect(engine).get_indexes("review_requests")
            }
            assert "ix_review_requests_owner_user_id" in idxs
            assert "ix_review_requests_subject_id" in idxs
            assert "ix_review_requests_claim_id" in idxs
            assert "ix_review_requests_review_state" in idxs
            assert "ix_review_requests_created_at" in idxs
            assert "uq_review_requests_active_claim" in idxs
        finally:
            engine.dispose()


@require_disposable_postgres
def test_f0010_downgrade_upgrade() -> None:
    with temporary_database(prefix=F10_PREFIX) as (_name, url):
        prepare_database(url)
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0009)
            tables = set(inspect(engine).get_table_names())
            assert "review_requests" not in tables
            assert "evidence_records" in tables
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            assert "review_requests" in set(inspect(engine).get_table_names())
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (F0010,)
        finally:
            engine.dispose()


def test_f0010_no_create_all_or_orm_imports() -> None:
    source = MIGRATION_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
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
    assert "create_all" not in source
    assert "drop_all" not in source
