"""
CareerKundi verification / review contracts (0053-F9 / F10).

F9: review states, actors, transitions, safe labels.
F10: private review-request service (request/cancel only).
No approve/reject UI. No claim status mutation. Request ≠ verification.
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
from app.platform.verification.service import (
    cancel_review_request,
    create_review_request,
    get_review_request_for_owner,
    list_review_requests_for_owner,
)
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
    "cancel_review_request",
    "can_display_verified_label",
    "create_review_request",
    "get_review_request_for_owner",
    "list_review_requests_for_owner",
    "map_review_outcome_to_claim_verification_status",
    "parse_review_actor_type",
    "parse_review_state",
    "parse_reviewer_type",
    "review_state_help_text",
    "review_state_label",
    "validate_review_transition",
    "verification_policy_warning",
]
