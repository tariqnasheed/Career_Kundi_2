"""Scanner adapter interface + no-op adapter tests (0053-F18)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app
from app.platform.evidence.attachment_safety import AttachmentSafetyStatus
from app.platform.evidence.attachment_scan_worker import (
    ScanWorkerAction,
    ScannerAvailability,
    ScannerVerdict,
    build_scan_job_update_from_result,
)
from app.platform.evidence.attachment_scanner_adapter import (
    NOOP_ADAPTER_NAME,
    NOOP_ADAPTER_WARNING,
    AttachmentScannerAdapter,
    NoopUnavailableScannerAdapter,
    ScannerAdapterCapability,
    ScannerAdapterName,
    configured_scanner_adapter_summary,
    get_configured_attachment_scanner_adapter,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
ADAPTER = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_scanner_adapter.py"
)
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"
FRONTEND_PAGES = [
    REPO_ROOT / "frontend" / "src" / "pages" / "EvidenceLibraryPage.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "passport"
    / "PassportEvidencePanel.tsx",
]


def test_factory_returns_noop_unavailable_adapter() -> None:
    adapter = get_configured_attachment_scanner_adapter()
    assert isinstance(adapter, NoopUnavailableScannerAdapter)
    assert isinstance(adapter, AttachmentScannerAdapter)
    info = adapter.adapter_info()
    assert info.name == NOOP_ADAPTER_NAME
    assert info.name == ScannerAdapterName.NOOP_UNAVAILABLE.value
    assert info.availability is ScannerAvailability.UNAVAILABLE
    assert info.capabilities == (ScannerAdapterCapability.UNAVAILABLE,)
    assert "not configured" in info.warning.lower()
    assert info.warning == NOOP_ADAPTER_WARNING


def test_noop_scan_result_is_not_run_and_maps_to_noop_plan() -> None:
    adapter = get_configured_attachment_scanner_adapter()
    result = adapter.scan_attachment(
        evidence_id="ignored",
        content_hash="a" * 64,
        mime_type="text/plain",
        size_bytes=12,
    )
    assert result.verdict is ScannerVerdict.NOT_RUN
    assert result.scanner_name == NOOP_ADAPTER_NAME
    assert result.scanner_version == "0"
    assert result.safe_error_code == "scanner_unavailable"
    assert "not configured" in (result.safe_error_message or "").lower()
    # Must not pretend to pass/fail/clean/safe.
    assert result.verdict is not ScannerVerdict.CLEAN

    plan = build_scan_job_update_from_result(result)
    assert plan.action is ScanWorkerAction.NO_OP
    assert plan.apply_to_database is False
    assert plan.quarantine_required is False
    assert plan.job_status is None
    assert (
        plan.attachment_safety_status
        == AttachmentSafetyStatus.SCAN_NOT_AVAILABLE.value
    )


def test_noop_does_not_require_real_file_path() -> None:
    adapter = NoopUnavailableScannerAdapter()
    # Call with no path-like arguments at all.
    result = adapter.scan_attachment()
    assert result.verdict is ScannerVerdict.NOT_RUN


def test_adapter_source_has_no_scanner_ocr_llm_file_io_or_network() -> None:
    source = ADAPTER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
    # Only stdlib/typing + F17 ScanResultContract + F19 policy seam.
    allowed_modules = {
        "__future__",
        "dataclasses",
        "enum",
        "typing",
        "app.platform.evidence.attachment_scan_worker",
        "app.platform.evidence.attachment_scanner_policy",
    }
    for mod in imports:
        assert mod in allowed_modules, mod
    blob = source.lower()
    for forbidden in (
        "clamav",
        "virustotal",
        "pyclamd",
        "pytesseract",
        "pdfplumber",
        "easyocr",
        "openai",
        "anthropic",
        "app.tools.llm",
        "import subprocess",
        "import urllib",
        "import httpx",
        "import requests",
        "import socket",
        "import pathlib",
        "import aiofiles",
        "open(",
        "read_bytes",
        "read_text",
        "sqlalchemy",
    ):
        assert forbidden not in blob, forbidden
    assert "app.platform.evidence.storage" not in imports
    assert "app.db.session" not in imports
    # Forbidden future class names must not appear yet.
    assert "ClamAVScannerAdapter" not in source
    assert "VirusTotalScannerAdapter" not in source
    assert "scan_file_with_clamav" not in source
    assert "scan_file_with_virustotal" not in source


def test_adapter_summary_is_safe() -> None:
    summary = configured_scanner_adapter_summary()
    assert summary["availability"] == "unavailable"
    assert summary["reads_file_bytes"] is False
    assert summary["calls_network_or_subprocess"] is False
    assert summary["applies_results_to_database"] is False
    blob = str(summary).lower()
    for phrase in (
        "safe file",
        "clean file",
        "trusted file",
        "verified document",
        "scan_passed",
    ):
        assert phrase not in blob


def test_no_scan_routes_or_ui() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        if path.startswith("/api/v1/evidence"):
            assert "/scan" not in path.lower(), path
        assert not path.startswith("/api/v1/verification")
        if path.startswith("/api/v1/evidence"):
            assert "/share" not in path.lower()
            assert "/public" not in path.lower()
    for page in FRONTEND_PAGES:
        text = page.read_text(encoding="utf-8").lower()
        for needle in (
            "scan now",
            "rescan",
            "mark safe",
            "mark clean",
            "quarantine",
            "verify file",
        ):
            assert needle not in text, f"{page}: {needle}"


def test_no_f0012_and_no_runtime_worker_modules() -> None:
    migrations = (
        REPO_ROOT
        / "backend"
        / "app"
        / "db"
        / "foundation_migrations"
        / "versions"
    )
    assert list(migrations.glob("f0012*")) == []
    assert (EVIDENCE_PKG / "attachment_scanner_adapter.py").exists()
    assert not (EVIDENCE_PKG / "clamav_adapter.py").exists()
    assert not (EVIDENCE_PKG / "virustotal_adapter.py").exists()
