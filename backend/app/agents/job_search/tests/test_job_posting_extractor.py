"""Tests for job posting URL extraction (Iteration 004E-B)."""

from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE", "false")

from app.agents.job_search.job_intelligence import build_job_intelligence_profile
from app.agents.job_search.job_posting_extractor import (
    JobPostingExtractionResult,
    _WARN_FETCH_FAILED_SAFE,
    _WARN_NO_USEFUL_INFO,
    _WARN_UNSAFE_REDIRECT,
    enrich_job_snapshot_from_posting_url,
    extract_job_posting_from_html,
    extract_json_ld_job_posting,
    fetch_and_extract_job_posting_url,
    merge_extraction_into_job_snapshot,
    normalize_job_posting_extraction,
)

JSON_LD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Data Analyst | Northline Analytics</title>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [
      {"@type": "Organization", "name": "Noise Org"},
      {
        "@type": "JobPosting",
        "title": "Data Analyst",
        "description": "Build dashboards and KPI reporting for retail analytics clients.",
        "datePosted": "2026-06-01",
        "validThrough": "2026-09-01",
        "employmentType": "FULL_TIME",
        "hiringOrganization": {
          "name": "Northline Analytics",
          "description": "Retail subscription analytics SaaS provider"
        },
        "jobLocation": {
          "@type": "Place",
          "address": {
            "addressLocality": "Manchester",
            "addressCountry": "UK"
          }
        },
        "responsibilities": [
          "Build SQL dashboards for stakeholder reporting",
          "Run daily data quality checks on warehouse tables"
        ],
        "qualifications": [
          "Strong SQL querying and dashboard creation",
          "Experience with data quality checks"
        ],
        "skills": ["SQL", "Power BI", "Python"],
        "baseSalary": {
          "currency": "GBP",
          "value": {"minValue": 45000, "maxValue": 55000, "unitText": "YEAR"}
        }
      }
    ]
  }
  </script>
</head>
<body><h1>Data Analyst</h1></body>
</html>
"""

JSON_LD_TYPE_LIST_HTML = """
<html><head>
<script type="application/ld+json">
{"@type": ["WebPage", "JobPosting"], "title": "Barista", "description": "Serve coffee.",
 "hiringOrganization": {"name": "Cafe Co"},
 "responsibilities": ["Prepare espresso drinks", "Maintain cleanliness"]}
</script>
</head><body></body></html>
"""

META_ONLY_HTML = """
<html><head>
<title>Senior Nurse - City Hospital</title>
<meta property="og:title" content="Senior Nurse" />
<meta property="og:description" content="Provide clinical care and patient safety compliance." />
<meta property="og:site_name" content="City Hospital" />
</head><body><p>Apply now</p></body></html>
"""

HTML_SECTIONS = """
<html><body>
<h2>Responsibilities</h2>
<ul>
  <li>Design LV distribution boards and load calculations</li>
  <li>Support cable sizing and protective device coordination</li>
</ul>
<h2>Requirements</h2>
<ul>
  <li>AutoCAD design experience</li>
  <li>Electrical safety and BS 7671 compliance</li>
</ul>
<h2>Preferred qualifications</h2>
<ul>
  <li>Commissioning experience on commercial sites</li>
</ul>
<h2>Tools</h2>
<ul>
  <li>AutoCAD</li>
  <li>Excel</li>
</ul>
</body></html>
"""

DUPLICATE_BULLETS_HTML = """
<html><body>
<h2>Responsibilities</h2>
<ul>
  <li>Build SQL dashboards</li>
  <li>Build SQL dashboards</li>
  <li>Run data quality checks</li>
</ul>
</body></html>
"""


def test_json_ld_extracts_core_fields():
    result = extract_job_posting_from_html(JSON_LD_HTML, "https://example.com/jobs/data-analyst")
    assert result.title == "Data Analyst"
    assert result.company_name == "Northline Analytics"
    assert "dashboards" in (result.description or "").lower()
    assert len(result.responsibilities) >= 2
    assert len(result.requirements) >= 2
    assert any("sql" in s.lower() for s in result.skills)
    assert result.location and "Manchester" in result.location
    assert result.employment_type
    assert result.date_posted == "2026-06-01"
    assert result.salary_text
    assert result.extraction_confidence == "high"
    assert "json_ld" in result.extraction_methods


def test_json_ld_graph_handled():
    posting = extract_json_ld_job_posting(JSON_LD_HTML)
    assert posting is not None
    assert posting.get("title") == "Data Analyst"


def test_json_ld_type_list_handled():
    result = extract_job_posting_from_html(JSON_LD_TYPE_LIST_HTML, "https://example.com/barista")
    assert result.title == "Barista"
    assert result.company_name == "Cafe Co"
    assert len(result.responsibilities) >= 2


def test_meta_fallback_when_no_json_ld():
    result = extract_job_posting_from_html(META_ONLY_HTML, "https://example.com/nurse")
    assert result.title == "Senior Nurse"
    assert result.description
    assert result.company_name == "City Hospital"
    assert result.extraction_confidence in ("low", "medium")
    assert "meta" in result.extraction_methods


def test_html_section_responsibilities_and_requirements():
    result = extract_job_posting_from_html(HTML_SECTIONS, "https://example.com/ee")
    assert any("distribution" in r.lower() for r in result.responsibilities)
    assert any("autocad" in r.lower() for r in result.requirements)
    assert any("commissioning" in p.lower() for p in result.preferred_qualifications)
    assert any("autocad" in t.lower() for t in result.tools)
    assert result.extraction_confidence in ("medium", "low")


def test_dedupe_repeated_bullets():
    result = extract_job_posting_from_html(DUPLICATE_BULLETS_HTML, "https://example.com/dup")
    lowered = [r.lower() for r in result.responsibilities]
    assert lowered.count("build sql dashboards") == 1


def test_user_fields_override_extracted():
    extraction = extract_job_posting_from_html(JSON_LD_HTML, "https://example.com/jobs/data-analyst")
    job = {
        "title": "Custom Title",
        "company_name": "User Corp",
        "description_raw": "User-written description that must win.",
        "responsibilities": ["User responsibility"],
        "requirements": ["User requirement"],
    }
    merged = merge_extraction_into_job_snapshot(job, extraction)
    assert merged["title"] == "Custom Title"
    assert merged["company_name"] == "User Corp"
    assert merged["description_raw"] == "User-written description that must win."
    assert merged["responsibilities"][0] == "User responsibility"
    assert any("sql" in r.lower() for r in merged["responsibilities"])


def test_extracted_fills_missing_user_fields():
    extraction = extract_job_posting_from_html(JSON_LD_HTML, "https://example.com/jobs/data-analyst")
    job = {"title": "Data Analyst"}
    merged = merge_extraction_into_job_snapshot(job, extraction)
    assert merged.get("company_name") == "Northline Analytics"
    assert merged.get("description_raw")
    assert len(merged.get("responsibilities") or []) >= 2
    assert merged.get("extracted_link_content")


def test_partial_extraction_warnings():
    result = extract_job_posting_from_html(META_ONLY_HTML, "https://example.com/nurse")
    assert result.warnings


def test_failed_confidence_has_warning():
    result = normalize_job_posting_extraction("https://example.com/empty", mapped={}, methods=[], warnings=[])
    assert result.extraction_confidence == "failed"
    assert len(result.warnings) >= 1
    assert _WARN_NO_USEFUL_INFO in result.warnings


@pytest.mark.asyncio
async def test_failed_fetch_does_not_crash(monkeypatch):
    from app.agents.job_search.job_posting_extractor import normalize_job_posting_extraction

    async def _fail(url: str) -> JobPostingExtractionResult:
        return normalize_job_posting_extraction(
            url,
            warnings=["The URL could not be fetched; generation will continue from manually provided fields."],
        )

    monkeypatch.setattr(
        "app.agents.job_search.job_posting_extractor.fetch_and_extract_job_posting_url",
        _fail,
    )
    merged, extraction = await enrich_job_snapshot_from_posting_url(
        {"title": "Engineer"},
        "https://example.com/job",
    )
    assert merged["title"] == "Engineer"
    assert extraction is not None
    assert extraction.warnings


def test_no_fake_url_generated():
    result = extract_job_posting_from_html(JSON_LD_HTML, "https://example.com/jobs/data-analyst")
    assert result.source_url == "https://example.com/jobs/data-analyst"
    assert result.final_url is None or result.final_url.startswith("http")


@pytest.mark.asyncio
async def test_enrich_from_html_fixture():
    merged, extraction = await enrich_job_snapshot_from_posting_url(
        {"title": "Data Analyst"},
        "https://example.com/jobs/data-analyst",
        html=JSON_LD_HTML,
    )
    assert extraction is not None
    assert extraction.extraction_confidence == "high"
    assert merged.get("company_name") == "Northline Analytics"


@pytest.mark.asyncio
async def test_coverage_audit_sees_extracted_items():
    from app.agents.job_search.mock_data import mock_generate_questions

    merged, _ = await enrich_job_snapshot_from_posting_url(
        {"title": "Data Analyst"},
        "https://example.com/jobs/data-analyst",
        html=JSON_LD_HTML,
    )
    questions = mock_generate_questions(merged, focus_areas=[], difficulty="auto")
    profile = build_job_intelligence_profile(merged)
    assert len(profile.responsibilities) >= 2 or len(profile.required_skills) >= 2
    assert profile.extracted_link_content
    assert len(questions) >= 5


@pytest.mark.asyncio
async def test_invalid_scheme_rejected():
    result = await fetch_and_extract_job_posting_url("file:///etc/passwd")
    assert result.extraction_confidence == "failed"
    assert result.warnings


def _public_dns(monkeypatch):
    monkeypatch.setattr(
        "app.agents.job_search.job_posting_extractor._resolve_host_addresses",
        lambda host: ["93.184.216.34"],
    )


def _patch_httpx_transport(monkeypatch, handler):
    import httpx

    transport = httpx.MockTransport(handler)

    class _PatchedClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            kwargs["follow_redirects"] = False
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("app.agents.job_search.job_posting_extractor.httpx.AsyncClient", _PatchedClient)


@pytest.mark.asyncio
async def test_redirect_to_localhost_blocked(monkeypatch):
    import httpx

    _public_dns(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "example.com":
            return httpx.Response(302, headers={"Location": "http://127.0.0.1/job"})
        return httpx.Response(200, text="<html></html>")

    _patch_httpx_transport(monkeypatch, handler)

    result = await fetch_and_extract_job_posting_url("https://example.com/job")
    assert result.extraction_confidence == "failed"
    assert _WARN_UNSAFE_REDIRECT in result.warnings


@pytest.mark.asyncio
async def test_redirect_to_metadata_ip_blocked(monkeypatch):
    import httpx

    _public_dns(monkeypatch)

    _patch_httpx_transport(
        monkeypatch,
        lambda request: httpx.Response(302, headers={"Location": "http://169.254.169.254/latest"}),
    )

    result = await fetch_and_extract_job_posting_url("https://example.com/job")
    assert result.extraction_confidence == "failed"
    assert _WARN_UNSAFE_REDIRECT in result.warnings


@pytest.mark.asyncio
async def test_redirect_to_private_ip_blocked(monkeypatch):
    import httpx

    _public_dns(monkeypatch)

    _patch_httpx_transport(
        monkeypatch,
        lambda request: httpx.Response(302, headers={"Location": "http://10.0.0.5/job"}),
    )

    result = await fetch_and_extract_job_posting_url("https://example.com/job")
    assert result.extraction_confidence == "failed"
    assert _WARN_UNSAFE_REDIRECT in result.warnings


@pytest.mark.asyncio
async def test_redirect_chain_exceeds_max(monkeypatch):
    import httpx

    _public_dns(monkeypatch)
    counter = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        counter["n"] += 1
        return httpx.Response(302, headers={"Location": f"https://example.com/redirect-{counter['n']}"})

    _patch_httpx_transport(monkeypatch, handler)

    result = await fetch_and_extract_job_posting_url("https://example.com/start")
    assert result.extraction_confidence == "failed"
    assert _WARN_FETCH_FAILED_SAFE in result.warnings


@pytest.mark.asyncio
async def test_safe_redirect_chain_succeeds(monkeypatch):
    import httpx

    _public_dns(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url).endswith("/start"):
            return httpx.Response(302, headers={"Location": "https://jobs.example.com/final"})
        return httpx.Response(200, text=JSON_LD_HTML)

    _patch_httpx_transport(monkeypatch, handler)

    result = await fetch_and_extract_job_posting_url("https://example.com/start")
    assert result.extraction_confidence == "high"
    assert result.final_url == "https://jobs.example.com/final"


@pytest.mark.asyncio
async def test_fetch_failure_returns_sanitized_warning(monkeypatch):
    import httpx

    _public_dns(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused to secret.internal:9999")

    _patch_httpx_transport(monkeypatch, handler)

    result = await fetch_and_extract_job_posting_url("https://example.com/job")
    assert result.extraction_confidence == "failed"
    assert _WARN_FETCH_FAILED_SAFE in result.warnings
    assert not any("secret.internal" in w for w in result.warnings)
    assert not any("connection refused" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_content_length_too_large_blocked(monkeypatch):
    import httpx

    _public_dns(monkeypatch)

    _patch_httpx_transport(
        monkeypatch,
        lambda request: httpx.Response(
            200, headers={"Content-Length": str(3 * 1024 * 1024)}, text="x"
        ),
    )

    result = await fetch_and_extract_job_posting_url("https://example.com/huge")
    assert result.extraction_confidence == "failed"
    assert any("too large" in w.lower() for w in result.warnings)


@pytest.mark.asyncio
async def test_resolved_private_ip_blocked(monkeypatch):
    monkeypatch.setattr(
        "app.agents.job_search.job_posting_extractor._resolve_host_addresses",
        lambda host: ["10.0.0.12"],
    )
    result = await fetch_and_extract_job_posting_url("https://jobs.example.com/posting")
    assert result.extraction_confidence == "failed"
    assert result.warnings
