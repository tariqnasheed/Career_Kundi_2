"""Question-specific study material source-awareness tests (004E-E)."""

from __future__ import annotations

from app.agents.job_search.knowledge.question_study_material import finalize_question_study_module
from app.agents.job_search.mock_data import mock_generate_questions


def test_finalize_links_source_ladder_metadata() -> None:
    job = {
        "title": "Data Analyst",
        "responsibilities": ["SQL dashboard creation"],
        "extracted_skills": [{"skill": "SQL"}],
        "source_ladder": {
            "source_status": {
                "user_fields": "used",
                "link_extraction": "not_present",
                "company_research": "not_configured",
                "model_knowledge": "disabled",
                "document_library": "not_configured",
                "local_fallback": "used",
            }
        },
    }
    question = {
        "question_id": "DA-SQL-001",
        "question": "How would you validate SQL dashboard outputs before stakeholder review?",
        "model_answer": "I would reconcile row counts, spot-check KPI definitions, and document assumptions.",
        "skill_tag": "SQL",
        "question_source_items": ["SQL"],
        "question_source_types": ["user_field"],
        "source_priority_used": ["user_field", "local_fallback"],
        "source_status": job["source_ladder"]["source_status"],
        "study_material": {
            "overview": "SQL validation for dashboard delivery.",
            "beginner_explanation": "Start with source tables and null checks for SQL outputs.",
            "intermediate_explanation": "Move to join logic, filter validation, and KPI definition checks.",
            "advanced_explanation": "Discuss metric governance and performance trade-offs for SQL pipelines.",
            "step_by_step_breakdown": ["Define KPI", "Query data", "Validate counts", "Review with stakeholder"],
            "common_mistakes": ["Sharing numbers without reconciliation"],
        },
        "study_sources": {"used_source_types": ["local_fallback"], "sources": []},
    }
    study = finalize_question_study_module(question, job)
    assert study["source_items_used"] == ["SQL"]
    assert "user_field" in study["source_types_used"]
    assert study["source_status"]["user_fields"] == "used"
    assert study["answer_summary"]
    assert "SQL" in study["what_this_question_tests"]


def test_rich_ladder_job_modules_are_source_aware() -> None:
    from app.agents.job_search.company_research import extract_company_from_html, merge_company_research_into_job_snapshot
    from app.agents.job_search.job_posting_extractor import extract_job_posting_from_html, merge_extraction_into_job_snapshot

    html = '<html><script type="application/ld+json">{"@type":"JobPosting","title":"Data Analyst","tools":["Power BI"]}</script></html>'
    org = '<html><script type="application/ld+json">{"@type":"Corporation","makesOffer":[{"name":"KPI dashboards"}]}</script></html>'
    extraction = extract_job_posting_from_html(html, "https://example.com/job")
    research = extract_company_from_html(org, "https://example.com/about")
    job = merge_company_research_into_job_snapshot(
        merge_extraction_into_job_snapshot(
            {"title": "Data Analyst", "company_name": "Acme", "extracted_skills": [{"skill": "SQL"}]},
            extraction,
        ),
        research,
    )
    questions = [
        q for q in mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
        if not q.get("export_blocked") and q.get("model_answer")
    ]
    aware = [
        q for q in questions
        if (q.get("study_material") or {}).get("source_items_used")
        or (q.get("study_material") or {}).get("source_types_used")
    ]
    assert len(aware) >= len(questions) // 2
