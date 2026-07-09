from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.services import job_discovery


def _settings(*, search_mode: str) -> SimpleNamespace:
    return SimpleNamespace(
        search_mode=search_mode,
        serpapi_key="test-serpapi-key" if search_mode == "live" else "",
    )


def test_live_url_preview_is_explicitly_unverified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        job_discovery,
        "settings",
        _settings(search_mode="live"),
    )

    hits = asyncio.run(
        job_discovery.discover_jobs(
            url="https://jobs.example.org/roles/senior-python-engineer",
        )
    )

    assert len(hits) == 1

    hit = hits[0]
    assert hit["source_url"] == (
        "https://jobs.example.org/roles/senior-python-engineer"
    )
    assert hit["verified"] is False
    assert "preview only" in hit["snippet"].lower()
    assert "not been fetched or verified yet" in hit["snippet"].lower()


def test_live_provider_failure_is_not_replaced_with_mock_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        job_discovery,
        "settings",
        _settings(search_mode="live"),
    )

    async def _provider_failure(
        query: str,
        location: str | None,
    ) -> list[dict]:
        del query, location
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(
        job_discovery,
        "_live_google_jobs",
        _provider_failure,
    )

    with pytest.raises(RuntimeError, match="provider unavailable"):
        asyncio.run(
            job_discovery.discover_jobs(
                q="Python backend engineer",
                location="London",
            )
        )


def test_explicit_mock_mode_still_returns_unverified_mock_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        job_discovery,
        "settings",
        _settings(search_mode="mock"),
    )

    hits = asyncio.run(
        job_discovery.discover_jobs(
            q="Python backend engineer",
            location="London",
        )
    )

    assert hits
    assert all(hit["verified"] is False for hit in hits)
    assert any(
        "mock listing" in (hit.get("snippet") or "").lower()
        for hit in hits
    )


def test_empty_google_jobs_results_still_use_organic_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        job_discovery,
        "settings",
        _settings(search_mode="live"),
    )

    calls: list[tuple[str, str]] = []

    async def _empty_google_jobs(
        query: str,
        location: str | None,
    ) -> list[dict]:
        del location
        calls.append(("google", query))
        return []

    async def _organic_results(
        query: str,
    ) -> list[dict]:
        calls.append(("organic", query))
        return [{
            "title": "Python Backend Engineer",
            "company_name": "Example Co",
            "location": None,
            "employment_type": None,
            "is_remote": False,
            "snippet": "Organic fallback result",
            "source_url": "https://example.org/jobs/python-backend",
            "source_site": "Example",
            "salary_hint": None,
            "verified": True,
        }]

    monkeypatch.setattr(
        job_discovery,
        "_live_google_jobs",
        _empty_google_jobs,
    )
    monkeypatch.setattr(
        job_discovery,
        "_live_organic_jobs",
        _organic_results,
    )

    hits = asyncio.run(
        job_discovery.discover_jobs(
            q="Python backend engineer",
            location="London",
        )
    )

    assert [source for source, _ in calls] == [
        "google",
        "organic",
    ]
    assert len(hits) == 1
    assert hits[0]["title"] == "Python Backend Engineer"
    assert hits[0]["verified"] is True
