"""Lifecycle ref unit tests."""

from __future__ import annotations

import pytest

from app.platform.kernel import new_entity_id
from app.platform.lifecycle import (
    AttemptRef,
    FeedbackRef,
    GoalRef,
    LifecycleRefError,
    OutcomeRef,
    RecommendationRef,
)


@pytest.mark.parametrize(
    ("cls", "field"),
    [
        (GoalRef, "goal_id"),
        (RecommendationRef, "recommendation_id"),
        (AttemptRef, "attempt_id"),
        (OutcomeRef, "outcome_id"),
        (FeedbackRef, "feedback_id"),
    ],
)
def test_lifecycle_ref_valid_immutable_malformed(cls, field: str) -> None:
    eid = new_entity_id()
    ref = cls(**{field: eid})
    assert getattr(ref, field) == eid
    with pytest.raises(AttributeError):
        setattr(ref, field, new_entity_id())
    with pytest.raises(LifecycleRefError):
        cls(**{field: "not-a-uuid"})
