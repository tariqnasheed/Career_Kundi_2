from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.routes import job_search
from app.schemas.job_search import SavedJobUpdate


def _saved_job(
    *,
    source_url: str | None,
    source_site: str | None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        title="Python Backend Engineer",
        source_url=source_url,
        source_site=source_site,
        import_method="search",
        verification_status="partial",
        verification_sources=[
            {
                "url": "https://evidence.example/source",
                "matched_fields": ["company_name"],
            }
        ],
        extracted_skills=[],
        match_score=None,
    )


def _db() -> SimpleNamespace:
    return SimpleNamespace(
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )


def test_changed_source_url_clears_omitted_stale_source_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _saved_job(
        source_url="https://linkedin.com/jobs/123",
        source_site="LinkedIn",
    )
    db = _db()
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    get_owned_job = AsyncMock(
        return_value=job,
    )
    monkeypatch.setattr(
        job_search,
        "_get_owned_job",
        get_owned_job,
    )

    returned = asyncio.run(
        job_search.update_saved_job(
            job_id=job.id,
            payload=SavedJobUpdate(
                source_url=(
                    "  https://company.workday.com/jobs/999  "
                ),
            ),
            user=user,
            db=db,
        )
    )

    assert returned is job
    assert job.source_url == (
        "https://company.workday.com/jobs/999"
    )
    assert job.source_site is None

    assert job.import_method == "search"
    assert job.verification_status == "partial"
    assert job.verification_sources == [
        {
            "url": "https://evidence.example/source",
            "matched_fields": ["company_name"],
        }
    ]

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(job)


def test_equivalent_trim_only_url_preserves_source_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _saved_job(
        source_url="https://example.com/jobs/123",
        source_site="Example",
    )
    db = _db()
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    monkeypatch.setattr(
        job_search,
        "_get_owned_job",
        AsyncMock(return_value=job),
    )

    returned = asyncio.run(
        job_search.update_saved_job(
            job_id=job.id,
            payload=SavedJobUpdate(
                source_url=(
                    "  https://example.com/jobs/123  "
                ),
            ),
            user=user,
            db=db,
        )
    )

    assert returned.source_url == (
        "https://example.com/jobs/123"
    )
    assert returned.source_site == "Example"


def test_changed_url_respects_explicit_source_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _saved_job(
        source_url="https://linkedin.com/jobs/123",
        source_site="LinkedIn",
    )
    db = _db()
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    monkeypatch.setattr(
        job_search,
        "_get_owned_job",
        AsyncMock(return_value=job),
    )

    returned = asyncio.run(
        job_search.update_saved_job(
            job_id=job.id,
            payload=SavedJobUpdate(
                source_url="https://company.example/jobs/999",
                source_site="Company Careers",
            ),
            user=user,
            db=db,
        )
    )

    assert returned.source_url == (
        "https://company.example/jobs/999"
    )
    assert returned.source_site == "Company Careers"


def test_omitted_source_url_preserves_existing_source_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _saved_job(
        source_url="https://example.com/jobs/123",
        source_site="Example",
    )
    db = _db()
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    monkeypatch.setattr(
        job_search,
        "_get_owned_job",
        AsyncMock(return_value=job),
    )

    returned = asyncio.run(
        job_search.update_saved_job(
            job_id=job.id,
            payload=SavedJobUpdate(
                title="Senior Python Backend Engineer",
            ),
            user=user,
            db=db,
        )
    )

    assert returned.title == (
        "Senior Python Backend Engineer"
    )
    assert returned.source_url == (
        "https://example.com/jobs/123"
    )
    assert returned.source_site == "Example"


def test_clearing_source_url_also_clears_omitted_source_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _saved_job(
        source_url="https://example.com/jobs/123",
        source_site="Example",
    )
    db = _db()
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    monkeypatch.setattr(
        job_search,
        "_get_owned_job",
        AsyncMock(return_value=job),
    )

    returned = asyncio.run(
        job_search.update_saved_job(
            job_id=job.id,
            payload=SavedJobUpdate(
                source_url="   ",
            ),
            user=user,
            db=db,
        )
    )

    assert returned.source_url is None
    assert returned.source_site is None


def test_clearing_source_url_overrides_explicit_source_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _saved_job(
        source_url="https://example.com/jobs/123",
        source_site="Example",
    )
    db = _db()
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    monkeypatch.setattr(
        job_search,
        "_get_owned_job",
        AsyncMock(return_value=job),
    )

    returned = asyncio.run(
        job_search.update_saved_job(
            job_id=job.id,
            payload=SavedJobUpdate(
                source_url="   ",
                source_site="LinkedIn",
            ),
            user=user,
            db=db,
        )
    )

    assert returned.source_url is None
    assert returned.source_site is None


def test_explicit_blank_url_clears_stale_site_when_url_was_already_null(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _saved_job(
        source_url=None,
        source_site="LinkedIn",
    )
    db = _db()
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )

    monkeypatch.setattr(
        job_search,
        "_get_owned_job",
        AsyncMock(return_value=job),
    )

    returned = asyncio.run(
        job_search.update_saved_job(
            job_id=job.id,
            payload=SavedJobUpdate(
                source_url="   ",
            ),
            user=user,
            db=db,
        )
    )

    assert returned.source_url is None
    assert returned.source_site is None
