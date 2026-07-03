"""Unit tests for company profile research (Iteration 004E-C)."""

from __future__ import annotations

import json

import pytest

from app.agents.job_search.company_research import (
    build_company_research_from_job_snapshot,
    extract_company_from_html,
    extract_company_sections_from_text,
    extract_json_ld_organization,
    fetch_and_research_company_url,
    merge_company_research,
    merge_company_research_into_job_snapshot,
)

ORG_JSON_LD_HTML = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Corporation",
  "name": "Northline Analytics",
  "legalName": "Northline Analytics Ltd",
  "description": "Retail subscription analytics SaaS for mid-market retailers.",
  "url": "https://northline.example/about",
  "sameAs": ["https://www.linkedin.com/company/northline"],
  "location": {"address": {"addressLocality": "Manchester", "addressCountry": "UK"}},
  "areaServed": ["United Kingdom", "Ireland"],
  "makesOffer": [{"name": "KPI dashboards"}, {"name": "Retail forecasting"}],
  "knowsAbout": ["Retail analytics", "SaaS"]
}
</script>
</head><body></body></html>
"""

GRAPH_HTML = """
<html><head><script type="application/ld+json">
{
  "@graph": [
    {"@type": "WebSite", "name": "Ignore"},
    {"@type": "LocalBusiness", "name": "Harbor Cafe Group", "description": "Specialty coffee retail chain."}
  ]
}
</script></head></html>
"""

TYPE_LIST_HTML = """
<html><head><script type="application/ld+json">
{"@type": ["Organization", "Corporation"], "name": "Dual Type Corp", "description": "Dual typed org."}
</script></head></html>
"""

META_FALLBACK_HTML = """
<html><head>
<title>Fallback Co — About</title>
<meta property="og:title" content="Fallback Co" />
<meta property="og:description" content="Fallback Co builds workflow automation tools for operations teams across Europe." />
<link rel="canonical" href="https://fallback.example/about" />
</head><body></body></html>
"""

SECTION_HTML = """
<html><body>
<nav><p>Home Careers Login Cookie policy</p></nav>
<h2>About Us</h2>
<p>Section Co designs industrial safety monitoring systems for manufacturing plants.</p>
<h2>Products</h2>
<ul><li>Gas leak sensors</li><li>Compliance dashboards</li></ul>
<h2>Industries</h2><p>Manufacturing, Energy</p>
<h2>Markets</h2><p>UK and EU industrial sites</p>
<footer>All rights reserved</footer>
</body></html>
"""


def test_extracts_from_schema_org_organization_json_ld() -> None:
    org = extract_json_ld_organization(ORG_JSON_LD_HTML)
    assert org is not None
    result = extract_company_from_html(ORG_JSON_LD_HTML, "https://northline.example/about")
    assert result.company_name == "Northline Analytics Ltd"
    assert "Retail subscription analytics" in (result.company_overview or "")
    assert result.official_website == "https://northline.example/about"
    assert "KPI dashboards" in result.products_services
    assert "Retail analytics" in result.industries
    assert result.research_confidence == "high"


def test_handles_graph() -> None:
    org = extract_json_ld_organization(GRAPH_HTML)
    assert org is not None
    result = extract_company_from_html(GRAPH_HTML, "https://harbor.example")
    assert result.company_name == "Harbor Cafe Group"
    assert "coffee" in (result.company_overview or "").lower()


def test_handles_type_as_list() -> None:
    org = extract_json_ld_organization(TYPE_LIST_HTML)
    assert org is not None
    result = extract_company_from_html(TYPE_LIST_HTML, "https://dual.example")
    assert result.company_name == "Dual Type Corp"


def test_extracts_products_from_makes_offer_and_html_sections() -> None:
    result = extract_company_from_html(SECTION_HTML, "https://section.example")
    assert any("sensor" in p.lower() for p in result.products_services)
    assert any("manufacturing" in i.lower() for i in result.industries)


def test_meta_fallback() -> None:
    result = extract_company_from_html(META_FALLBACK_HTML, "https://fallback.example/about")
    assert result.company_overview
    assert "workflow automation" in result.company_overview.lower()
    assert result.research_confidence in ("low", "medium")


def test_html_section_extraction_from_text() -> None:
    text = """
About Us
Section Co designs industrial safety monitoring systems.

Products
Gas leak sensors
Compliance dashboards
"""
    sections = extract_company_sections_from_text(text)
    assert sections["overview"]
    assert sections["products_services"]


def test_user_profile_overrides_extracted_profile() -> None:
    job = {
        "company_name": "User Corp",
        "company_profile": {"summary": "User-written company overview that must win."},
        "company_url": "https://northline.example/about",
    }
    page = extract_company_from_html(ORG_JSON_LD_HTML, job["company_url"])
    merged_job = merge_company_research_into_job_snapshot(job, page)
    assert merged_job["company_profile"]["summary"].startswith("User-written")


def test_extracted_research_fills_missing_fields() -> None:
    job = {"company_name": "Northline Analytics", "company_profile": {}}
    page = extract_company_from_html(ORG_JSON_LD_HTML, "https://northline.example/about")
    merged_job = merge_company_research_into_job_snapshot(job, page)
    cp = merged_job["company_profile"]
    assert cp.get("summary")
    assert cp.get("products_services")
    assert cp.get("industry")


def test_source_urls_only_real_input_urls() -> None:
    job = {
        "company_url": "https://northline.example/about",
        "company_profile": {"summary": "Manual profile"},
    }
    base = build_company_research_from_job_snapshot(job)
    assert all(u.startswith("https://") for u in base.source_urls)
    assert "https://northline.example/about" in base.source_urls
    assert not any("fake-url" in u or "placeholder" in u for u in base.source_urls)


def test_no_fake_urls_generated() -> None:
    result = extract_company_from_html(ORG_JSON_LD_HTML, "https://northline.example/about")
    for url in result.source_urls:
        assert "example.invalid" not in url
        assert "fake-url" not in url
        assert "placeholder-url" not in url


def test_unavailable_research_warning() -> None:
    result = extract_company_from_html("<html><body><p>Jobs</p></body></html>", "https://empty.example")
    assert result.research_confidence == "unavailable"
    assert any("unavailable" in w.lower() for w in result.warnings)


def test_unavailable_source_confidence_not_medium() -> None:
    result = extract_company_from_html("<html><body><p>Jobs</p></body></html>", "https://empty.example")
    assert result.research_confidence == "unavailable"
    if result.sources:
        assert result.sources[0].confidence == "unavailable"


def test_source_confidence_aligns_with_research_confidence() -> None:
    result = extract_company_from_html(META_FALLBACK_HTML, "https://fallback.example/about")
    assert result.sources
    assert result.sources[0].confidence == result.research_confidence
    assert result.sources[0].confidence == "low"


def test_merge_company_research_dedupes_lists() -> None:
    a = extract_company_from_html(ORG_JSON_LD_HTML, "https://northline.example/about")
    b = extract_company_from_html(SECTION_HTML, "https://section.example")
    merged = merge_company_research(a, b)
    assert merged.company_name
    assert len(merged.products_services) >= len(a.products_services)


@pytest.mark.asyncio
async def test_safe_fetch_blocks_unsafe_url(monkeypatch: pytest.MonkeyPatch) -> None:
    result = await fetch_and_research_company_url("http://127.0.0.1/company")
    assert result.research_confidence == "unavailable"
    assert result.source_status.get("company_page") == "failed"


@pytest.mark.asyncio
async def test_fetch_uses_mocked_html(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agents.job_search.job_posting_extractor._resolve_host_addresses",
        lambda host: ["93.184.216.34"],
    )

    async def fake_fetch(url: str):
        return ORG_JSON_LD_HTML, url, []

    monkeypatch.setattr(
        "app.agents.job_search.company_research._fetch_html_safely",
        fake_fetch,
    )
    result = await fetch_and_research_company_url("https://northline.example/about")
    assert result.research_confidence == "high"
    assert result.company_name == "Northline Analytics Ltd"
