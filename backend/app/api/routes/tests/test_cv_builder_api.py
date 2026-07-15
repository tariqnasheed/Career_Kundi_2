"""CORE-VALUE-R1: CV Builder API schema + quick_intake contract smoke."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.cv_builder import CVGenerateRequest, ManualProfileInput


def test_profile_mode_still_valid_without_manual():
    req = CVGenerateRequest(generation_mode="profile", tone="concise")
    assert req.generation_mode == "profile"
    assert req.manual_profile_input is None


def test_quick_intake_requires_manual_and_role():
    with pytest.raises(ValidationError):
        CVGenerateRequest(generation_mode="quick_intake")

    with pytest.raises(ValidationError):
        CVGenerateRequest(
            generation_mode="quick_intake",
            manual_profile_input=ManualProfileInput(
                target_role="   ",
                career_level="beginner",
            ),
        )

    req = CVGenerateRequest(
        generation_mode="quick_intake",
        manual_profile_input=ManualProfileInput(
            full_name="Ada",
            target_role="Backend Engineer",
            career_level="intermediate",
            skills_text="Python, SQL",
        ),
    )
    assert req.manual_profile_input.career_level == "intermediate"


def test_career_level_enum():
    with pytest.raises(ValidationError):
        ManualProfileInput(target_role="X", career_level="novice")  # type: ignore[arg-type]
