from __future__ import annotations

import re

from app.agents.job_search.knowledge.study_synthesis import contains_blocked_generic_phrase
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import (
    INTERMEDIATE_QUALITY_CHECKS,
    OUTCOME_QUALITY_IMPROVES,
    STABILIZE_MAINTAIN_PIPELINES,
    STRUCTURED_VERIFICATION,
)
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

ROLE_SNAPSHOTS: list[dict] = [
    {
        "slug": "data_analyst",
        "title": "Data Analyst",
        "primary_skill": "SQL",
        "responsibilities": [
            "SQL querying and dashboard creation for stakeholder reporting",
            "Data cleaning, data quality checks, and KPI/metrics reporting",
        ],
        "requirements": ["SQL querying", "dashboard creation", "data quality checks", "KPI/metrics reporting"],
        "extracted_skills": ["SQL", "Data Quality", "Dashboarding", "Excel"],
        "domain_markers": ("sql", "dashboard", "kpi", "data quality", "joins", "null", "query"),
    },
    {
        "slug": "electrical_engineer",
        "title": "Electrical Engineer",
        "primary_skill": "Electrical Installation",
        "responsibilities": [
            "LV distribution design support and load calculations",
            "Cable sizing, testing, commissioning, and standards compliance",
        ],
        "requirements": ["load calculations", "cable sizing", "commissioning", "electrical safety"],
        "extracted_skills": ["Electrical Installation", "Load Calculations", "Cable Sizing", "Commissioning"],
        "domain_markers": ("load calculation", "cable sizing", "commissioning", "safety", "compliance", "protective device"),
    },
    {
        "slug": "clinical_pharmacist",
        "title": "Clinical Pharmacist",
        "primary_skill": "Pharmacology",
        "responsibilities": [
            "Medication review, prescribing safety, and patient counselling",
            "Clinical documentation, escalation, and governance",
        ],
        "requirements": ["medication review", "prescribing safety", "patient counselling", "escalation"],
        "extracted_skills": ["Pharmacology", "Medication Review", "Patient Counselling", "Clinical Governance"],
        "domain_markers": (
            "medication review", "contraindication", "interaction", "allergy", "dose", "counselling", "governance", "escalation"
        ),
    },
    {
        "slug": "barista",
        "title": "Barista",
        "primary_skill": "Coffee Preparation",
        "responsibilities": [
            "Espresso preparation, milk steaming, and drink consistency",
            "Hygiene, allergen controls, customer service, and stock handling",
        ],
        "requirements": ["espresso preparation", "milk steaming", "hygiene", "allergens", "customer service"],
        "extracted_skills": ["Coffee Preparation", "HACCP", "Customer Service", "Stock Control"],
        "domain_markers": ("espresso", "milk texture", "allergen", "hygiene", "queue", "drink consistency"),
    },
    {
        "slug": "devops_engineer",
        "title": "DevOps Engineer",
        "primary_skill": "AWS",
        "responsibilities": [
            "AWS infrastructure automation with CI/CD, Docker, and Kubernetes",
            "Monitoring, incident response, and rollback/recovery",
        ],
        "requirements": ["AWS", "CI/CD", "Docker", "Kubernetes", "monitoring", "incident response"],
        "extracted_skills": ["AWS", "CI/CD", "Docker", "Kubernetes", "Monitoring"],
        "domain_markers": (
            "deployment health", "rollback", "monitoring", "pipeline", "infrastructure", "incident response"
        ),
    },
]

_BLOCKED_MARKERS = (
    OUTCOME_QUALITY_IMPROVES,
    STRUCTURED_VERIFICATION,
    INTERMEDIATE_QUALITY_CHECKS,
    STABILIZE_MAINTAIN_PIPELINES,
)

_ROLE_SPECIFIC_LABEL = "Role " + "Specific"
_ROLE_SPECIFIC_LINE = re.compile(r"\*\*Related skills:\*\*.*\b" + re.escape(_ROLE_SPECIFIC_LABEL) + r"\b", re.I)
_ROLE_SPECIFIC_BODY = re.compile(r"\b" + re.escape(_ROLE_SPECIFIC_LABEL) + r"\b")


def _job(snapshot: dict) -> dict:
    return {
        "title": snapshot["title"],
        "responsibilities": snapshot["responsibilities"],
        "requirements": snapshot["requirements"],
        "extracted_skills": [{"skill": s} for s in snapshot["extracted_skills"]],
    }


def _document_library_used(question: dict) -> bool:
    for source in (question.get("study_sources") or {}).get("sources") or []:
        if source.get("source_type") == "document_library" and source.get("status") == "used":
            return True
    return False


def test_no_user_facing_role_specific_in_related_skills() -> None:
    for snapshot in ROLE_SNAPSHOTS:
        job = _job(snapshot)
        focus = [snapshot["primary_skill"]] + [
            s for s in snapshot["extracted_skills"] if s != snapshot["primary_skill"]
        ]
        questions = mock_generate_questions(job, focus_areas=focus, difficulty="mid")
        pack_md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
            role_overview=build_role_overview(snapshot["title"], job),
        )
        assert not _ROLE_SPECIFIC_LINE.search(pack_md), (
            f"{snapshot['title']}: exported pack still contains internal category label in related skills"
        )
        assert not _ROLE_SPECIFIC_BODY.search(pack_md), (
            f"{snapshot['title']}: exported pack still contains internal category label in study/answer text"
        )
        for question in questions:
            if question.get("export_blocked"):
                continue
            for skill in question.get("related_skills") or []:
                assert skill.lower().replace("_", " ") not in {"role specific", "role_specific"}, (
                    f"{snapshot['title']}: related skill label still internal: {skill!r}"
                )


def test_study_material_and_source_status_present() -> None:
    for snapshot in ROLE_SNAPSHOTS:
        job = _job(snapshot)
        questions = mock_generate_questions(
            job,
            focus_areas=[snapshot["primary_skill"]],
            difficulty="mid",
        )
        exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
        assert exportable, f"{snapshot['title']}: no exportable questions"
        assert all(q.get("study_material") for q in exportable)
        assert all(q.get("study_sources") for q in exportable)


def test_saved_material_insight_when_document_library_used() -> None:
    for snapshot in ROLE_SNAPSHOTS:
        job = _job(snapshot)
        questions = mock_generate_questions(
            job,
            focus_areas=[snapshot["primary_skill"]],
            difficulty="mid",
        )
        for question in questions:
            if question.get("export_blocked") or not _document_library_used(question):
                continue
            study = question.get("study_material") or {}
            assert study.get("saved_material_insight"), (
                f"{snapshot['title']}: document library used but saved_material_insight missing for "
                f'"{(question.get("question") or "")[:80]}"'
            )


def test_blocked_generic_phrases_absent_from_exports() -> None:
    for snapshot in ROLE_SNAPSHOTS:
        job = _job(snapshot)
        questions = mock_generate_questions(
            job,
            focus_areas=[snapshot["primary_skill"]],
            difficulty="mid",
        )
        pack_md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
            role_overview=build_role_overview(snapshot["title"], job),
        )
        for marker in _BLOCKED_MARKERS:
            assert marker.lower() not in pack_md.lower(), (
                f"{snapshot['title']}: blocked phrase {marker!r} found in export"
            )
        for question in questions:
            if question.get("export_blocked"):
                continue
            blob = " ".join(
                [
                    question.get("model_answer") or "",
                    question.get("answer_explanation") or "",
                    str(question.get("study_material") or {}),
                ]
            )
            assert not contains_blocked_generic_phrase(blob), (
                f"{snapshot['title']}: blocked generic phrase in question payload"
            )


def test_role_family_domain_phrasing_in_exports() -> None:
    for snapshot in ROLE_SNAPSHOTS:
        job = _job(snapshot)
        questions = mock_generate_questions(
            job,
            focus_areas=[snapshot["primary_skill"]],
            difficulty="mid",
        )
        pack_md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
            role_overview=build_role_overview(snapshot["title"], job),
        ).lower()
        assert any(marker in pack_md for marker in snapshot["domain_markers"]), (
            f"{snapshot['title']}: export missing expected domain phrasing from {snapshot['domain_markers']}"
        )


def test_answers_under_500_words() -> None:
    for snapshot in ROLE_SNAPSHOTS:
        job = _job(snapshot)
        questions = mock_generate_questions(
            job,
            focus_areas=[snapshot["primary_skill"]],
            difficulty="mid",
        )
        for question in questions:
            if question.get("export_blocked"):
                continue
            answer = question.get("model_answer") or ""
            word_count = len(answer.split())
            assert word_count <= ABSOLUTE_MAX_WORDS, (
                f"{snapshot['title']}: answer over {ABSOLUTE_MAX_WORDS} words ({word_count})"
            )


def test_learning_path_fields_present() -> None:
    for snapshot in ROLE_SNAPSHOTS:
        job = _job(snapshot)
        questions = mock_generate_questions(
            job,
            focus_areas=[snapshot["primary_skill"]],
            difficulty="mid",
        )
        for question in questions:
            if question.get("export_blocked"):
                continue
            study = question.get("study_material") or {}
            for key in ("beginner_explanation", "intermediate_explanation", "advanced_explanation"):
                assert study.get(key), f"{snapshot['title']}: missing {key}"
            assert study.get("technical_skills_covered"), f"{snapshot['title']}: missing technical_skills_covered"


def test_saved_material_insight_sentence_boundaries() -> None:
    from app.agents.job_search.knowledge.study_synthesis import build_saved_material_insight

    insight = build_saved_material_insight(
        role="Barista",
        matched_skills=["Coffee Preparation", "Customer Service"],
        supporting_focus=[
            "espresso consistency",
            "grind and dose control",
            "queue management",
        ],
        role_family="hospitality",
        skill_tag="Coffee Preparation",
    )
    assert "flow Pay" not in insight
    assert ". before practising" not in insight
    assert "  " not in insight
    assert "Coffee Preparation and Customer Service" in insight
    assert insight.endswith(".")
    assert "before practising your answer." in insight
    assert "Pay special attention to" in insight
    assert re.search(r"queue flow before practising", insight)

    barista_job = next(s for s in ROLE_SNAPSHOTS if s["slug"] == "barista")
    job = _job(barista_job)
    questions = mock_generate_questions(
        job,
        focus_areas=[barista_job["primary_skill"]],
        difficulty="mid",
    )
    insights = [
        (q.get("study_material") or {}).get("saved_material_insight", "")
        for q in questions
        if (q.get("study_material") or {}).get("saved_material_insight")
    ]
    assert insights, "expected at least one saved material insight for Barista"
    for text in insights:
        assert "flow Pay" not in text
        assert ". before practising" not in text
        assert "  " not in text
        assert not re.search(r"[.!?]{2,}", text)
