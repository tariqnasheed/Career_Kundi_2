"""Attachment safety planning contracts (0053-F13). No scanner engine."""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app
from app.platform.evidence.attachment_safety import (
    ATTACHMENT_SAFETY_WARNING,
    DEFAULT_ATTACHMENT_SAFETY_STATUS,
    FORBIDDEN_ATTACHMENT_SAFETY_WORDING,
    AttachmentSafetyStatus,
    all_attachment_safety_labels,
    attachment_safety_fields,
    attachment_safety_label,
    attachment_safety_warning,
    current_attachment_safety_status,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"
ROUTES = REPO_ROOT / "backend" / "app" / "api" / "routes"
MIGRATIONS = (
    REPO_ROOT / "backend" / "app" / "db" / "foundation_migrations" / "versions"
)


def test_default_status_is_scan_not_available() -> None:
    assert current_attachment_safety_status() is AttachmentSafetyStatus.SCAN_NOT_AVAILABLE
    assert DEFAULT_ATTACHMENT_SAFETY_STATUS.value == "scan_not_available"
    fields = attachment_safety_fields()
    assert fields["attachment_safety_status"] == "scan_not_available"
    assert fields["attachment_safety_label"] == "Scan not available"
    assert fields["attachment_safety_warning"] == ATTACHMENT_SAFETY_WARNING


def test_warning_covers_not_scanned_parsed_reviewed_verified() -> None:
    warning = attachment_safety_warning().lower()
    assert "not malware-scanned" in warning
    assert "parsed" in warning
    assert "reviewed" in warning
    assert "verified" in warning
    assert "not" in warning


def test_labels_forbid_unsafe_trust_wording() -> None:
    blob = " ".join(all_attachment_safety_labels() + [attachment_safety_warning()]).lower()
    for forbidden in FORBIDDEN_ATTACHMENT_SAFETY_WORDING:
        assert forbidden not in blob
    # "verified" only as negation in warning
    assert "not" in blob and "verified" in blob
    assert "verified document" not in blob
    assert attachment_safety_label(AttachmentSafetyStatus.SCAN_PASSED) == "Scan passed"


def test_no_scan_parse_ocr_ai_review_or_approve_routes() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        lower = path.lower()
        if not path.startswith("/api/v1/evidence"):
            continue
        for needle in (
            "/scan",
            "/parse",
            "/ocr",
            "/ai-review",
            "/approve",
            "/reject",
            "/conflict",
        ):
            assert needle not in lower, path
    for path in paths:
        lower = path.lower()
        if not path.startswith("/api/v1/"):
            continue
        for needle in ("/approve", "/reject", "/conflict", "/ai-review"):
            if path.startswith("/api/v1/job-search"):
                continue
            assert needle not in lower or "/cancel" in lower, path
    assert "/api/v1/evidence/{evidence_id}/attachment" in paths
    assert "/api/v1/evidence/{evidence_id}/scan" not in paths
    assert "/api/v1/evidence/{evidence_id}/parse" not in paths
    assert "/api/v1/evidence/{evidence_id}/ocr" not in paths
    assert not (ROUTES / "verification.py").exists()


def test_no_scanner_ocr_llm_imports_or_migrations() -> None:
    forbidden_mod_hints = (
        "clamav",
        "pyclamd",
        "virustotal",
        "pytesseract",
        "pdfplumber",
        "easyocr",
        "openai",
        "anthropic",
        "app.tools.llm",
    )
    for path in EVIDENCE_PKG.rglob("*.py"):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").lower()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                for hint in forbidden_mod_hints:
                    assert hint not in mod, f"{path}: {mod}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.lower()
                    for hint in forbidden_mod_hints:
                        assert hint not in name, path
        # Skip forbidden-wording constant lists (they document banned terms).
        if "forbidden" in text and "wallet" in text:
            continue
        for hint in ("clamav", "virustotal", "pytesseract"):
            assert hint not in text, f"{path}: {hint}"

    for name in ("f0011", "f0012", "f0013"):
        matches = list(MIGRATIONS.glob(f"{name}*"))
        assert matches == [], matches

    # No quarantine storage module
    assert not (EVIDENCE_PKG / "quarantine.py").exists()
    storage = (EVIDENCE_PKG / "storage.py").read_text(encoding="utf-8").lower()
    assert "quarantine" not in storage
