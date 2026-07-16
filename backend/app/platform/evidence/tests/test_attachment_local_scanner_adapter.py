"""Disabled local process scanner adapter skeleton tests (0053-F20)."""

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
from app.platform.evidence.attachment_local_scanner_adapter import (
    DISABLED_LOCAL_ADAPTER_NAME,
    DISABLED_LOCAL_ADAPTER_WARNING,
    DISABLED_LOCAL_SAFE_ERROR_CODE,
    DisabledLocalProcessScannerAdapter,
    disabled_local_scanner_adapter_summary,
)
from app.platform.evidence.attachment_scanner_adapter import (
    AttachmentScannerAdapter,
    NoopUnavailableScannerAdapter,
    ScannerAdapterName,
    get_configured_attachment_scanner_adapter,
)
from app.platform.evidence.attachment_scanner_policy import (
    DISABLED_LOCAL_SCANNER_ADAPTER_NAME,
    REAL_SCANNER_ENABLED,
    real_scanner_is_enabled,
    select_configured_scanner_adapter_name,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
LOCAL_ADAPTER = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_local_scanner_adapter.py"
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
POLICY = EVIDENCE_PKG / "attachment_scanner_policy.py"
ADAPTER_FACTORY = EVIDENCE_PKG / "attachment_scanner_adapter.py"


def test_disabled_local_adapter_exists_and_is_unavailable() -> None:
    assert LOCAL_ADAPTER.exists()
    adapter = DisabledLocalProcessScannerAdapter()
    assert isinstance(adapter, AttachmentScannerAdapter)
    info = adapter.adapter_info()
    assert info.name == DISABLED_LOCAL_ADAPTER_NAME
    assert info.name == ScannerAdapterName.LOCAL_PROCESS_DISABLED.value
    assert info.name == DISABLED_LOCAL_SCANNER_ADAPTER_NAME
    assert info.version == "0"
    assert info.availability is ScannerAvailability.UNAVAILABLE
    assert "disabled" in info.warning.lower()
    assert info.warning == DISABLED_LOCAL_ADAPTER_WARNING


def test_disabled_scan_result_is_not_run_and_maps_to_noop_plan() -> None:
    adapter = DisabledLocalProcessScannerAdapter()
    result = adapter.scan_attachment(
        evidence_id="ignored",
        content_hash="b" * 64,
        mime_type="application/pdf",
        size_bytes=99,
    )
    assert result.verdict is ScannerVerdict.NOT_RUN
    assert result.scanner_name == DISABLED_LOCAL_ADAPTER_NAME
    assert result.safe_error_code == DISABLED_LOCAL_SAFE_ERROR_CODE
    assert "disabled" in (result.safe_error_message or "").lower()
    assert result.verdict is not ScannerVerdict.CLEAN

    plan = build_scan_job_update_from_result(result)
    assert plan.action is ScanWorkerAction.NO_OP
    assert plan.apply_to_database is False
    assert plan.quarantine_required is False
    assert (
        plan.attachment_safety_status
        == AttachmentSafetyStatus.SCAN_NOT_AVAILABLE.value
    )


def test_disabled_adapter_does_not_require_path_or_bytes() -> None:
    result = DisabledLocalProcessScannerAdapter().scan_attachment()
    assert result.verdict is ScannerVerdict.NOT_RUN


def test_factory_still_returns_noop_not_disabled_local() -> None:
    assert REAL_SCANNER_ENABLED is False
    assert real_scanner_is_enabled() is False
    assert select_configured_scanner_adapter_name() == "noop_unavailable"
    active = get_configured_attachment_scanner_adapter()
    assert isinstance(active, NoopUnavailableScannerAdapter)
    assert not isinstance(active, DisabledLocalProcessScannerAdapter)


def test_local_adapter_source_has_no_subprocess_network_scanner_ocr_llm() -> None:
    source = LOCAL_ADAPTER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
    allowed = {
        "__future__",
        "app.platform.evidence.attachment_scan_worker",
        "app.platform.evidence.attachment_scanner_adapter",
        "app.platform.evidence.attachment_scanner_runtime_policy",
    }
    for mod in imports:
        assert mod in allowed, mod
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
        "popen",
        "sqlalchemy",
        "app.core.config",
        "os.environ",
        "getenv",
    ):
        assert forbidden not in blob, forbidden
    assert "ClamAVScannerAdapter" not in source
    assert "VirusTotalScannerAdapter" not in source


def test_summary_and_no_env_enable_toggle() -> None:
    summary = disabled_local_scanner_adapter_summary()
    assert summary["selected_by_factory"] is False
    assert summary["implementation_disabled"] is True
    assert summary["reads_file_bytes"] is False
    assert summary["calls_network_or_subprocess"] is False
    assert summary["is_verification"] is False
    policy_src = POLICY.read_text(encoding="utf-8")
    factory_src = ADAPTER_FACTORY.read_text(encoding="utf-8")
    assert "os.environ" not in policy_src
    assert "getenv" not in policy_src
    assert "app.core.config" not in policy_src
    assert "os.environ" not in factory_src
    assert "getenv" not in factory_src


def test_no_scan_routes_ui_or_f0012() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        if path.startswith("/api/v1/evidence"):
            assert "/scan" not in path.lower(), path
            assert "/share" not in path.lower()
            assert "/public" not in path.lower()
        assert not path.startswith("/api/v1/verification")
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
    migrations = (
        REPO_ROOT
        / "backend"
        / "app"
        / "db"
        / "foundation_migrations"
        / "versions"
    )
    assert list(migrations.glob("f0012*")) == []
