from __future__ import annotations

import uuid
from collections.abc import Collection

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.job import SavedJob


def exact_source_url_key(
    source_url: str | None,
) -> str | None:
    """
    Return the conservative exact-match key for a source URL.

    B2.1 intentionally performs no canonicalization beyond trimming
    outer whitespace. Query strings, fragments, path casing, schemes,
    hosts, and trailing slashes are preserved exactly.
    """
    if source_url is None:
        return None

    key = source_url.strip()
    return key or None


async def find_owned_saved_job_by_exact_source_url(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    source_url: str | None,
    import_methods: Collection[str] | None = None,
) -> SavedJob | None:
    """
    Return the newest owned SavedJob with the same exact source URL key.

    Optional import-method filtering keeps this first reuse guard narrow:
    parsed URL imports reuse parsed URL imports, while search preview/mock
    saves reuse search saves.
    """
    key = exact_source_url_key(source_url)
    if key is None:
        return None

    statement = select(SavedJob).where(
        SavedJob.user_id == user_id,
        SavedJob.source_url == key,
    )

    methods = tuple(sorted({
        method
        for method in (import_methods or ())
        if method
    }))

    if methods:
        statement = statement.where(
            SavedJob.import_method.in_(methods)
        )

    statement = (
        statement
        .order_by(SavedJob.created_at.desc())
        .limit(1)
    )

    result = await db.execute(statement)
    return result.scalars().first()
