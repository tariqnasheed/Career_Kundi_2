"""Scan worker contract tests (0053-F17). Pure mapping; no scanner engine."""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app
from app.platform.evidence.attachment_safety import AttachmentSafetyStatus
from app.platform.evidence.attachment_scan_queue import AttachmentScanJobStatus
from app.platform.evidence.attachment_scan_worker import (
    DEFAULT_SCANNER_AVAILABILITY,
    ScanJobUpdatePlan,
    ScanResultContract,
    ScannerAvailability,
    ScannerVerdict,
    ScanWorkerAction,
    assert_no_file_byte_access_in_plan,
    build_scan_job_update_from_result,
    current_scanner_availability,
    default_scanner_name,
    default_scanner_version,
    plan_when_scanner_unavailable,
    worker_contract_summary,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
WORKER = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_scan_worker.py"
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


def test_scanner_availability_defaults_to_unavailable() -> None:
    assert current_scanner_availability() is ScannerAvailability.UNAVAILABLE
    assert DEFAULT_SCANNER_AVAILABILITY == "unavailable"
    assert default_scanner_name() is None
    assert default_scanner_version() is None
    summary = worker_contract_summary()
    assert summary["scanner_availability"] == "unavailable"
    assert summary["applies_results_to_database"] is False
    assert summary["reads_file_bytes"] is False
    assert summary["registers_startup_worker"] is False


def test_worker_source_has_no_scanner_ocr_llm_or_file_io() -> None:
    source = WORKER.read_text(encoding="utf-8")
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
        "clamav",
        "virustotal",
        "pyclamd",
        "pytesseract",
        "pdfplumber",
        "easyocr",
        "openai",
        "anthropic",
        "app.tools.llm",
        "open(",
        "pathlib",
        "path(",
        "read_bytes",
        "read_text",
        "aiofiles",
    ):
        assert forbidden not in blob, forbidden
    for mod in imports:
        lower = mod.lower()
        assert "clamav" not in lower
        assert "virustotal" not in lower
        assert "llm" not in lower
        assert not lower.startswith("app.tools.llm")
    # No DB session / storage imports — pure contract only.
    assert "sqlalchemy" not in imports
    assert "app.platform.evidence.storage" not in imports
    assert "app.db.session" not in imports


def test_clean_verdict_maps_to_passed_plan_not_applied() -> None:
    plan = build_scan_job_update_from_result(
        ScanResultContract(
            scanner_name="future-scanner",
            scanner_version="0.0.0",
            verdict=ScannerVerdict.CLEAN,
        )
    )
    assert isinstance(plan, ScanJobUpdatePlan)
    assert plan.action is ScanWorkerAction.COMPLETE_PASSED
    assert plan.job_status == AttachmentScanJobStatus.COMPLETED.value
    assert plan.attachment_safety_status == AttachmentSafetyStatus.SCAN_PASSED.value
    assert plan.quarantine_required is False
    assert plan.apply_to_database is False
    assert_no_file_byte_access_in_plan(plan)


def test_malicious_and_suspicious_map_to_failed_quarantine_required() -> None:
    for verdict in (ScannerVerdict.MALICIOUS, ScannerVerdict.SUSPICIOUS):
        plan = build_scan_job_update_from_result(
            ScanResultContract(
                scanner_name="future-scanner",
                scanner_version="0.0.0",
                verdict=verdict,
            )
        )
        assert plan.action is ScanWorkerAction.QUARANTINE_REQUIRED
        assert plan.job_status == AttachmentScanJobStatus.COMPLETED.value
        assert plan.attachment_safety_status == AttachmentSafetyStatus.SCAN_FAILED.value
        assert plan.quarantine_required is True
        assert plan.apply_to_database is False


def test_timeout_error_unsupported_map_to_scan_error() -> None:
    for verdict in (
        ScannerVerdict.TIMEOUT,
        ScannerVerdict.ERROR,
        ScannerVerdict.UNSUPPORTED,
    ):
        plan = build_scan_job_update_from_result(
            ScanResultContract(
                scanner_name=None,
                scanner_version=None,
                verdict=verdict,
                safe_error_code=verdict.value,
            )
        )
        assert plan.action is ScanWorkerAction.MARK_ERROR
        assert plan.job_status == AttachmentScanJobStatus.FAILED.value
        assert plan.attachment_safety_status == AttachmentSafetyStatus.SCAN_ERROR.value
        assert plan.quarantine_required is False
        assert plan.apply_to_database is False


def test_not_run_and_unavailable_do_not_pass_or_fail() -> None:
    not_run = build_scan_job_update_from_result(
        ScanResultContract(
            scanner_name=None,
            scanner_version=None,
            verdict=ScannerVerdict.NOT_RUN,
        )
    )
    assert not_run.action is ScanWorkerAction.NO_OP
    assert not_run.job_status is None
    assert (
        not_run.attachment_safety_status
        == AttachmentSafetyStatus.SCAN_NOT_AVAILABLE.value
    )
    assert not_run.apply_to_database is False

    unavailable = plan_when_scanner_unavailable()
    assert unavailable.action is ScanWorkerAction.NO_OP
    assert unavailable.apply_to_database is False
    assert unavailable.quarantine_required is False
    assert (
        unavailable.attachment_safety_status
        == AttachmentSafetyStatus.SCAN_NOT_AVAILABLE.value
    )


def test_safe_error_messages_strip_paths() -> None:
    plan = build_scan_job_update_from_result(
        ScanResultContract(
            scanner_name=None,
            scanner_version=None,
            verdict=ScannerVerdict.ERROR,
            safe_error_code="error",
            safe_error_message="failed at /tmp/evidence_files/secret.bin",
        )
    )
    assert plan.safe_error_message == "Scanner reported an error."
    assert "/tmp/" not in (plan.safe_error_message or "")
    assert "evidence_files" not in (plan.safe_error_message or "")


def test_no_scan_routes_or_ui() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        if path.startswith("/api/v1/evidence"):
            assert "/scan" not in path.lower(), path
        if path.startswith("/api/v1/"):
            assert "/admin/scan" not in path.lower()
    assert "/api/v1/evidence/{evidence_id}/scan" not in paths
    for page in FRONTEND_PAGES:
        text = page.read_text(encoding="utf-8").lower()
        for needle in (
            "scan now",
            "rescan",
            "mark safe",
            "mark clean",
            "quarantine",
            "release from quarantine",
            "verify file",
        ):
            assert needle not in text, f"{page}: {needle}"


def test_no_forbidden_worker_trust_wording_in_module() -> None:
    blob = WORKER.read_text(encoding="utf-8").lower()
    # Constant set documents forbidden terms; skip that block by checking helpers.
    summary = str(worker_contract_summary()).lower()
    for phrase in (
        "safe file",
        "clean file",
        "trusted file",
        "verified document",
        "protected by scan",
    ):
        assert phrase not in summary


def test_no_f0012_migration_added() -> None:
    migrations = (
        REPO_ROOT
        / "backend"
        / "app"
        / "db"
        / "foundation_migrations"
        / "versions"
    )
    assert list(migrations.glob("f0012*")) == []
    assert not (EVIDENCE_PKG / "scan_worker.py").exists()
    assert not (EVIDENCE_PKG / "quarantine.py").exists()
