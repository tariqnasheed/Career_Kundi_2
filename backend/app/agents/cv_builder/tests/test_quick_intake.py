"""CORE-VALUE-R1: Quick CV intake — honest starter, no Profile/Passport mutation."""

from __future__ import annotations

import pytest

from app.agents.cv_builder.mock_data import (
    build_profile_snapshot_from_manual_input,
    mock_generate_quick_intake_cv,
)
from app.agents.cv_builder.render import render_cv
from app.schemas.cv_builder import CVGenerateRequest, ManualProfileInput


def test_manual_snapshot_minimum_fields_no_fake_employers():
    snap = build_profile_snapshot_from_manual_input(
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone=None,
        location=None,
        target_role="AI Engineer",
        career_level="beginner",
        summary_context=None,
        skills_text=None,
        experience_text=None,
        education_text=None,
        projects_text=None,
    )
    assert snap["full_name"] == "Ada Lovelace"
    companies = [w["company_name"] for w in snap["work_experiences"]]
    assert all("Add your" in c for c in companies)
    assert not any(
        fake in " ".join(companies).lower()
        for fake in ("google", "meta", "amazon", "previous organization", "acme")
    )
    assert snap["certifications"] == []
    institutions = [e["institution"] for e in snap["educations"]]
    assert all("Add your" in i for i in institutions)


def test_quick_intake_draft_and_render():
    snap = build_profile_snapshot_from_manual_input(
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone=None,
        location="London",
        target_role="Software Engineer",
        career_level="beginner",
        summary_context="Learning systems design",
        skills_text="Python, Git",
        experience_text=None,
        education_text=None,
        projects_text=None,
    )
    sections = ["summary", "experience", "education", "skills"]
    draft = mock_generate_quick_intake_cv(
        snap, sections, "concise", "Software Engineer", "beginner"
    )
    assert draft["generation_mode"] == "quick_intake"
    assert draft["needs_manual_input"] is True
    assert "placeholder" in (draft.get("manual_input_reason") or "").lower() or "Add your" in draft[
        "manual_input_reason"
    ]
    rendered = render_cv(
        profile=snap,
        target_job=None,
        draft=draft,
        section_ids=sections,
        template="modern",
        tone="concise",
        citations=[],
        confidence_score=0.5,
    )
    assert rendered["personal_info"]["full_name"] == "Ada Lovelace"
    assert rendered["meta"]["generation_mode"] == "quick_intake"
    assert not any(s.get("section_id") == "certifications" for s in rendered["sections"])
    blob = str(rendered).lower()
    assert "google" not in blob
    assert "stanford" not in blob
    assert "aws certified" not in blob


def test_cv_generate_request_requires_manual_for_quick_intake():
    with pytest.raises(Exception):
        CVGenerateRequest(generation_mode="quick_intake")

    req = CVGenerateRequest(
        generation_mode="quick_intake",
        manual_profile_input=ManualProfileInput(
            full_name="Ada",
            target_role="AI Engineer",
            career_level="beginner",
        ),
    )
    assert req.generation_mode == "quick_intake"
    assert req.manual_profile_input.target_role == "AI Engineer"


def test_quick_intake_pipeline_does_not_need_profile_orm(monkeypatch):
    import asyncio

    from app.agents.cv_builder.graph import run_cv_generation_pipeline
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "mock")
    snap = build_profile_snapshot_from_manual_input(
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone=None,
        location=None,
        target_role="AI Engineer",
        career_level="beginner",
        summary_context=None,
        skills_text="Python",
        experience_text=None,
        education_text=None,
        projects_text=None,
    )
    result = asyncio.run(
        run_cv_generation_pipeline(
            user_id="00000000-0000-0000-0000-000000000001",
            profile_snapshot=snap,
            generation_mode="quick_intake",
            target_role_title="AI Engineer",
            career_level="beginner",
        )
    )
    draft = result["state"]["draft_output"]
    assert draft.get("professional_summary")
    assert draft.get("generation_mode") == "quick_intake"
    assert "placeholder" in str(draft.get("enhanced_work_experiences")).lower()
    assert draft.get("needs_manual_input") is True