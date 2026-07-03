"""Source ladder integration tests (Iteration 004E-D)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.agents.job_search.job_intelligence import build_job_intelligence_profile
from app.agents.job_search.knowledge.source_ladder import (
    apply_source_ladder_to_job,
    build_source_ladder_questions,
    build_source_ladder_status,
    collect_source_derived_items,
    refresh_source_ladder_usage_from_questions,
)
from app.agents.job_search.company_research import extract_company_from_html, merge_company_research_into_job_snapshot
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.agents.job_search.quality.silly_question_guard import is_silly_question
from app.core.config import settings

RICH_JOB = {
    "title": "Data Analyst",
    "company_name": "Northline Analytics",
    "description_raw": "Build dashboards and KPI reporting for retail analytics clients.",
    "responsibilities": ["SQL dashboard creation", "Daily data quality checks"],
    "requirements": ["Strong SQL", "Stakeholder communication", "Preferred: Python automation"],
    "extracted_skills": [{"skill": "SQL"}, {"skill": "Python"}, {"skill": "Excel"}],
    "company_profile": {"summary": "User-written boutique analytics consultancy."},
}

URL_JOB = {
    "title": "Data Analyst",
    "company_name": "Northline Analytics",
    "description_raw": "",
    "responsibilities": [],
    "requirements": [],
    "extracted_skills": [{"skill": "SQL"}],
    "job_posting_extraction": {
        "extraction_confidence": "high",
        "responsibilities": ["Build executive KPI dashboards", "Automate weekly reporting"],
        "tools": ["Power BI", "SQL"],
        "skills": ["SQL", "Python"],
        "requirements": ["3+ years analytics experience"],
    },
    "extracted_link_content": "Data Analyst Northline Build executive KPI dashboards",
}

COMPANY_JOB = {
    **RICH_JOB,
    "company_research": {
        "research_confidence": "high",
        "products_services": ["KPI dashboards", "Retail forecasting"],
        "industries": ["Retail analytics"],
        "markets": ["United Kingdom"],
        "source_status": {"company_page": "used", "user_company_profile": "used"},
    },
}


def test_user_fields_override_weaker_sources_in_profile() -> None:
    job = {
        **URL_JOB,
        "company_profile": {"summary": "User company overview wins."},
        "responsibilities": ["User-listed stakeholder communication"],
    }
    profile = build_job_intelligence_profile(job)
    assert profile.company_profile == "User company overview wins."
    assert "User-listed" in profile.responsibilities[0]


def test_url_extraction_items_added_to_audit() -> None:
    profile = build_job_intelligence_profile(URL_JOB)
    url_items = [i for i in profile.extracted_items if i.source == "job_posting_extraction"]
    assert len(url_items) >= 2
    assert any("dashboard" in i.text.lower() for i in url_items)


def test_company_research_items_in_audit() -> None:
    profile = build_job_intelligence_profile(COMPANY_JOB)
    cr_items = [i for i in profile.extracted_items if i.source == "company_research"]
    assert any(i.item_type == "company_product_service" for i in cr_items)
    assert any(i.item_type == "company_industry" for i in cr_items)


def test_url_extraction_generates_responsibility_questions() -> None:
    ctx = apply_source_ladder_to_job(dict(URL_JOB))
    qs = build_source_ladder_questions(URL_JOB, ctx)
    assert any("job posting" in q.get("why_asked", "").lower() for q in qs)
    assert any("dashboard" in q.get("question", "").lower() for q in qs)


def test_url_tools_generate_tool_questions() -> None:
    ctx = apply_source_ladder_to_job(dict(URL_JOB))
    qs = build_source_ladder_questions(URL_JOB, ctx)
    assert any("Power BI" in q.get("question", "") for q in qs)


def test_company_research_generates_company_questions() -> None:
    ctx = apply_source_ladder_to_job(dict(COMPANY_JOB))
    qs = build_source_ladder_questions(COMPANY_JOB, ctx)
    assert any("KPI dashboards" in q.get("question", "") for q in qs)
    assert any("Retail analytics" in q.get("question", "") for q in qs)


def test_model_knowledge_disabled_by_default() -> None:
    assert settings.job_search_enable_model_knowledge is False
    status = build_source_ladder_status(RICH_JOB)
    assert status["model_knowledge"] == "disabled"


def test_source_status_reflects_url_and_company() -> None:
    job = {**COMPANY_JOB, **URL_JOB}
    status = build_source_ladder_status(job)
    assert status["link_extraction"] == "used"
    assert status["company_research"] == "used"


def test_questions_carry_source_metadata() -> None:
    job = dict(COMPANY_JOB)
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    assert questions
    meta_q = [q for q in questions if q.get("question_source_types")]
    assert meta_q
    assert meta_q[0].get("source_status")


def test_no_silly_or_generic_questions() -> None:
    job = dict(COMPANY_JOB)
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    exportable = [q for q in questions if q.get("model_answer")]
    blob = " ".join(q.get("question", "") + " " + q.get("model_answer", "") for q in exportable)
    assert export_blocked_phrase_count(blob) == 0
    assert not any(is_silly_question(q.get("question", "")) for q in exportable)


def test_no_role_specific_leaks() -> None:
    import re

    job = dict(COMPANY_JOB)
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    blob = " ".join(q.get("question", "") + " " + q.get("model_answer", "") for q in questions)
    assert not re.search(r"\bRole Specific\b", blob)


def test_title_only_limited_coverage() -> None:
    job = {"title": "Mystery Role"}
    questions = mock_generate_questions(job, focus_areas=[], difficulty="auto")
    audit = job.get("coverage_audit") or {}
    assert audit.get("coverage_score", 0) == 0 or audit.get("total_items", 0) == 0


def test_answers_within_length_limit() -> None:
    job = dict(RICH_JOB)
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    over = [q for q in questions if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS]
    assert not over


def test_source_ladder_has_no_direct_network_imports() -> None:
    path = Path(__file__).resolve().parents[1] / "knowledge" / "source_ladder.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    banned = {"httpx", "requests", "urllib", "aiohttp"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned


def test_collect_source_derived_dedupes_user_fields() -> None:
    profile = build_job_intelligence_profile(RICH_JOB)
    extra = collect_source_derived_items(RICH_JOB, profile.extracted_items)
    assert not extra  # user fields already cover responsibilities/skills


ORG_HTML = """
<html><head><script type="application/ld+json">
{"@type":"Corporation","legalName":"Northline Analytics Ltd","description":"Retail analytics SaaS.",
 "makesOffer":[{"name":"KPI dashboards"}],"knowsAbout":["Retail analytics"]}
</script></head></html>
"""


def test_html_company_extraction_marks_research_used() -> None:
    research = extract_company_from_html(ORG_HTML, "https://northline.example/about")
    job = merge_company_research_into_job_snapshot({"title": "Data Analyst"}, research)
    status = build_source_ladder_status(job)
    assert status["company_research"] == "used"
    assert status["web_research"] == "used"


def test_document_library_marked_used_after_generation() -> None:
    job = {
        "title": "Barista",
        "company_name": "Harbour Cafe",
        "description_raw": "Espresso and HACCP hygiene during rush service.",
        "responsibilities": ["Espresso preparation", "HACCP hygiene controls"],
        "requirements": ["Coffee preparation", "HACCP"],
        "extracted_skills": [{"skill": "Coffee Preparation"}, {"skill": "HACCP"}],
    }
    questions = mock_generate_questions(job, focus_areas=["Coffee Preparation", "HACCP"], difficulty="mid")
    status = build_source_ladder_status(job)
    assert status["document_library"] == "used"
    assert any(
        any(
            s.get("source_type") == "document_library" and s.get("status") == "used"
            for s in (q.get("study_sources") or {}).get("sources") or []
        )
        for q in questions
    )


def test_refresh_source_ladder_promotes_company_research() -> None:
    job = dict(COMPANY_JOB)
    apply_source_ladder_to_job(job)
    questions = [
        {
            "question": "How would you support KPI dashboards?",
            "question_source_types": ["company_research"],
            "generation_stage_meta": {"source_type": "company_research", "source_item_text": "KPI dashboards"},
        }
    ]
    refresh_source_ladder_usage_from_questions(job, questions)
    assert job["source_ladder"]["source_status"]["company_research"] == "used"


def test_refresh_source_ladder_skips_when_no_exportable_questions() -> None:
    job = {
        "title": "Barista",
        "source_ladder": {
            "source_status": {
                "document_library": "available_not_used",
                "company_research": "available_not_used",
            },
            "source_priority_used": [],
        },
    }
    refresh_source_ladder_usage_from_questions(job, [])
    status = job["source_ladder"]["source_status"]
    assert status.get("document_library") != "used"
    assert status.get("company_research") != "used"
