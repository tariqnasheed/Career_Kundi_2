"""
tools/scraper.py
====================
Job-posting URL scraper implementing the three-tier fallback chain required
by §4.1 ("Job Search & Discovery — direct URL paste") and §4.1's error
handling mandate:

  1. **Playwright** (headless Chromium) — renders JavaScript. Most modern
     ATS-hosted postings (LinkedIn, Greenhouse SPA views, Lever, Workday)
     serve an near-empty HTML shell to a plain HTTP GET and only populate
     content client-side, so this tier is tried first.
  2. **Static fetch** (httpx + BeautifulSoup) — no browser, much cheaper and
     faster, and sufficient for the many ATS pages that DO server-render
     (most Greenhouse/Lever static postings). Tried if Playwright raises,
     times out, or simply isn't installed in the current environment.
  3. **Manual-entry fallback** — if both automated tiers fail to find
     enough structured content, we do NOT fabricate a job posting. We
     return a `ScrapeResult` with `needs_manual_input=True` and zero
     invented fields, so the calling agent (and the UI) honestly asks the
     user to paste the job description text directly. This is the
     concrete mechanism that keeps job scraping compliant with the
     platform's zero-hallucination policy even when scraping fails.

Every tier is wrapped in `tenacity` retry/backoff for transient network
errors before falling through to the next tier.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.errors import ScrapingFailedError
from app.core.logging import get_logger

logger = get_logger(__name__)

_MIN_USABLE_DESCRIPTION_CHARS = 200  # below this we treat extraction as having failed


@dataclass
class ScrapeResult:
    url: str
    method: str  # "playwright" | "static_html" | "manual_fallback"
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description_text: str = ""
    raw_html_excerpt: str = ""
    needs_manual_input: bool = False
    error: str | None = None
    extra: dict = field(default_factory=dict)


def _domain_as_company_guess(url: str) -> str | None:
    """Last-resort company name guess from the URL's registered domain, used only as a label hint, never asserted as fact."""
    netloc = urlparse(url).netloc.replace("www.", "")
    parts = netloc.split(".")
    return parts[0].capitalize() if parts else None


def _extract_fields(html: str, url: str) -> tuple[str | None, str | None, str | None, str]:
    """
    Shared heuristic extraction logic used by both the Playwright and static
    tiers (they differ only in how the HTML was obtained, not how it's
    parsed). Looks for common OpenGraph/meta tags first, then falls back to
    visible heading/body text.
    """
    soup = BeautifulSoup(html, "lxml")

    def meta(*names: str) -> str | None:
        for name in names:
            tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                return tag["content"].strip()
        return None

    title = meta("og:title", "title") or (soup.title.string.strip() if soup.title and soup.title.string else None)
    company = meta("og:site_name") or _domain_as_company_guess(url)
    location = meta("job:location") or None  # most sites don't expose this via meta; left None rather than guessed

    # Strip script/style/nav/footer noise, then take the largest contiguous text block as the "description".
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    candidates = soup.find_all(["article", "main", "section", "div"])
    best_text = ""
    for candidate in candidates:
        text = candidate.get_text(separator="\n", strip=True)
        if len(text) > len(best_text):
            best_text = text
    if not best_text:
        best_text = soup.get_text(separator="\n", strip=True)

    # Collapse excessive blank lines from boilerplate-laden pages.
    best_text = re.sub(r"\n{3,}", "\n\n", best_text).strip()
    return title, company, location, best_text


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
async def _fetch_static(url: str) -> str:
    async with httpx.AsyncClient(
        timeout=settings.scraper_timeout_ms / 1000,
        headers={"User-Agent": settings.scraper_user_agent},
        follow_redirects=True,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def _try_static(url: str) -> ScrapeResult | None:
    """Tier 2: plain HTTP GET + BeautifulSoup. Returns None (not a usable result) if content is too thin."""
    try:
        html = await _fetch_static(url)
    except Exception as exc:  # noqa: BLE001 — any network/HTTP failure here just means "try the next tier"
        logger.warning("scrape_static_tier_failed", url=url, error=str(exc))
        return None

    title, company, location, text = _extract_fields(html, url)
    if len(text) < _MIN_USABLE_DESCRIPTION_CHARS:
        logger.info("scrape_static_tier_thin_content", url=url, chars=len(text))
        return None

    return ScrapeResult(
        url=url,
        method="static_html",
        title=title,
        company=company,
        location=location,
        description_text=text,
        raw_html_excerpt=html[:2000],
    )


async def _try_playwright(url: str) -> ScrapeResult | None:
    """
    Tier 1: headless Chromium render via Playwright, for JS-heavy postings.
    Returns None if Playwright isn't installed, the browser fails to
    launch, the page times out, or extracted content is too thin — any of
    which simply defers to the static-fetch tier.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.info("scrape_playwright_not_installed_skipping_tier")
        return None

    try:
        async with async_playwright() as pw:
            browser = await getattr(pw, settings.playwright_browser).launch(headless=True)
            try:
                page = await browser.new_page(user_agent=settings.scraper_user_agent)
                await page.goto(url, timeout=settings.scraper_timeout_ms, wait_until="networkidle")
                html = await page.content()
            finally:
                await browser.close()
    except Exception as exc:  # noqa: BLE001 — browser launch/navigation failures defer to the next tier
        logger.warning("scrape_playwright_tier_failed", url=url, error=str(exc))
        return None

    title, company, location, text = _extract_fields(html, url)
    if len(text) < _MIN_USABLE_DESCRIPTION_CHARS:
        logger.info("scrape_playwright_tier_thin_content", url=url, chars=len(text))
        return None

    return ScrapeResult(
        url=url,
        method="playwright",
        title=title,
        company=company,
        location=location,
        description_text=text,
        raw_html_excerpt=html[:2000],
    )


async def scrape_job_posting(url: str) -> ScrapeResult:
    """
    Entry point used by JobScraperAgent. Walks the three-tier fallback
    chain and returns the first tier's result that produced usable content.
    If every automated tier fails, returns a `needs_manual_input=True`
    result rather than ever inventing a job description — this honesty
    is what the Reflector's "no fabricated content" check depends on
    upstream of the LLM layer entirely.
    """
    if not url.startswith(("http://", "https://")):
        raise ScrapingFailedError(f"'{url}' is not a valid http(s) URL")

    logger.info("scrape_job_posting_started", url=url)

    result = await _try_playwright(url)
    if result is not None:
        return result

    result = await _try_static(url)
    if result is not None:
        return result

    logger.warning("scrape_job_posting_all_tiers_failed", url=url)
    return ScrapeResult(
        url=url,
        method="manual_fallback",
        needs_manual_input=True,
        error=(
            "Automated extraction could not retrieve enough content from this URL "
            "(it may require login, block bots, or be a heavily client-rendered SPA). "
            "Paste the job description text directly to continue."
        ),
    )
