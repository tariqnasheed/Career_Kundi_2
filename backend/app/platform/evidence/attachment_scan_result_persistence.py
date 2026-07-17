"""
AttachmentScanJob result persistence guard (0053-F22).

Internal, tightly guarded application of an explicit scan-job update plan to
AttachmentScanJob rows only. Does not scan, open files, spawn processes, call
network scanners, or mutate EvidenceRecord / ClaimRecord / ReviewRequest.

Persisting a scan-job result is not verification.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.attachment_scan import AttachmentScanJob
from app.platform.evidence.attachment_safety import AttachmentSafetyStatus
from app.platform.evidence.attachment_scan_queue import (
    AttachmentScanJobStatus,
    get_attachment_scan_job_for_owner,
)
from app.platform.evidence.attachment_scan_worker import (
    ScanJobUpdatePlan,
    ScanWorkerAction,
)
from app.platform.evidence.attachment_scanner_runtime_policy import (
    normalize_scanner_error_code,
    normalize_scanner_error_message,
)
from app.platform.evidence.refs import EvidenceRefError

ALLOWED_SCAN_JOB_UPDATE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "job_status",
        "attachment_safety_status",
        "engine_name",
        "engine_version",
        "attempt_count",
        "safe_error_code",
        "safe_error_message",
        "started_at",
        "completed_at",
        "cancelled_at",
        "updated_at",
    }
)

ALLOWED_JOB_TRANSITIONS: Final[frozenset[tuple[str, str]]] = frozenset(
    {
        (
            AttachmentScanJobStatus.QUEUED.value,
            AttachmentScanJobStatus.RESERVED.value,
        ),
        (
            AttachmentScanJobStatus.RESERVED.value,
            AttachmentScanJobStatus.COMPLETED.value,
        ),
        (
            AttachmentScanJobStatus.RESERVED.value,
            AttachmentScanJobStatus.FAILED.value,
        ),
        (
            AttachmentScanJobStatus.QUEUED.value,
            AttachmentScanJobStatus.CANCELLED.value,
        ),
        (
            AttachmentScanJobStatus.RESERVED.value,
            AttachmentScanJobStatus.CANCELLED.value,
        ),
    }
)

TERMINAL_JOB_STATUSES: Final[frozenset[str]] = frozenset(
    {
        AttachmentScanJobStatus.COMPLETED.value,
        AttachmentScanJobStatus.FAILED.value,
        AttachmentScanJobStatus.CANCELLED.value,
    }
)

_PERSISTABLE_ACTIONS: Final[frozenset[ScanWorkerAction]] = frozenset(
    {
        ScanWorkerAction.RESERVE_JOB,
        ScanWorkerAction.COMPLETE_PASSED,
        ScanWorkerAction.COMPLETE_FAILED,
        ScanWorkerAction.MARK_ERROR,
        ScanWorkerAction.CANCEL_JOB,
        # Quarantine storage is not implemented; status must stay scan_failed.
        ScanWorkerAction.QUARANTINE_REQUIRED,
    }
)


class ScanJobPersistenceError(EvidenceRefError):
    """Raised when a scan-job update plan is not allowed to persist."""


def plan_is_persistable(plan: ScanJobUpdatePlan) -> bool:
    if not isinstance(plan, ScanJobUpdatePlan):
        return False
    if plan.apply_to_database is not True:
        return False
    if plan.action is ScanWorkerAction.NO_OP:
        return False
    if plan.job_status is None:
        return False
    return plan.action in _PERSISTABLE_ACTIONS


def normalize_scan_job_update_plan(plan: ScanJobUpdatePlan) -> ScanJobUpdatePlan:
    """Normalize safe error fields via F21 helpers. Does not force apply=True."""
    if not isinstance(plan, ScanJobUpdatePlan):
        raise TypeError("plan must be ScanJobUpdatePlan")

    code = plan.safe_error_code
    message = plan.safe_error_message
    if code is not None:
        code = normalize_scanner_error_code(code)
    if message is not None:
        message = normalize_scanner_error_message(message)
    return replace(plan, safe_error_code=code, safe_error_message=message)


def build_persistable_scan_job_update_plan(
    *,
    action: ScanWorkerAction,
    job_status: str,
    attachment_safety_status: str,
    engine_name: str | None = None,
    engine_version: str | None = None,
    safe_error_code: str | None = None,
    safe_error_message: str | None = None,
    quarantine_required: bool = False,
) -> ScanJobUpdatePlan:
    """
    Build an explicit persistable plan for tests / future workers.

    F17 adapter-derived plans remain apply_to_database=False and must not
    be persisted unless rebuilt through this helper (or equivalent).
    """
    plan = ScanJobUpdatePlan(
        action=action,
        job_status=job_status,
        attachment_safety_status=attachment_safety_status,
        engine_name=engine_name,
        engine_version=engine_version,
        safe_error_code=safe_error_code,
        safe_error_message=safe_error_message,
        quarantine_required=quarantine_required,
        apply_to_database=True,
    )
    return normalize_scan_job_update_plan(plan)


def assert_scan_job_update_allowed(
    job: AttachmentScanJob,
    plan: ScanJobUpdatePlan,
) -> None:
    if not plan_is_persistable(plan):
        raise ScanJobPersistenceError(
            "Scan job update plan is not persistable "
            "(apply_to_database must be True and action must not be no_op)."
        )

    current = str(job.job_status)
    if current in TERMINAL_JOB_STATUSES:
        raise ScanJobPersistenceError(
            f"Terminal scan job status cannot be changed: {current}"
        )

    target = str(plan.job_status)
    if (current, target) not in ALLOWED_JOB_TRANSITIONS:
        raise ScanJobPersistenceError(
            f"Disallowed scan job transition: {current} → {target}"
        )

    safety = plan.attachment_safety_status
    if safety == AttachmentSafetyStatus.QUARANTINED.value:
        raise ScanJobPersistenceError(
            "quarantined attachment_safety_status is not allowed "
            "(quarantine storage inactive in F22/F23)"
        )

    if safety == AttachmentSafetyStatus.SCAN_PASSED.value and target != (
        AttachmentScanJobStatus.COMPLETED.value
    ):
        raise ScanJobPersistenceError("scan_passed requires job_status=completed")

    if safety == AttachmentSafetyStatus.SCAN_FAILED.value and target != (
        AttachmentScanJobStatus.COMPLETED.value
    ):
        raise ScanJobPersistenceError("scan_failed requires job_status=completed")

    if safety == AttachmentSafetyStatus.SCAN_ERROR.value and target != (
        AttachmentScanJobStatus.FAILED.value
    ):
        raise ScanJobPersistenceError("scan_error requires job_status=failed")

    # Action / status consistency (soft checks for common actions).
    if plan.action is ScanWorkerAction.RESERVE_JOB and target != (
        AttachmentScanJobStatus.RESERVED.value
    ):
        raise ScanJobPersistenceError("reserve_job requires job_status=reserved")
    if plan.action is ScanWorkerAction.CANCEL_JOB and target != (
        AttachmentScanJobStatus.CANCELLED.value
    ):
        raise ScanJobPersistenceError("cancel_job requires job_status=cancelled")
    if plan.action in (
        ScanWorkerAction.COMPLETE_PASSED,
        ScanWorkerAction.COMPLETE_FAILED,
        ScanWorkerAction.QUARANTINE_REQUIRED,
    ) and target != AttachmentScanJobStatus.COMPLETED.value:
        raise ScanJobPersistenceError(
            f"{plan.action.value} requires job_status=completed"
        )
    if plan.action is ScanWorkerAction.MARK_ERROR and target != (
        AttachmentScanJobStatus.FAILED.value
    ):
        raise ScanJobPersistenceError("mark_error requires job_status=failed")


async def apply_scan_job_update_plan(
    db: AsyncSession,
    *,
    job_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    plan: ScanJobUpdatePlan,
) -> AttachmentScanJob:
    """
    Apply a persistable plan to an owned AttachmentScanJob row only.

    Does not mutate EvidenceRecord, ClaimRecord, or ReviewRequest.
    """
    normalized = normalize_scan_job_update_plan(plan)
    job = await get_attachment_scan_job_for_owner(
        db, job_id=job_id, owner_user_id=owner_user_id
    )
    if job is None:
        raise ScanJobPersistenceError(f"scan job does not exist: {job_id}")

    assert_scan_job_update_allowed(job, normalized)

    now = datetime.now(timezone.utc)
    target = str(normalized.job_status)

    job.job_status = target
    if normalized.attachment_safety_status is not None:
        job.attachment_safety_status = normalized.attachment_safety_status
    if normalized.engine_name is not None:
        job.engine_name = normalized.engine_name
    if normalized.engine_version is not None:
        job.engine_version = normalized.engine_version
    if normalized.safe_error_code is not None:
        job.safe_error_code = normalized.safe_error_code
    if normalized.safe_error_message is not None:
        job.safe_error_message = normalized.safe_error_message

    if target == AttachmentScanJobStatus.RESERVED.value:
        job.attempt_count = int(job.attempt_count or 0) + 1
        if job.started_at is None:
            job.started_at = now
    elif target == AttachmentScanJobStatus.COMPLETED.value:
        job.completed_at = now
    elif target == AttachmentScanJobStatus.FAILED.value:
        job.completed_at = now
    elif target == AttachmentScanJobStatus.CANCELLED.value:
        job.cancelled_at = now

    await db.commit()
    await db.refresh(job)
    return job


def persistence_guard_summary() -> dict[str, object]:
    return {
        "allowed_row": "AttachmentScanJob",
        "allowed_fields": sorted(ALLOWED_SCAN_JOB_UPDATE_FIELDS),
        "allowed_transitions": sorted(
            f"{a}->{b}" for a, b in ALLOWED_JOB_TRANSITIONS
        ),
        "mutates_evidence_record": False,
        "mutates_claim_record": False,
        "mutates_review_request": False,
        "runs_scanner": False,
        "reads_file_bytes": False,
        "is_verification": False,
        "quarantine_storage_active": False,
        "quarantine_audit_active": False,
        "scan_admin_override_active": False,
    }
