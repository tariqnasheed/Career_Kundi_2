"""
db/session.py
=================
Async SQLAlchemy engine + session factory, and the FastAPI dependency that
yields a request-scoped `AsyncSession`.

We use SQLAlchemy's async engine (backed by `asyncpg`) throughout the app so
that a slow query never blocks the event loop that's also juggling LLM
streaming responses and concurrent agent tool calls.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# The 'engine' is the core connection to the database. It manages a pool of
# connections so we don't have to open a new one for every single request.
# `pool_pre_ping` avoids "server closed the connection unexpectedly" errors
# by checking if a connection is alive before using it.
engine = create_async_engine(
    settings.database_url,
    # In development, 'echo' prints all the SQL queries to the terminal so we can debug them.
    echo=settings.app_debug and settings.app_env == "development",
    pool_pre_ping=True,
    # Keep 10 connections open and ready, but allow up to 30 (10+20) during spikes
    pool_size=10,
    max_overflow=20,
)

# A 'sessionmaker' is a factory that spits out new database sessions.
# A session is a temporary "workspace" where you can read or write data.
# When you're done, you commit the session to save the changes.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    # expire_on_commit=False means we can still access the data on an object
    # even after we've committed it and closed the session.
    expire_on_commit=False,
    autoflush=False,
)

# Alias used by background tasks that need their own independent session
# (outside the request lifecycle — e.g. the queue worker in api/routes/queue.py).
async_session_factory = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a transactional, request-scoped session.

    Usage: `db: AsyncSession = Depends(get_db)` in any route. The session is
    always closed at the end of the request, and any uncommitted changes are
    rolled back automatically if an exception propagates out of the route.
    """
    # Create a new session for this specific web request
    async with AsyncSessionLocal() as session:
        try:
            # Yield hands the session over to your route function
            yield session
        except Exception:
            # If your route crashes (throws an error), we undo any database
            # changes that hadn't been committed yet to keep data safe.
            await session.rollback()
            raise
        finally:
            # Always close the session when the request is done, freeing up
            # the connection for the next user.
            await session.close()
