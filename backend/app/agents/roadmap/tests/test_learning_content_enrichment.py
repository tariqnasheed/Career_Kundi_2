"""Career Roadmap enrichment: content is rich, field-adaptive, and never empty.

Covers the deep-enhancement of skill content into a Bloom-aligned learning path
(layered study material + flashcards + quizzes + projects + reflection) across
several educational fields, and the graceful degradation that fixes the
original "nothing loads" bug.
"""

from __future__ import annotations

import pytest

from app.agents.roadmap import learning_content as lc
from app.agents.roadmap import mock_data
from app.agents.roadmap.content_quality import (
    normalize_practice_activities,
    normalize_study_material,
)
from app.schemas.roadmap import RoadmapPracticeActivities, RoadmapStudyMaterial

# (skill, role, expected field) spanning distinct educational streams.
CASES = [
    ("Python", "AI Engineer", "technology"),
    ("Medication Review", "Clinical Pharmacist", "healthcare"),
    ("Safe Isolation", "Electrical Maintenance Engineer", "engineering"),
    ("Financial Modelling", "Investment Analyst", "finance"),
    ("Espresso Extraction", "Barista", "general"),
    ("Lesson Planning", "Secondary Teacher", "education"),
]


@pytest.mark.parametrize("skill, role, field", CASES)
def test_detect_field(skill: str, role: str, field: str) -> None:
    assert lc.detect_field(skill, role) == field


@pytest.mark.parametrize("skill, role, _field", CASES)
def test_study_material_is_rich_and_layered(skill: str, role: str, _field: str) -> None:
    sm = mock_data.build_study_overview(skill, role)
    assert sm["overview"].strip()
    assert sm["why_it_matters"].strip()
    assert len(sm["learning_objectives"]) >= 5  # Bloom ladder
    assert sm["beginner_explanation"].strip()
    assert sm["intermediate_explanation"].strip()
    assert sm["advanced_explanation"].strip()
    assert len(sm["concepts"]) >= 3
    assert all(c["term"] and c["definition"] for c in sm["concepts"])
    assert sm["worked_example"].strip()
    assert len(sm["common_mistakes"]) >= 3
    assert len(sm["revision_notes"]) >= 3
    # every field references the real skill somewhere (adaptive, not blank template)
    assert skill.lower() in (sm["overview"] + sm["beginner_explanation"] + sm["worked_example"]).lower()
    RoadmapStudyMaterial.model_validate(sm)


@pytest.mark.parametrize("skill, role, _field", CASES)
def test_practice_has_all_modalities(skill: str, role: str, _field: str) -> None:
    pa = mock_data.build_practice_activities(skill, role, ["Neighbour Skill"])
    # flashcards (active recall)
    assert len(pa["flashcards"]) >= 4
    assert all(f["front"].strip() and f["back"].strip() for f in pa["flashcards"])
    # quizzes (assessment gateways)
    assert len(pa["quizzes"]) >= 3
    for q in pa["quizzes"]:
        assert q["question"].strip()
        assert len(q["options"]) >= 2
        assert 0 <= q["answer_index"] < len(q["options"])
        assert q["explanation"].strip()
    # projects (project-based, tiered)
    assert len(pa["projects"]) >= 2
    difficulties = {p["difficulty"] for p in pa["projects"]}
    assert "beginner" in difficulties
    assert all(p["title"] and p["brief"] for p in pa["projects"])
    # reflection (synthesis)
    assert len(pa["reflection_questions"]) >= 3
    RoadmapPracticeActivities.model_validate(pa)


def test_normalize_backfills_empty_llm_output() -> None:
    """Empty/None Ollama output must never persist as blank content."""
    sm = normalize_study_material(None, "Kubernetes", "Platform Engineer")
    assert sm["overview"] and sm["learning_objectives"] and sm["concepts"]
    RoadmapStudyMaterial.model_validate(sm)

    pa = normalize_practice_activities({}, "Kubernetes", "Platform Engineer", ["Linux"])
    assert pa["flashcards"] and pa["quizzes"] and pa["projects"] and pa["reflection_questions"]
    RoadmapPracticeActivities.model_validate(pa)


def test_normalize_preserves_good_llm_flashcards() -> None:
    good = {
        "exercises": ["Do X"],
        "project_idea": "Build Y",
        "self_assessment_questions": ["Can you Z?"],
        "flashcards": [{"front": "What is a pod?", "back": "The smallest deployable unit in Kubernetes."}] * 3,
    }
    pa = normalize_practice_activities(good, "Kubernetes", "Platform Engineer", [])
    assert any("pod" in f["front"].lower() for f in pa["flashcards"])  # LLM cards kept
    assert pa["quizzes"] and pa["projects"]  # missing modalities still backfilled


def test_curated_resources_never_empty_and_field_agnostic() -> None:
    for skill, role, _f in CASES:
        res = mock_data.curated_resources(skill, role)
        assert len(res) >= 3
        assert all(r["url"].startswith("http") for r in res)
        assert all(r["curated"] and not r["verified"] for r in res)
