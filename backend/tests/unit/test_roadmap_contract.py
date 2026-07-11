"""
ROAD-F2 — Roadmap save/load contract unit tests.

Covers schema truth the frontend depends on, milestone ORM drafting, and
ownership filter presence on object routes. Full HTTP+DB ownership fixtures
are heavier than this slice needs; those remain available for later API
integration tests.
"""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.api.routes import roadmap as roadmap_routes
from app.api.routes.roadmap import _milestones_to_orm
from app.schemas.roadmap import (
    RoadmapGenerateRequest,
    RoadmapMilestoneRead,
    RoadmapRead,
    RoadmapSkillRead,
    RoadmapSkillStatusUpdate,
)


def test_generate_request_requires_target_role():
    with pytest.raises(ValidationError):
        RoadmapGenerateRequest(target_role="")
    req = RoadmapGenerateRequest(target_role="Data Engineer", pace="normal")
    assert req.target_role == "Data Engineer"
    assert req.pace == "normal"
    assert req.personalization_inputs.weekly_hours_available is None


def test_generate_request_rejects_invalid_pace():
    with pytest.raises(ValidationError):
        RoadmapGenerateRequest(target_role="Backend Engineer", pace="turbo")


def test_roadmap_read_has_no_status_field():
    """Frontend must not require nonexistent roadmap.status / milestone.status."""
    assert "status" not in RoadmapRead.model_fields
    assert "status" not in RoadmapMilestoneRead.model_fields
    assert "status" in RoadmapSkillRead.model_fields


def test_roadmap_read_accepts_backend_list_shape_without_user_id():
    rid = uuid.uuid4()
    mid = uuid.uuid4()
    sid = uuid.uuid4()
    now = datetime.now(timezone.utc)
    read = RoadmapRead.model_validate(
        {
            "id": rid,
            "target_role": "Software Engineer",
            "pace": "fast",
            "starting_skill_level": "beginner",
            "personalization_inputs": {"weekly_hours_available": 8},
            "milestones": [
                {
                    "id": mid,
                    "title": "Month 0-3: Foundations",
                    "timeframe_label": "0-3 months",
                    "skills": [
                        {
                            "id": sid,
                            "skill_name": "Python",
                            "importance": "critical",
                            "estimated_hours": 12,
                            "status": "not_started",
                            "resources": [{"title": "Docs", "url": None, "resource_type": "documentation"}],
                            "study_material": {"overview": "Learn Python", "key_concepts": ["syntax"]},
                            "practice_activities": {
                                "exercises": ["Write a script"],
                                "project_idea": None,
                                "self_assessment_questions": ["Can you use lists?"],
                            },
                            "lateral_connections": ["Git"],
                        }
                    ],
                }
            ],
            "created_at": now,
            "updated_at": now,
        }
    )
    assert read.target_role == "Software Engineer"
    assert read.milestones[0].skills[0].status == "not_started"
    assert read.milestones[0].skills[0].resources[0].url is None
    assert getattr(read, "status", None) is None


def test_skill_status_update_literals():
    assert RoadmapSkillStatusUpdate(status="completed").status == "completed"
    with pytest.raises(ValidationError):
        RoadmapSkillStatusUpdate(status="done")


def test_milestones_to_orm_preserves_skill_progress_defaults():
    milestones = _milestones_to_orm(
        [
            {
                "title": "Foundations",
                "timeframe_label": "Month 0-2",
                "skills": [
                    {"skill_name": "SQL", "importance": "critical", "estimated_hours": 10},
                    {
                        "skill_name": "Python",
                        "status": "in_progress",
                        "resources": [],
                        "study_material": {},
                        "practice_activities": {},
                        "lateral_connections": [],
                    },
                ],
            }
        ]
    )
    assert len(milestones) == 1
    assert milestones[0].title == "Foundations"
    assert milestones[0].order_index == 0
    assert milestones[0].skills[0].skill_name == "SQL"
    assert milestones[0].skills[0].status == "not_started"
    assert milestones[0].skills[1].status == "in_progress"
    assert milestones[0].skills[1].order_index == 1


def test_owned_roadmap_helpers_filter_by_user_id():
    """Contract: object routes must scope by authenticated user (no cross-user leak)."""
    src = inspect.getsource(roadmap_routes._get_owned_roadmap)
    assert "Roadmap.user_id == user.id" in src
    assert "NotFoundError" in src

    list_src = inspect.getsource(roadmap_routes.list_roadmaps)
    assert "Roadmap.user_id == user.id" in list_src

    delete_src = inspect.getsource(roadmap_routes.delete_roadmap)
    assert "_get_owned_roadmap" in delete_src

    get_src = inspect.getsource(roadmap_routes.get_roadmap)
    assert "_get_owned_roadmap" in get_src

    regen_src = inspect.getsource(roadmap_routes.regenerate_roadmap)
    assert "_get_owned_roadmap" in regen_src
