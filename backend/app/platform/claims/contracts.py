"""
0053-F1 Claim Service create-time contract validators.

Pure domain validation — no FastAPI, SQLAlchemy models, Passport, or feature
domains. Existence checks for subject/source/snapshot stay in service.py.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.platform.claims.refs import ClaimRefError
from app.platform.claims.status import (
    ClaimKind,
    ClaimOrigin,
    SupportStatus,
    VerificationStatus,
    parse_claim_kind,
    parse_claim_origin,
    parse_support_status,
    parse_verification_status,
)

# F1 create-time allowlists (before evidence / verification workflows exist).
ALLOWED_CREATE_VERIFICATION: frozenset[VerificationStatus] = frozenset(
    {VerificationStatus.UNVERIFIED}
)

ALLOWED_CREATE_SUPPORT: frozenset[SupportStatus] = frozenset(
    {
        SupportStatus.NOT_PROVIDED,
        SupportStatus.PROFILE_SUPPORTED,
        SupportStatus.SOURCE_LINKED,
    }
)

DISALLOWED_CREATE_VERIFICATION: frozenset[VerificationStatus] = frozenset(
    {
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.CONFLICTING,
        VerificationStatus.UNKNOWN,
    }
)

DISALLOWED_CREATE_SUPPORT: frozenset[SupportStatus] = frozenset(
    {
        SupportStatus.EVIDENCE_BACKED,
        SupportStatus.ASSESSMENT_DEMONSTRATED,
        SupportStatus.UNKNOWN,
    }
)


@dataclass(frozen=True, slots=True)
class ValidatedClaimCreate:
    """Parsed create-time enums after F1 contract checks pass."""

    claim_kind: ClaimKind
    claim_origin: ClaimOrigin
    support_status: SupportStatus
    verification_status: VerificationStatus
    source_id: uuid.UUID | None
    snapshot_id: uuid.UUID | None


def validate_claim_verification_status_for_create(
    verification_status: object,
) -> VerificationStatus:
    verification = parse_verification_status(verification_status)
    if verification not in ALLOWED_CREATE_VERIFICATION:
        raise ClaimRefError(
            "F1 create_claim allows only verification_status=unverified; "
            f"got {verification.value!r}. Verification workflows are not implemented yet."
        )
    return verification


def validate_claim_support_status_for_create(
    support_status: object,
) -> SupportStatus:
    support = parse_support_status(support_status)
    if support not in ALLOWED_CREATE_SUPPORT:
        raise ClaimRefError(
            "F1 create_claim disallows support_status="
            f"{support.value!r}. Evidence-backed / assessment / unknown support "
            "requires evidence or assessment modules that do not exist yet."
        )
    return support


def validate_source_snapshot_contract(
    *,
    support_status: SupportStatus,
    source_id: uuid.UUID | None,
    snapshot_id: uuid.UUID | None,
) -> None:
    """Structural source/snapshot rules (DB existence checked in service)."""
    if snapshot_id is not None and source_id is None:
        raise ClaimRefError("snapshot_id requires source_id")

    if support_status == SupportStatus.SOURCE_LINKED and source_id is None:
        raise ClaimRefError(
            "support_status=source_linked requires source_id "
            "(a source/snapshot link is provenance, not verification)"
        )

    if source_id is None and snapshot_id is None:
        if support_status == SupportStatus.SOURCE_LINKED:
            raise ClaimRefError(
                "support_status=source_linked is invalid without source_id"
            )


def assert_no_claim_truth_upgrade(
    *,
    support_status: SupportStatus,
    verification_status: VerificationStatus,
    source_id: uuid.UUID | None,
    snapshot_id: uuid.UUID | None,
) -> None:
    """
    Refuse create-time combinations that would silently look like truth upgrades.

    Source/snapshot linkage must never imply verified or evidence-backed.
    """
    if verification_status != VerificationStatus.UNVERIFIED:
        raise ClaimRefError(
            "create_claim cannot set verification_status other than unverified"
        )

    if support_status in DISALLOWED_CREATE_SUPPORT:
        raise ClaimRefError(
            f"create_claim cannot set support_status={support_status.value!r}"
        )

    if source_id is not None or snapshot_id is not None:
        if verification_status != VerificationStatus.UNVERIFIED:
            raise ClaimRefError(
                "source/snapshot-linked claims must remain verification_status=unverified"
            )
        if support_status == SupportStatus.EVIDENCE_BACKED:
            raise ClaimRefError(
                "source/snapshot linkage must not upgrade support_status to evidence_backed"
            )


def validate_claim_create_contract(
    *,
    claim_kind: object,
    claim_origin: object,
    support_status: object,
    verification_status: object,
    source_id: uuid.UUID | None = None,
    snapshot_id: uuid.UUID | None = None,
) -> ValidatedClaimCreate:
    """
    Full F1 create-time contract. Raises ClaimRefError; never silently corrects.
    """
    kind = parse_claim_kind(claim_kind)
    origin = parse_claim_origin(claim_origin)
    support = validate_claim_support_status_for_create(support_status)
    verification = validate_claim_verification_status_for_create(verification_status)

    validate_source_snapshot_contract(
        support_status=support,
        source_id=source_id,
        snapshot_id=snapshot_id,
    )
    assert_no_claim_truth_upgrade(
        support_status=support,
        verification_status=verification,
        source_id=source_id,
        snapshot_id=snapshot_id,
    )

    return ValidatedClaimCreate(
        claim_kind=kind,
        claim_origin=origin,
        support_status=support,
        verification_status=verification,
        source_id=source_id,
        snapshot_id=snapshot_id,
    )
