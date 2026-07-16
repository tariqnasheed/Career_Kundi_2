"""JOB-INT-R1 §10/§14: study material is tied to the exact question and useful.

Every exported question must carry study material that (a) has a non-empty
overview, (b) teaches something concrete (definitions / key concepts / a
method), and (c) is not simply a copy of the spoken model answer.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("LLM_PROVIDER", "mock")

from app.agents.job_search import mock_data
from app.agents.job_search.quality.candidate_answer_contract import study_material_violations

_ROLES = {
    "Data Analyst": (["Build dashboards and reports", "Clean datasets"], ["SQL", "Data Cleaning"]),
    "Clinical Pharmacist": (["Review medication charts"], ["Medication Review", "Drug Interactions"]),
}

_CACHE: dict[str, list[dict]] = {}


def _pack(title: str) -> list[dict]:
    if title not in _CACHE:
        resp, skills = _ROLES[title]
        job = {
            "title": title,
            "responsibilities": resp,
            "requirements": skills,
            "extracted_skills": [{"skill": s, "importance": "critical"} for s in skills],
        }
        qs = mock_data.mock_generate_questions(job, focus_areas=[], difficulty="auto")
        _CACHE[title] = [q for q in qs if (q.get("model_answer") or "").strip()]
    return _CACHE[title]


@pytest.mark.parametrize("title", list(_ROLES))
def test_study_material_is_present_and_concrete(title: str) -> None:
    for q in _pack(title):
        study = q.get("study_material") or {}
        problems = study_material_violations(study, question=q.get("question", ""))
        assert problems == [], f"{title} [{q.get('category')}]: {problems}"


@pytest.mark.parametrize("title", list(_ROLES))
def test_study_overview_not_blank(title: str) -> None:
    for q in _pack(title):
        overview = (q.get("study_material") or {}).get("overview") or ""
        assert overview.strip(), f"{title}: blank study overview for {q.get('question','')[:60]}"


@pytest.mark.parametrize("title", list(_ROLES))
def test_study_overview_not_just_the_model_answer(title: str) -> None:
    for q in _pack(title):
        overview = ((q.get("study_material") or {}).get("overview") or "").strip()
        answer = (q.get("model_answer") or "").strip()
        if overview and answer:
            assert overview != answer, f"{title}: study overview duplicates the model answer"


@pytest.mark.parametrize("title", list(_ROLES))
def test_technical_questions_teach_definitions_or_concepts(title: str) -> None:
    for q in _pack(title):
        if q.get("category") != "technical":
            continue
        study = q.get("study_material") or {}
        has_teaching = any(
            study.get(k)
            for k in ("definitions", "key_concepts", "key_principles", "step_by_step_method", "step_by_step_breakdown")
        )
        assert has_teaching, f"{title}: technical study material lacks definitions/concepts/method"
