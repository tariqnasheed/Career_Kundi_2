"""
Safe evidence display labels (0053-F2).

Evidence linkage is not verification. No official/trusted/verified/public wording.
"""

from __future__ import annotations

from app.platform.evidence.refs import EvidenceRefError
from app.platform.evidence.status import (
    ClaimEvidenceLinkRole,
    EvidenceKind,
    EvidencePrivacyClass,
    parse_claim_evidence_link_role,
    parse_evidence_kind,
    parse_evidence_privacy_class,
)

_KIND_LABELS: dict[EvidenceKind, str] = {
    EvidenceKind.DOCUMENT: "Document material",
    EvidenceKind.CERTIFICATE: "Certificate material",
    EvidenceKind.TRANSCRIPT: "Transcript material",
    EvidenceKind.PORTFOLIO: "Portfolio material",
    EvidenceKind.ASSESSMENT: "Assessment material",
    EvidenceKind.REFERENCE: "Reference material",
    EvidenceKind.SOURCE_SNAPSHOT: "Source snapshot material",
    EvidenceKind.OTHER: "Other material",
}

_PRIVACY_LABELS: dict[EvidencePrivacyClass, str] = {
    EvidencePrivacyClass.PRIVATE: "Private",
    EvidencePrivacyClass.SENSITIVE: "Sensitive",
    EvidencePrivacyClass.RESTRICTED: "Restricted",
}

_LINK_ROLE_LABELS: dict[ClaimEvidenceLinkRole, str] = {
    ClaimEvidenceLinkRole.SUPPORTS: "Linked as support material",
    ClaimEvidenceLinkRole.CONTESTS: "Linked as contesting material",
    ClaimEvidenceLinkRole.CONTEXT: "Linked as context material",
}

FORBIDDEN_EVIDENCE_WORDING: frozenset[str] = frozenset(
    {
        "verified",
        "official",
        "trusted",
        "truth",
        "public credential",
        "wallet",
        "blockchain",
        "did",
        "proof of truth",
        "verified by careerkundi",
    }
)


def evidence_kind_label(value: object) -> str:
    return _KIND_LABELS[parse_evidence_kind(value)]


def evidence_privacy_label(value: object) -> str:
    return _PRIVACY_LABELS[parse_evidence_privacy_class(value)]


def claim_evidence_link_role_label(value: object) -> str:
    return _LINK_ROLE_LABELS[parse_claim_evidence_link_role(value)]


def evidence_truth_warning() -> str:
    return (
        "Evidence material linked to a claim is private metadata only. "
        "A link is not independent review and does not change verification status."
    )


def all_evidence_display_labels() -> list[str]:
    labels = (
        list(_KIND_LABELS.values())
        + list(_PRIVACY_LABELS.values())
        + list(_LINK_ROLE_LABELS.values())
        + [evidence_truth_warning()]
    )
    for label in labels:
        lowered = label.lower()
        for forbidden in FORBIDDEN_EVIDENCE_WORDING:
            if forbidden in lowered:
                raise EvidenceRefError(
                    f"unsafe evidence display wording {forbidden!r} in {label!r}"
                )
    return labels
