"""
db/migration_runner.py
======================
CareerKundi foundation database prepare (0050-PF1-S1R1A).

Schema authority: explicit Alembic lineage under foundation_migrations/
Version table: public.careerkundi_foundation_version

States:
  EMPTY                     → advisory lock → reclassify → upgrade head
  FOUNDATION_VERSIONED      → lock → validate revisions → upgrade head
  NONEMPTY_UNOWNED          → FATAL (no mutate)
  INVALID_FOUNDATION_VERSION→ FATAL (no mutate)

Production CLI uses settings.database_url_sync only (no --url / env overrides).
Tests may call prepare_database(explicit_url) as dependency injection.
"""

from __future__ import annotations

import hashlib
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection

from app.core.config import settings

_SYSTEM_SCHEMAS = frozenset({"pg_catalog", "information_schema", "pg_toast"})

FOUNDATION_VERSION_TABLE = "careerkundi_foundation_version"
FOUNDATION_VERSION_SCHEMA = "public"
FOUNDATION_HEAD = "f0001_foundation_baseline"

# Default lock wait for production/startup (seconds). Tests may override.
DEFAULT_LOCK_TIMEOUT_SECONDS = 30.0
_LOCK_POLL_SECONDS = 0.05

# Namespace salt for advisory lock key derivation (not a secret).
_LOCK_NAMESPACE = b"careerkundi.foundation.migration.v1"


class DatabaseState(StrEnum):
    EMPTY = "empty"
    FOUNDATION_VERSIONED = "foundation_versioned"
    NONEMPTY_UNOWNED = "nonempty_unowned"
    INVALID_FOUNDATION_VERSION = "invalid_foundation_version"


class MigrationPrepareError(RuntimeError):
    """Fatal prepare failure (unowned / invalid / lock / verify)."""


class MigrationLockTimeoutError(MigrationPrepareError):
    """Could not acquire the foundation migration advisory lock in time."""


@dataclass(frozen=True)
class ClassificationResult:
    state: DatabaseState
    application_tables: tuple[str, ...]
    foundation_revisions: tuple[str, ...]


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def database_name_from_url(url: str) -> str:
    """Return DB name only (never log full URL/credentials)."""
    normalized = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    normalized = normalized.replace("postgresql+asyncpg://", "postgresql://", 1)
    return (urlparse(normalized).path or "").lstrip("/") or "<unknown>"


def build_foundation_alembic_config() -> Config:
    ini_path = _backend_root() / "foundation-alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option(
        "script_location",
        str(_backend_root() / "app" / "db" / "foundation_migrations"),
    )
    # URL unused when connection is injected; set for ScriptDirectory / CLI parity.
    cfg.set_main_option("sqlalchemy.url", settings.database_url_sync)
    return cfg


def foundation_script_directory(cfg: Config | None = None) -> ScriptDirectory:
    return ScriptDirectory.from_config(cfg or build_foundation_alembic_config())


def foundation_heads(cfg: Config | None = None) -> list[str]:
    return list(foundation_script_directory(cfg).get_heads())


def foundation_bases(cfg: Config | None = None) -> list[str]:
    return list(foundation_script_directory(cfg).get_bases())


def advisory_lock_keys(database_name: str) -> tuple[int, int]:
    """
    Deterministic PostgreSQL advisory lock key pair.

    Uses SHA-256 (not Python hash()) over namespace + database name so:
    - same DB → same lock
    - different DB names → different keys (when practical)
    """
    digest = hashlib.sha256(_LOCK_NAMESPACE + b"\0" + database_name.encode("utf-8")).digest()
    # Two signed 32-bit ints for pg_try_advisory_lock(key1, key2)
    k1 = int.from_bytes(digest[0:4], "big", signed=True)
    k2 = int.from_bytes(digest[4:8], "big", signed=True)
    return k1, k2


def list_non_system_tables(connection: Connection) -> tuple[str, ...]:
    """All base tables in non-system schemas as schema.table (public.t → t)."""
    inspector = inspect(connection)
    found: list[str] = []
    for schema in inspector.get_schema_names():
        if schema in _SYSTEM_SCHEMAS or schema.startswith("pg_"):
            continue
        for name in inspector.get_table_names(schema=schema):
            found.append(name if schema == "public" else f"{schema}.{name}")
    return tuple(sorted(found))


def _has_exact_foundation_version_table(connection: Connection) -> bool:
    inspector = inspect(connection)
    if FOUNDATION_VERSION_SCHEMA not in inspector.get_schema_names():
        return False
    return FOUNDATION_VERSION_TABLE in inspector.get_table_names(
        schema=FOUNDATION_VERSION_SCHEMA
    )


def read_foundation_revisions(connection: Connection) -> tuple[str, ...]:
    if not _has_exact_foundation_version_table(connection):
        return ()
    rows = connection.execute(
        text(
            f'SELECT version_num FROM "{FOUNDATION_VERSION_SCHEMA}".'
            f'"{FOUNDATION_VERSION_TABLE}"'
        )
    ).fetchall()
    return tuple(str(r[0]) for r in rows)


def classify_database(connection: Connection) -> ClassificationResult:
    """
    Classify using the live connection.

    Ownership requires exactly public.careerkundi_foundation_version.
    Legacy public.alembic_version or other_schema.alembic_version never counts.
    """
    tables = list_non_system_tables(connection)
    has_foundation = _has_exact_foundation_version_table(connection)
    app_tables = tuple(
        t
        for t in tables
        if t != FOUNDATION_VERSION_TABLE
        and t != f"{FOUNDATION_VERSION_SCHEMA}.{FOUNDATION_VERSION_TABLE}"
    )

    if has_foundation:
        revisions = read_foundation_revisions(connection)
        if not revisions:
            return ClassificationResult(
                DatabaseState.INVALID_FOUNDATION_VERSION, app_tables, ()
            )
        script = foundation_script_directory()
        for rev in revisions:
            try:
                resolved = script.get_revision(rev)
            except Exception:  # noqa: BLE001 — Alembic raises on unknown idents
                return ClassificationResult(
                    DatabaseState.INVALID_FOUNDATION_VERSION, app_tables, revisions
                )
            if resolved is None:
                return ClassificationResult(
                    DatabaseState.INVALID_FOUNDATION_VERSION, app_tables, revisions
                )
        return ClassificationResult(
            DatabaseState.FOUNDATION_VERSIONED, app_tables, revisions
        )

    if not app_tables:
        return ClassificationResult(DatabaseState.EMPTY, (), ())

    return ClassificationResult(DatabaseState.NONEMPTY_UNOWNED, app_tables, ())


@contextmanager
def migration_advisory_lock(
    connection: Connection,
    database_name: str,
    *,
    timeout_seconds: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
):
    """
    Serialize foundation prepare for one database via pg_try_advisory_lock.

    Lock is session-scoped and released in finally (and on connection close).
    """
    k1, k2 = advisory_lock_keys(database_name)
    deadline = time.monotonic() + timeout_seconds
    acquired = False
    while True:
        row = connection.execute(
            text("SELECT pg_try_advisory_lock(:k1, :k2)"), {"k1": k1, "k2": k2}
        ).scalar()
        if row:
            acquired = True
            break
        if time.monotonic() >= deadline:
            raise MigrationLockTimeoutError(
                f"Timed out after {timeout_seconds:.1f}s waiting for foundation "
                f"migration lock on database={database_name!r}."
            )
        time.sleep(_LOCK_POLL_SECONDS)
    try:
        yield
    finally:
        if acquired:
            connection.execute(
                text("SELECT pg_advisory_unlock(:k1, :k2)"), {"k1": k1, "k2": k2}
            )


def _upgrade_head_on_connection(connection: Connection) -> None:
    cfg = build_foundation_alembic_config()
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


def _verify_head(connection: Connection) -> None:
    heads = foundation_heads()
    if len(heads) != 1:
        raise MigrationPrepareError(f"Foundation ScriptDirectory must have one head; got {heads}")
    expected = heads[0]
    if not _has_exact_foundation_version_table(connection):
        raise MigrationPrepareError("Foundation version table missing after upgrade")
    revisions = read_foundation_revisions(connection)
    if not revisions:
        raise MigrationPrepareError("Foundation version table empty after upgrade")
    if expected not in revisions:
        raise MigrationPrepareError(
            f"Expected head {expected!r} not in foundation revisions {revisions!r}"
        )
    script = foundation_script_directory()
    for rev in revisions:
        if script.get_revision(rev) is None:
            raise MigrationPrepareError(f"Unresolved foundation revision after upgrade: {rev}")


def prepare_database(
    database_url_sync: str | None = None,
    *,
    lock_timeout_seconds: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
) -> ClassificationResult:
    """
    Classify (under lock) and prepare the foundation database.

    Pass database_url_sync only from tests/internal DI. Production CLI omits it.
    """
    url = database_url_sync or settings.database_url_sync
    db_name = database_name_from_url(url)
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            with migration_advisory_lock(
                connection, db_name, timeout_seconds=lock_timeout_seconds
            ):
                # Critical: reclassify AFTER lock acquisition.
                result = classify_database(connection)
                print(
                    f"[migration_runner] db={db_name} state={result.state.value} "
                    f"app_tables={len(result.application_tables)} "
                    f"foundation_revisions={list(result.foundation_revisions)}",
                    flush=True,
                )

                if result.state is DatabaseState.NONEMPTY_UNOWNED:
                    sample = ", ".join(result.application_tables[:12])
                    more = "" if len(result.application_tables) <= 12 else ", …"
                    raise MigrationPrepareError(
                        "NONEMPTY_UNOWNED: refusing to mutate a non-empty database "
                        "without valid public.careerkundi_foundation_version ownership. "
                        f"Tables ({len(result.application_tables)}): {sample}{more}. "
                        "Provision a fresh empty database for the new foundation."
                    )

                if result.state is DatabaseState.INVALID_FOUNDATION_VERSION:
                    raise MigrationPrepareError(
                        "INVALID_FOUNDATION_VERSION: careerkundi_foundation_version is "
                        f"empty or contains unresolvable revisions "
                        f"{list(result.foundation_revisions)}. No schema mutation."
                    )

                if result.state is DatabaseState.EMPTY:
                    print(
                        "[migration_runner] path=EMPTY → foundation alembic upgrade head",
                        flush=True,
                    )
                else:
                    print(
                        "[migration_runner] path=FOUNDATION_VERSIONED → upgrade head",
                        flush=True,
                    )

                _upgrade_head_on_connection(connection)
                connection.commit()
                _verify_head(connection)
                # Re-read post-upgrade classification for return value.
                return classify_database(connection)
    finally:
        engine.dispose()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        # Production CLI: no target switching.
        print(
            "usage: python -m app.db.migration_runner\n"
            "Target database is settings.database_url_sync only. "
            "CLI flags such as --url / -u are not supported.",
            file=sys.stderr,
            flush=True,
        )
        return 2

    try:
        prepare_database()
    except MigrationPrepareError as exc:
        print(f"[migration_runner] FATAL: {exc}", file=sys.stderr, flush=True)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(
            f"[migration_runner] FATAL: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
