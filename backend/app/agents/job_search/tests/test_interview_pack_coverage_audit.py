"""Tests for interview pack coverage audit (Iteration 004E-A)."""

from __future__ import annotations

import json
import os
import re

import pytest

os.environ.setdefault("JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE", "false")

from app.agents.job_search.job_coverage_audit import (
    audit_pack_coverage,
    build_missing_coverage_questions,
)
from app.agents.job_search.job_intelligence import build_job_intelligence_profile
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import (
    INTERMEDIATE_QUALITY_CHECKS,
    OUTCOME_QUALITY_IMPROVES,
    STABILIZE_MAINTAIN_PIPELINES,
    STRUCTURED_VERIFICATION,
    export_blocked_phrase_count,
)
from app.agents.job_search.quality.silly_question_guard import is_silly_question

TITLE_ONLY_JOB = {"title": "Data Analyst"}

RICH_DATA_ANALYST_JOB = {
    "title": "Data Analyst",
    "company_name": "Northline Analytics",
    "description_raw": (
        "Responsibilities:\n"
        "- Build SQL dashboards and KPI definitions for stakeholder reporting\n"
        "- Run daily data quality checks on warehouse tables\n"
        "- Partner with finance on Excel and Power BI reporting\n"
        "Requirements:\n"
        "- Strong SQL querying and dashboard creation\n"
        "- Experience with data quality checks\n"
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
}

RICH_ELECTRICAL_JOB = {
    "title": "Electrical Engineer",
    "company_name": "GridForm Projects",
    "description_raw": (
        "Support LV distribution design, load calculations, cable sizing, site inspections, "
        "AutoCAD drawings, testing/commissioning, and electrical safety compliance."
    ),
    "responsibilities": [
        "LV distribution design support and load calculations",
        "Cable sizing and protective device coordination",
        "Site inspections, testing, and commissioning",
    ],
    "requirements": ["AutoCAD design experience", "Electrical safety and standards compliance"],
    "extracted_skills": [{"skill": "AutoCAD", "importance": "critical"}],
    "company_profile": {"summary": "Commercial electrical contractor", "industry": "Construction"},
}

RICH_CREATOR_JOB = {
    "title": "Social Media Creator",
    "company_name": "BrightLoop Media",
    "description_raw": (
        "Own the content calendar, short-form video production, audience growth analytics, "
        "brand safety reviews, sponsorship awareness, copyright checks, and community management."
    ),
    "responsibilities": [
        "Plan and publish the weekly content calendar",
        "Produce short-form video and hooks for audience growth",
        "Review analytics and community feedback daily",
        "Apply brand safety and copyright checks before publishing",
    ],
    "requirements": [
        "Short-form video editing",
        "Analytics and audience growth reporting",
        "Brand safety and sponsorship awareness",
    ],
    "extracted_skills": [
        {"skill": "Content Planning", "importance": "critical"},
        {"skill": "Analytics", "importance": "high"},
    ],
    "company_profile": {
        "summary": "Creator-led media studio",
        "products_services": "Short-form video campaigns",
        "industry": "Digital media",
    },
}

_BLOCKED_MARKERS = (
    OUTCOME_QUALITY_IMPROVES,
    STRUCTURED_VERIFICATION,
    INTERMEDIATE_QUALITY_CHECKS,
    STABILIZE_MAINTAIN_PIPELINES,
    "Role Specific",
)


def _exportable(questions: list[dict]) -> list[dict]:
    return [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]


def _generate(job: dict) -> list[dict]:
    skills = [s["skill"] for s in job.get("extracted_skills", []) if isinstance(s, dict)]
    return _exportable(mock_generate_questions(job, focus_areas=skills, difficulty="mid"))


def test_title_only_profile_has_zero_coverage_score():
    profile = build_job_intelligence_profile(TITLE_ONLY_JOB)
    audit = audit_pack_coverage(profile, [{"question_id": "q-1", "question": "Sample Data Analyst question."}])
    assert profile.completeness_score <= 30
    assert len(profile.extracted_items) == 0
    assert audit.total_items == 0
    assert audit.coverage_score == 0
    assert any("no detailed job intelligence items" in w.lower() for w in audit.warnings)


def test_title_only_generation_attaches_coverage_warning():
    job = dict(TITLE_ONLY_JOB)
    _generate(job)
    audit = job.get("coverage_audit") or {}
    assert audit.get("coverage_score") == 0
    assert any("no detailed job intelligence items" in w.lower() for w in audit.get("warnings", []))


def test_rich_profile_higher_completeness_than_title_only():
    thin = build_job_intelligence_profile(TITLE_ONLY_JOB)
    rich = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    assert rich.completeness_score > thin.completeness_score


def test_rich_profile_maintains_high_coverage():
    job = dict(RICH_DATA_ANALYST_JOB)
    _generate(job)
    audit = job.get("coverage_audit") or {}
    assert audit.get("total_items", 0) > 0
    assert audit.get("coverage_score", 0) >= 80


def test_generated_rich_pack_has_zero_generic_phrase_hits():
    job = dict(RICH_DATA_ANALYST_JOB)
    questions = _generate(job)
    from app.services.role_pack_library import build_role_overview
    from app.tools.document_export import build_interview_pack_markdown

    pack_md = build_interview_pack_markdown(
        job_title=job["title"],
        company_name=job.get("company_name"),
        questions=questions,
        role_overview=build_role_overview(job["title"], job),
    )
    assert export_blocked_phrase_count(pack_md) == 0


def test_coverage_audit_detects_uncovered_items_for_sparse_pack():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    sparse = [{"question_id": "q-1", "question": "Tell me about teamwork in general terms only."}]
    audit = audit_pack_coverage(profile, sparse)
    assert audit.covered_items < audit.total_items
    assert audit.missing_items


def test_missing_responsibilities_trigger_added_questions():
    profile = build_job_intelligence_profile(RICH_DATA_ANALYST_JOB)
    seed = [{"question_id": "q-1", "question": "General interview opener without role detail."}]
    added = build_missing_coverage_questions(profile, seed)
    assert added
    blob = " ".join(q["question"].lower() for q in added)
    assert "sql" in blob or "dashboard" in blob or "data quality" in blob


def test_rich_data_analyst_pack_covers_skills_and_tools():
    questions = _generate(RICH_DATA_ANALYST_JOB)
    blob = " ".join(q["question"].lower() for q in questions)
    assert "sql" in blob
    assert job_has_coverage_audit(RICH_DATA_ANALYST_JOB)
    assert "power bi" in blob or "dashboard" in blob or "kpi" in blob


def test_rich_electrical_pack_has_safety_and_tool_questions():
    questions = _generate(RICH_ELECTRICAL_JOB)
    blob = " ".join(q["question"].lower() for q in questions)
    assert "autocad" in blob or "load" in blob or "cable" in blob
    assert "safety" in blob or "compliance" in blob


def test_rich_creator_pack_avoids_silly_questions():
    questions = _generate(RICH_CREATOR_JOB)
    for q in questions:
        assert not is_silly_question(q.get("question", ""))


def test_difficulty_progression_present_for_rich_posting():
    questions = _generate(RICH_DATA_ANALYST_JOB)
    labels = {
        (q.get("generation_stage_meta") or {}).get("progression_label")
        for q in questions
        if (q.get("generation_stage_meta") or {}).get("progression_label")
    }
    difficulties = {q.get("difficulty") for q in questions}
    assert len(labels) >= 2 or len(difficulties) >= 2


def test_no_fake_urls_in_generated_pack():
    questions = _generate(RICH_DATA_ANALYST_JOB)
    parts: list[str] = []
    for q in questions:
        parts.append(q.get("question", "") or "")
        parts.append(q.get("model_answer", "") or "")
        parts.append(json.dumps(q.get("study_sources", {})))
    blob = " ".join(parts)
    assert not re.search(r"https?://", blob)


def test_no_blocked_generic_phrases():
    questions = _generate(RICH_DATA_ANALYST_JOB)
    blob = " ".join(q.get("question", "") + " " + q.get("model_answer", "") for q in questions)
    for marker in _BLOCKED_MARKERS:
        if marker == "Role Specific":
            assert not re.search(r"\bRole\s+Specific\b", blob), f"found {marker!r}"
        else:
            assert marker.lower() not in blob.lower()


def test_answers_under_500_words():
    questions = _generate(RICH_DATA_ANALYST_JOB)
    for q in questions:
        assert len((q.get("model_answer") or "").split()) <= ABSOLUTE_MAX_WORDS


def test_title_only_generation_still_allowed_with_warning():
    profile = build_job_intelligence_profile(TITLE_ONLY_JOB)
    questions = _generate(TITLE_ONLY_JOB)
    assert profile.warnings
    assert questions


def test_coverage_audit_attached_to_job_snapshot():
    job = dict(RICH_DATA_ANALYST_JOB)
    _generate(job)
    assert job.get("coverage_audit")
    assert job["coverage_audit"]["coverage_score"] >= 0


def job_has_coverage_audit(job: dict) -> bool:
    snapshot = dict(job)
    _generate(snapshot)
    return bool(snapshot.get("coverage_audit"))


def test_added_coverage_questions_are_item_specific():
    profile = build_job_intelligence_profile(RICH_ELECTRICAL_JOB)
    added = build_missing_coverage_questions(profile, [])
    assert added
    assert all(len(q["question"]) > 40 for q in added)
