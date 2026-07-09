from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.routes import job_search
from app.schemas.job_search import SavedJobRead


class _ScalarCollection:
    def __init__(
        self,
        items: list[SavedJobRead],
    ) -> None:
        self._items = items

    def all(self) -> list[SavedJobRead]:
        return list(self._items)


class _RowsResult:
    def __init__(
        self,
        items: list[SavedJobRead],
    ) -> None:
        self._items = items

    def scalars(self) -> _ScalarCollection:
        return _ScalarCollection(
            self._items,
        )


def _job(
    title: str,
) -> SavedJobRead:
    now = datetime.now(
        timezone.utc,
    )

    return SavedJobRead(
        id=uuid.uuid4(),
        import_method="search",
        title=title,
        created_at=now,
        updated_at=now,
    )


def _db_with_rows(
    rows: list[SavedJobRead],
) -> SimpleNamespace:
    return SimpleNamespace(
        execute=AsyncMock(
            return_value=_RowsResult(rows),
        ),
    )


def test_paginated_search_uses_lookahead_for_has_next() -> None:
    rows = [
        _job("Job A"),
        _job("Job B"),
        _job("Job C"),
    ]
    db = _db_with_rows(rows)
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    response = asyncio.run(
        job_search.search_saved_jobs_paginated(
            q=None,
            location=None,
            employment_type=None,
            remote=None,
            page=1,
            page_size=2,
            user=user,
            db=db,
        )
    )

    assert response.items == rows[:2]
    assert response.page == 1
    assert response.page_size == 2
    assert response.has_next is True


def test_full_final_page_does_not_report_false_next() -> None:
    rows = [
        _job("Job C"),
        _job("Job D"),
    ]
    db = _db_with_rows(rows)
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    response = asyncio.run(
        job_search.search_saved_jobs_paginated(
            q=None,
            location=None,
            employment_type=None,
            remote=None,
            page=2,
            page_size=2,
            user=user,
            db=db,
        )
    )

    assert response.items == rows
    assert response.page == 2
    assert response.page_size == 2
    assert response.has_next is False


def test_paginated_search_uses_page_size_plus_one_and_expected_offset() -> None:
    db = _db_with_rows([])
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    asyncio.run(
        job_search.search_saved_jobs_paginated(
            q=None,
            location=None,
            employment_type=None,
            remote=None,
            page=3,
            page_size=4,
            user=user,
            db=db,
        )
    )

    statement = db.execute.await_args.args[0]
    sql = str(
        statement.compile(
            compile_kwargs={
                "literal_binds": True,
            },
        )
    )

    assert "LIMIT 5" in sql
    assert "OFFSET 8" in sql


def test_paginated_search_keeps_filters_and_user_scope_in_one_statement() -> None:
    db = _db_with_rows([])
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    asyncio.run(
        job_search.search_saved_jobs_paginated(
            q="Engineer",
            location="London",
            employment_type="Full-time",
            remote=False,
            page=1,
            page_size=20,
            user=user,
            db=db,
        )
    )

    statement = db.execute.await_args.args[0]
    where_sql = str(
        statement.whereclause
    )
    params = statement.compile().params

    assert "saved_jobs.user_id" in where_sql
    assert "saved_jobs.title" in where_sql
    assert "saved_jobs.company_name" in where_sql
    assert "saved_jobs.description_raw" in where_sql
    assert "saved_jobs.location" in where_sql
    assert "saved_jobs.employment_type" in where_sql
    assert "saved_jobs.is_remote" in where_sql

    assert user.id in params.values()
    assert "%Engineer%" in params.values()
    assert "%London%" in params.values()
    assert "Full-time" in params.values()


def test_paginated_search_has_deterministic_tie_break_order() -> None:
    db = _db_with_rows([])
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    asyncio.run(
        job_search.search_saved_jobs_paginated(
            q=None,
            location=None,
            employment_type=None,
            remote=None,
            page=1,
            page_size=20,
            user=user,
            db=db,
        )
    )

    statement = db.execute.await_args.args[0]
    sql = str(
        statement.compile(
            compile_kwargs={
                "literal_binds": True,
            },
        )
    )

    assert (
        "ORDER BY saved_jobs.created_at DESC, "
        "saved_jobs.id DESC"
    ) in sql


def test_legacy_search_keeps_array_return_contract() -> None:
    rows = [
        _job("Job A"),
        _job("Job B"),
    ]
    db = _db_with_rows(rows)
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    response = asyncio.run(
        job_search.search_saved_jobs(
            q=None,
            location=None,
            employment_type=None,
            remote=None,
            page=1,
            page_size=20,
            user=user,
            db=db,
        )
    )

    assert isinstance(
        response,
        list,
    )
    assert response == rows
