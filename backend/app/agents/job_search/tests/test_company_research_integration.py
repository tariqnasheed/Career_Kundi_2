"""Integration tests for company research in interview-pack flow (Iteration 004E-C)."""

from __future__ import annotations

import pytest

from app.agents.job_search.company_research import (
    enrich_job_snapshot_with_company_research,
    extract_company_from_html,
    research_to_dict,
)
from app.agents.job_search.job_intelligence import build_job_intelligence_profile
from app.agents.job_search.mock_data import mock_generate_questions

ORG_HTML = """
<html><head><script type="application/ld+json">
{"@type": "Organization", "name": "GridServe Energy", "description": "Battery storage and grid services.",
 "makesOffer": [{"name": "Battery storage"}], "knowsAbout": ["Renewable energy"]}
</script></head></html>
"""


@pytest.mark.asyncio
async def test_enrich_job_snapshot_with_company_research(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agents.job_search.job_posting_extractor._resolve_host_addresses",
        lambda host: ["93.184.216.34"],
    )

    async def fake_fetch(url: str):
        return ORG_HTML, url, []

    monkeypatch.setattr(
        "app.agents.job_search.company_research._fetch_html_safely",
        fake_fetch,
    )
    job = {
        "title": "Energy Analyst",
        "company_name": "GridServe Energy",
        "company_url": "https://gridserve.example/about",
        "company_profile": {},
        "description_raw": "Analyze battery performance data.",
        "responsibilities": [],
        "requirements": ["SQL"],
    }
    merged, research = await enrich_job_snapshot_with_company_research(job)
    assert merged.get("company_research")
    assert research.research_confidence in ("high", "medium")
    assert merged["company_profile"].get("summary")


def test_company_research_in_job_intelligence_profile() -> None:
    page = extract_company_from_html(ORG_HTML, "https://gridserve.example/about")
    job = {
        "title": "Energy Analyst",
        "company_name": "GridServe Energy",
        "company_url": "https://gridserve.example/about",
        "company_profile": {"summary": page.company_overview, "products_services": ", ".join(page.products_services)},
        "company_research": research_to_dict(page),
        "description_raw": "Analyze battery performance.",
        "responsibilities": ["Monitor storage KPIs"],
        "requirements": ["SQL"],
    }
    profile = build_job_intelligence_profile(job)
    assert profile.company_profile
    assert profile.company_products_services
    assert profile.source_status.get("web_research") in ("used", "available_not_used", "not_configured")


def test_company_specific_questions_from_research() -> None:
    page = extract_company_from_html(ORG_HTML, "https://gridserve.example/about")
    job = {
        "title": "Data Analyst",
        "company_name": "GridServe Energy",
        "company_profile": {"summary": page.company_overview, "products_services": "Battery storage"},
        "company_research": research_to_dict(page),
        "description_raw": "Analyze battery performance and grid storage KPIs.",
        "responsibilities": [
            "SQL dashboard creation for storage KPI reporting",
            "Data quality checks on battery telemetry feeds",
        ],
        "requirements": ["SQL querying", "Renewable energy awareness", "Excel or BI tools"],
        "extracted_skills": [{"skill": "SQL"}, {"skill": "Data Quality"}, {"skill": "Excel"}],
    }
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    company_qs = [q for q in questions if q.get("category") == "company_specific"]
    assert len(company_qs) >= 2
