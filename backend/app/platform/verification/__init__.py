"""
CareerKundi verification / review state-machine contracts (0053-F9).

Defines review states, actors, transitions, and safe labels only.
No DB models, migrations, API routes, or user-facing verification UI.
"""

from app.platform.verification.contracts import (
    ValidatedReviewTransition,
    assert_claim_verification_change_requires_review,
    assert_link_does_not_verify,
    assert_source_does_not_verify,
    assert_upload_does_not_verify,
    map_review_outcome_to_claim_verification_status,
    validate_review_transition,
)
from app.platform.verification.display import (
    can_display_verified_label,
    review_state_help_text,
    review_state_label,
    verification_policy_warning,
)
from app.platform.verification.refs import VerificationRefError
from app.platform.verification.status import (
    ReviewActorType,
    ReviewerType,
    ReviewState,
    parse_review_actor_type,
    parse_review_state,
    parse_reviewer_type,
)

__all__ = [
    "ReviewActorType",
    "ReviewState",
    "ReviewerType",
    "ValidatedReviewTransition",
    "VerificationRefError",
    "assert_claim_verification_change_requires_review",
    "assert_link_does_not_verify",
    "assert_source_does_not_verify",
    "assert_upload_does_not_verify",
    "can_display_verified_label",
    "map_review_outcome_to_claim_verification_status",
    "parse_review_actor_type",
    "parse_review_state",
    "parse_reviewer_type",
    "review_state_help_text",
    "review_state_label",
    "validate_review_transition",
    "verification_policy_warning",
]
