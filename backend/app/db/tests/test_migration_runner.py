"""Foundation migration_runner integration tests (0050-PF1-S1R1A)."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

import app.db.models  # noqa: F401
from app.db.base import Base
from app.db.migration_runner import (
    FOUNDATION_VERSION_TABLE,
    DatabaseState,
    MigrationLockTimeoutError,
    MigrationPrepareError,
    advisory_lock_keys,
    classify_database,
    foundation_heads,
    prepare_database,
    read_foundation_revisions,
)
from app.db.tests.pf1_test_db import (
    PRIMARY_APP_DB,
    assert_safe_disposable_name,
    require_disposable_postgres,
    temporary_database,
)

BACKEND_ROOT = Path(__file__).resolve().parents[3]


@require_disposable_postgres
def test_empty_upgrade_applies_baseline() -> None:
    with temporary_database() as (name, url):
        result = prepare_database(url)
        assert result.state is DatabaseState.FOUNDATION_VERSIONED
        head = foundation_heads()[0]
        assert head in result.foundation_revisions
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert "users" in tables
            assert FOUNDATION_VERSION_TABLE in tables
            assert "alembic_version" not in tables
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (head,)
        finally:
            engine.dispose()


@require_disposable_postgres
def test_legacy_unowned_with_alembic_version_fails_closed() -> None:
    with temporary_database() as (name, url):
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE TABLE users (id INT PRIMARY KEY)"))
                conn.execute(
                    text(
                        "CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)"
                    )
                )
                conn.execute(
                    text("INSERT INTO alembic_version(version_num) VALUES ('0001_initial')")
                )
            before = set(inspect(engine).get_table_names())
        finally:
            engine.dispose()

        with pytest.raises(MigrationPrepareError, match="NONEMPTY_UNOWNED"):
            prepare_database(url)

        engine = create_engine(url)
        try:
            after = set(inspect(engine).get_table_names())
            assert after == before
            assert FOUNDATION_VERSION_TABLE not in after
        finally:
            engine.dispose()


@require_disposable_postgres
def test_unrelated_schema_alembic_version_is_unowned() -> None:
    with temporary_database() as (name, url):
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE SCHEMA other_schema"))
                conn.execute(
                    text(
                        "CREATE TABLE other_schema.alembic_version "
                        "(version_num VARCHAR(32) PRIMARY KEY)"
                    )
                )
                conn.execute(
                    text(
                        "INSERT INTO other_schema.alembic_version(version_num) "
                        "VALUES ('whatever')"
                    )
                )
            with engine.connect() as conn:
                cls = classify_database(conn)
            assert cls.state is DatabaseState.NONEMPTY_UNOWNED
        finally:
            engine.dispose()

        with pytest.raises(MigrationPrepareError, match="NONEMPTY_UNOWNED"):
            prepare_database(url)


@require_disposable_postgres
def test_unknown_foundation_revision_invalid() -> None:
    with temporary_database() as (name, url):
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        f'CREATE TABLE {FOUNDATION_VERSION_TABLE} '
                        f"(version_num VARCHAR(64) PRIMARY KEY)"
                    )
                )
                conn.execute(
                    text(
                        f"INSERT INTO {FOUNDATION_VERSION_TABLE}(version_num) "
                        f"VALUES ('not_a_real_revision')"
                    )
                )
            with engine.connect() as conn:
                assert classify_database(conn).state is DatabaseState.INVALID_FOUNDATION_VERSION
        finally:
            engine.dispose()

        with pytest.raises(MigrationPrepareError, match="INVALID_FOUNDATION_VERSION"):
            prepare_database(url)

        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert tables == {FOUNDATION_VERSION_TABLE}
            assert "users" not in tables
        finally:
            engine.dispose()


@require_disposable_postgres
def test_empty_foundation_version_table_invalid() -> None:
    with temporary_database() as (name, url):
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        f"CREATE TABLE {FOUNDATION_VERSION_TABLE} "
                        f"(version_num VARCHAR(64) PRIMARY KEY)"
                    )
                )
            with engine.connect() as conn:
                assert classify_database(conn).state is DatabaseState.INVALID_FOUNDATION_VERSION
        finally:
            engine.dispose()

        with pytest.raises(MigrationPrepareError, match="INVALID_FOUNDATION_VERSION"):
            prepare_database(url)


@require_disposable_postgres
def test_valid_foundation_versioned_upgrade_and_idempotency() -> None:
    with temporary_database() as (name, url):
        r1 = prepare_database(url)
        r2 = prepare_database(url)
        r3 = prepare_database(url)
        assert r1.state is DatabaseState.FOUNDATION_VERSIONED
        assert r2.state is DatabaseState.FOUNDATION_VERSIONED
        assert r3.state is DatabaseState.FOUNDATION_VERSIONED
        assert r1.foundation_revisions == r2.foundation_revisions == r3.foundation_revisions
        engine = create_engine(url)
        try:
            with engine.connect() as conn:
                n = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            assert n == 0
            names = inspect(engine).get_table_names()
            assert names.count("users") == 1
            assert names.count(FOUNDATION_VERSION_TABLE) == 1
        finally:
            engine.dispose()


@require_disposable_postgres
def test_concurrent_first_initialization() -> None:
    with temporary_database() as (name, url):
        errors: list[BaseException] = []
        results: list[DatabaseState] = []

        def _run() -> None:
            try:
                r = prepare_database(url, lock_timeout_seconds=60.0)
                results.append(r.state)
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=_run) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
            assert not t.is_alive()

        assert not errors, errors
        assert results == [DatabaseState.FOUNDATION_VERSIONED, DatabaseState.FOUNDATION_VERSIONED]
        engine = create_engine(url)
        try:
            with engine.connect() as conn:
                revs = read_foundation_revisions(conn)
            assert revs == (foundation_heads()[0],)
            assert "users" in inspect(engine).get_table_names()
        finally:
            engine.dispose()


@require_disposable_postgres
def test_lock_timeout_no_mutation() -> None:
    with temporary_database() as (name, url):
        holder = create_engine(url)
        runner_engine = create_engine(url)
        try:
            with holder.connect() as hold_conn:
                k1, k2 = advisory_lock_keys(name)
                ok = hold_conn.execute(
                    text("SELECT pg_try_advisory_lock(:k1, :k2)"), {"k1": k1, "k2": k2}
                ).scalar()
                assert ok
                hold_conn.commit()  # keep session lock; commit does not release advisory

                with pytest.raises(MigrationLockTimeoutError):
                    prepare_database(url, lock_timeout_seconds=0.3)

                tables = set(inspect(runner_engine).get_table_names())
                assert tables == set()
                assert FOUNDATION_VERSION_TABLE not in tables

                hold_conn.execute(
                    text("SELECT pg_advisory_unlock(:k1, :k2)"), {"k1": k1, "k2": k2}
                )
                hold_conn.commit()
        finally:
            holder.dispose()
            runner_engine.dispose()


@require_disposable_postgres
def test_baseline_drift_zero_after_real_upgrade() -> None:
    with temporary_database() as (name, url):
        prepare_database(url)
        engine = create_engine(url)
        try:
            def _include_object(object, name, type_, reflected, compare_to):
                if type_ == "table" and name == FOUNDATION_VERSION_TABLE:
                    return False
                return True

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


def test_primary_db_guard_rejects_careerkundi() -> None:
    with pytest.raises(RuntimeError, match="primary"):
        assert_safe_disposable_name(PRIMARY_APP_DB)
    with pytest.raises(RuntimeError, match="required pattern"):
        assert_safe_disposable_name("ck_pf1_oldprefix")
    with pytest.raises(RuntimeError, match="system DB"):
        assert_safe_disposable_name("postgres")


def test_cli_rejects_url_flags() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "app.db.migration_runner", "--url", "postgresql://x"],
        cwd=str(BACKEND_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 2
    assert "--url" in (proc.stderr + proc.stdout)

    # No CAREERKUNDI_ALEMBIC_URL dependency in runner source.
    src = (BACKEND_ROOT / "app" / "db" / "migration_runner.py").read_text(encoding="utf-8")
    assert "CAREERKUNDI_ALEMBIC_URL" not in src
    env_legacy = (BACKEND_ROOT / "app" / "db" / "migrations" / "env.py").read_text(
        encoding="utf-8"
    )
    assert "CAREERKUNDI_ALEMBIC_URL" not in env_legacy
