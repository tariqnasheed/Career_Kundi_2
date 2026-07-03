"""Tests for Job Intelligence Profile extraction (Iteration 004E-A)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE", "false")

from app.agents.job_search.job_intelligence import build_job_intelligence_profile
from app.agents.job_search.quality.silly_question_guard import is_silly_question
from app.core.config import settings


TITLE_ONLY_JOB = {"title": "Data Analyst"}

RICH_DATA_ANALYST_JOB = {
    "title": "Data Analyst",
    "company_name": "Northline Analytics",
    "description_raw": (
        "Northline Analytics builds subscription analytics products for retail brands.\n\n"
        "Responsibilities:\n"
        "- Build SQL dashboards and KPI definitions for stakeholder reporting\n"
        "- Run daily data quality checks on warehouse tables\n"
        "- Partner with finance on Excel and Power BI reporting\n\n"
        "Requirements:\n"
        "- Strong SQL querying and dashboard creation\n"
        "- Experience with data quality checks and stakeholder communication\n"
        "- Preferred: Python for automation"
    ),
    "responsibilities": [
        "SQL querying and dashboard creation for stakeholder reporting",
        "Daily data quality checks on warehouse tables",
        "KPI definitions and executive reporting",
    ],
    "requirements": [
        "Strong SQL querying and dashboard creation",
        "Experience with data quality checks",
        "Preferred: Python for automation",
    ],
    "extracted_skills": [
        {"skill": "SQL", "importance": "critical"},
        {"skill": "Power BI", "importance": "high"},
    ],
    "company_profile": {
        "summary": "Retail subscription analytics SaaS provider",
        "industry": "Retail analytics",
        "products_services": "Subscription analytics dashboards",
    },
    "location": "Manchester, UK",
}

RICH_ELECTRICAL_JOB = {
    "title": "Electrical Engineer",
    "company_name": "GridForm Projects",
    "description_raw": (
        "You will support LV distribution design, load calculations, cable sizing, site inspections, "
        "and testing/commissioning with strict electrical safety and BS 7671 compliance."
    ),
    "responsibilities": [
        "LV distribution design support and load calculations",
        "Cable sizing and protective device coordination",
        "Site inspections, testing, and commissioning",
    ],
    "requirements": [
        "AutoCAD design experience",
        "Electrical safety and standards compliance",
        "Commissioning and inspection records",
    ],
    "extracted_skills": [{"skill": "AutoCAD", "importance": "critical"}],
    "company_profile": {"summary": "Commercial electrical contractor", "industry": "Construction"},
}

JOB_WITH_URL_ONLY = {
    "title": "Data Analyst",
    "source_url": "https://example.com/jobs/data-analyst",
}


def test_role_title_only_warning():
    profile = build_job_intelligence_profile(TITLE_ONLY_JOB)
    assert profile.completeness_score <= 30
    assert any("only a role title" in w.lower() for w in profile.warnings)


def test_rich_posting_higher_completeness_than_title_only():
    thin = build_job_intelligence_profile(TITLE_ONLY_JOB)
    rich = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    assert rich.completeness_score > thin.completeness_score
    assert rich.completeness_score >= 61


def test_responsibilities_extracted():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    assert len(profile.responsibilities) >= 3
    assert any("sql" in r.lower() for r in profile.responsibilities)


def test_required_skills_extracted():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    assert any("sql" in s.lower() for s in profile.required_skills)


def test_preferred_skills_extracted():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    assert any("python" in s.lower() for s in profile.preferred_skills)


def test_tools_extracted():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    lowered = [t.lower() for t in profile.tools_software]
    assert "sql" in lowered or "power bi" in lowered or "excel" in lowered


def test_company_profile_captured():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    assert profile.company_profile
    assert profile.industry_domain
    assert profile.company_products_services


def test_compliance_clues_captured_for_electrical():
    profile = build_job_intelligence_profile(RICH_ELECTRICAL_JOB)
    blob = " ".join(profile.compliance_safety_ethics).lower()
    assert "safety" in blob or "compliance" in blob or "bs 7671" in blob


def test_job_url_without_extraction_warning():
    profile = build_job_intelligence_profile(JOB_WITH_URL_ONLY)
    assert profile.job_posting_url
    assert any("extraction" in w.lower() for w in profile.warnings)


def test_source_status_transparent():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    assert profile.source_status["user_fields"] == "used"
    assert profile.source_status["web_research"] == "not_configured"
    assert profile.source_status["link_extraction"] in ("not_present", "not_configured")


def test_model_knowledge_disabled_by_default():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    assert profile.source_status["model_knowledge"] == "disabled"
    assert settings.job_search_enable_model_knowledge is False


def test_extracted_items_populated():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    assert len(profile.extracted_items) >= 5
    types = {item.item_type for item in profile.extracted_items}
    assert "responsibility" in types
    assert "required_skill" in types or "tool" in types


@pytest.mark.parametrize(
    "text",
    [
        "Do you like this job?",
        "Are you good at teamwork?",
        "Can you use a computer?",
        "What is your favourite tool?",
    ],
)
def test_silly_questions_detected(text: str):
    assert is_silly_question(text)
