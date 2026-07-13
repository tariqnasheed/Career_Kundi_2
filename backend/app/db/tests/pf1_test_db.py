"""
Disposable PostgreSQL helpers for foundation migration tests (0050-PF1-S1R1A).

Destructive DROP is allowed only for databases matching the approved prefix.
Primary `careerkundi` is never targeted.
"""

from __future__ import annotations

import os
import re
import subprocess
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, text

ADMIN_DB = "postgres"
PRIMARY_APP_DB = "careerkundi"
# Approved disposable prefixes (PF1 + later foundation slices).
DISPOSABLE_PREFIX = "ck_pf1r1a_"
APPROVED_DISPOSABLE_PREFIXES = (
    "ck_pf1r1a_",
    "ck_pf3s1_",
    "ck_pf4s1_",
    "ck_pf5s1_",
    "ck_pf6s1_",
    "ck_pf7s1_",
    "ck_pf8s1_",
    "ck_pf9s1_",
    "ck_0052f3_",
)
_DISPOSABLE_NAME_RE = re.compile(
    rf"^({'|'.join(re.escape(p) for p in APPROVED_DISPOSABLE_PREFIXES)})[a-z0-9_]+$"
)

DOCKER_DB_CONTAINER = os.environ.get("CK_PF1_PG_CONTAINER", "careerkundi-db")
PG_USER = os.environ.get("POSTGRES_USER", "careerkundi")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "careerkundi")
PG_HOST = os.environ.get("CK_PF1_PG_HOST", "localhost")
PG_PORT = os.environ.get("CK_PF1_PG_PORT", "5432")


def sync_url(dbname: str) -> str:
    return f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{dbname}"


def assert_safe_disposable_name(dbname: str) -> None:
    """Central guard: reject primary and non-prefix names before any DROP."""
    if dbname == PRIMARY_APP_DB:
        raise RuntimeError(f"refusing destructive operation on primary DB {PRIMARY_APP_DB!r}")
    if dbname in {"postgres", "template0", "template1"}:
        raise RuntimeError(f"refusing destructive operation on system DB {dbname!r}")
    if not _DISPOSABLE_NAME_RE.match(dbname):
        raise RuntimeError(
            f"refusing destructive operation on {dbname!r}; "
            f"required pattern {_DISPOSABLE_NAME_RE.pattern}"
        )


def _docker_available() -> bool:
    try:
        r = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", DOCKER_DB_CONTAINER],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return r.returncode == 0 and r.stdout.strip() == "true"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _psql(dbname: str, sql: str) -> None:
    if dbname != ADMIN_DB:
        assert_safe_disposable_name(dbname)
    subprocess.run(
        [
            "docker",
            "exec",
            "-e",
            f"PGPASSWORD={PG_PASSWORD}",
            DOCKER_DB_CONTAINER,
            "psql",
            "-U",
            PG_USER,
            "-d",
            dbname,
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )


def drop_disposable_database(dbname: str) -> None:
    assert_safe_disposable_name(dbname)
    _psql(
        ADMIN_DB,
        f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{dbname}' AND pid <> pg_backend_pid();
        """,
    )
    _psql(ADMIN_DB, f'DROP DATABASE IF EXISTS "{dbname}";')


def disposable_postgres_ready() -> bool:
    if not _docker_available():
        return False
    try:
        engine = create_engine(sync_url(ADMIN_DB), pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


require_disposable_postgres = pytest.mark.skipif(
    not disposable_postgres_ready(),
    reason=(
        f"Disposable PostgreSQL unavailable (need Docker {DOCKER_DB_CONTAINER} "
        f"at {PG_HOST}:{PG_PORT})"
    ),
)


@contextmanager
def temporary_database(prefix: str = DISPOSABLE_PREFIX) -> Iterator[tuple[str, str]]:
    """Yield (dbname, sync_url) for a fresh empty disposable database."""
    if prefix not in APPROVED_DISPOSABLE_PREFIXES:
        raise RuntimeError(f"unapproved disposable prefix {prefix!r}")
    name = f"{prefix}{uuid.uuid4().hex[:12]}"
    assert_safe_disposable_name(name)
    _psql(ADMIN_DB, f'CREATE DATABASE "{name}";')
    url = sync_url(name)
    try:
        yield name, url
    finally:
        drop_disposable_database(name)
