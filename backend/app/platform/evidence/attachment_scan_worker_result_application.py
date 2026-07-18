"""
Scanner worker result application guard (0053-F29).

Applies an already-produced, persistable ScanJobUpdatePlan to an
AttachmentScanJob only when owner, state, triple-hash, policy, idempotency and
PostgreSQL concurrency requirements pass.

Does not run a scanner, open files, spawn processes, call network scanners,
emit audit, mutate EvidenceRecord / ClaimRecord / ReviewRequest, or register a
worker loop.

Applying a worker result plan is not verification.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.attachment_scan import AttachmentScanJob
from app.db.models.evidence import EvidenceRecord
from app.platform.evidence.attachment_scan_queue import AttachmentScanJobStatus
from app.platform.evidence.attachment_scan_result_persistence import (
    TERMINAL_JOB_STATUSES,
    ScanJobPersistenceError,
    apply_normalized_scan_job_update_to_loaded_job,
    assert_scan_job_update_allowed,
    normalize_scan_job_update_plan,
    plan_is_persistable,
)
from app.platform.evidence.attachment_scan_worker import (
    ScanJobUpdatePlan,
    ScanWorkerAction,
)
from app.platform.evidence.refs import EvidenceRefError

SCAN_WORKER_RESULT_APPLICATION_GUARD_ENABLED: Final[bool] = True
SCAN_WORKER_RESULT_APPLICATION_EXECUTES_SCANNER: Final[bool] = False
SCAN_WORKER_RESULT_APPLICATION_READS_FILES: Final[bool] = False
SCAN_WORKER_RESULT_APPLICATION_REGISTERS_WORKER: Final[bool] = False
SCAN_WORKER_RESULT_APPLICATION_EXPOSES_ROUTE: Final[bool] = False
SCAN_WORKER_RESULT_APPLICATION_MUTATES_ONLY_SCAN_JOB: Final[bool] = True
SCAN_WORKER_RESULT_APPLICATION_LOCK_ORDER: Final[str] = (
    "attachment_scan_job_then_evidence_record"
)

_F29_ALLOWED_ACTIONS: Final[frozenset[ScanWorkerAction]] = frozenset(
    {
        ScanWorkerAction.COMPLETE_PASSED,
        ScanWorkerAction.COMPLETE_FAILED,
        ScanWorkerAction.QUARANTINE_REQUIRED,
        ScanWorkerAction.MARK_ERROR,
    }
)

_F29_ALLOWED_TARGETS: Final[frozenset[str]] = frozenset(
    {
        AttachmentScanJobStatus.COMPLETED.value,
        AttachmentScanJobStatus.FAILED.value,
    }
)

_IDEMPOTENCY_FIELDS: Final[tuple[str, ...]] = (
    "job_status",
    "attachment_safety_status",
    "engine_name",
    "engine_version",
    "safe_error_code",
    "safe_error_message",
)


class ScanWorkerResultApplicationDecision(StrEnum):
    APPLIED = "applied"
    ALREADY_APPLIED = "already_applied"
    NOT_FOUND = "not_found"
    EVIDENCE_NOT_FOUND = "evidence_not_found"
    HASH_MISMATCH = "hash_mismatch"
    NOT_RESERVED = "not_reserved"
    ACTION_NOT_ALLOWED = "action_not_allowed"
    PLAN_NOT_PERSISTABLE = "plan_not_persistable"
    CONFLICTING_REPLAY = "conflicting_replay"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class ScanWorkerResultApplicationResult:
    applied: bool
    decision: ScanWorkerResultApplicationDecision
    job_id: uuid.UUID | None
    owner_user_id: uuid.UUID | None
    previous_status: str | None
    new_status: str | None
    attempt_count: int | None
    completed_at: datetime | None
    safe_message: str


class ScanWorkerResultApplicationError(EvidenceRefError):
    """Raised when result-application assertion fails."""

    def __init__(
        self,
        message: str,
        *,
        decision: ScanWorkerResultApplicationDecision,
    ) -> None:
        super().__init__(message)
        self.decision = decision


def _result(
    *,
    applied: bool,
    decision: ScanWorkerResultApplicationDecision,
    job_id: uuid.UUID | None,
    owner_user_id: uuid.UUID | None,
    previous_status: str | None,
    new_status: str | None,
    attempt_count: int | None,
    completed_at: datetime | None,
    safe_message: str,
) -> ScanWorkerResultApplicationResult:
    return ScanWorkerResultApplicationResult(
        applied=applied,
        decision=decision,
        job_id=job_id,
        owner_user_id=owner_user_id,
        previous_status=previous_status,
        new_status=new_status,
        attempt_count=attempt_count,
        completed_at=completed_at,
        safe_message=safe_message,
    )


def _effective_terminal_projection(
    job: AttachmentScanJob,
    normalized_plan: ScanJobUpdatePlan,
) -> tuple[object, ...]:
    """
    Effective six-field projection after F22 non-None write semantics.

    None plan fields preserve the stored job values (same as F22 mutate).
    """
    return (
        str(normalized_plan.job_status),
        (
            normalized_plan.attachment_safety_status
            if normalized_plan.attachment_safety_status is not None
            else job.attachment_safety_status
        ),
        (
            normalized_plan.engine_name
            if normalized_plan.engine_name is not None
            else job.engine_name
        ),
        (
            normalized_plan.engine_version
            if normalized_plan.engine_version is not None
            else job.engine_version
        ),
        (
            normalized_plan.safe_error_code
            if normalized_plan.safe_error_code is not None
            else job.safe_error_code
        ),
        (
            normalized_plan.safe_error_message
            if normalized_plan.safe_error_message is not None
            else job.safe_error_message
        ),
    )


def _stored_terminal_projection(job: AttachmentScanJob) -> tuple[object, ...]:
    return (
        str(job.job_status),
        job.attachment_safety_status,
        job.engine_name,
        job.engine_version,
        job.safe_error_code,
        job.safe_error_message,
    )


def assert_f29_result_plan_allowed(plan: ScanJobUpdatePlan) -> None:
    """Validate F29-specific action/target surface before lock-held apply."""
    if not isinstance(plan, ScanJobUpdatePlan):
        raise ScanWorkerResultApplicationError(
            "Scan job update plan is not persistable.",
            decision=ScanWorkerResultApplicationDecision.PLAN_NOT_PERSISTABLE,
        )
    if not plan_is_persistable(plan):
        raise ScanWorkerResultApplicationError(
            "Scan job update plan is not persistable "
            "(apply_to_database must be True and action must not be no_op).",
            decision=ScanWorkerResultApplicationDecision.PLAN_NOT_PERSISTABLE,
        )
    if plan.action not in _F29_ALLOWED_ACTIONS:
        raise ScanWorkerResultApplicationError(
            f"F29 result application rejects action: {plan.action.value}",
            decision=ScanWorkerResultApplicationDecision.ACTION_NOT_ALLOWED,
        )
    target = str(plan.job_status)
    if target not in _F29_ALLOWED_TARGETS:
        raise ScanWorkerResultApplicationError(
            f"F29 result application rejects target status: {target}",
            decision=ScanWorkerResultApplicationDecision.ACTION_NOT_ALLOWED,
        )
    if target == AttachmentScanJobStatus.CANCELLED.value:
        raise ScanWorkerResultApplicationError(
            "F29 result application rejects cancelled target.",
            decision=ScanWorkerResultApplicationDecision.ACTION_NOT_ALLOWED,
        )


async def _lock_owner_scoped_scan_job(
    db: AsyncSession,
    *,
    scan_job_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> AttachmentScanJob | None:
    """Lock AttachmentScanJob first (owner-scoped). Missing → None (safe 404)."""
    return (
        await db.execute(
            select(AttachmentScanJob)
            .where(
                AttachmentScanJob.id == scan_job_id,
                AttachmentScanJob.owner_user_id == owner_user_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()


async def _lock_owner_scoped_evidence(
    db: AsyncSession,
    *,
    evidence_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> EvidenceRecord | None:
    """Lock EvidenceRecord second (owner-scoped). Missing → None (safe 404)."""
    return (
        await db.execute(
            select(EvidenceRecord)
            .where(
                EvidenceRecord.id == evidence_id,
                EvidenceRecord.owner_user_id == owner_user_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()


async def apply_attachment_scan_worker_result(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    scan_job_id: uuid.UUID,
    expected_content_hash_snapshot: str,
    plan: ScanJobUpdatePlan,
) -> ScanWorkerResultApplicationResult:
    """
    Apply a persistable ScanJobUpdatePlan under F29 guards.

    Lock order (mandatory): AttachmentScanJob FOR UPDATE, then EvidenceRecord
    FOR UPDATE. Validates triple-hash and F22 policy, then mutates the job only.
    Exact-match terminal replay returns already_applied without rewriting fields.
    """
    if not SCAN_WORKER_RESULT_APPLICATION_GUARD_ENABLED:
        return _result(
            applied=False,
            decision=ScanWorkerResultApplicationDecision.DISABLED,
            job_id=scan_job_id,
            owner_user_id=owner_user_id,
            previous_status=None,
            new_status=None,
            attempt_count=None,
            completed_at=None,
            safe_message="Scan worker result application is disabled in this version.",
        )

    job = await _lock_owner_scoped_scan_job(
        db, scan_job_id=scan_job_id, owner_user_id=owner_user_id
    )
    if job is None:
        # Owner-scoped miss: do not distinguish missing vs other-owner.
        return _result(
            applied=False,
            decision=ScanWorkerResultApplicationDecision.NOT_FOUND,
            job_id=scan_job_id,
            owner_user_id=owner_user_id,
            previous_status=None,
            new_status=None,
            attempt_count=None,
            completed_at=None,
            safe_message="Scan job was not found for this owner.",
        )

    # Capture identity/status before any rollback (rollback expires the ORM row).
    locked_job_id = job.id
    locked_evidence_id = job.evidence_id
    previous = str(job.job_status)
    prior_attempt = int(job.attempt_count or 0)
    prior_completed = job.completed_at
    prior_snapshot = str(job.content_hash_snapshot or "").strip()
    prior_projection = _stored_terminal_projection(job)

    try:
        evidence = await _lock_owner_scoped_evidence(
            db, evidence_id=locked_evidence_id, owner_user_id=owner_user_id
        )
        if evidence is None:
            await db.rollback()
            return _result(
                applied=False,
                decision=ScanWorkerResultApplicationDecision.EVIDENCE_NOT_FOUND,
                job_id=locked_job_id,
                owner_user_id=owner_user_id,
                previous_status=previous,
                new_status=previous,
                attempt_count=prior_attempt,
                completed_at=prior_completed,
                safe_message="Linked evidence was not found for this owner.",
            )

        expected = str(expected_content_hash_snapshot).strip()
        live_hash = str(evidence.content_hash or "").strip()
        if not expected or not prior_snapshot or not live_hash:
            await db.rollback()
            return _result(
                applied=False,
                decision=ScanWorkerResultApplicationDecision.HASH_MISMATCH,
                job_id=locked_job_id,
                owner_user_id=owner_user_id,
                previous_status=previous,
                new_status=previous,
                attempt_count=prior_attempt,
                completed_at=prior_completed,
                safe_message="Content hash guard failed for this scan job.",
            )
        if not (live_hash == prior_snapshot == expected):
            await db.rollback()
            return _result(
                applied=False,
                decision=ScanWorkerResultApplicationDecision.HASH_MISMATCH,
                job_id=locked_job_id,
                owner_user_id=owner_user_id,
                previous_status=previous,
                new_status=previous,
                attempt_count=prior_attempt,
                completed_at=prior_completed,
                safe_message="Content hash guard failed for this scan job.",
            )

        try:
            assert_f29_result_plan_allowed(plan)
        except ScanWorkerResultApplicationError as exc:
            await db.rollback()
            return _result(
                applied=False,
                decision=exc.decision,
                job_id=locked_job_id,
                owner_user_id=owner_user_id,
                previous_status=previous,
                new_status=previous,
                attempt_count=prior_attempt,
                completed_at=prior_completed,
                safe_message=str(exc),
            )

        normalized = normalize_scan_job_update_plan(plan)

        # Terminal exact-match soft replay (after locks + hash + normalize).
        if previous in TERMINAL_JOB_STATUSES:
            # Rebuild a lightweight view from captured fields + normalized plan.
            effective = (
                str(normalized.job_status),
                (
                    normalized.attachment_safety_status
                    if normalized.attachment_safety_status is not None
                    else prior_projection[1]
                ),
                (
                    normalized.engine_name
                    if normalized.engine_name is not None
                    else prior_projection[2]
                ),
                (
                    normalized.engine_version
                    if normalized.engine_version is not None
                    else prior_projection[3]
                ),
                (
                    normalized.safe_error_code
                    if normalized.safe_error_code is not None
                    else prior_projection[4]
                ),
                (
                    normalized.safe_error_message
                    if normalized.safe_error_message is not None
                    else prior_projection[5]
                ),
            )
            if effective == prior_projection:
                await db.rollback()
                return _result(
                    applied=False,
                    decision=ScanWorkerResultApplicationDecision.ALREADY_APPLIED,
                    job_id=locked_job_id,
                    owner_user_id=owner_user_id,
                    previous_status=previous,
                    new_status=previous,
                    attempt_count=prior_attempt,
                    completed_at=prior_completed,
                    safe_message=(
                        "Scan job result already applied (exact-match replay)."
                    ),
                )
            await db.rollback()
            return _result(
                applied=False,
                decision=ScanWorkerResultApplicationDecision.CONFLICTING_REPLAY,
                job_id=locked_job_id,
                owner_user_id=owner_user_id,
                previous_status=previous,
                new_status=previous,
                attempt_count=prior_attempt,
                completed_at=prior_completed,
                safe_message=(
                    "Conflicting terminal replay rejected; "
                    f"projection fields={','.join(_IDEMPOTENCY_FIELDS)}."
                ),
            )

        if previous != AttachmentScanJobStatus.RESERVED.value:
            await db.rollback()
            return _result(
                applied=False,
                decision=ScanWorkerResultApplicationDecision.NOT_RESERVED,
                job_id=locked_job_id,
                owner_user_id=owner_user_id,
                previous_status=previous,
                new_status=previous,
                attempt_count=prior_attempt,
                completed_at=prior_completed,
                safe_message=(
                    "Only reserved scan jobs can accept a worker result; "
                    f"current={previous}"
                ),
            )

        try:
            assert_scan_job_update_allowed(job, normalized)
        except ScanJobPersistenceError as exc:
            await db.rollback()
            return _result(
                applied=False,
                decision=ScanWorkerResultApplicationDecision.ACTION_NOT_ALLOWED,
                job_id=locked_job_id,
                owner_user_id=owner_user_id,
                previous_status=previous,
                new_status=previous,
                attempt_count=prior_attempt,
                completed_at=prior_completed,
                safe_message=str(exc),
            )

        now = datetime.now(timezone.utc)
        apply_normalized_scan_job_update_to_loaded_job(job, normalized, now)
        new_status = str(job.job_status)
        new_attempt = int(job.attempt_count or 0)
        new_completed = job.completed_at
        await db.commit()

        return _result(
            applied=True,
            decision=ScanWorkerResultApplicationDecision.APPLIED,
            job_id=locked_job_id,
            owner_user_id=owner_user_id,
            previous_status=previous,
            new_status=new_status,
            attempt_count=new_attempt,
            completed_at=new_completed,
            safe_message=(
                "Scan job worker result applied. "
                "Result application is not verification."
            ),
        )
    except Exception:
        await db.rollback()
        raise


def result_application_guard_summary() -> dict[str, object]:
    return {
        "guard_enabled": SCAN_WORKER_RESULT_APPLICATION_GUARD_ENABLED,
        "executes_scanner": SCAN_WORKER_RESULT_APPLICATION_EXECUTES_SCANNER,
        "reads_files": SCAN_WORKER_RESULT_APPLICATION_READS_FILES,
        "registers_worker": SCAN_WORKER_RESULT_APPLICATION_REGISTERS_WORKER,
        "exposes_route": SCAN_WORKER_RESULT_APPLICATION_EXPOSES_ROUTE,
        "mutates_only_scan_job": SCAN_WORKER_RESULT_APPLICATION_MUTATES_ONLY_SCAN_JOB,
        "lock_order": SCAN_WORKER_RESULT_APPLICATION_LOCK_ORDER,
        "allowed_transitions": sorted(
            f"{AttachmentScanJobStatus.RESERVED.value}->{t}"
            for t in _F29_ALLOWED_TARGETS
        ),
        "allowed_actions": sorted(a.value for a in _F29_ALLOWED_ACTIONS),
        "idempotency_projection": list(_IDEMPOTENCY_FIELDS),
        "triple_hash": (
            "evidence.content_hash==job.content_hash_snapshot"
            "==expected_content_hash_snapshot"
        ),
        "allowed_row": "AttachmentScanJob",
        "reuses_f22_normalize_assert_mutate": True,
        "calls_public_apply_scan_job_update_plan": False,
        "calls_scanner_adapter": False,
        "emits_audit": False,
        "mutates_evidence_record": False,
        "mutates_claim_record": False,
        "mutates_review_request": False,
        "is_scanning": False,
        "is_verification": False,
    }
