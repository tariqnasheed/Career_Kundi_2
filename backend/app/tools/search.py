"""
tools/search.py
====================
Google Search grounding tool, used by Reflector agents to independently
re-verify factual claims (§2 "Google Search Grounding", §3.6 anti-
hallucination enforcement) before an Executor's output is approved.

Live mode calls SerpAPI's Google Search API. Mock mode returns clearly
labeled, deterministic "unverified" results built from the local seed
corpus (app/data/seed_corpus.py) so the SAME reflection code path — "search
for claim, check if any result supports it" — runs identically whether or
not SERPAPI_KEY is configured. This matters: it means a developer can read
the Reflector's rejection logic and trust it behaves the same in mock and
live mode, modulo result quality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.data.seed_corpus import SEED_DOCUMENTS

logger = get_logger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    verified: bool  # False in mock mode — always surfaced to the user/Reflector as unverified


class BaseSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """Run a web search and return ranked results."""


class SerpAPISearchProvider(BaseSearchProvider):
    """Live Google Search grounding via SerpAPI."""

    BASE_URL = "https://serpapi.com/search"

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        params = {"q": query, "api_key": settings.serpapi_key, "num": num_results, "engine": "google"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic_results", [])[:num_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    verified=True,
                )
            )
        return results


class MockSearchProvider(BaseSearchProvider):
    """
    Offline grounding stand-in. Performs naive keyword overlap against the
    local seed corpus rather than calling out to the internet, and is
    HONEST about it: every result is returned with `verified=False` so
    Reflector logic and the UI can clearly label these as "unverified —
    configure SERPAPI_KEY for live grounding" rather than silently
    presenting mock data as ground truth.
    """

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        query_terms = set(query.lower().split())
        scored = []
        for doc in SEED_DOCUMENTS:
            doc_terms = set((doc.title + " " + doc.text).lower().split())
            overlap = len(query_terms & doc_terms)
            if overlap > 0:
                scored.append((overlap, doc))
        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [
            SearchResult(
                title=doc.title,
                url=doc.source if doc.source.startswith("http") else f"internal://{doc.doc_id}",
                snippet=doc.text[:240],
                verified=False,
            )
            for _, doc in scored[:num_results]
        ]


_PROVIDER: BaseSearchProvider | None = None


def get_search_provider() -> BaseSearchProvider:
    """Return the configured search provider singleton (live SerpAPI or offline mock)."""
    global _PROVIDER
    if _PROVIDER is None:
        _PROVIDER = SerpAPISearchProvider() if settings.search_mode == "live" else MockSearchProvider()
        logger.info("search_provider_initialized", mode=settings.search_mode)
    return _PROVIDER


async def verify_claim(claim: str) -> tuple[bool, list[SearchResult]]:
    """
    Search for independent support of a factual `claim` string. Returns
    `(is_grounded, results)` where `is_grounded` is True only when at least
    one *verified* (live-mode) result is returned — in mock mode this is
    always False by design, which is exactly what lets the Reflector's
    confidence-scoring logic correctly downgrade confidence when running
    without a real search backend, instead of overstating certainty.
    """
    results = await get_search_provider().search(claim, num_results=3)
    is_grounded = any(r.verified for r in results)
    return is_grounded, results
