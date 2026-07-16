"""Local scanner runtime safety contract tests (0053-F21)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app
from app.platform.evidence.attachment_local_scanner_adapter import (
    DisabledLocalProcessScannerAdapter,
)
from app.platform.evidence.attachment_scanner_adapter import (
    NoopUnavailableScannerAdapter,
    get_configured_attachment_scanner_adapter,
)
from app.platform.evidence.attachment_scanner_policy import (
    REAL_SCANNER_ENABLED,
    real_scanner_is_enabled,
)
from app.platform.evidence.attachment_scanner_runtime_policy import (
    ALLOW_FILE_PARSING_FOR_SCAN,
    ALLOW_LLM_REVIEW_FOR_SCAN,
    ALLOW_NETWORK_SCANNER,
    ALLOW_OCR_FOR_SCAN,
    ALLOW_RAW_SCANNER_OUTPUT_TO_USER,
    ALLOW_SHELL_EXECUTION,
    ALLOWED_SCANNER_BINARY_NAMES,
    DEFAULT_SAFE_ERROR_MESSAGE,
    DEFAULT_SCANNER_TIMEOUT_SECONDS,
    LOCAL_SCANNER_RUNTIME_ENABLED,
    MAX_SAFE_MESSAGE_LENGTH,
    MAX_SCANNER_TIMEOUT_SECONDS,
    ScannerRuntimeMode,
    current_scanner_runtime_policy,
    normalize_scanner_error_code,
    normalize_scanner_error_message,
    redact_scanner_output_for_user,
    scanner_runtime_is_enabled,
    scanner_runtime_policy_summary,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"
RUNTIME = EVIDENCE_PKG / "attachment_scanner_runtime_policy.py"
SCANNER_MODULES = [
    EVIDENCE_PKG / "attachment_scanner_runtime_policy.py",
    EVIDENCE_PKG / "attachment_scanner_policy.py",
    EVIDENCE_PKG / "attachment_scanner_adapter.py",
    EVIDENCE_PKG / "attachment_local_scanner_adapter.py",
    EVIDENCE_PKG / "attachment_scan_worker.py",
]
FRONTEND_PAGES = [
    REPO_ROOT / "frontend" / "src" / "pages" / "EvidenceLibraryPage.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "passport"
    / "PassportEvidencePanel.tsx",
]


def test_runtime_flags_disabled_and_timeout_bounded() -> None:
    assert LOCAL_SCANNER_RUNTIME_ENABLED is False
    assert scanner_runtime_is_enabled() is False
    assert ALLOW_SHELL_EXECUTION is False
    assert ALLOW_NETWORK_SCANNER is False
    assert ALLOW_RAW_SCANNER_OUTPUT_TO_USER is False
    assert ALLOW_FILE_PARSING_FOR_SCAN is False
    assert ALLOW_LLM_REVIEW_FOR_SCAN is False
    assert ALLOW_OCR_FOR_SCAN is False
    assert ALLOWED_SCANNER_BINARY_NAMES == ()
    assert 1 <= DEFAULT_SCANNER_TIMEOUT_SECONDS <= MAX_SCANNER_TIMEOUT_SECONDS
    assert MAX_SCANNER_TIMEOUT_SECONDS <= 120
    policy = current_scanner_runtime_policy()
    assert policy.runtime_enabled is False
    assert policy.shell_allowed is False
    assert policy.network_allowed is False
    assert policy.mode is ScannerRuntimeMode.DISABLED
    assert policy.allowed_binary_names == ()
    assert "disabled" in policy.warning.lower()


def test_normalize_error_codes() -> None:
    assert normalize_scanner_error_code("local_scanner_disabled") == (
        "local_scanner_disabled"
    )
    assert normalize_scanner_error_code("scanner_timeout") == "scanner_timeout"
    assert normalize_scanner_error_code("scanner_unavailable") == (
        "scanner_unavailable"
    )
    assert normalize_scanner_error_code("totally_unknown_code") == (
        "scanner_output_unavailable"
    )
    assert normalize_scanner_error_code(None) == "scanner_output_unavailable"
    assert normalize_scanner_error_code("  ") == "scanner_output_unavailable"


def test_normalize_message_redacts_paths_and_uris_and_truncates() -> None:
    assert (
        normalize_scanner_error_message("/tmp/evil.bin found")
        == DEFAULT_SAFE_ERROR_MESSAGE
    )
    assert (
        normalize_scanner_error_message(
            "failed local-evidence://user/abc/file.pdf"
        )
        == DEFAULT_SAFE_ERROR_MESSAGE
    )
    assert (
        normalize_scanner_error_message(r"C:\Users\me\secret.bin")
        == DEFAULT_SAFE_ERROR_MESSAGE
    )
    assert (
        normalize_scanner_error_message("/Users/me/Desktop/file.pdf")
        == DEFAULT_SAFE_ERROR_MESSAGE
    )
    long = "x" * (MAX_SAFE_MESSAGE_LENGTH + 50)
    out = normalize_scanner_error_message(long)
    assert len(out) <= MAX_SAFE_MESSAGE_LENGTH
    assert out.endswith("…")
    assert normalize_scanner_error_message(None) == DEFAULT_SAFE_ERROR_MESSAGE
    assert (
        redact_scanner_output_for_user("FOUND /tmp/x VIRUS DUMP")
        == DEFAULT_SAFE_ERROR_MESSAGE
    )


def test_disabled_adapter_uses_safe_disabled_message_and_factory_noop() -> None:
    result = DisabledLocalProcessScannerAdapter().scan_attachment()
    assert result.safe_error_code == "local_scanner_disabled"
    assert "disabled" in (result.safe_error_message or "").lower()
    assert REAL_SCANNER_ENABLED is False
    assert real_scanner_is_enabled() is False
    active = get_configured_attachment_scanner_adapter()
    assert isinstance(active, NoopUnavailableScannerAdapter)
    assert not isinstance(active, DisabledLocalProcessScannerAdapter)


def test_runtime_module_has_no_subprocess_network_scanner_ocr_llm_or_env() -> None:
    source = RUNTIME.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
    allowed = {"__future__", "dataclasses", "enum", "typing"}
    for mod in imports:
        assert mod in allowed, mod
    blob = source.lower()
    for forbidden in (
        "import subprocess",
        "popen",
        "clamav",
        "virustotal",
        "pytesseract",
        "pdfplumber",
        "openai",
        "anthropic",
        "app.tools.llm",
        "app.core.config",
        "os.environ",
        "getenv",
        "import httpx",
        "import requests",
        "import socket",
        "import pathlib",
        "open(",
        "read_bytes",
    ):
        assert forbidden not in blob, forbidden


def test_scanner_modules_have_no_subprocess_or_scanner_packages() -> None:
    for path in SCANNER_MODULES:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module.lower()
                assert "subprocess" not in mod
                assert "clamav" not in mod
                assert "virustotal" not in mod
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "subprocess" not in alias.name.lower()


def test_no_scan_routes_ui_or_f0012_and_summary_safe() -> None:
    summary = scanner_runtime_policy_summary()
    assert summary["runtime_enabled"] is False
    assert summary["executes_commands"] is False
    assert summary["is_verification"] is False
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
