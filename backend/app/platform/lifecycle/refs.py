"""
Lifecycle loop reference value objects (0050-PF7-S1).

Pure Python — Goal → Recommendation → Attempt → Outcome → Feedback refs.
No workflow, scoring, or agent semantics embedded.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.platform.kernel.ids import (
    CanonicalEntityId,
    EntityIdError,
    parse_entity_id,
)


class LifecycleRefError(ValueError):
    """Invalid lifecycle ref / kind / status input."""


@dataclass(frozen=True, slots=True)
class GoalRef:
    goal_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "goal_id", parse_entity_id(self.goal_id))
        except EntityIdError as exc:
            raise LifecycleRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class RecommendationRef:
    recommendation_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(
                self, "recommendation_id", parse_entity_id(self.recommendation_id)
            )
        except EntityIdError as exc:
            raise LifecycleRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class AttemptRef:
    attempt_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "attempt_id", parse_entity_id(self.attempt_id))
        except EntityIdError as exc:
            raise LifecycleRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class OutcomeRef:
    outcome_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "outcome_id", parse_entity_id(self.outcome_id))
        except EntityIdError as exc:
            raise LifecycleRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class FeedbackRef:
    feedback_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "feedback_id", parse_entity_id(self.feedback_id))
        except EntityIdError as exc:
            raise LifecycleRefError(str(exc)) from exc
