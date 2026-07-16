"""F10 review requests must not grant verification power."""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app
from app.platform.verification.contracts import (
    map_review_outcome_to_claim_verification_status,
)
from app.platform.verification.status import ReviewState

REPO_ROOT = Path(__file__).resolve().parents[5]
BACKEND = REPO_ROOT / "backend"
VERIFICATION_PKG = BACKEND / "app" / "platform" / "verification"
ROUTES = BACKEND / "app" / "api" / "routes"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"


def _py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def test_no_approve_reject_conflict_endpoints() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        lower = path.lower()
        if not path.startswith("/api/v1/"):
            continue
        for needle in ("/approve", "/reject", "/conflict", "/under-review", "/verify"):
            assert needle not in lower, path
    assert "/api/v1/review-requests" in paths
    assert "/api/v1/review-requests/{request_id}/cancel" in paths


def test_service_does_not_create_terminal_review_states() -> None:
    service = (VERIFICATION_PKG / "service.py").read_text(encoding="utf-8")
    assert "ReviewState.APPROVED" not in service
    assert "ReviewState.REJECTED" not in service
    assert "ReviewState.CONFLICTED" not in service
    assert "ReviewState.UNDER_REVIEW" not in service
    assert "support_status =" not in service
    assert "verification_status =" not in service
    assert ReviewState.REQUESTED.value == "requested"


def test_routes_do_not_call_outcome_mapping() -> None:
    for path in _py_files(ROUTES):
        text = path.read_text(encoding="utf-8")
        assert "map_review_outcome_to_claim_verification_status" not in text
    assert map_review_outcome_to_claim_verification_status("approved") is not None


def test_no_frontend_verify_or_approve_surfaces() -> None:
    if not FRONTEND_SRC.exists():
        return
    # F11/F12 may have Passport request/cancel UI; still no verify/approve surfaces.
    unexpected = []
    for path in FRONTEND_SRC.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        name = path.name.lower()
        if "verify" in name and "test" not in name:
            unexpected.append(rel)
        if "approve" in name or "rejectreview" in name.replace("_", "").replace(
            "-", ""
        ):
            unexpected.append(rel)
    assert unexpected == []
    panel = FRONTEND_SRC / "features" / "passport" / "PassportEvidencePanel.tsx"
    if panel.exists():
        text = panel.read_text(encoding="utf-8")
        assert "Verify claim" not in text
        assert "Approve" not in text
        assert "Reject" not in text


def test_no_llm_or_ocr_in_f10_service_and_routes() -> None:
    targets = [
        VERIFICATION_PKG / "service.py",
        ROUTES / "review_requests.py",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8").lower()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("app.tools.llm"), path
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("app.tools.llm"), path
        for hint in (
            "pytesseract",
            "pdfplumber",
            "easyocr",
            "wallet",
            "blockchain",
            "openai",
            "anthropic",
        ):
            assert hint not in text, f"{path}: {hint}"
