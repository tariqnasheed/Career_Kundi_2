#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004E-C company research samples."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE", "false")
os.environ.setdefault("JOB_SEARCH_MODEL_KNOWLEDGE_PROVIDER", "disabled")

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.job_search.company_research import (
    extract_company_from_html,
    merge_company_research_into_job_snapshot,
    research_to_dict,
)
from app.agents.job_search.job_intelligence import build_job_intelligence_profile, profile_summary_text
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.agents.job_search.quality.silly_question_guard import is_silly_question
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004e_c_company_research"

ORG_JSON_LD_HTML = """
<html><head><script type="application/ld+json">
{
  "@type": "Corporation",
  "legalName": "Northline Analytics Ltd",
  "description": "Retail subscription analytics SaaS for mid-market retailers.",
  "url": "https://northline.example/about",
  "sameAs": ["https://www.linkedin.com/company/northline"],
  "location": {"address": {"addressLocality": "Manchester", "addressCountry": "UK"}},
  "areaServed": ["United Kingdom"],
  "makesOffer": [{"name": "KPI dashboards"}, {"name": "Retail forecasting"}],
  "knowsAbout": ["Retail analytics", "SaaS"]
}
</script></head><body></body></html>
"""

HTML_FALLBACK = """
<html><body>
<h2>About Us</h2><p>Harbor Tools builds precision calibration equipment for aerospace maintenance teams.</p>
<h2>Products</h2><ul><li>Torque calibration rigs</li><li>Digital audit trails</li></ul>
<h2>Industries</h2><p>Aerospace, Defence</p>
<h2>Markets</h2><p>UK and EU MRO facilities</p>
</body></html>
"""

_URL_RE = re.compile(r"https?://", re.I)


def _company_facts_count(research: dict[str, Any]) -> int:
    count = 0
    if research.get("company_overview"):
        count += 1
    count += len(research.get("products_services") or [])
    count += len(research.get("industries") or [])
    count += len(research.get("markets") or [])
    count += len(research.get("mission_or_values") or [])
    return count


def _analyze_pack(job: dict[str, Any], questions: list[dict], pack_md: str) -> dict[str, Any]:
    profile = build_job_intelligence_profile(job)
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    audit = job.get("coverage_audit") or {}
    research = job.get("company_research") or {}
    company_qs = [q for q in questions if q.get("category") == "company_specific"]
    return {
        "research_confidence": research.get("research_confidence"),
        "source_urls_count": len(research.get("source_urls") or []),
        "company_facts_count": _company_facts_count(research),
        "products_services_count": len(research.get("products_services") or []),
        "industries_markets_count": len(research.get("industries") or []) + len(research.get("markets") or []),
        "warnings_count": len(research.get("warnings") or []),
        "company_specific_questions_count": len(company_qs),
        "coverage_score": audit.get("coverage_score", 0),
        "fake_urls": len(_URL_RE.findall(pack_md)),
        "generic_phrase_hits": export_blocked_phrase_count(pack_md),
        "silly_question_hits": sum(1 for q in exportable if is_silly_question(q.get("question", ""))),
        "answers_over_500": sum(
            1 for q in exportable if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS
        ),
        "questions": len(exportable),
        "profile_summary": profile_summary_text(profile),
    }


async def _build_json_ld_sample() -> dict[str, Any]:
    research = extract_company_from_html(ORG_JSON_LD_HTML, "https://northline.example/about")
    job = merge_company_research_into_job_snapshot(
        {
            "title": "Data Analyst",
            "company_name": "Northline Analytics",
            "company_url": "https://northline.example/about",
            "description_raw": "Build dashboards and KPI reporting.",
            "responsibilities": ["SQL dashboard creation"],
            "requirements": ["Strong SQL", "Excel"],
            "extracted_skills": [{"skill": "SQL"}, {"skill": "Excel"}],
        },
        research,
    )
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    overview = build_role_overview(job["title"], job)
    pack_md = build_interview_pack_markdown(
        job_title=job["title"],
        company_name=job.get("company_name"),
        questions=questions,
        role_overview=overview,
    )
    payload = {
        "company_research": research_to_dict(research),
        "merged_job": {k: v for k, v in job.items() if k != "job_intelligence_profile"},
        "pack_metrics": _analyze_pack(job, questions, pack_md),
    }
    (OUTPUT_DIR / "sample_organization_json_ld_research.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "sample_interview_pack_with_company_context.md").write_text(pack_md, encoding="utf-8")
    return {
        "sample": "Organization JSON-LD",
        "research_method": ",".join(research.research_methods),
        "confidence": research.research_confidence,
        "company_facts": _company_facts_count(research_to_dict(research)),
        "source_urls": len(research.source_urls),
        "warnings": len(research.warnings),
        **payload["pack_metrics"],
    }


async def _build_html_fallback_sample() -> dict[str, Any]:
    research = extract_company_from_html(HTML_FALLBACK, "https://harbor.example/about")
    job = merge_company_research_into_job_snapshot(
        {
            "title": "Calibration Technician",
            "company_name": "Harbor Tools",
            "company_url": "https://harbor.example/about",
            "description_raw": "Maintain calibration equipment.",
            "responsibilities": ["Equipment checks"],
            "requirements": ["Attention to detail", "Calibration standards"],
            "extracted_skills": [{"skill": "Calibration"}, {"skill": "Quality Control"}],
        },
        research,
    )
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    pack_md = build_interview_pack_markdown(
        job_title=job["title"],
        company_name=job.get("company_name"),
        questions=questions,
    )
    payload = {
        "company_research": research_to_dict(research),
        "merged_job": {k: v for k, v in job.items() if k != "job_intelligence_profile"},
        "pack_metrics": _analyze_pack(job, questions, pack_md),
    }
    (OUTPUT_DIR / "sample_company_html_fallback_research.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    return {
        "sample": "HTML section fallback",
        "research_method": ",".join(research.research_methods),
        "confidence": research.research_confidence,
        "company_facts": _company_facts_count(research_to_dict(research)),
        "source_urls": len(research.source_urls),
        "warnings": len(research.warnings),
        **payload["pack_metrics"],
    }


async def _build_manual_override_sample() -> dict[str, Any]:
    research = extract_company_from_html(ORG_JSON_LD_HTML, "https://northline.example/about")
    merged = merge_company_research_into_job_snapshot(
        {
            "title": "Data Analyst",
            "company_name": "User Override Corp",
            "company_url": "https://northline.example/about",
            "company_profile": {
                "summary": "User-written overview: boutique analytics consultancy focused on retail clients.",
                "products_services": "Custom retail dashboards",
            },
            "description_raw": "Build KPI reporting.",
            "responsibilities": ["Dashboard delivery"],
            "requirements": ["SQL"],
            "extracted_skills": [{"skill": "SQL"}],
        },
        research,
    )

    lines = [
        "# Manual company profile override",
        "",
        "## User-provided (preserved)",
        f"- Summary: {merged['company_profile']['summary']}",
        f"- Products: {merged['company_profile'].get('products_services')}",
        "",
        "## Extracted from mocked company page (filled gaps only)",
        f"- Industries added: {merged['company_profile'].get('industry', 'none')}",
        f"- Research confidence: {research.research_confidence}",
        f"- Source URLs: {', '.join(research.source_urls)}",
        "",
        "User-provided company profile remains primary; extracted research fills missing industry/products fields only.",
    ]
    (OUTPUT_DIR / "sample_manual_company_profile_override.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "sample": "Manual profile override",
        "research_method": ",".join(research.research_methods),
        "confidence": research.research_confidence,
        "company_facts": _company_facts_count(research_to_dict(research)),
        "source_urls": len(research.source_urls),
        "warnings": len(research.warnings),
        "user_summary_preserved": merged["company_profile"]["summary"].startswith("User-written"),
        "industry_filled_from_research": bool(merged["company_profile"].get("industry")),
    }


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        await _build_json_ld_sample(),
        await _build_html_fallback_sample(),
        await _build_manual_override_sample(),
    ]
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    summary_lines = [
        "# Iteration 004E-C Company Profile and Source-Cited Research Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Implementation notes",
        "",
        "- Company research priority: user profile → job posting derived → official company page → meta/HTML fallback.",
        "- Schema.org Organization JSON-LD (`Corporation`, `LocalBusiness`, etc.) is parsed when present.",
        "- HTML section headings (About, Products, Services, Industries, Markets, Mission) provide fallback context.",
        "- Source URLs are real input/captured URLs only — no fabricated citations.",
        "- Safe fetch reuses 004E-B SSRF redirect validation, DNS/IP checks, and 2 MB response cap.",
        "- Model knowledge remains disabled; 004F global job search remains deferred.",
        "",
        "## Sample metrics",
        "",
        "| Sample | Research Method | Confidence | Company Facts | Source URLs | Warnings | Company Questions Added | Fake URLs | Generic Phrase Hits | Silly Question Hits |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        summary_lines.append(
            f"| {row['sample']} | {row.get('research_method', '')} | {row.get('confidence', '')} | "
            f"{row.get('company_facts', 0)} | {row.get('source_urls', 0)} | {row.get('warnings', 0)} | "
            f"{row.get('company_specific_questions_count', row.get('company_questions', 0))} | "
            f"{row.get('fake_urls', 0)} | {row.get('generic_phrase_hits', 0)} | {row.get('silly_question_hits', 0)} |"
        )
    summary_lines.extend(
        [
            "",
            "## Research-assisted development",
            "",
            "- Primary structured source: Schema.org Organization JSON-LD (`application/ld+json`).",
            "- Useful fields: name, legalName, description, url, sameAs, location, areaServed, makesOffer, knowsAbout.",
            "- Fallback: OpenGraph/meta tags and HTML section headings.",
            "- No fake URLs or fabricated company facts.",
            "",
        ]
    )
    (OUTPUT_DIR / "iteration_004e_c_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"Wrote samples to {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
