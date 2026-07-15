"""CORE-VALUE-R1: empty Ollama study/practice payloads must normalize to useful content."""

from __future__ import annotations

import pytest

from app.agents.roadmap.content_quality import (
    is_useful_practice_activities,
    is_useful_study_material,
    normalize_practice_activities,
    normalize_study_material,
)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"overview": "", "key_concepts": []},
        {"overview": "   ", "key_concepts": ["", None]},
        {"overview": "Only overview", "key_concepts": []},
    ],
)
def test_empty_study_material_is_not_useful(payload):
    assert is_useful_study_material(payload) is False


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"exercises": [], "project_idea": "", "self_assessment_questions": []},
        {"exercises": [""], "project_idea": "  ", "self_assessment_questions": []},
    ],
)
def test_empty_practice_is_not_useful(payload):
    assert is_useful_practice_activities(payload) is False


def test_normalize_study_replaces_empty_ollama_payload():
    out = normalize_study_material(
        {"overview": "", "key_concepts": []},
        "Python",
        "AI Engineer",
    )
    assert is_useful_study_material(out)
    assert "Python" in out["overview"]
    assert "AI Engineer" in out["overview"]
    assert len(out["key_concepts"]) >= 4
    assert "not source-verified" in out["overview"].lower() or "foundational" in out["overview"].lower()


def test_normalize_study_replaces_refusal_overview():
    refusal = {
        "overview": (
            "Unfortunately, no relevant material was found in the provided context "
            "to create a study overview for Deep Learning."
        ),
        "key_concepts": ["A", "B"],
    }
    out = normalize_study_material(refusal, "Deep Learning", "AI Engineer")
    assert is_useful_study_material(out)
    assert "Deep Learning" in out["overview"]
    assert "no relevant material" not in out["overview"].lower()
    assert len(out["key_concepts"]) >= 4


def test_normalize_practice_replaces_empty_ollama_payload():
    out = normalize_practice_activities(
        {"exercises": [], "project_idea": "", "self_assessment_questions": []},
        "Python",
        "AI Engineer",
        ["Machine Learning", "SQL"],
    )
    assert is_useful_practice_activities(out)
    assert len(out["exercises"]) >= 4
    assert out["project_idea"].strip()
    assert len(out["self_assessment_questions"]) >= 5
    assert "Python" in out["project_idea"]


def test_normalize_preserves_useful_ollama_content():
    useful = {
        "overview": "Python matters for AI engineering workflows.",
        "key_concepts": ["syntax", "data structures", "packages", "virtual environments"],
        "estimated_reading_time_minutes": 12,
    }
    out = normalize_study_material(useful, "Python", "AI Engineer")
    assert out["overview"] == useful["overview"]
    assert out["key_concepts"][:4] == useful["key_concepts"]
