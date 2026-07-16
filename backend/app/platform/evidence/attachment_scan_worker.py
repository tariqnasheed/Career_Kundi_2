"""
Scan worker contract (0053-F17).

Pure planning types and mapping helpers for a future scanner worker.
Does not run a worker, open files, call scanners, or mutate DB rows.

A scan contract / update plan is not a scan result and is not verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.platform.evidence.attachment_quarantine_policy import (
    should_quarantine_scan_verdict,
)
from app.platform.evidence.attachment_safety import AttachmentSafetyStatus
from app.platform.evidence.attachment_scan_queue import AttachmentScanJobStatus

# F17: no scanner engine is configured or available.
DEFAULT_SCANNER_AVAILABILITY = "unavailable"
DEFAULT_SCANNER_NAME: str | None = None
DEFAULT_SCANNER_VERSION: str | None = None

FORBIDDEN_WORKER_WORDING: frozenset[str] = frozenset(
    {
        "safe file",
        "clean file",
        "trusted file",
        "verified document",
        "official document",
        "protected by scan",
        "public credential",
    }
)


class ScannerAvailability(StrEnum):
    UNAVAILABLE = "unavailable"
    AVAILABLE = "available"


class ScannerVerdict(StrEnum):
    NOT_RUN = "not_run"
    CLEAN = "clean"
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNSUPPORTED = "unsupported"


class ScanWorkerAction(StrEnum):
    NO_OP = "no_op"
    RESERVE_JOB = "reserve_job"
    COMPLETE_PASSED = "complete_passed"
    COMPLETE_FAILED = "complete_failed"
    MARK_ERROR = "mark_error"
    QUARANTINE_REQUIRED = "quarantine_required"
    CANCEL_JOB = "cancel_job"


@dataclass(frozen=True, slots=True)
class ScanResultContract:
    """Future scanner outcome contract. Not produced from file bytes in F17."""

    scanner_name: str | None
    scanner_version: str | None
    verdict: ScannerVerdict
    safe_error_code: str | None = None
    safe_error_message: str | None = None
    duration_ms: int | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ScanJobUpdatePlan:
    """
    Proposed job-field updates derived from a ScanResultContract.

    F17 does not apply this plan to the database.
    """

    action: ScanWorkerAction
    job_status: str | None
    attachment_safety_status: str | None
    engine_name: str | None
    engine_version: str | None
    safe_error_code: str | None
    safe_error_message: str | None
    quarantine_required: bool
    apply_to_database: bool = False


def current_scanner_availability() -> ScannerAvailability:
    """F17 default: no scanner engine is available."""
    return ScannerAvailability.UNAVAILABLE


def default_scanner_name() -> str | None:
    return DEFAULT_SCANNER_NAME


def default_scanner_version() -> str | None:
    return DEFAULT_SCANNER_VERSION


def _sanitize_safe_text(value: str | None, *, max_len: int = 500) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    lower = text.lower()
    # Never leak filesystem / storage paths in safe messages.
    for needle in ("/tmp/", "evidence_files", "local-evidence://", "\\", ":\\"):
        if needle in lower:
            return "Scanner reported an error."
    for forbidden in FORBIDDEN_WORKER_WORDING:
        if forbidden in lower:
            return "Scanner reported an error."
    return text[:max_len]


def build_scan_job_update_from_result(result: ScanResultContract) -> ScanJobUpdatePlan:
    """
    Map a future scanner result to a proposed job update plan.

    Does not write the database, open files, or execute a scanner.
    """
    if not isinstance(result, ScanResultContract):
        raise TypeError("result must be ScanResultContract")

    verdict = (
        result.verdict
        if isinstance(result.verdict, ScannerVerdict)
        else ScannerVerdict(str(result.verdict))
    )
    safe_code = _sanitize_safe_text(result.safe_error_code, max_len=128)
    safe_message = _sanitize_safe_text(result.safe_error_message)

    if verdict in (ScannerVerdict.NOT_RUN,):
        return ScanJobUpdatePlan(
            action=ScanWorkerAction.NO_OP,
            job_status=None,
            attachment_safety_status=AttachmentSafetyStatus.SCAN_NOT_AVAILABLE.value,
            engine_name=result.scanner_name,
            engine_version=result.scanner_version,
            safe_error_code=safe_code,
            safe_error_message=safe_message,
            quarantine_required=False,
            apply_to_database=False,
        )

    if verdict is ScannerVerdict.CLEAN:
        return ScanJobUpdatePlan(
            action=ScanWorkerAction.COMPLETE_PASSED,
            job_status=AttachmentScanJobStatus.COMPLETED.value,
            attachment_safety_status=AttachmentSafetyStatus.SCAN_PASSED.value,
            engine_name=result.scanner_name,
            engine_version=result.scanner_version,
            safe_error_code=None,
            safe_error_message=None,
            quarantine_required=False,
            apply_to_database=False,
        )

    if verdict in (ScannerVerdict.MALICIOUS, ScannerVerdict.SUSPICIOUS):
        return ScanJobUpdatePlan(
            action=ScanWorkerAction.QUARANTINE_REQUIRED,
            job_status=AttachmentScanJobStatus.COMPLETED.value,
            attachment_safety_status=AttachmentSafetyStatus.SCAN_FAILED.value,
            engine_name=result.scanner_name,
            engine_version=result.scanner_version,
            safe_error_code=safe_code or verdict.value,
            safe_error_message=safe_message
            or "Scanner reported a concerning attachment result.",
            quarantine_required=should_quarantine_scan_verdict(verdict),
            apply_to_database=False,
        )

    # timeout / error / unsupported
    return ScanJobUpdatePlan(
        action=ScanWorkerAction.MARK_ERROR,
        job_status=AttachmentScanJobStatus.FAILED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_ERROR.value,
        engine_name=result.scanner_name,
        engine_version=result.scanner_version,
        safe_error_code=safe_code or verdict.value,
        safe_error_message=safe_message or "Scanner reported an error.",
        quarantine_required=False,
        apply_to_database=False,
    )


def plan_when_scanner_unavailable() -> ScanJobUpdatePlan:
    """Default plan while no scanner engine exists."""
    return ScanJobUpdatePlan(
        action=ScanWorkerAction.NO_OP,
        job_status=None,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_NOT_AVAILABLE.value,
        engine_name=None,
        engine_version=None,
        safe_error_code="scanner_unavailable",
        safe_error_message="Malware scanning is not available in this version.",
        quarantine_required=False,
        apply_to_database=False,
    )


def assert_no_file_byte_access_in_plan(plan: ScanJobUpdatePlan) -> None:
    """Test helper: plans never imply file reads or storage paths."""
    blob = " ".join(
        str(v).lower()
        for v in (
            plan.safe_error_code,
            plan.safe_error_message,
            plan.engine_name,
            plan.engine_version,
        )
        if v is not None
    )
    assert "evidence_files" not in blob
    assert "/tmp/" not in blob
    assert "local-evidence://" not in blob


def worker_contract_summary() -> dict[str, Any]:
    """Safe introspection for docs/tests — no side effects."""
    return {
        "scanner_availability": current_scanner_availability().value,
        "default_scanner_name": default_scanner_name(),
        "default_scanner_version": default_scanner_version(),
        "applies_results_to_database": False,
        "reads_file_bytes": False,
        "registers_startup_worker": False,
    }
