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

    # F16 adds scan-queue skeleton migration only; no later scanner migrations yet.
    f0011 = list(MIGRATIONS.glob("f0011*"))
    assert f0011 == [
        MIGRATIONS / "f0011_attachment_scan_queue.py"
    ], f0011
    for name in ("f0012", "f0013", "f0014"):
        matches = list(MIGRATIONS.glob(f"{name}*"))
        assert matches == [], matches

    # No quarantine storage module / runtime worker loop (F17 is policy/contract only)
    assert not (EVIDENCE_PKG / "quarantine.py").exists()
    assert not (EVIDENCE_PKG / "scan_worker.py").exists()
    assert (EVIDENCE_PKG / "attachment_quarantine_policy.py").exists()
    assert (EVIDENCE_PKG / "attachment_scan_worker.py").exists()
    # F18–F20: no-op + policy + disabled local skeleton; no real scanners.
    assert (EVIDENCE_PKG / "attachment_scanner_adapter.py").exists()
    assert (EVIDENCE_PKG / "attachment_scanner_policy.py").exists()
    assert (EVIDENCE_PKG / "attachment_local_scanner_adapter.py").exists()
    assert not (EVIDENCE_PKG / "clamav_adapter.py").exists()
    assert not (EVIDENCE_PKG / "virustotal_adapter.py").exists()
    local_src = (EVIDENCE_PKG / "attachment_local_scanner_adapter.py").read_text(
        encoding="utf-8"
    )
    assert "DisabledLocalProcessScannerAdapter" in local_src
    assert "local_scanner_disabled" in local_src
    assert "import subprocess" not in local_src
    assert "ClamAVScannerAdapter" not in local_src
    storage = (EVIDENCE_PKG / "storage.py").read_text(encoding="utf-8").lower()
    assert "quarantine" not in storage
    queue_src = (EVIDENCE_PKG / "attachment_scan_queue.py").read_text(encoding="utf-8")
    assert "clamav" not in queue_src.lower()
    assert "virustotal" not in queue_src.lower()
    worker_src = (EVIDENCE_PKG / "attachment_scan_worker.py").read_text(encoding="utf-8")
    assert "apply_to_database=False" in worker_src or "apply_to_database: bool = False" in worker_src
    assert "clamav" not in worker_src.lower()
    adapter_src = (EVIDENCE_PKG / "attachment_scanner_adapter.py").read_text(
        encoding="utf-8"
    )
    assert "NoopUnavailableScannerAdapter" in adapter_src
    assert "ClamAVScannerAdapter" not in adapter_src
    assert "VirusTotalScannerAdapter" not in adapter_src
