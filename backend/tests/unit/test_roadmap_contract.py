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


def test_skill_status_and_refresh_routes_require_owned_skill():
    status_src = inspect.getsource(roadmap_routes.update_skill_status)
    assert "_get_owned_skill" in status_src
    assert "skill.status = payload.status" in status_src

    refresh_src = inspect.getsource(roadmap_routes.refresh_skill_content)
    assert "_get_owned_skill" in refresh_src

    owned_skill_src = inspect.getsource(roadmap_routes._get_owned_skill)
    assert "_get_owned_roadmap" in owned_skill_src
    assert "NotFoundError" in owned_skill_src


def test_no_task_model_skills_are_progress_units():
    """ROAD-F3: progress contract is skill status — no Task ORM/schema required."""
    assert "status" in RoadmapSkillRead.model_fields
    assert RoadmapSkillStatusUpdate.model_fields["status"].annotation
    # Ensure contract tests do not invent a Task schema import
    import app.schemas.roadmap as roadmap_schemas

    assert not hasattr(roadmap_schemas, "TaskRead")
    assert not hasattr(roadmap_schemas, "RoadmapTaskRead")


def test_generate_request_accepts_taxonomy_under_personalization():
    """0051-F10: advisory _taxonomy nests under personalization_inputs without being required."""
    req = RoadmapGenerateRequest(
        target_role="Electrical Engineer",
        pace="normal",
        personalization_inputs={
            "weekly_hours_available": 10,
            "_taxonomy": {
                "target_role_text": "Electrical Engineer",
                "matched_role_id": "electrical_engineer",
                "matched_skill_id": None,
                "normalized_text": "electrical engineer",
                "source": "user_provided",
                "confidence": "suggested",
                "explanation": "Deterministic match from internal seed catalog.",
                "accepted_by_user": True,
                "kept_freeform": False,
                "suggested_skill_ids": ["load_calculations"],
                "suggested_skill_labels": ["Load calculations"],
                "matched_role_title": "Electrical Engineer",
            },
        },
    )
    dumped = roadmap_routes._dump_personalization(req.personalization_inputs)
    assert dumped["weekly_hours_available"] == 10
    assert dumped["_taxonomy"]["matched_role_id"] == "electrical_engineer"
    assert dumped["_taxonomy"]["accepted_by_user"] is True
    assert "taxonomy" not in dumped  # alias key only


def test_generate_request_works_without_taxonomy():
    req = RoadmapGenerateRequest(target_role="Software Developer", pace="fast")
    dumped = roadmap_routes._dump_personalization(req.personalization_inputs)
    assert "_taxonomy" not in dumped


def test_merge_personalization_preserves_taxonomy_when_role_unchanged():
    existing = {
        "weekly_hours_available": 8,
        "_taxonomy": {
            "matched_role_id": "software_developer",
            "accepted_by_user": True,
            "kept_freeform": False,
        },
    }
    incoming = {"weekly_hours_available": 10, "additional_context": "refresh"}
    merged = roadmap_routes._merge_personalization_on_regenerate(
        existing,
        incoming,
        previous_role="Software Developer",
        new_role="Software Developer",
    )
    assert merged["weekly_hours_available"] == 10
    assert merged["_taxonomy"]["matched_role_id"] == "software_developer"
    assert merged["additional_context"] == "refresh"


def test_merge_personalization_drops_stale_taxonomy_when_role_changes():
    existing = {
        "_taxonomy": {"matched_role_id": "software_developer", "accepted_by_user": True},
    }
    incoming = {"weekly_hours_available": 6}
    merged = roadmap_routes._merge_personalization_on_regenerate(
        existing,
        incoming,
        previous_role="Software Developer",
        new_role="Data Engineer",
    )
    assert "_taxonomy" not in merged
    assert merged["weekly_hours_available"] == 6


def test_merge_personalization_keeps_incoming_taxonomy_over_existing():
    existing = {"_taxonomy": {"matched_role_id": "old_role"}}
    incoming = {
        "_taxonomy": {"matched_role_id": "new_role", "accepted_by_user": False},
    }
    merged = roadmap_routes._merge_personalization_on_regenerate(
        existing,
        incoming,
        previous_role="Same Role",
        new_role="Same Role",
    )
    assert merged["_taxonomy"]["matched_role_id"] == "new_role"


def test_dump_and_merge_helpers_do_not_import_agent_taxonomy():
    """0051-F10 boundary: roadmap route helpers stay decoupled from RoleTaxonomyAgent."""
    dump_src = inspect.getsource(roadmap_routes._dump_personalization)
    merge_src = inspect.getsource(roadmap_routes._merge_personalization_on_regenerate)
    route_src = inspect.getsource(roadmap_routes)
    assert "RoleTaxonomyAgent" not in dump_src
    assert "RoleTaxonomyAgent" not in merge_src
    assert "TaxonomyRegistry" not in route_src
    assert "RoleTaxonomyAgent" not in route_src
