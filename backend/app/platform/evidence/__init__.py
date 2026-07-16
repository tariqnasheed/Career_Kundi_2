"""
CareerKundi evidence domain (0053-F2).

Private evidence metadata + claim-evidence links. Not verification.
No public routes, upload/download, or Passport ownership in F2.
"""

from app.platform.evidence.contracts import (
    validate_claim_evidence_link_contract,
    validate_evidence_create_contract,
)
from app.platform.evidence.display import (
    claim_evidence_link_role_label,
    evidence_kind_label,
    evidence_privacy_label,
    evidence_truth_warning,
)
from app.platform.evidence.refs import EvidenceRef, EvidenceRefError
from app.platform.evidence.status import (
    ClaimEvidenceLinkRole,
    EvidenceKind,
    EvidencePrivacyClass,
    parse_claim_evidence_link_role,
    parse_evidence_kind,
    parse_evidence_privacy_class,
)

__all__ = [
    "ClaimEvidenceLinkRole",
    "EvidenceKind",
    "EvidencePrivacyClass",
    "EvidenceRef",
    "EvidenceRefError",
    "claim_evidence_link_role_label",
    "evidence_kind_label",
    "evidence_privacy_label",
    "evidence_truth_warning",
    "parse_claim_evidence_link_role",
    "parse_evidence_kind",
    "parse_evidence_privacy_class",
    "validate_claim_evidence_link_contract",
    "validate_evidence_create_contract",
]
