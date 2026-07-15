"""CORE-VALUE-R1: Roadmap content quality contract smoke (API-adjacent)."""

from __future__ import annotations

from app.agents.roadmap.content_quality import (
    is_useful_practice_activities,
    is_useful_study_material,
    normalize_practice_activities,
    normalize_study_material,
)
from app.schemas.roadmap import RoadmapPracticeActivities, RoadmapStudyMaterial


def test_schema_accepts_normalized_study_and_practice():
    study = normalize_study_material({}, "Kubernetes", "Platform Engineer")
    practice = normalize_practice_activities({}, "Kubernetes", "Platform Engineer", ["Linux"])
    assert is_useful_study_material(study)
    assert is_useful_practice_activities(practice)
    RoadmapStudyMaterial.model_validate(study)
    RoadmapPracticeActivities.model_validate(practice)
    assert len(study["key_concepts"]) >= 4
    assert len(practice["self_assessment_questions"]) >= 5
