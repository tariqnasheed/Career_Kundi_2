"""Pure contract validators for 0053-F2 evidence domain."""

from __future__ import annotations

import uuid

import pytest

from app.platform.evidence.contracts import (
    validate_claim_evidence_link_contract,
    validate_evidence_create_contract,
    validate_evidence_source_snapshot_contract,
)
from app.platform.evidence.display import (
    all_evidence_display_labels,
    evidence_kind_label,
    evidence_privacy_label,
    evidence_truth_warning,
)
from app.platform.evidence.refs import EvidenceRefError
from app.platform.evidence.status import (
    ClaimEvidenceLinkRole,
    EvidenceKind,
    EvidencePrivacyClass,
)


def test_create_rejects_empty_title() -> None:
    with pytest.raises(EvidenceRefError, match="title must not be empty"):
        validate_evidence_create_contract(title="  ", evidence_kind=EvidenceKind.DOCUMENT)


def test_create_rejects_unknown_kind() -> None:
    with pytest.raises(EvidenceRefError, match="unknown evidence_kind"):
        validate_evidence_create_contract(title="Doc", evidence_kind="not_a_kind")


def test_create_rejects_public_and_shared_privacy() -> None:
    with pytest.raises(EvidenceRefError, match="rejected"):
        validate_evidence_create_contract(
            title="Doc",
            evidence_kind=EvidenceKind.DOCUMENT,
            privacy_class="public",
        )
    with pytest.raises(EvidenceRefError, match="rejected"):
        validate_evidence_create_contract(
            title="Doc",
            evidence_kind=EvidenceKind.DOCUMENT,
            privacy_class="shared",
        )


def test_create_defaults_privacy_private() -> None:
    validated = validate_evidence_create_contract(
        title=" Certificate ",
        evidence_kind=EvidenceKind.CERTIFICATE,
    )
    assert validated.title == "Certificate"
    assert validated.privacy_class == EvidencePrivacyClass.PRIVATE


def test_snapshot_requires_source() -> None:
    with pytest.raises(EvidenceRefError, match="snapshot_id requires source_id"):
        validate_evidence_source_snapshot_contract(
            source_id=None, snapshot_id=uuid.uuid4()
        )
    with pytest.raises(EvidenceRefError, match="snapshot_id requires source_id"):
        validate_evidence_create_contract(
            title="Doc",
            evidence_kind=EvidenceKind.DOCUMENT,
            snapshot_id=uuid.uuid4(),
        )


def test_link_rejects_unknown_role() -> None:
    with pytest.raises(EvidenceRefError, match="unknown link_role"):
        validate_claim_evidence_link_contract(
            claim_id=uuid.uuid4(),
            evidence_id=uuid.uuid4(),
            link_role="proves_truth",
        )


def test_link_accepts_known_roles() -> None:
    for role in ClaimEvidenceLinkRole:
        validated = validate_claim_evidence_link_contract(
            claim_id=uuid.uuid4(),
            evidence_id=uuid.uuid4(),
            link_role=role,
        )
        assert validated.link_role == role


def test_display_labels_have_no_forbidden_trust_wording() -> None:
    labels = all_evidence_display_labels()
    joined = " ".join(labels).lower()
    for forbidden in (
        "verified",
        "official",
        "trusted",
        "truth",
        "wallet",
        "blockchain",
        "did",
        "public credential",
    ):
        assert forbidden not in joined
    assert "document material" in evidence_kind_label(EvidenceKind.DOCUMENT).lower()
    assert evidence_privacy_label(EvidencePrivacyClass.PRIVATE) == "Private"
    assert "not independent review" in evidence_truth_warning().lower()
