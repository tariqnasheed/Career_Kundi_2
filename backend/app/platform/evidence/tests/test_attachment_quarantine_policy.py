"""Attachment quarantine policy tests (0053-F17). Policy only; not active."""

from __future__ import annotations

import ast
from pathlib import Path

from app.platform.evidence.attachment_quarantine_policy import (
    FORBIDDEN_QUARANTINE_WORDING,
    quarantine_is_available,
    quarantine_policy_summary,
    quarantine_policy_warning,
    quarantine_storage_not_implemented_warning,
    safe_scan_error_message,
    should_quarantine_scan_verdict,
)
from app.platform.evidence.attachment_scan_worker import ScannerVerdict

REPO_ROOT = Path(__file__).resolve().parents[5]
POLICY = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_quarantine_policy.py"
)


def test_quarantine_is_not_available() -> None:
    assert quarantine_is_available() is False
    summary = quarantine_policy_summary()
    assert summary["quarantine_available"] is False
    assert summary["moves_or_deletes_files"] is False
    assert summary["storage_enabled"] is False
    assert summary["storage_mode"] == "disabled"
    assert summary["audit_sink_enabled"] is False
    warning = quarantine_policy_warning().lower()
    assert "planned but not active" in warning
    storage = quarantine_storage_not_implemented_warning().lower()
    assert "not implemented" in storage
    assert "moved or deleted" in storage
    contract = str(summary["storage_contract_warning"]).lower()
    assert "planned but not active" in contract
    audit = str(summary["audit_warning"]).lower()
    assert "audit persistence" in audit
    assert "planned but not active" in audit


def test_quarantine_required_only_for_malicious_suspicious() -> None:
    assert should_quarantine_scan_verdict(ScannerVerdict.MALICIOUS) is True
    assert should_quarantine_scan_verdict(ScannerVerdict.SUSPICIOUS) is True
    assert should_quarantine_scan_verdict(ScannerVerdict.CLEAN) is False
    assert should_quarantine_scan_verdict(ScannerVerdict.ERROR) is False
    assert should_quarantine_scan_verdict(ScannerVerdict.TIMEOUT) is False
    assert should_quarantine_scan_verdict(ScannerVerdict.NOT_RUN) is False
    assert should_quarantine_scan_verdict("malicious") is True
    assert should_quarantine_scan_verdict("clean") is False


def test_safe_scan_error_messages() -> None:
    assert "not available" in safe_scan_error_message("scanner_unavailable").lower()
    assert "timed out" in safe_scan_error_message("timeout").lower()
    assert "error" in safe_scan_error_message("error").lower()
    # Path-like codes must not leak.
    msg = safe_scan_error_message("/tmp/evidence_files/x.bin")
    assert "/tmp" not in msg.lower()
    assert "evidence_files" not in msg.lower()


def test_policy_source_has_no_file_move_or_scanner_imports() -> None:
    source = POLICY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
    blob = source.lower()
    for forbidden in (
        "shutil",
        "os.remove",
        "unlink",
        "rmtree",
        "move(",
        "clamav",
        "virustotal",
        "sqlalchemy",
        "open(",
        "pathlib",
        "app.tools.llm",
    ):
        assert forbidden not in blob, forbidden
    assert "sqlalchemy" not in imports
    assert "app.platform.evidence.storage" not in imports


def test_policy_warnings_forbid_trust_wording() -> None:
    blob = " ".join(
        [
            quarantine_policy_warning(),
            quarantine_storage_not_implemented_warning(),
            safe_scan_error_message("error"),
            safe_scan_error_message("malicious"),
        ]
    ).lower()
    for phrase in FORBIDDEN_QUARANTINE_WORDING:
        assert phrase not in blob
