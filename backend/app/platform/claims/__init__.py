"""
CareerKundi claim domain (0050-PF5-S1).

Public exports are ClaimRef and status-axis enums/parsers.
Persistence/service live in sibling modules and db models.
"""

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
    "parse_claim_kind",
    "parse_claim_origin",
    "parse_support_status",
    "parse_verification_status",
]
