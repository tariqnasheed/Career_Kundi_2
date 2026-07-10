"""Lifecycle kind/status unit tests."""

from __future__ import annotations

import pytest

from app.platform.lifecycle import (
    AttemptKind,
    FeedbackKind,
    GoalKind,
    LifecycleRefError,
    LifecycleStatus,
    OutcomeKind,
    RecommendationKind,
    parse_attempt_kind,
    parse_feedback_kind,
    parse_goal_kind,
    parse_lifecycle_status,
    parse_outcome_kind,
    parse_recommendation_kind,
)

_PARSERS = [
    (GoalKind, parse_goal_kind),
    (RecommendationKind, parse_recommendation_kind),
    (AttemptKind, parse_attempt_kind),
    (OutcomeKind, parse_outcome_kind),
    (FeedbackKind, parse_feedback_kind),
    (LifecycleStatus, parse_lifecycle_status),
]


@pytest.mark.parametrize(("enum_cls", "parser"), _PARSERS)
def test_known_values_accepted(enum_cls, parser) -> None:
    for member in enum_cls:
        assert parser(member) is member
        assert parser(member.value) is member


@pytest.mark.parametrize(("enum_cls", "parser"), _PARSERS)
def test_empty_and_unknown_rejected(enum_cls, parser) -> None:
    with pytest.raises(LifecycleRefError):
        parser("")
    with pytest.raises(LifecycleRefError):
        parser("   ")
    with pytest.raises(LifecycleRefError):
        parser("not_a_real_value")


def test_no_silent_fallback_to_unknown_or_other() -> None:
    with pytest.raises(LifecycleRefError):
        parse_goal_kind("mystery")
    assert parse_goal_kind("unknown") is GoalKind.UNKNOWN
    assert parse_goal_kind("other") is GoalKind.OTHER
    with pytest.raises(LifecycleRefError):
        parse_recommendation_kind("mystery")
