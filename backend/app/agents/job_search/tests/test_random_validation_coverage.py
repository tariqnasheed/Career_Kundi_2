"""Random validation coverage floor tests — Iteration 004D-S."""

from __future__ import annotations

import re

import pytest

from app.agents.job_search.knowledge.coverage_planner import MIN_EXPORTABLE_PACK_QUESTIONS
from app.agents.job_search.knowledge.model_knowledge import is_model_knowledge_enabled
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import (
    INTERMEDIATE_QUALITY_CHECKS,
    OUTCOME_QUALITY_IMPROVES,
    STABILIZE_MAINTAIN_PIPELINES,
    STRUCTURED_VERIFICATION,
)
from app.data.popular_roles_catalog import catalog_role_to_job_snapshot, get_all_catalog_roles
from app.tools.document_export import build_interview_pack_markdown

_ROLE_SPECIFIC_LABEL = "Role " + "Specific"
_FAKE_URL_RE = re.compile(r"https?://[^\s\])\"']+")
_BLOCKED = (
    OUTCOME_QUALITY_IMPROVES,
    STRUCTURED_VERIFICATION,
    INTERMEDIATE_QUALITY_CHECKS,
    STABILIZE_MAINTAIN_PIPELINES,
)

_CREATIVE_SNAPSHOTS = [
    {
        "title": "Journalist",
        "from_catalog": True,
    },
    {
        "title": "Social Media Creator",
        "from_catalog": False,
        "job": {
            "title": "Social Media Creator",
            "responsibilities": [
                "Platform content planning, filming, editing, and publishing on a consistent schedule",
                "Community engagement, analytics review, and brand-safe sponsorship integration",
            ],
            "requirements": ["content strategy", "video editing", "community management", "analytics review"],
            "extracted_skills": [
                {"skill": "Content Strategy"},
                {"skill": "Video Editing"},
                {"skill": "Community Management"},
                {"skill": "Analytics"},
            ],
        },
    },
    {
        "title": "YouTuber",
        "from_catalog": False,
        "job": {
            "title": "YouTuber",
            "responsibilities": [
                "Scripting, filming, editing, and publishing long-form video content",
                "Audience growth, sponsorship integration, and community moderation",
            ],
            "requirements": ["video editing", "storytelling", "analytics", "thumbnail design"],
            "extracted_skills": [
                {"skill": "Video Editing"},
                {"skill": "Storytelling"},
                {"skill": "Audience Growth"},
                {"skill": "Analytics"},
            ],
        },
    },
    {
        "title": "Footballer",
        "from_catalog": False,
        "job": {
            "title": "Footballer",
            "responsibilities": [
                "Match preparation, training discipline, and on-field teamwork",
                "Performance review with coaching staff and recovery between fixtures",
            ],
            "requirements": ["training discipline", "teamwork", "tactical awareness", "fitness"],
            "extracted_skills": [
                {"skill": "Training Discipline"},
                {"skill": "Teamwork"},
                {"skill": "Match Preparation"},
                {"skill": "Tactical Awareness"},
            ],
        },
    },
]


def _job_for(snapshot: dict) -> dict:
    if snapshot.get("job"):
        return snapshot["job"]
    if snapshot.get("from_catalog"):
        role = next(r for r in get_all_catalog_roles() if r.get("title") == snapshot["title"])
        return catalog_role_to_job_snapshot(role)
    raise ValueError(f"No job snapshot for {snapshot['title']}")


def _generate(snapshot: dict) -> list[dict]:
    job = _job_for(snapshot)
    skills = [
        s.get("skill") if isinstance(s, dict) else s for s in job.get("extracted_skills") or []
    ]
    return mock_generate_questions(job, focus_areas=skills, difficulty="mid")


def _exportable(questions: list[dict]) -> list[dict]:
    return [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]


@pytest.mark.parametrize("snapshot", _CREATIVE_SNAPSHOTS, ids=[s["title"] for s in _CREATIVE_SNAPSHOTS])
def test_archetype_role_meets_coverage_floor(snapshot: dict) -> None:
    exportable = _exportable(_generate(snapshot))
    assert len(exportable) >= MIN_EXPORTABLE_PACK_QUESTIONS, (
        f"{snapshot['title']} only generated {len(exportable)} exportable questions"
    )


def test_journalist_meets_coverage_floor() -> None:
    exportable = _exportable(_generate(_CREATIVE_SNAPSHOTS[0]))
    assert len(exportable) >= 28


def test_social_media_creator_meets_coverage_floor() -> None:
    exportable = _exportable(_generate(_CREATIVE_SNAPSHOTS[1]))
    assert len(exportable) >= 28


def test_youtuber_meets_coverage_floor() -> None:
    exportable = _exportable(_generate(_CREATIVE_SNAPSHOTS[2]))
    assert len(exportable) >= 28


def test_footballer_meets_coverage_floor() -> None:
    exportable = _exportable(_generate(_CREATIVE_SNAPSHOTS[3]))
    assert len(exportable) >= 28


def test_creative_roles_include_required_categories() -> None:
    for snapshot in _CREATIVE_SNAPSHOTS[:2]:
        questions = _exportable(_generate(snapshot))
        categories = {q.get("category") for q in questions}
        qtypes = {q.get("question_type") for q in questions}
        blob = " ".join((q.get("question") or "").lower() for q in questions)
        assert "hr" in categories
        assert "daily_routine" in categories
        assert (
            any(t in qtypes for t in ("practical_task", "case_study"))
            or "practical task" in blob
            or "case study" in blob
        )
        assert any(
            t in qtypes
            for t in ("ethics", "copyright", "brand_safety", "crisis_reputation", "sportsmanship")
        ) or any(k in blob for k in ("ethics", "copyright", "brand safety", "sportsmanship"))
        assert any(
            t in qtypes
            for t in ("platform_tools", "analytics_kpi", "audience_research", "content_niche")
        ) or any(k in blob for k in ("platform", "analytics", "audience"))


def test_no_role_specific_label_in_creative_packs() -> None:
    for snapshot in _CREATIVE_SNAPSHOTS:
        questions = _generate(snapshot)
        md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
        )
        assert _ROLE_SPECIFIC_LABEL not in md


def test_no_blocked_phrases_in_creative_packs() -> None:
    for snapshot in _CREATIVE_SNAPSHOTS:
        questions = _generate(snapshot)
        md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
        ).lower()
        for marker in _BLOCKED:
            assert marker.lower() not in md


def test_no_fake_urls_in_creative_packs() -> None:
    for snapshot in _CREATIVE_SNAPSHOTS:
        questions = _generate(snapshot)
        md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
        )
        assert not _FAKE_URL_RE.search(md)


def test_answers_under_500_words_for_creative_roles() -> None:
    for snapshot in _CREATIVE_SNAPSHOTS:
        for q in _exportable(_generate(snapshot)):
            assert len((q.get("model_answer") or "").split()) <= ABSOLUTE_MAX_WORDS


def test_model_knowledge_still_disabled_by_default() -> None:
    assert is_model_knowledge_enabled() is False
