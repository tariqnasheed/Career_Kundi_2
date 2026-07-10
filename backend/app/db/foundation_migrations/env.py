"""
Foundation Alembic environment (0050-PF1-S1R1A).

Schema authority for the NEW CareerKundi foundation lineage.
Version table: public.careerkundi_foundation_version

When `config.attributes["connection"]` is set (migration_runner), migrations
run on that exact shared connection. Otherwise CLI falls back to
settings.database_url_sync.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base
from app.db.models import *  # noqa: F401,F403  — metadata for autogenerate only

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

FOUNDATION_VERSION_TABLE = "careerkundi_foundation_version"
FOUNDATION_VERSION_SCHEMA = "public"


def _include_object(object, name, type_, reflected, compare_to):
    """Exclude Alembic version table from autogenerate diffs."""
    if type_ == "table" and name == FOUNDATION_VERSION_TABLE:
        return False
    return True


def _configure_context(connection=None, *, url: str | None = None) -> None:
    kwargs = {
        "target_metadata": target_metadata,
        "version_table": FOUNDATION_VERSION_TABLE,
        "version_table_schema": FOUNDATION_VERSION_SCHEMA,
        "include_object": _include_object,
    }
    if connection is not None:
        context.configure(connection=connection, **kwargs)
    else:
        context.configure(url=url, literal_binds=True, **kwargs)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url") or settings.database_url_sync
    _configure_context(url=url)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Shared connection from migration_runner (required for lock/classify/migrate).
    connection = config.attributes.get("connection")
    if connection is not None:
        _configure_context(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
        return

    if not config.get_main_option("sqlalchemy.url"):
        config.set_main_option("sqlalchemy.url", settings.database_url_sync)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as conn:
        _configure_context(connection=conn)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
