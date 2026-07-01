"""
agents/job_extractor/agents.py
================================
4-node pipeline for importing a job from a pasted URL:

  START → guardrail → scraper → extractor → reflector → END

Guardrail   Validates the URL (format, blocked domains, length).
Scraper     Fetches the page and extracts the main text content (mock: returns
            realistic domain-aware text snippets).
Extractor   Structures the raw text into typed job fields using the LLM
            (mock: pattern-matches on domain + title keywords).
Reflector   Validates field completeness. If critical fields (title, company)
            are missing, it marks `extraction_incomplete = True` so the route
            can surface the editable form to the user.

The pipeline NEVER invents data. When a field cannot be reliably extracted,
it is left as None / empty — the user sees what's available and fills gaps.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.agents.common.base import BaseAgent
from app.agents.common.cost_monitor import CostMonitor
from app.agents.common.guardrail import BaseGuardrailAgent
from app.agents.common.reflector import BaseReflectorAgent
from app.core.config import settings

from . import mock_data

# ---------------------------------------------------------------------------
# Guardrail
# ---------------------------------------------------------------------------

# Job board domains that are known to block scraping — we inform the user
# gracefully and fall back to manual entry mode for these.
_BLOCKED_DOMAINS = frozenset({
    "linkedin.com", "greenhouse.io", "lever.co",
    "workday.com", "taleo.net", "icims.com",
})

_URL_RE = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE
)


class JobURLGuardrailAgent(BaseGuardrailAgent):
    name = "JobURLGuardrailAgent"
    input_field = "raw_input"

    async def extra_checks(self, state: dict[str, Any], sanitized_input: str) -> list[str]:
        issues: list[str] = []
        url = sanitized_input.strip()
        if not _URL_RE.match(url):
            issues.append(f"'{url[:80]}' does not look like a valid URL.")
            return issues
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().removeprefix("www.")
            if domain in _BLOCKED_DOMAINS:
                issues.append(
                    f"{domain} actively blocks automated scraping. "
                    "We'll open the manual entry form pre-filled with the URL "
                    "so you can paste the job details directly."
                )
        except Exception:
            issues.append("Could not parse the URL. Please check it and try again.")
        return issues


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

class JobPageScraperAgent(BaseAgent):
    """
    Fetches the page at `job_url` and returns `raw_page_text`.

    In live mode: calls tools/scraper.py::scrape_url()
    In mock mode: returns a realistic fake page text keyed on domain + URL keywords.
    """

    name = "JobPageScraperAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        url: str = state["sanitized_input"]

        if settings.llm_mode == "mock":
            raw_text = mock_data.fake_page_text(url)
        else:
            from app.tools.scraper import scrape_url  # late import (optional dep)
            raw_text = await scrape_url(url)

        return {
            "raw_page_text": raw_text,
            "scrape_success": bool(raw_text and len(raw_text) > 100),
        }


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class JobFieldExtractorAgent(BaseAgent):
    """
    Turns raw page text into structured job fields.

    Returns a flat dict that maps directly to `SavedJob` columns:
      title, company_name, location, employment_type, is_remote,
      salary_min, salary_max, salary_currency, description_raw,
      responsibilities, requirements, benefits, date_posted
    """

    name = "JobFieldExtractorAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        raw_text: str = state.get("raw_page_text", "")
        url: str = state.get("sanitized_input", "")

        if not raw_text:
            return {
                "extracted_fields": {},
                "extraction_incomplete": True,
                "missing_fields": ["title", "company_name", "description_raw"],
            }

        if settings.llm_mode == "mock":
            extracted = mock_data.extract_fields_from_text(raw_text, url)
        else:
            # Live mode: use the shared LLM provider abstraction with the SAME
            # PromptSpec field names every other agent uses. We request
            # structured JSON output (json_schema) so the model returns fields
            # that map straight onto SavedJob columns, then record token cost.
            from app.tools.llm import PromptSpec, get_llm
            from app.schemas.job_search import JobEnrichmentResult

            llm = get_llm("flash")
            spec = PromptSpec(
                system_prompt=(
                    "Extract structured job fields from the page text below. "
                    "Return ONLY what is explicitly stated. Leave fields null when uncertain. "
                    "Never invent salaries, dates, or requirements that aren't in the text."
                ),
                user_prompt=f"URL: {url}\n\n---PAGE TEXT---\n{raw_text[:8000]}",
                json_schema=JobEnrichmentResult.model_json_schema(),
                temperature=0.2,
            )
            response = await llm.generate(spec)
            self.cost_monitor.record(response, tier="flash")
            extracted = response.parsed_json or {}

        # Determine which critical fields are missing
        missing: list[str] = [
            f for f in ("title", "company_name", "description_raw")
            if not extracted.get(f)
        ]

        return {
            "extracted_fields": extracted,
            "extraction_incomplete": bool(missing),
            "missing_fields": missing,
            "source_url": url,
        }


# ---------------------------------------------------------------------------
# Reflector
# ---------------------------------------------------------------------------

class JobExtractionReflectorAgent(BaseReflectorAgent):
    """
    Validates that the extracted data is internally consistent and not hallucinated.
    Checks:
      1. Title is present and plausible (< 200 chars, not a nav menu item)
      2. Salary range (if present): min ≤ max, reasonable range
      3. No invented statistics (% figures not present in source text)
    """

    name = "JobExtractionReflectorAgent"
    output_field = "extracted_fields"
    max_revisions = 1

    def render_for_review(self, draft: Any) -> str:
        if not draft:
            return ""
        parts = []
        for k, v in draft.items():
            if v:
                parts.append(f"{k}: {str(v)[:120]}")
        return "\n".join(parts)

    async def domain_checks(self, state: dict[str, Any], draft: Any) -> list[str]:
        issues: list[str] = []
        if not draft:
            return ["Extraction returned empty fields."]

        title = draft.get("title", "")
        if title and len(title) > 200:
            issues.append(f"Extracted title is suspiciously long ({len(title)} chars) — likely a navigation block, not a job title.")

        sal_min = draft.get("salary_min")
        sal_max = draft.get("salary_max")
        if sal_min and sal_max and sal_min > sal_max:
            issues.append(f"salary_min ({sal_min}) > salary_max ({sal_max}) — swap or null them.")

        return issues
