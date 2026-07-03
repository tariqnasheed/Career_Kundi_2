"""004E-E interview-pack study material finalization tests."""

from __future__ import annotations

import re

import pytest

from app.agents.job_search.company_research import (
    extract_company_from_html,
    merge_company_research_into_job_snapshot,
)
from app.agents.job_search.job_posting_extractor import (
    extract_job_posting_from_html,
    merge_extraction_into_job_snapshot,
)
from app.agents.job_search.knowledge.question_study_material import (
    count_empty_study_sections,
    study_module_fingerprint,
)
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.core.config import settings
from app.tools.document_export import build_interview_pack_markdown

JOB_HTML = """
<html><head><script type="application/ld+json">
{"@type":"JobPosting","title":"Data Analyst","description":"Build dashboards.",
 "responsibilities":["SQL dashboard creation","Daily data quality checks"],
 "tools":["Power BI","SQL"],"skills":["SQL","Python"]}
</script></head></html>
"""

ORG_HTML = """
<html><head><script type="application/ld+json">
{"@type":"Corporation","legalName":"Northline Analytics Ltd",
 "makesOffer":[{"name":"KPI dashboards"}],"knowsAbout":["Retail analytics"]}
</script></head></html>
"""

_ROLE_SPECIFIC_RE = re.compile(r"\bRole Specific\b")
_URL_RE = re.compile(r"https?://", re.I)


def _exportable(questions: list[dict]) -> list[dict]:
    return [q for q in questions if q.get("model_answer") and not q.get("export_blocked")]


def _full_ladder_job() -> dict:
    extraction = extract_job_posting_from_html(JOB_HTML, "https://northline.example/jobs/analyst")
    research = extract_company_from_html(ORG_HTML, "https://northline.example/about")
    job = merge_extraction_into_job_snapshot(
        {
            "title": "Data Analyst",
            "company_name": "Northline Analytics",
            "description_raw": "Build dashboards and KPI reporting.",
            "responsibilities": ["SQL dashboard creation"],
            "requirements": ["Strong SQL"],
            "extracted_skills": [{"skill": "SQL"}, {"skill": "Excel"}],
        },
        extraction,
    )
    return merge_company_research_into_job_snapshot(job, research)


def test_every_exportable_question_has_study_module() -> None:
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    assert questions
    for q in questions:
        study = q.get("study_material") or {}
        assert study, f"Missing study_material for {q.get('question_id')}"
        assert study.get("question_id") == q.get("question_id")
        assert study.get("question_text") == q.get("question")


def test_study_module_tied_to_question_text() -> None:
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    for q in questions:
        study = q.get("study_material") or {}
        qtext = (q.get("question") or "").lower()
        blob = " ".join(
            str(study.get(k, ""))
            for k in ("what_this_question_tests", "core_idea", "interview_application")
        ).lower()
        token = next((t for t in qtext.split() if len(t) > 5), None)
        skill = (q.get("skill_tag") or "").lower()
        assert skill in blob or (token and token in blob) or study.get("source_items_used"), (
            f"Study module not tied to question: {q.get('question_id')}"
        )


def test_responsibility_question_has_responsibility_study() -> None:
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    resp_q = [
        q for q in questions
        if "dashboard" in (q.get("question") or "").lower() and "posting" in (q.get("question") or "").lower()
    ]
    assert resp_q
    study = resp_q[0].get("study_material") or {}
    blob = " ".join(str(v) for v in study.values() if isinstance(v, str)).lower()
    assert "dashboard" in blob or "sql" in blob


def test_tool_question_has_tool_study() -> None:
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    tool_q = [
        q for q in questions
        if "posting mentions" in (q.get("question") or "").lower()
        or "job_posting_extraction" in (q.get("question_source_types") or [])
    ]
    assert tool_q
    study = tool_q[0].get("study_material") or {}
    assert study.get("source_items_used") or "power bi" in (study.get("what_this_question_tests") or "").lower()


def test_company_context_study_uses_captured_metadata() -> None:
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    company_q = [
        q for q in questions
        if "KPI dashboards" in (q.get("question") or "") or "company_research" in (q.get("question_source_types") or [])
    ]
    assert company_q
    study = company_q[0].get("study_material") or {}
    assert study.get("web_or_company_source_insight") or study.get("source_types_used")


def test_document_library_insight_when_used() -> None:
    job = {
        "title": "Barista",
        "company_name": "Harbour Cafe",
        "description_raw": "Espresso and HACCP hygiene.",
        "responsibilities": ["Espresso preparation", "HACCP hygiene controls"],
        "requirements": ["Coffee preparation", "HACCP"],
        "extracted_skills": [{"skill": "Coffee Preparation"}, {"skill": "HACCP"}],
    }
    questions = _exportable(
        mock_generate_questions(job, focus_areas=["Coffee Preparation", "HACCP"], difficulty="mid")
    )
    doc_insights = [
        q.get("study_material", {}).get("document_library_insight")
        for q in questions
        if (q.get("study_material") or {}).get("document_library_insight")
    ]
    assert doc_insights, "Expected at least one document-library insight"


def test_model_knowledge_disabled_by_default() -> None:
    assert settings.job_search_enable_model_knowledge is False
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    for q in questions:
        study = q.get("study_material") or {}
        status = study.get("source_status") or {}
        assert status.get("model_knowledge") == "disabled"
        insight = study.get("model_insight") or ""
        assert "disabled" in insight.lower()


def test_title_only_fallback_is_question_specific() -> None:
    job = {"title": "Mystery Role"}
    questions = _exportable(mock_generate_questions(job, focus_areas=[], difficulty="auto"))
    assert questions
    for q in questions:
        study = q.get("study_material") or {}
        assert study.get("what_this_question_tests")
        assert count_empty_study_sections(study) == 0


def test_no_internal_label_leaks_or_blocked_phrases() -> None:
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    blob = " ".join(
        str(v)
        for q in questions
        for v in (q.get("study_material") or {}).values()
        if isinstance(v, str)
    )
    assert not _ROLE_SPECIFIC_RE.search(blob)
    assert export_blocked_phrase_count(blob) == 0
    assert not _URL_RE.search(blob)


def test_no_empty_study_sections() -> None:
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    for q in questions:
        study = q.get("study_material") or {}
        assert count_empty_study_sections(study) == 0, q.get("question_id")


def test_no_duplicate_identical_modules() -> None:
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    fingerprints = [
        study_module_fingerprint(q.get("study_material") or {}, q.get("question") or "")
        for q in questions
    ]
    assert len(fingerprints) == len(set(fingerprints))


def test_export_markdown_includes_per_question_study() -> None:
    job = _full_ladder_job()
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    md = build_interview_pack_markdown(
        job_title="Data Analyst",
        company_name="Northline Analytics",
        questions=questions,
    )
    assert md.count("### Study material") >= len(questions)
