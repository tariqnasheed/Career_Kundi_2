"""
CareerKundi claim domain (0050-PF5-S1 / 0053-F1).

Public exports are ClaimRef, status-axis enums/parsers, F1 create contracts,
and safe display labels. Persistence/service live in sibling modules.
"""

from app.platform.claims.contracts import validate_claim_create_contract
from app.platform.claims.display import (
    claim_display_state,
    claim_truth_warning,
    support_status_label,
    verification_status_label,
)
from app.platform.claims.refs import ClaimRef, ClaimRefError
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

__all__ = [
    "ClaimKind",
    "ClaimOrigin",
    "ClaimRef",
    "ClaimRefError",
    "SupportStatus",
    "VerificationStatus",
    "claim_display_state",
    "claim_truth_warning",
    "parse_claim_kind",
    "parse_claim_origin",
    "parse_support_status",
    "parse_verification_status",
    "support_status_label",
    "validate_claim_create_contract",
    "verification_status_label",
]
