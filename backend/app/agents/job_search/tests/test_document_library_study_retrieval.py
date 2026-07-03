"""Tests for document-library study material retrieval (Iteration 004B)."""

from __future__ import annotations

import json
import re

import pytest

from app.agents.job_search.knowledge.coverage_planner import _hr_motivation_question
from app.agents.job_search.knowledge.document_library_retriever import (
    _build_supporting_focus,
    _extract_snippets,
    _format_matched_skill_label,
    _is_core_terminology_snippet,
    _is_generic_snippet,
    _is_role_specific_placeholder_snippet,
    find_role_study_documents,
    match_document_material_to_question,
    retrieve_study_material_snippets,
)
from app.agents.job_search.knowledge.study_sources import attach_study_source_metadata
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import (
    APPLY_DOC_PROCEDURES,
    DOCUMENTED_CONTROL_POINTS,
    INTERMEDIATE_QUALITY_CHECKS,
    OUTCOME_QUALITY_IMPROVES,
    REDUCED_REWORK_STRUCTURED,
    STABILIZE_MAINTAIN_PIPELINES,
    STABILIZE_UNDER_CONSTRAINTS,
    STRUCTURED_VERIFICATION,
)
from app.tools.document_export import build_interview_pack_markdown

_ROLE_SPECIFIC_LABEL = "Role " + "Specific"

ROLE_SNAPSHOTS = [
    {
        "title": "Data Analyst",
        "primary_skill": "SQL",
        "responsibilities": [
            "SQL querying and dashboard creation for stakeholder reporting",
            "Data cleaning, data quality checks, and KPI/metrics reporting",
            "Query performance tuning and validation of analytical outputs",
            "Excel or BI tool delivery for recurring business reviews",
        ],
        "requirements": [
            "SQL querying", "dashboard creation", "stakeholder reporting", "data cleaning",
            "data quality checks", "query performance", "KPI/metrics reporting", "Excel or BI tools",
        ],
        "extracted_skills": ["SQL", "Data Quality", "Dashboarding", "Excel"],
    },
    {
        "title": "Electrical Engineer",
        "primary_skill": "Electrical Installation",
        "responsibilities": [
            "LV distribution design support and load calculations",
            "Cable sizing, lighting/power layout review, and site coordination",
            "Testing, commissioning, electrical safety, and standards compliance",
        ],
        "requirements": [
            "LV distribution", "load calculations", "cable sizing", "lighting or power layout review",
            "testing and commissioning", "electrical safety", "standards/compliance", "site coordination",
        ],
        "extracted_skills": ["Electrical Installation", "Load Calculations", "Cable Sizing", "Commissioning"],
    },
    {
        "title": "Clinical Pharmacist",
        "primary_skill": "Pharmacology",
        "responsibilities": [
            "Medication review, prescribing safety, and patient counselling",
            "Clinical documentation, escalation, and governance in multidisciplinary teams",
            "Risk management for high-risk medicines and care transitions",
        ],
        "requirements": [
            "medication review", "prescribing safety", "patient counselling", "clinical documentation",
            "escalation", "governance", "multidisciplinary working", "risk management",
        ],
        "extracted_skills": ["Pharmacology", "Medication Review", "Patient Counselling", "Clinical Governance"],
    },
    {
        "title": "Barista",
        "primary_skill": "Coffee Preparation",
        "responsibilities": [
            "Espresso preparation, milk steaming, and drink consistency during rush hours",
            "Hygiene, allergen controls, customer service, and stock handling",
        ],
        "requirements": [
            "espresso preparation", "milk steaming", "drink consistency", "hygiene",
            "allergens", "customer service", "speed during rush hours", "stock handling",
        ],
        "extracted_skills": ["Coffee Preparation", "HACCP", "Customer Service", "Stock Control"],
    },
    {
        "title": "DevOps Engineer",
        "primary_skill": "AWS",
        "responsibilities": [
            "AWS infrastructure automation with CI/CD, Docker, and Kubernetes",
            "Monitoring, incident response, security controls, and rollback/recovery",
        ],
        "requirements": [
            "AWS", "CI/CD", "Docker", "Kubernetes", "monitoring",
            "incident response", "security", "rollback/recovery", "infrastructure automation",
        ],
        "extracted_skills": ["AWS", "CI/CD", "Docker", "Kubernetes", "Monitoring"],
    },
]

_FAKE_URL_RE = re.compile(r"https?://[^\s\])\"']+")


def _job(snapshot: dict) -> dict:
    return {
        "title": snapshot["title"],
        "responsibilities": snapshot["responsibilities"],
        "requirements": snapshot["requirements"],
        "extracted_skills": [{"skill": s} for s in snapshot["extracted_skills"]],
    }


def _generate(snapshot: dict) -> list[dict]:
    job = _job(snapshot)
    focus = [snapshot["primary_skill"]] + [
        s for s in snapshot["extracted_skills"] if s != snapshot["primary_skill"]
    ]
    return mock_generate_questions(job, focus_areas=focus, difficulty="mid")


def _exportable(questions: list[dict]) -> list[dict]:
    return [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]


def _document_source(question: dict) -> dict:
    for source in (question.get("study_sources") or {}).get("sources") or []:
        if source.get("source_type") == "document_library":
            return source
    return {}


def test_find_role_study_documents_for_saved_devops_pack() -> None:
    docs = find_role_study_documents("DevOps Engineer")
    assert docs is not None
    assert docs.get("structured_path")
    assert docs.get("questions")
    assert "devops_engineer" in (docs.get("role_slug") or "")


def test_find_role_study_documents_missing_for_data_analyst() -> None:
    assert find_role_study_documents("Data Analyst") is None


def test_matching_uses_skill_overlap_not_random_role() -> None:
    docs = find_role_study_documents("DevOps Engineer")
    assert docs
    job = _job(next(s for s in ROLE_SNAPSHOTS if s["title"] == "DevOps Engineer"))
    question = {
        "category": "technical",
        "skill_tag": "Kubernetes",
        "related_skills": ["AWS", "Docker"],
        "question": "How would you operate Kubernetes deployments with CI/CD guardrails?",
    }
    matched, score, skills, evidence = match_document_material_to_question(
        question,
        docs["questions"],
        role_overview=docs.get("role_overview"),
        job=job,
    )
    assert matched is not None
    assert evidence is not None
    assert score >= 4.0
    assert skills
    assert "kubernetes" in {s.lower() for s in skills} or "aws" in {s.lower() for s in skills}


def test_weak_match_not_marked_used() -> None:
    job = {"title": "DevOps Engineer", "extracted_skills": [{"skill": "AWS"}]}
    question = {
        "category": "hr",
        "skill_tag": "Motivation",
        "related_skills": [],
        "question": "Why do you want this role and what motivates you personally?",
    }
    result = retrieve_study_material_snippets(question, job)
    assert result.status == "available_not_used"
    assert "HR/behavioral" in result.note


def test_hr_motivation_not_used_because_role_pack_exists() -> None:
    job = _job(next(s for s in ROLE_SNAPSHOTS if s["title"] == "Electrical Engineer"))
    question = {
        "category": "hr",
        "skill_tag": "Motivation",
        "related_skills": [],
        "question": _hr_motivation_question(job),
    }
    result = retrieve_study_material_snippets(question, job)
    assert result.status == "available_not_used"
    assert result.pack_exists
    assert "HR/behavioral" in result.note


def test_technical_skill_question_can_mark_document_library_used() -> None:
    job = _job(next(s for s in ROLE_SNAPSHOTS if s["title"] == "Clinical Pharmacist"))
    question = {
        "category": "technical",
        "skill_tag": "Medication Review",
        "related_skills": ["Pharmacology", "Patient Counselling"],
        "question": "How do you conduct a medication review and check prescribing safety?",
    }
    result = retrieve_study_material_snippets(question, job)
    assert result.status == "used"
    assert result.snippets
    assert result.supporting_focus
    assert all(len(s) >= 80 for s in result.snippets)


def test_heading_only_and_short_snippets_filtered() -> None:
    study = {
        "overview": "Circuit Design",
        "key_concepts": ["Circuit Design", "Cable Sizing"],
        "principles": [
            "Outcome quality improves when assumptions are explicit and testable.",
            "Traceability prevents repeated failures in handoffs.",
        ],
        "step_by_step_breakdown": [
            "Validate cable sizing against load calculations, protective-device ratings, and installation standards before energising the circuit.",
            "Record test results and commissioning evidence for traceability during handover.",
        ],
    }
    snippets = _extract_snippets(study)
    assert snippets
    assert all(len(s) >= 80 for s in snippets)
    assert all("Circuit Design" != s for s in snippets)
    assert not any("Outcome quality improves" in s for s in snippets)


def test_generic_process_snippets_filtered() -> None:
    assert _is_generic_snippet(
        "Outcome quality improves when assumptions are explicit and testable."
    )
    assert _is_generic_snippet("Traceability prevents repeated failures in handoffs.")
    assert _is_generic_snippet("AWS")


def test_core_terminology_alone_does_not_mark_document_library_used() -> None:
    job = _job(next(s for s in ROLE_SNAPSHOTS if s["title"] == "Electrical Engineer"))
    question = {
        "category": "technical",
        "skill_tag": "Core Terminology",
        "related_skills": [],
        "question": "Which professional vocabulary separates a competent vs weak Electrical Engineer practitioner?",
    }
    result = retrieve_study_material_snippets(question, job)
    assert result.status == "available_not_used"
    assert "generic core-terminology overlap" in result.note


def test_core_terminology_snippets_filtered() -> None:
    generic = (
        "Core terminology for Core Terminology — precise definitions required "
        "for Electrical Engineer interviews."
    )
    assert _is_core_terminology_snippet(generic)
    assert _is_generic_snippet(generic)
    study = {
        "overview": generic,
        "practical_example": (
            "In DevOps Engineer, I applied AWS to "
            + STABILIZE_MAINTAIN_PIPELINES
            + " under constraints, "
            + DOCUMENTED_CONTROL_POINTS
            + ", and "
            + REDUCED_REWORK_STRUCTURED
            + "."
        ),
    }
    snippets = _extract_snippets(study, matched_skills=["aws", "docker"])
    assert not any("Core terminology for Core Terminology" in s for s in snippets)
    assert not any(STRUCTURED_VERIFICATION in s.lower() for s in snippets)


def test_role_specific_snippets_filtered() -> None:
    generic_snippets = (
        "Apply " + _ROLE_SPECIFIC_LABEL + " using " + APPLY_DOC_PROCEDURES.replace("apply using ", "") + ".",
        "In DevOps Engineer, I applied " + _ROLE_SPECIFIC_LABEL + " to "
        + STABILIZE_MAINTAIN_PIPELINES
        + " under constraints, "
        + DOCUMENTED_CONTROL_POINTS
        + ", and "
        + REDUCED_REWORK_STRUCTURED
        + ".",
    )
    for text in generic_snippets:
        assert _is_role_specific_placeholder_snippet(text)
        assert _is_generic_snippet(text)
    study = {
        "practical_example": generic_snippets[1],
        "step_by_step_breakdown": [
            "Configure Kubernetes rolling updates with readiness probes before shifting production traffic.",
        ],
    }
    snippets = _extract_snippets(study, matched_skills=["kubernetes", "aws"])
    assert snippets
    assert not any(_ROLE_SPECIFIC_LABEL in s for s in snippets)
    assert not any(STRUCTURED_VERIFICATION in s.lower() for s in snippets)


def test_skill_labels_render_with_correct_casing() -> None:
    assert _format_matched_skill_label("aws") == "AWS"
    assert _format_matched_skill_label("ci/cd") == "CI/CD"
    assert _format_matched_skill_label("sql") == "SQL"
    assert _format_matched_skill_label("haccp") == "HACCP"
    job = _job(next(s for s in ROLE_SNAPSHOTS if s["title"] == "DevOps Engineer"))
    question = {
        "category": "technical",
        "skill_tag": "AWS",
        "related_skills": ["Docker", "Kubernetes", "CI/CD"],
        "question": "Explain how AWS deployment pipelines stay reliable under production constraints.",
    }
    result = retrieve_study_material_snippets(question, job)
    if result.status == "used":
        labels = set(result.matched_skills)
        assert "AWS" in labels or "Docker" in labels or "Kubernetes" in labels or "CI/CD" in labels
        assert "Aws" not in labels
        assert "Ci/Cd" not in labels


def test_exported_support_sections_exclude_role_specific_placeholders() -> None:
    forbidden = (
        "Apply " + _ROLE_SPECIFIC_LABEL,
        "applied " + _ROLE_SPECIFIC_LABEL,
        INTERMEDIATE_QUALITY_CHECKS,
        STRUCTURED_VERIFICATION,
        "Core terminology for Core Terminology",
    )
    for snapshot in ROLE_SNAPSHOTS:
        md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=_exportable(_generate(snapshot)),
        )
        for block in re.findall(
            r"### Document-library support\s*\n(.*?)(?=\n### |\n---|\Z)",
            md,
            flags=re.S,
        ):
            for phrase in forbidden:
                assert phrase not in block, f"{phrase!r} in {snapshot['title']} support block"
            assert "Matched skills: Aws" not in block
            assert "Matched skills: Ci/Cd" not in block


def test_substantive_technical_match_still_marks_used() -> None:
    job = _job(next(s for s in ROLE_SNAPSHOTS if s["title"] == "Clinical Pharmacist"))
    question = {
        "category": "technical",
        "skill_tag": "Medication Review",
        "related_skills": ["Pharmacology", "Patient Counselling"],
        "question": "How do you conduct a medication review and check prescribing safety?",
    }
    result = retrieve_study_material_snippets(question, job)
    assert result.status == "used"
    assert result.matched_skills
    assert "core terminology" not in {s.lower() for s in result.matched_skills}
    assert "Aws" not in result.matched_skills
    assert "Ci/Cd" not in result.matched_skills
    if result.snippets:
        joined = " ".join(result.snippets).lower()
        assert "role specific" not in joined
        assert STRUCTURED_VERIFICATION not in joined


def test_supporting_focus_is_skill_linked_not_generic() -> None:
    question = {
        "category": "technical",
        "skill_tag": "Cable Sizing",
        "related_skills": ["Load Calculations"],
        "question": "How do you verify cable sizing and protective-device coordination?",
    }
    study = {
        "step_by_step_breakdown": [
            "Validate cable sizing against load calculations and protective-device ratings.",
            "Record commissioning evidence before energising the circuit.",
        ],
        "common_mistakes": [
            "Selecting cable size without checking installation method derating factors.",
        ],
    }
    focus = _build_supporting_focus(
        question,
        ["cable sizing", "load calculations"],
        study,
        {"cable", "sizing", "protective", "device"},
    )
    assert focus
    joined = " ".join(focus).lower()
    assert OUTCOME_QUALITY_IMPROVES[:24] not in joined
    assert "traceability prevents repeated failures" not in joined
    assert any(
        token in joined
        for token in ("cable", "load", "protective", "commissioning", "installation")
    )


def test_summary_metrics_distinguish_used_available_not_used_not_configured() -> None:
    metrics: dict[str, set[str]] = {}
    for snapshot in ROLE_SNAPSHOTS:
        statuses = {_document_source(q).get("status") for q in _exportable(_generate(snapshot))}
        metrics[snapshot["title"]] = {s for s in statuses if s}
    assert metrics["Data Analyst"] == {"not_configured"}
    for role in ("Clinical Pharmacist", "Barista"):
        role_statuses = metrics[role]
        assert "not_configured" not in role_statuses
        assert "used" in role_statuses
        assert "available_not_used" in role_statuses
    devops_statuses = metrics["DevOps Engineer"]
    assert "not_configured" not in devops_statuses
    assert "available_not_used" in devops_statuses
    electrical_statuses = metrics["Electrical Engineer"]
    assert "not_configured" not in electrical_statuses
    assert "available_not_used" in electrical_statuses


def test_hr_questions_mostly_available_not_used_for_saved_roles() -> None:
    for role in ("DevOps Engineer", "Electrical Engineer", "Clinical Pharmacist", "Barista"):
        snapshot = next(s for s in ROLE_SNAPSHOTS if s["title"] == role)
        hr_questions = [q for q in _exportable(_generate(snapshot)) if q.get("category") == "hr"]
        assert hr_questions, f"expected HR questions for {role}"
        for q in hr_questions:
            doc = _document_source(q)
            assert doc.get("status") == "available_not_used"
            assert "HR/behavioral" in (doc.get("note") or "")


@pytest.mark.parametrize(
    ("role", "expect_used"),
    [
        ("DevOps Engineer", False),
        ("Electrical Engineer", False),
        ("Clinical Pharmacist", True),
        ("Barista", True),
        ("Data Analyst", False),
    ],
)
def test_generated_questions_document_library_metadata(role: str, expect_used: bool) -> None:
    snapshot = next(s for s in ROLE_SNAPSHOTS if s["title"] == role)
    questions = _exportable(_generate(snapshot))
    assert questions
    statuses = {_document_source(q).get("status") for q in questions}
    if expect_used:
        assert "used" in statuses
    elif role == "Data Analyst":
        assert "used" not in statuses
        assert "not_configured" in statuses
    else:
        assert "used" not in statuses
        assert "available_not_used" in statuses


def test_no_fake_urls_in_document_metadata() -> None:
    for snapshot in ROLE_SNAPSHOTS:
        for q in _exportable(_generate(snapshot)):
            blob = json.dumps(q.get("study_sources") or {})
            assert not _FAKE_URL_RE.search(blob)
            for source in (q.get("study_sources") or {}).get("sources") or []:
                assert not source.get("url")


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_markdown_export_shows_document_library_status(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    md = build_interview_pack_markdown(
        job_title=snapshot["title"],
        company_name=None,
        questions=questions,
    )
    assert "### Source / fallback status" in md
    assert "Document library" in md or "document library" in md.lower()
    if snapshot["title"] != "Data Analyst":
        if snapshot["title"] in ("Data Analyst", "Electrical Engineer", "DevOps Engineer"):
            assert "Document library" in md or "document library" in md.lower()
        else:
            assert "Document-library support" in md or "document-library support" in md.lower()


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_study_material_and_metadata_still_present(snapshot: dict) -> None:
    for q in _exportable(_generate(snapshot)):
        assert q.get("study_material")
        assert q.get("study_sources")
        assert len((q.get("study_sources") or {}).get("sources") or []) == 4


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_answers_under_500_words(snapshot: dict) -> None:
    for q in _exportable(_generate(snapshot)):
        assert len((q.get("model_answer") or "").split()) <= ABSOLUTE_MAX_WORDS


def test_attach_preserves_study_sources_on_regenerated_question() -> None:
    job = _job(next(s for s in ROLE_SNAPSHOTS if s["title"] == "DevOps Engineer"))
    q = {
        "category": "technical",
        "skill_tag": "AWS",
        "related_skills": ["Docker", "Kubernetes"],
        "question": "Explain AWS deployment reliability patterns.",
        "study_material": {"overview": "Local study module."},
    }
    attach_study_source_metadata(q, job)
    assert q.get("study_sources")
    doc = _document_source(q)
    if doc.get("status") == "used":
        assert (q.get("study_material") or {}).get("document_library_support")
