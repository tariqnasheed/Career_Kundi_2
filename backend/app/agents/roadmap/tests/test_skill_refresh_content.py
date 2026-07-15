"""CORE-VALUE-R1: Skill refresh applies study/practice normalization."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.roadmap.agents import SkillRefreshExecutorAgent
from app.agents.roadmap.content_quality import (
    is_useful_practice_activities,
    is_useful_study_material,
)
from app.core.config import settings


def test_skill_refresh_stores_nonempty_study_and_practice(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "mock")
    agent = SkillRefreshExecutorAgent(cost_monitor=MagicMock())
    state = {
        "skill_name": "Python",
        "target_role": "AI Engineer",
        "plan": {"tier": "flash"},
        "citations": [],
    }

    async def _run():
        with (
            patch("app.agents.roadmap.agents.retrieve", return_value=[]),
            patch("app.agents.roadmap.agents.get_search_provider") as search_provider,
            patch("app.agents.roadmap.agents.get_related_skills", return_value=[]),
            patch("app.agents.roadmap.agents.add_skill_resource_edge"),
        ):
            provider = MagicMock()
            provider.search = AsyncMock(return_value=[])
            search_provider.return_value = provider
            return await agent.run(state)

    out = asyncio.run(_run())
    draft = out["draft_output"]
    study = draft["study_material"]
    practice = draft["practice_activities"]
    assert is_useful_study_material(study)
    assert is_useful_practice_activities(practice)
    assert len(study["key_concepts"]) >= 4
    assert len(practice["exercises"]) >= 4


def test_skill_refresh_normalizes_empty_llm_json(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    empty = {"overview": "", "key_concepts": []}
    empty_practice = {"exercises": [], "project_idea": "", "self_assessment_questions": []}

    llm = MagicMock()
    llm.generate = AsyncMock(
        side_effect=[
            MagicMock(parsed_json=empty, prompt_tokens=1, completion_tokens=1, total_tokens=2),
            MagicMock(parsed_json=empty_practice, prompt_tokens=1, completion_tokens=1, total_tokens=2),
        ]
    )
    cost = MagicMock()
    agent = SkillRefreshExecutorAgent(cost_monitor=cost)
    state = {
        "skill_name": "Docker",
        "target_role": "DevOps Engineer",
        "plan": {"tier": "flash"},
        "citations": [],
    }

    async def _run():
        with (
            patch("app.agents.roadmap.agents.retrieve", return_value=[]),
            patch("app.agents.roadmap.agents.get_llm", return_value=llm),
            patch("app.agents.roadmap.agents.get_search_provider") as search_provider,
            patch("app.agents.roadmap.agents.get_related_skills", return_value=[]),
            patch("app.agents.roadmap.agents.add_skill_resource_edge"),
        ):
            provider = MagicMock()
            provider.search = AsyncMock(return_value=[])
            search_provider.return_value = provider
            return await agent.run(state)

    out = asyncio.run(_run())
    draft = out["draft_output"]
    assert is_useful_study_material(draft["study_material"])
    assert is_useful_practice_activities(draft["practice_activities"])
    assert "Docker" in draft["study_material"]["overview"]
