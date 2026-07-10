"""
db/migrations/env.py
========================
Alembic environment script. Wires Alembic's migration runner to our
SQLAlchemy `Base.metadata` (for autogenerate) and to the synchronous
database URL from `app.core.config.settings` (Alembic itself runs sync,
even though the application uses the async engine at runtime).

Legacy environment — frozen historical lineage (0001_initial). New CareerKundi
foundation schema evolution uses `foundation-alembic.ini` /
`app/db/foundation_migrations/` instead.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import every model so Base.metadata is fully populated before autogenerate
# introspects it for "what tables/columns should exist" diffs.
from app.core.config import settings
from app.db.base import Base
from app.db.models import *  # noqa: F401,F403  (intentional star-import for side effects)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the URL from alembic.ini with our typed settings object so there's
# exactly one place (.env) controlling which database migrations run against.
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without a live DB connection (`alembic upgrade --sql`)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live database connection (the common path)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
