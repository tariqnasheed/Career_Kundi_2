"""Full coverage audit with source-derived items (Iteration 004E-D)."""

from __future__ import annotations

from app.agents.job_search.job_coverage_audit import audit_pack_coverage, build_audit_items_for_profile
from app.agents.job_search.job_intelligence import build_job_intelligence_profile
from app.agents.job_search.knowledge.source_ladder import apply_source_ladder_to_job
from app.agents.job_search.mock_data import mock_generate_questions

FULL_JOB = {
    "title": "Data Analyst",
    "company_name": "Northline Analytics",
    "description_raw": "Build dashboards and KPI reporting.",
    "responsibilities": ["SQL dashboard creation", "Daily data quality checks"],
    "requirements": ["Strong SQL", "Excel", "Preferred: Python"],
    "extracted_skills": [{"skill": "SQL"}, {"skill": "Python"}, {"skill": "Excel"}],
    "job_posting_extraction": {
        "extraction_confidence": "high",
        "responsibilities": ["Stakeholder reporting cadence"],
        "tools": ["Power BI"],
    },
    "company_research": {
        "research_confidence": "high",
        "products_services": ["KPI dashboards"],
        "industries": ["Retail analytics"],
        "source_status": {"company_page": "used"},
    },
}


def test_coverage_audit_includes_source_types() -> None:
    job = dict(FULL_JOB)
    apply_source_ladder_to_job(job)
    profile = build_job_intelligence_profile(job)
    items = build_audit_items_for_profile(profile)
    sources = {i["source_type"] for i in items}
    assert "user_field" in sources
    assert "job_posting_extraction" in sources
    assert "company_research" in sources


def test_missing_items_generate_coverage_questions() -> None:
    job = dict(FULL_JOB)
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    audit = job.get("coverage_audit") or {}
    assert audit.get("total_items", 0) > 0
    assert isinstance(audit.get("audit_items"), list)
    assert len(audit["audit_items"]) > 0


def test_audit_items_have_ids_and_labels() -> None:
    job = dict(FULL_JOB)
    mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    audit = job["coverage_audit"]
    for row in audit.get("audit_items", []):
        assert row.get("item_id")
        assert row.get("source_label")
        assert row.get("action") in ("covered", "add_question")


def test_pack_coverage_score_reasonable_for_rich_job() -> None:
    job = dict(FULL_JOB)
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    profile = build_job_intelligence_profile(job)
    audit = audit_pack_coverage(profile, questions)
    assert audit.coverage_score >= 40
