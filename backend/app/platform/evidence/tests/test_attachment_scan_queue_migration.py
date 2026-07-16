"""f0011 attachment scan queue skeleton migration tests (0053-F16)."""

from __future__ import annotations

import ast
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, inspect

from app.db.migration_runner import (
    build_foundation_alembic_config,
    foundation_heads,
    prepare_database,
    read_foundation_revisions,
)
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database

F16_PREFIX = "ck_f2svc_"
F0010 = "f0010_review_request_foundation"
F0011 = "f0011_attachment_scan_queue"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
    / "f0011_attachment_scan_queue.py"
)


@require_disposable_postgres
def test_f0011_attachment_scan_jobs_table_exists() -> None:
    with temporary_database(prefix=F16_PREFIX) as (_name, url):
        result = prepare_database(url)
        assert foundation_heads() == [F0011]
        assert result.foundation_revisions == (F0011,)
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert "attachment_scan_jobs" in tables
            assert "review_requests" in tables
            idxs = {
                i["name"] for i in inspect(engine).get_indexes("attachment_scan_jobs")
            }
            assert "ix_attachment_scan_jobs_owner_user_id" in idxs
            assert "ix_attachment_scan_jobs_evidence_id" in idxs
            assert "ix_attachment_scan_jobs_job_status" in idxs
            assert "ix_attachment_scan_jobs_attachment_safety_status" in idxs
            assert "ix_attachment_scan_jobs_created_at" in idxs
            assert "ix_attachment_scan_jobs_evidence_content_hash" in idxs
            assert "uq_attachment_scan_jobs_active_evidence_hash" in idxs
            cols = {
                c["name"] for c in inspect(engine).get_columns("attachment_scan_jobs")
            }
            for required in (
                "owner_user_id",
                "evidence_id",
                "content_hash_snapshot",
                "mime_type_snapshot",
                "size_bytes_snapshot",
                "job_status",
                "attachment_safety_status",
                "engine_name",
                "engine_version",
                "attempt_count",
                "safe_error_code",
                "safe_error_message",
                "started_at",
                "completed_at",
                "cancelled_at",
            ):
                assert required in cols
            assert "storage_uri" not in cols
            assert "filesystem_path" not in cols
            assert "public_url" not in cols
        finally:
            engine.dispose()


@require_disposable_postgres
def test_f0011_downgrade_upgrade() -> None:
    with temporary_database(prefix=F16_PREFIX) as (_name, url):
        prepare_database(url)
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0010)
            tables = set(inspect(engine).get_table_names())
            assert "attachment_scan_jobs" not in tables
            assert "review_requests" in tables
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            assert "attachment_scan_jobs" in set(inspect(engine).get_table_names())
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (F0011,)
        finally:
            engine.dispose()


def test_f0011_no_create_all_or_orm_imports() -> None:
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
    assert "clamav" not in source.lower()
    assert "virustotal" not in source.lower()
