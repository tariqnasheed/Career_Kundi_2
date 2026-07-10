"""
CareerKundi lifecycle domain (0050-PF7-S1).

Public exports are refs and kind/status enums/parsers.
Persistence/service live in sibling modules and db models.
"""

from app.platform.lifecycle.kinds import (
    AttemptKind,
    FeedbackKind,
    GoalKind,
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
from app.platform.lifecycle.refs import (
    AttemptRef,
    FeedbackRef,
    GoalRef,
    LifecycleRefError,
    OutcomeRef,
    RecommendationRef,
)

__all__ = [
    "AttemptKind",
    "AttemptRef",
    "FeedbackKind",
    "FeedbackRef",
    "GoalKind",
    "GoalRef",
    "LifecycleRefError",
    "LifecycleStatus",
    "OutcomeKind",
    "OutcomeRef",
    "RecommendationKind",
    "RecommendationRef",
    "parse_attempt_kind",
    "parse_feedback_kind",
    "parse_goal_kind",
    "parse_lifecycle_status",
    "parse_outcome_kind",
    "parse_recommendation_kind",
]
