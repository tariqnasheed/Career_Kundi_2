"""0053-F1 create-time contract boundary tests (no evidence / verification / API)."""

from __future__ import annotations

import ast
import uuid
from pathlib import Path

import pytest

from app.platform.claims import ClaimKind, ClaimOrigin, ClaimRefError, SupportStatus, VerificationStatus
from app.platform.claims.contracts import (
    ALLOWED_CREATE_SUPPORT,
    ALLOWED_CREATE_VERIFICATION,
    validate_claim_create_contract,
    validate_claim_support_status_for_create,
    validate_claim_verification_status_for_create,
)

CLAIMS_ROOT = Path(__file__).resolve().parents[1]
API_ROUTES = Path(__file__).resolve().parents[3] / "api" / "routes"


@pytest.mark.parametrize(
    "status",
    [
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.CONFLICTING,
        VerificationStatus.UNKNOWN,
        "verified",
        "rejected",
        "conflicting",
        "unknown",
    ],
)
def test_create_rejects_non_unverified_verification(status: object) -> None:
    with pytest.raises(ClaimRefError, match="unverified"):
        validate_claim_verification_status_for_create(status)


@pytest.mark.parametrize(
    "status",
    [
        SupportStatus.EVIDENCE_BACKED,
        SupportStatus.ASSESSMENT_DEMONSTRATED,
        SupportStatus.UNKNOWN,
        "evidence_backed",
        "assessment_demonstrated",
        "unknown",
    ],
)
def test_create_rejects_disallowed_support(status: object) -> None:
    with pytest.raises(ClaimRefError, match="disallows support_status"):
        validate_claim_support_status_for_create(status)


def test_source_linked_requires_source_id() -> None:
    with pytest.raises(ClaimRefError, match="source_linked requires source_id"):
        validate_claim_create_contract(
            claim_kind=ClaimKind.SKILL,
            claim_origin=ClaimOrigin.USER_ASSERTED,
            support_status=SupportStatus.SOURCE_LINKED,
            verification_status=VerificationStatus.UNVERIFIED,
            source_id=None,
            snapshot_id=None,
        )


def test_snapshot_requires_source_id() -> None:
    with pytest.raises(ClaimRefError, match="snapshot_id requires source_id"):
        validate_claim_create_contract(
            claim_kind=ClaimKind.SKILL,
            claim_origin=ClaimOrigin.USER_ASSERTED,
            support_status=SupportStatus.PROFILE_SUPPORTED,
            verification_status=VerificationStatus.UNVERIFIED,
            source_id=None,
            snapshot_id=uuid.uuid4(),
        )


def test_source_linked_create_remains_unverified() -> None:
    source_id = uuid.uuid4()
    validated = validate_claim_create_contract(
        claim_kind=ClaimKind.EXPERIENCE,
        claim_origin=ClaimOrigin.DOCUMENT_EXTRACTED,
        support_status=SupportStatus.SOURCE_LINKED,
        verification_status=VerificationStatus.UNVERIFIED,
        source_id=source_id,
        snapshot_id=None,
    )
    assert validated.verification_status is VerificationStatus.UNVERIFIED
    assert validated.support_status is SupportStatus.SOURCE_LINKED
    assert validated.source_id == source_id


def test_snapshot_linked_create_remains_unverified() -> None:
    source_id = uuid.uuid4()
    snapshot_id = uuid.uuid4()
    validated = validate_claim_create_contract(
        claim_kind=ClaimKind.EDUCATION,
        claim_origin=ClaimOrigin.EXTERNAL_IMPORTED,
        support_status=SupportStatus.SOURCE_LINKED,
        verification_status=VerificationStatus.UNVERIFIED,
        source_id=source_id,
        snapshot_id=snapshot_id,
    )
    assert validated.verification_status is VerificationStatus.UNVERIFIED
    assert validated.snapshot_id == snapshot_id


def test_verified_with_source_still_rejected() -> None:
    with pytest.raises(ClaimRefError, match="unverified"):
        validate_claim_create_contract(
            claim_kind=ClaimKind.SKILL,
            claim_origin=ClaimOrigin.USER_ASSERTED,
            support_status=SupportStatus.SOURCE_LINKED,
            verification_status=VerificationStatus.VERIFIED,
            source_id=uuid.uuid4(),
        )


def test_evidence_backed_with_source_still_rejected() -> None:
    with pytest.raises(ClaimRefError, match="disallows support_status"):
        validate_claim_create_contract(
            claim_kind=ClaimKind.SKILL,
            claim_origin=ClaimOrigin.USER_ASSERTED,
            support_status=SupportStatus.EVIDENCE_BACKED,
            verification_status=VerificationStatus.UNVERIFIED,
            source_id=uuid.uuid4(),
        )


def test_allowlists_match_f1_decisions() -> None:
    assert ALLOWED_CREATE_VERIFICATION == {VerificationStatus.UNVERIFIED}
    assert ALLOWED_CREATE_SUPPORT == {
        SupportStatus.NOT_PROVIDED,
        SupportStatus.PROFILE_SUPPORTED,
        SupportStatus.SOURCE_LINKED,
    }


def test_claims_module_imports_no_feature_domains() -> None:
    forbidden_prefixes = (
        "app.career_passport",
        "app.agents.cv_builder",
        "app.agents.roadmap",
        "app.agents.job_search",
        "app.api.routes.passport",
        "app.api.routes.cv_builder",
        "app.api.routes.roadmap",
        "app.api.routes.job_search",
    )
    for path in CLAIMS_ROOT.rglob("*.py"):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in forbidden_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{path} imports {node.module}"
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_prefixes:
                        assert not alias.name.startswith(prefix), (
                            f"{path} imports {alias.name}"
                        )


def test_no_claims_api_route_file() -> None:
    assert not (API_ROUTES / "claims.py").exists()
    for path in API_ROUTES.glob("*claim*"):
        raise AssertionError(f"unexpected claims route file: {path}")


def test_no_evidence_or_verification_modules_in_claims_package() -> None:
    names = {p.name for p in CLAIMS_ROOT.iterdir()}
    assert "evidence.py" not in names
    assert "verification.py" not in names
    assert not (CLAIMS_ROOT / "evidence").exists()
    for path in CLAIMS_ROOT.rglob("*.py"):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        assert "class EvidenceRecord" not in text
        assert "ClaimEvidenceLink" not in text
        assert "VerificationReview" not in text
