from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Response

from app.api.routes import job_search
from app.schemas.job_search import (
    JobParseRequest,
    SavedJobCreate,
)
from app.services.saved_job_identity import (
    exact_source_url_key,
    find_owned_saved_job_by_exact_source_url,
)


def test_exact_source_url_key_only_trims_outer_whitespace() -> None:
    source_url = (
        "  HTTPS://Example.COM/jobs/123"
        "?ref=linkedin#apply  "
    )

    assert exact_source_url_key(source_url) == (
        "HTTPS://Example.COM/jobs/123"
        "?ref=linkedin#apply"
    )


def test_exact_source_url_key_preserves_distinct_variants() -> None:
    base = "https://example.com/jobs/123"

    assert exact_source_url_key(base) != exact_source_url_key(
        f"{base}/"
    )
    assert exact_source_url_key(base) != exact_source_url_key(
        f"{base}?utm_source=linkedin"
    )
    assert exact_source_url_key(base) != exact_source_url_key(
        f"{base}#apply"
    )


def test_blank_source_url_skips_database_lookup() -> None:
    db = SimpleNamespace(
        execute=AsyncMock(),
    )

    result = asyncio.run(
        find_owned_saved_job_by_exact_source_url(
            db,
            user_id=uuid.uuid4(),
            source_url="   ",
            import_methods={"search"},
        )
    )

    assert result is None
    db.execute.assert_not_awaited()


def test_exact_source_url_lookup_returns_existing_job() -> None:
    existing_job = SimpleNamespace(
        id=uuid.uuid4(),
        source_url="https://example.com/jobs/123",
        import_method="search",
    )

    scalar_result = MagicMock()
    scalar_result.first.return_value = existing_job

    query_result = MagicMock()
    query_result.scalars.return_value = scalar_result

    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=query_result,
        ),
    )

    returned = asyncio.run(
        find_owned_saved_job_by_exact_source_url(
            db,
            user_id=uuid.uuid4(),
            source_url="  https://example.com/jobs/123  ",
            import_methods={"search"},
        )
    )

    assert returned is existing_job
    db.execute.assert_awaited_once()

    statement = db.execute.await_args.args[0]
    statement_text = str(statement)

    assert "saved_jobs.user_id" in statement_text
    assert "saved_jobs.source_url" in statement_text
    assert "saved_jobs.import_method" in statement_text


def test_parse_job_reuses_existing_parsed_url_before_enrichment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_job = SimpleNamespace(
        id=uuid.uuid4(),
        source_url="https://example.com/jobs/123",
        import_method="pasted_url",
    )

    lookup = AsyncMock(
        return_value=existing_job,
    )
    pipeline = AsyncMock(
        side_effect=AssertionError(
            "enrichment must not run for reused parsed URL"
        ),
    )

    monkeypatch.setattr(
        job_search,
        "find_owned_saved_job_by_exact_source_url",
        lookup,
    )
    monkeypatch.setattr(
        job_search,
        "run_job_enrichment_pipeline",
        pipeline,
    )

    response = Response(
        status_code=201,
    )
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )
    db = SimpleNamespace()

    returned = asyncio.run(
        job_search.parse_job(
            payload=JobParseRequest(
                url="https://example.com/jobs/123",
            ),
            response=response,
            user=user,
            db=db,
        )
    )

    assert returned is existing_job
    assert response.status_code == 200

    lookup.assert_awaited_once()
    assert (
        lookup.await_args.kwargs["import_methods"]
        == {"pasted_url"}
    )
    pipeline.assert_not_awaited()


def test_search_save_reuses_existing_search_row_before_scoring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_job = SimpleNamespace(
        id=uuid.uuid4(),
        source_url="https://example.com/jobs/123",
        import_method="search",
    )

    lookup = AsyncMock(
        return_value=existing_job,
    )
    user_skills = AsyncMock(
        side_effect=AssertionError(
            "match scoring inputs must not load for reused row"
        ),
    )

    monkeypatch.setattr(
        job_search,
        "find_owned_saved_job_by_exact_source_url",
        lookup,
    )
    monkeypatch.setattr(
        job_search,
        "_user_skill_names",
        user_skills,
    )

    response = Response(
        status_code=201,
    )
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )
    db = SimpleNamespace()

    returned = asyncio.run(
        job_search.save_job(
            payload=SavedJobCreate(
                title="Python Backend Engineer",
                source_url=(
                    "https://example.com/jobs/123"
                ),
                import_method="search",
            ),
            response=response,
            user=user,
            db=db,
        )
    )

    assert returned is existing_job
    assert response.status_code == 200

    lookup.assert_awaited_once()
    assert (
        lookup.await_args.kwargs["import_methods"]
        == {"search"}
    )
    user_skills.assert_not_awaited()


def test_search_save_persists_the_same_trimmed_url_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lookup = AsyncMock(
        return_value=None,
    )
    user_skills = AsyncMock(
        return_value=set(),
    )

    monkeypatch.setattr(
        job_search,
        "find_owned_saved_job_by_exact_source_url",
        lookup,
    )
    monkeypatch.setattr(
        job_search,
        "_user_skill_names",
        user_skills,
    )
    monkeypatch.setattr(
        job_search,
        "compute_match_score",
        lambda user_skill_names, job_skills: None,
    )

    db = SimpleNamespace(
        add=MagicMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )
    response = Response(
        status_code=201,
    )

    returned = asyncio.run(
        job_search.save_job(
            payload=SavedJobCreate(
                title="Python Backend Engineer",
                source_url=(
                    "  https://example.com/jobs/123  "
                ),
                import_method="search",
            ),
            response=response,
            user=user,
            db=db,
        )
    )

    assert returned.source_url == (
        "https://example.com/jobs/123"
    )
    assert response.status_code == 201

    lookup.assert_awaited_once()
    assert lookup.await_args.kwargs["source_url"] == (
        "https://example.com/jobs/123"
    )

    db.add.assert_called_once_with(returned)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(returned)


def test_parse_job_uses_and_persists_trimmed_url_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lookup = AsyncMock(
        return_value=None,
    )
    user_skills = AsyncMock(
        return_value=set(),
    )
    cost_monitor = SimpleNamespace(
        persist=AsyncMock(),
    )
    pipeline = AsyncMock(
        return_value={
            "state": {
                "draft_output": {
                    "title": "Python Backend Engineer",
                    "extracted_skills": [],
                },
                "job_text": "Full posting text",
                "verification_status": "unverified",
                "verification_sources": [],
                "model_tier_used": "test",
            },
            "cost_monitor": cost_monitor,
            "source_meta": {
                "source_url": (
                    "  https://example.com/jobs/123  "
                ),
                "source_site": "Example",
                "import_method": "pasted_url",
            },
        }
    )

    monkeypatch.setattr(
        job_search,
        "find_owned_saved_job_by_exact_source_url",
        lookup,
    )
    monkeypatch.setattr(
        job_search,
        "_user_skill_names",
        user_skills,
    )
    monkeypatch.setattr(
        job_search,
        "run_job_enrichment_pipeline",
        pipeline,
    )

    db = SimpleNamespace(
        add=MagicMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )
    response = Response(
        status_code=201,
    )

    returned = asyncio.run(
        job_search.parse_job(
            payload=JobParseRequest(
                url=(
                    "  https://example.com/jobs/123  "
                ),
            ),
            response=response,
            user=user,
            db=db,
        )
    )

    assert returned.source_url == (
        "https://example.com/jobs/123"
    )
    assert response.status_code == 201

    lookup.assert_awaited_once()
    assert lookup.await_args.kwargs["source_url"] == (
        "https://example.com/jobs/123"
    )

    pipeline.assert_awaited_once()
    assert pipeline.await_args.kwargs["url"] == (
        "https://example.com/jobs/123"
    )

    db.add.assert_called_once_with(returned)
    assert db.commit.await_count == 2
    db.refresh.assert_awaited_once_with(returned)

    cost_monitor.persist.assert_awaited_once()


def test_manual_save_does_not_use_search_reuse_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lookup = AsyncMock(
        side_effect=AssertionError(
            "manual save must not use search reuse lookup"
        ),
    )
    user_skills = AsyncMock(
        return_value=set(),
    )

    monkeypatch.setattr(
        job_search,
        "find_owned_saved_job_by_exact_source_url",
        lookup,
    )
    monkeypatch.setattr(
        job_search,
        "_user_skill_names",
        user_skills,
    )
    monkeypatch.setattr(
        job_search,
        "compute_match_score",
        lambda user_skill_names, job_skills: None,
    )

    db = SimpleNamespace(
        add=MagicMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )
    user = SimpleNamespace(
        id=uuid.uuid4(),
    )
    response = Response(
        status_code=201,
    )

    returned = asyncio.run(
        job_search.save_job(
            payload=SavedJobCreate(
                title="Manual Role",
                source_url="https://example.com/jobs/123",
                import_method="manual",
            ),
            response=response,
            user=user,
            db=db,
        )
    )

    lookup.assert_not_awaited()
    assert returned.import_method == "manual"
    assert response.status_code == 201

    db.add.assert_called_once_with(returned)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(returned)
