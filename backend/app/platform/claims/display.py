"""
0053-F1 safe display-language mapping for claim status axes.

Domain-only labels for future UI. Never maps support status to "verified".
Does not own Passport, frontend, or verification workflows.
"""

from __future__ import annotations

from typing import Any

from app.platform.claims.refs import ClaimRefError
from app.platform.claims.status import (
    SupportStatus,
    VerificationStatus,
    parse_support_status,
    parse_verification_status,
)

_FORBIDDEN_SUPPORT_LABEL_TERMS = (
    "official",
    "truth",
    "trusted",
    "verified",
    "proof of truth",
    "verified by careerkundi",
    "public credential",
    "wallet",
    "blockchain",
    "did",
)

_SUPPORT_LABELS: dict[SupportStatus, str] = {
    SupportStatus.NOT_PROVIDED: "Not supported yet",
    SupportStatus.PROFILE_SUPPORTED: "Profile-backed",
    SupportStatus.SOURCE_LINKED: "Source-linked",
    SupportStatus.EVIDENCE_BACKED: "Evidence-linked",
    SupportStatus.ASSESSMENT_DEMONSTRATED: "Assessment demonstrated",
    SupportStatus.UNKNOWN: "Unknown",
}

_VERIFICATION_LABELS: dict[VerificationStatus, str] = {
    VerificationStatus.UNVERIFIED: "Not independently verified",
    VerificationStatus.VERIFIED: "Verified",
    VerificationStatus.REJECTED: "Rejected",
    VerificationStatus.CONFLICTING: "Conflicting information",
    VerificationStatus.UNKNOWN: "Unknown",
}


def support_status_label(value: object) -> str:
    status = parse_support_status(value)
    label = _SUPPORT_LABELS[status]
    _assert_safe_support_label(label)
    return label


def verification_status_label(value: object) -> str:
    status = parse_verification_status(value)
    return _VERIFICATION_LABELS[status]


def claim_truth_warning(row_or_statuses: object = None) -> str:
    """
    Always-true F1 warning: provenance/support is not independent verification.
    """
    _ = row_or_statuses  # reserved for future richer context
    return (
        "A source or snapshot link is not verification. "
        "This claim is private and not independently verified."
    )


def claim_display_state(
    *,
    support_status: object,
    verification_status: object,
    source_id: object | None = None,
    snapshot_id: object | None = None,
) -> dict[str, Any]:
    """Structured safe display payload for future UI (not an HTTP contract)."""
    support = parse_support_status(support_status)
    verification = parse_verification_status(verification_status)
    return {
        "support_status": support.value,
        "support_label": support_status_label(support),
        "verification_status": verification.value,
        "verification_label": verification_status_label(verification),
        "has_source_link": source_id is not None,
        "has_snapshot_link": snapshot_id is not None,
        "truth_warning": claim_truth_warning(),
        "is_independently_verified": verification == VerificationStatus.VERIFIED,
    }


def _assert_safe_support_label(label: str) -> None:
    lowered = label.lower()
    for term in _FORBIDDEN_SUPPORT_LABEL_TERMS:
        if term in lowered:
            raise ClaimRefError(
                f"unsafe support-status display wording contains {term!r}: {label!r}"
            )


def forbidden_support_label_terms() -> tuple[str, ...]:
    """Exported for tests — terms that must never appear in support labels."""
    return _FORBIDDEN_SUPPORT_LABEL_TERMS
