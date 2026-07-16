"""JOB-INT-R1 §9/§14: realistic candidate-voice gold samples across streams.

The contract is checked against the FINALIZED, user-facing pack (the output of
``mock_generate_questions`` — the same finalizer the live Ollama path runs
through), so export-blocked drafts are already excluded and what we assert is
exactly what a candidate would see. Every exported model answer, for six
representative roles spanning different streams, must read like a real candidate
speaking: first person, no coaching, no persona leak, no fabricated history,
with useful question-tied study material.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("LLM_PROVIDER", "mock")

from app.agents.job_search import mock_data
from app.agents.job_search.quality.candidate_answer_contract import (
    candidate_voice_violations,
    study_material_violations,
)

# role -> (responsibilities, skills) chosen to exercise different streams.
ROLES: dict[str, tuple[list[str], list[str]]] = {
    "Electrical Maintenance Engineer": (
        ["Maintain and repair electrical plant", "Carry out safe isolation and testing"],
        ["Safe Isolation", "Fault Finding", "Wiring Regulations"],
    ),
    "Data Analyst": (
        ["Build dashboards and reports", "Clean and validate datasets"],
        ["SQL", "Data Cleaning", "Dashboards"],
    ),
    "Barista": (
        ["Prepare coffee drinks to standard", "Serve customers at pace", "Keep the bar clean"],
        ["Customer Service", "Espresso Extraction", "Teamwork"],
    ),
    "Clinical Pharmacist": (
        ["Review medication charts", "Counsel patients on medicines"],
        ["Medication Review", "Drug Interactions", "Patient Counselling"],
    ),
    "Software Engineer": (
        ["Build and maintain backend services", "Write and run tests"],
        ["Python", "REST APIs", "Testing"],
    ),
    "Civil Service Administrator": (
        ["Process casework to deadline", "Keep accurate records"],
        ["Casework", "Records Management", "Data Protection"],
    ),
}

_PACK_CACHE: dict[str, list[dict]] = {}


def _pack(title: str) -> list[dict]:
    """Memoized finalized pack for a role (heavy; generate once per role)."""
    if title not in _PACK_CACHE:
        resp, skills = ROLES[title]
        job = {
            "title": title,
            "responsibilities": resp,
            "requirements": skills,
            "extracted_skills": [{"skill": s, "importance": "critical"} for s in skills],
        }
        qs = mock_data.mock_generate_questions(job, focus_areas=[], difficulty="auto")
        _PACK_CACHE[title] = [q for q in qs if (q.get("model_answer") or "").strip()]
    return _PACK_CACHE[title]


@pytest.mark.parametrize("title", list(ROLES))
def test_every_exported_answer_reads_like_a_candidate(title: str) -> None:
    pack = _pack(title)
    assert pack, f"{title}: no exportable answers generated"
    for q in pack:
        answer = q.get("model_answer") or ""
        problems = candidate_voice_violations(
            answer, role=title, question=q.get("question", ""), category=q.get("category", "")
        )
        assert problems == [], (
            f"{title} [{q.get('category')}] {q.get('question','')[:70]}: {problems}\nANSWER: {answer}"
        )


@pytest.mark.parametrize("title", list(ROLES))
def test_no_persona_or_coaching_leak_anywhere(title: str) -> None:
    for q in _pack(title):
        answer = (q.get("model_answer") or "").lower()
        for banned in (
            "phd-level scholar",
            "world's foremost expert",
            "master teacher",
            "you should say",
            "a strong answer",
            "**situation:**",
            "structured with star",
        ):
            assert banned not in answer, f"{title}: leaked '{banned}'"


@pytest.mark.parametrize("title", list(ROLES))
def test_answers_are_mostly_distinct(title: str) -> None:
    answers = [q.get("model_answer") or "" for q in _pack(title)]
    # Allow the odd shared closing, but the pack must not be one template reused.
    distinct = len(set(answers))
    assert distinct >= max(3, int(len(answers) * 0.7)), (
        f"{title}: only {distinct}/{len(answers)} distinct answers"
    )


@pytest.mark.parametrize("title", list(ROLES))
def test_every_exported_question_has_usable_study_material(title: str) -> None:
    for q in _pack(title):
        study = q.get("study_material") or {}
        problems = study_material_violations(study, question=q.get("question", ""))
        assert problems == [], f"{title} [{q.get('category')}]: study problems {problems}"
        assert (study.get("overview") or "").strip(), f"{title}: empty study overview"


def test_behavioral_answers_do_not_invent_employers() -> None:
    # A thin job (no user experience) must never fabricate an employer/history.
    for title in ("Software Engineer", "Clinical Pharmacist"):
        for q in _pack(title):
            if q.get("category") != "behavioral":
                continue
            low = (q.get("model_answer") or "").lower()
            for fabricated in ("at my previous company", "in my last role at", "at my last employer"):
                assert fabricated not in low, f"{title}: fabricated employer in behavioral answer"
