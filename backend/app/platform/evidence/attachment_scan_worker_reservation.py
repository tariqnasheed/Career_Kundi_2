"""
Scanner worker reservation guard (0053-F27).

Guarded internal reservation of an AttachmentScanJob row for a future worker.
Allows only queued → reserved with owner scoping and content-hash snapshot
match. Does not run a worker loop, call scanners, read files, apply scan
results, emit audit, or mutate evidence / claim / review rows.

Reservation is not scanning and is not verification.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.attachment_scan import AttachmentScanJob
from app.platform.evidence.attachment_scan_queue import (
    AttachmentScanJobStatus,
    get_attachment_scan_job_for_owner,
)
from app.platform.evidence.refs import EvidenceRefError

SCAN_WORKER_RESERVATION_GUARD_ENABLED: Final[bool] = True
SCAN_WORKER_RESERVATION_EXECUTES_SCANNER: Final[bool] = False
SCAN_WORKER_RESERVATION_READS_FILES: Final[bool] = False
SCAN_WORKER_RESERVATION_REGISTERS_WORKER: Final[bool] = False
SCAN_WORKER_RESERVATION_EXPOSES_ROUTE: Final[bool] = False
SCAN_WORKER_RESERVATION_MUTATES_ONLY_SCAN_JOB: Final[bool] = True


class ScanWorkerReservationDecision(StrEnum):
    RESERVED = "reserved"
    NOT_FOUND = "not_found"
    NOT_OWNER_SCOPED = "not_owner_scoped"
    NOT_QUEUED = "not_queued"
    HASH_MISMATCH = "hash_mismatch"
    SCANNER_UNAVAILABLE = "scanner_unavailable"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class ScanWorkerReservationResult:
    reserved: bool
    decision: ScanWorkerReservationDecision
    job_id: uuid.UUID | None
    owner_user_id: uuid.UUID | None
    previous_status: str | None
    new_status: str | None
    attempt_count: int | None
    safe_message: str


class ScanWorkerReservationError(EvidenceRefError):
    """Raised when reservation assertion fails."""

    def __init__(
        self,
        message: str,
        *,
        decision: ScanWorkerReservationDecision,
    ) -> None:
        super().__init__(message)
        self.decision = decision


def assert_scan_worker_reservation_allowed(
    job: AttachmentScanJob,
    *,
    expected_content_hash_snapshot: str,
) -> None:
    """
    Validate that a loaded job may be reserved.

    Does not read files or call scanners. Hash check is snapshot equality only.
    """
    if not SCAN_WORKER_RESERVATION_GUARD_ENABLED:
        raise ScanWorkerReservationError(
            "Scan worker reservation guard is disabled.",
            decision=ScanWorkerReservationDecision.DISABLED,
        )
    if str(job.job_status) != AttachmentScanJobStatus.QUEUED.value:
        raise ScanWorkerReservationError(
            f"Only queued scan jobs can be reserved; current={job.job_status}",
            decision=ScanWorkerReservationDecision.NOT_QUEUED,
        )
    expected = str(expected_content_hash_snapshot).strip()
    current = str(job.content_hash_snapshot or "").strip()
    if not expected or current != expected:
        raise ScanWorkerReservationError(
            "Scan job content_hash_snapshot does not match expected snapshot.",
            decision=ScanWorkerReservationDecision.HASH_MISMATCH,
        )


async def reserve_attachment_scan_job_for_worker(
    db: AsyncSession,
    *,
    job_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    expected_content_hash_snapshot: str,
) -> ScanWorkerReservationResult:
    """
    Reserve an owned queued AttachmentScanJob for a future worker.

    Mutates AttachmentScanJob only: job_status, attempt_count, started_at
    (and updated_at via mixin). Does not scan, read files, or apply results.
    """
    if not SCAN_WORKER_RESERVATION_GUARD_ENABLED:
        return ScanWorkerReservationResult(
            reserved=False,
            decision=ScanWorkerReservationDecision.DISABLED,
            job_id=job_id,
            owner_user_id=owner_user_id,
            previous_status=None,
            new_status=None,
            attempt_count=None,
            safe_message="Scan worker reservation is disabled in this version.",
        )

    job = await get_attachment_scan_job_for_owner(
        db, job_id=job_id, owner_user_id=owner_user_id
    )
    if job is None:
        # Owner-scoped miss: do not distinguish missing vs other-owner.
        return ScanWorkerReservationResult(
            reserved=False,
            decision=ScanWorkerReservationDecision.NOT_FOUND,
            job_id=job_id,
            owner_user_id=owner_user_id,
            previous_status=None,
            new_status=None,
            attempt_count=None,
            safe_message="Scan job was not found for this owner.",
        )

    previous = str(job.job_status)
    try:
        assert_scan_worker_reservation_allowed(
            job,
            expected_content_hash_snapshot=expected_content_hash_snapshot,
        )
    except ScanWorkerReservationError as exc:
        return ScanWorkerReservationResult(
            reserved=False,
            decision=exc.decision,
            job_id=job.id,
            owner_user_id=job.owner_user_id,
            previous_status=previous,
            new_status=previous,
            attempt_count=int(job.attempt_count or 0),
            safe_message=str(exc),
        )

    now = datetime.now(timezone.utc)
    job.job_status = AttachmentScanJobStatus.RESERVED.value
    job.attempt_count = int(job.attempt_count or 0) + 1
    if job.started_at is None:
        job.started_at = now

    await db.commit()
    await db.refresh(job)

    return ScanWorkerReservationResult(
        reserved=True,
        decision=ScanWorkerReservationDecision.RESERVED,
        job_id=job.id,
        owner_user_id=job.owner_user_id,
        previous_status=previous,
        new_status=str(job.job_status),
        attempt_count=int(job.attempt_count or 0),
        safe_message="Scan job reserved for a future worker. Reservation is not a scan.",
    )


def reservation_guard_summary() -> dict[str, object]:
    return {
        "guard_enabled": SCAN_WORKER_RESERVATION_GUARD_ENABLED,
        "executes_scanner": SCAN_WORKER_RESERVATION_EXECUTES_SCANNER,
        "reads_files": SCAN_WORKER_RESERVATION_READS_FILES,
        "registers_worker": SCAN_WORKER_RESERVATION_REGISTERS_WORKER,
        "exposes_route": SCAN_WORKER_RESERVATION_EXPOSES_ROUTE,
        "mutates_only_scan_job": SCAN_WORKER_RESERVATION_MUTATES_ONLY_SCAN_JOB,
        "allowed_transition": (
            f"{AttachmentScanJobStatus.QUEUED.value}"
            f"->{AttachmentScanJobStatus.RESERVED.value}"
        ),
        "allowed_row": "AttachmentScanJob",
        "calls_apply_scan_job_update_plan": False,
        "calls_scanner_adapter": False,
        "emits_audit": False,
        "mutates_evidence_record": False,
        "mutates_claim_record": False,
        "mutates_review_request": False,
        "is_scanning": False,
        "is_verification": False,
    }
