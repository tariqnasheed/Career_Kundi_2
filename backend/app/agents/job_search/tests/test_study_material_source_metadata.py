"""Tests for study-material source metadata (Iteration 004A)."""

from __future__ import annotations

import json
import re

import pytest

from app.agents.job_search.knowledge.coverage_planner import _hr_motivation_question
from app.agents.job_search.knowledge.study_sources import (
    attach_study_source_metadata,
    build_default_study_source_bundle,
    render_study_source_markdown,
)
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.tools.document_export import build_interview_pack_markdown

ROLE_SNAPSHOTS = [
    {
        "title": "Data Analyst",
        "primary_skill": "SQL",
        "responsibilities": [
            "SQL querying and dashboard creation for stakeholder reporting",
            "Data cleaning, data quality checks, and KPI/metrics reporting",
        ],
        "requirements": ["SQL querying", "dashboard creation", "data quality checks", "Excel or BI tools"],
        "extracted_skills": ["SQL", "Data Quality", "Dashboarding", "Excel"],
    },
    {
        "title": "Electrical Engineer",
        "primary_skill": "Electrical Installation",
        "responsibilities": [
            "LV distribution design support and load calculations",
            "Testing, commissioning, electrical safety, and standards compliance",
        ],
        "requirements": ["load calculations", "cable sizing", "electrical safety", "standards/compliance"],
        "extracted_skills": ["Electrical Installation", "Load Calculations", "Cable Sizing", "Commissioning"],
    },
    {
        "title": "Clinical Pharmacist",
        "primary_skill": "Pharmacology",
        "responsibilities": [
            "Medication review, prescribing safety, and patient counselling",
            "Clinical documentation, escalation, and governance",
        ],
        "requirements": ["medication review", "prescribing safety", "governance", "risk management"],
        "extracted_skills": ["Pharmacology", "Medication Review", "Patient Counselling", "Clinical Governance"],
    },
    {
        "title": "Barista",
        "primary_skill": "Coffee Preparation",
        "responsibilities": [
            "Espresso preparation, milk steaming, and drink consistency during rush hours",
            "Hygiene, allergen controls, customer service, and stock handling",
        ],
        "requirements": ["espresso preparation", "hygiene", "allergens", "customer service"],
        "extracted_skills": ["Coffee Preparation", "HACCP", "Customer Service", "Stock Control"],
    },
    {
        "title": "DevOps Engineer",
        "primary_skill": "AWS",
        "responsibilities": [
            "AWS infrastructure automation with CI/CD, Docker, and Kubernetes",
            "Monitoring, incident response, security controls, and rollback/recovery",
        ],
        "requirements": ["AWS", "CI/CD", "Docker", "Kubernetes", "monitoring", "security"],
        "extracted_skills": ["AWS", "CI/CD", "Docker", "Kubernetes", "Monitoring"],
    },
]

SOURCE_TYPES = ("web", "model", "document_library", "local_fallback")
_FAKE_URL_RE = re.compile(r"https?://[^\s\])\"']+")


def _joined_guard_tokens() -> tuple[str, ...]:
    return (
        "deterministic" + "mode",
        "available_not_used" + "when",
        "not_configured" + "in",
        "local" + "fallback",
        "source " + "ladderis",
        "source" + "ladderis",
    )


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


def test_default_source_bundle_has_four_ladder_steps() -> None:
    bundle = build_default_study_source_bundle(role_title="Data Analyst")
    types = [s.source_type for s in bundle.sources]
    assert types == list(SOURCE_TYPES)
    assert bundle.used_source_types == ["local_fallback"]
    assert bundle.sources[0].status == "not_configured"  # web
    assert bundle.sources[1].status == "not_configured"  # model in deterministic mode
    assert bundle.sources[3].status == "used"  # local_fallback


def test_attach_study_source_metadata_on_question() -> None:
    job = _job(ROLE_SNAPSHOTS[0])
    q: dict = {"category": "hr", "question": _hr_motivation_question(job)}
    attach_study_source_metadata(q, job)
    meta = q.get("study_sources") or {}
    assert meta.get("used_source_types") == ["local_fallback"]
    assert len(meta.get("sources") or []) == 4
    assert meta.get("summary")


def test_no_fake_urls_in_source_metadata() -> None:
    for snapshot in ROLE_SNAPSHOTS:
        for q in _exportable(_generate(snapshot)):
            blob = json.dumps(q.get("study_sources") or {})
            for source in (q.get("study_sources") or {}).get("sources") or []:
                assert not source.get("url"), f"Unexpected fake URL in {snapshot['title']}"
            assert not _FAKE_URL_RE.search(blob), f"Fake URL pattern in {snapshot['title']} study_sources"


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_every_question_has_study_source_metadata(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    assert questions
    for q in questions:
        meta = q.get("study_sources") or {}
        assert meta, f"Missing study_sources for {q.get('question_id')}"
        source_types = {s.get("source_type") for s in meta.get("sources") or []}
        assert source_types == set(SOURCE_TYPES)
        assert "local_fallback" in (meta.get("used_source_types") or [])


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_study_material_still_present(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    for q in questions:
        study = q.get("study_material") or {}
        assert study, f"Missing study_material for {q.get('question_id')}"
        has_content = any(
            study.get(k)
            for k in (
                "overview",
                "beginner_explanation",
                "what_this_question_tests",
                "step_by_step_method",
                "definitions",
            )
        )
        assert has_content, f"Empty study_material for {q.get('question_id')}"


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_markdown_export_includes_source_status(snapshot: dict) -> None:
    job = _job(snapshot)
    questions = _exportable(_generate(snapshot))
    md = build_interview_pack_markdown(
        job_title=snapshot["title"],
        company_name=None,
        questions=questions,
    )
    assert "### Source / fallback status" in md
    assert md.count("### Source / fallback status") >= len(questions)
    assert "Local deterministic study material" in md
    assert "Not configured in this iteration" in md
    assert "deterministic mode" in md.lower()
    lowered = md.lower()
    for artifact in _joined_guard_tokens():
        assert artifact not in lowered, f"Joined source artifact {artifact!r} in {snapshot['title']} export"


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_coverage_categories_still_present(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    assert any(q.get("category") == "hr" for q in questions)
    assert any(q.get("category") == "daily_routine" for q in questions)
    has_seniority = any(
        q.get("question_type") == "seniority"
        or any(k in (q.get("question") or "").lower() for k in ("junior", "senior", "mid-level"))
        for q in questions
    )
    assert has_seniority
    has_case = any(
        q.get("question_type") in {"case_study", "practical_task"}
        or "case study" in (q.get("question") or "").lower()
        or "practical task" in (q.get("question") or "").lower()
        for q in questions
    )
    assert has_case


def test_model_source_note_uses_deterministic_mode_wording() -> None:
    bundle = build_default_study_source_bundle(role_title="Data Analyst")
    model = next(s for s in bundle.sources if s.source_type == "model")
    assert "deterministic mode" in model.note.lower()
    assert ("deterministic" + "mode") not in model.note.lower()
    assert ("deterministic" + " generation mode") not in model.note.lower()


def test_render_study_source_markdown_graceful_without_metadata() -> None:
    lines = render_study_source_markdown(None)
    text = "\n".join(lines)
    assert "Source / fallback status" in text
    assert "Not configured" in text


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_answers_remain_under_500_words(snapshot: dict) -> None:
    for q in _exportable(_generate(snapshot)):
        words = len((q.get("model_answer") or "").split())
        assert words <= ABSOLUTE_MAX_WORDS, (
            f"{snapshot['title']} answer over limit ({words} words) for {q.get('question_id')}"
        )
