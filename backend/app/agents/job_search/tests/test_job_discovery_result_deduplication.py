from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import job_discovery
from app.services.job_discovery_dedupe import (
    exact_discovery_source_url_key,
    suppress_duplicate_discovery_results,
)


def _settings(*, search_mode: str) -> SimpleNamespace:
    return SimpleNamespace(
        search_mode=search_mode,
        serpapi_key=(
            "test-serpapi-key"
            if search_mode == "live"
            else ""
        ),
    )


def _hit(
    title: str,
    source_url: str,
    *,
    verified: bool = True,
) -> dict:
    return {
        "title": title,
        "company_name": "Example Co",
        "location": "London",
        "employment_type": "Full-time",
        "is_remote": False,
        "snippet": f"{title} snippet",
        "source_url": source_url,
        "source_site": "Example",
        "salary_hint": None,
        "verified": verified,
    }


def test_exact_discovery_source_url_key_only_trims_outer_whitespace() -> None:
    source_url = (
        "  HTTPS://Example.COM/jobs/123"
        "?ref=linkedin#apply  "
    )

    assert exact_discovery_source_url_key(
        source_url,
    ) == (
        "HTTPS://Example.COM/jobs/123"
        "?ref=linkedin#apply"
    )

    assert exact_discovery_source_url_key(
        "   ",
    ) is None

    assert exact_discovery_source_url_key(
        None,
    ) is None


def test_first_exact_url_result_wins_and_order_is_preserved() -> None:
    first = _hit(
        "First",
        "  https://example.com/jobs/123  ",
    )
    duplicate = _hit(
        "Duplicate",
        "https://example.com/jobs/123",
    )
    other = _hit(
        "Other",
        "https://example.com/jobs/999",
    )

    returned = suppress_duplicate_discovery_results([
        first,
        duplicate,
        other,
    ])

    assert [
        hit["title"]
        for hit in returned
    ] == [
        "First",
        "Other",
    ]

    assert returned[0]["source_url"] == (
        "https://example.com/jobs/123"
    )

    assert first["source_url"] == (
        "  https://example.com/jobs/123  "
    )


def test_url_variants_remain_distinct() -> None:
    base = "https://example.com/jobs/123"

    returned = suppress_duplicate_discovery_results([
        _hit("Base", base),
        _hit("Trailing slash", f"{base}/"),
        _hit(
            "Query",
            f"{base}?utm_source=linkedin",
        ),
        _hit("Fragment", f"{base}#apply"),
    ])

    assert [
        hit["title"]
        for hit in returned
    ] == [
        "Base",
        "Trailing slash",
        "Query",
        "Fragment",
    ]


def test_keyless_results_are_retained_without_guessing_identity() -> None:
    blank_one = {
        "title": "Blank one",
        "source_url": "   ",
    }
    blank_two = {
        "title": "Blank two",
        "source_url": "   ",
    }
    missing = {
        "title": "Missing URL",
    }

    returned = suppress_duplicate_discovery_results([
        blank_one,
        blank_two,
        missing,
    ])

    assert returned == [
        blank_one,
        blank_two,
        missing,
    ]


def test_explicit_mock_mode_suppresses_duplicate_cards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        job_discovery,
        "settings",
        _settings(search_mode="mock"),
    )

    mock_results = [
        _hit(
            "First",
            "  https://careers.example.com/jobs/123  ",
            verified=False,
        ),
        _hit(
            "Duplicate",
            "https://careers.example.com/jobs/123",
            verified=False,
        ),
        _hit(
            "Other",
            "https://careers.example.com/jobs/999",
            verified=False,
        ),
    ]

    monkeypatch.setattr(
        job_discovery,
        "_mock_discover",
        lambda *args: mock_results,
    )

    returned = asyncio.run(
        job_discovery.discover_jobs(
            q="Python engineer",
        )
    )

    assert [
        hit["title"]
        for hit in returned
    ] == [
        "First",
        "Other",
    ]

    assert returned[0]["source_url"] == (
        "https://careers.example.com/jobs/123"
    )


def test_live_google_results_are_suppressed_without_reranking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        job_discovery,
        "settings",
        _settings(search_mode="live"),
    )

    google = AsyncMock(
        return_value=[
            _hit(
                "First",
                "https://example.com/jobs/123",
            ),
            _hit(
                "Duplicate",
                "  https://example.com/jobs/123  ",
            ),
            _hit(
                "Other",
                "https://example.com/jobs/999",
            ),
        ]
    )
    organic = AsyncMock(
        side_effect=AssertionError(
            "organic fallback must not run "
            "when Google returned results"
        ),
    )

    monkeypatch.setattr(
        job_discovery,
        "_live_google_jobs",
        google,
    )
    monkeypatch.setattr(
        job_discovery,
        "_live_organic_jobs",
        organic,
    )

    returned = asyncio.run(
        job_discovery.discover_jobs(
            q="Python engineer",
            location="London",
        )
    )

    assert [
        hit["title"]
        for hit in returned
    ] == [
        "First",
        "Other",
    ]

    google.assert_awaited_once()
    organic.assert_not_awaited()


def test_organic_fallback_results_are_also_suppressed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        job_discovery,
        "settings",
        _settings(search_mode="live"),
    )

    google = AsyncMock(
        return_value=[],
    )
    organic = AsyncMock(
        return_value=[
            _hit(
                "Organic first",
                "https://example.com/jobs/123",
            ),
            _hit(
                "Organic duplicate",
                "https://example.com/jobs/123",
            ),
            _hit(
                "Organic other",
                "https://example.com/jobs/999",
            ),
        ]
    )

    monkeypatch.setattr(
        job_discovery,
        "_live_google_jobs",
        google,
    )
    monkeypatch.setattr(
        job_discovery,
        "_live_organic_jobs",
        organic,
    )

    returned = asyncio.run(
        job_discovery.discover_jobs(
            q="Python engineer",
            location="London",
        )
    )

    assert [
        hit["title"]
        for hit in returned
    ] == [
        "Organic first",
        "Organic other",
    ]

    google.assert_awaited_once()
    organic.assert_awaited_once()
