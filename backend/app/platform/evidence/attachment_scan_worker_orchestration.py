"""
Scanner worker single-job orchestration guard (0053-F31).

One internal, supplied-job callable that orchestrates a single attachment scan
attempt across three separate database boundaries:

    1. reservation transaction (F27) — queued → reserved, then closed
    2. adapter execution — no active DB session, transaction or lock
    3. result-application transaction (F29) — reserved → completed|failed

Before any database lookup it preflights the configured adapter using
``adapter_info()`` only. When no executable scanner is configured (the normal
production state), it returns a generic scanner_unavailable outcome and leaves
the job queued and untouched: no F27, no ``scan_attachment``, no F29, no
attempt_count / started_at change, no scan_error, no fabricated clean result.

This module does not run a worker loop, poll the queue, select jobs, register
on startup, schedule work, add a real scanner dependency, read files/storage,
spawn processes, call the network, emit audit, or expose routes/UI. It applies
results only through the F29 guard and never bypasses it.

Orchestrating one guarded scan attempt is not scanning and is not verification.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import async_session_factory
from app.platform.evidence.attachment_safety import AttachmentSafetyStatus
from app.platform.evidence.attachment_scan_queue import AttachmentScanJobStatus
from app.platform.evidence.attachment_scan_result_persistence import (
    build_persistable_scan_job_update_plan,
    plan_is_persistable,
)
from app.platform.evidence.attachment_scan_worker import (
    ScanJobUpdatePlan,
    ScannerVerdict,
    ScanResultContract,
    ScanWorkerAction,
    build_scan_job_update_from_result,
)
from app.platform.evidence.attachment_scan_worker_reservation import (
    ReservedJobSnapshot,
    ScanWorkerReservationDecision,
    reserve_attachment_scan_job_for_worker,
)
from app.platform.evidence.attachment_scan_worker_result_application import (
    ScanWorkerResultApplicationDecision,
    apply_attachment_scan_worker_result,
)
from app.platform.evidence.attachment_scanner_adapter import (
    AttachmentScannerAdapter,
    ScannerAdapterCapability,
    ScannerAdapterInfo,
    ScannerAvailability,
    get_configured_attachment_scanner_adapter,
)

SCAN_WORKER_ORCHESTRATION_GUARD_ENABLED: Final[bool] = True
SCAN_WORKER_ORCHESTRATION_RUNS_WORKER_LOOP: Final[bool] = False
SCAN_WORKER_ORCHESTRATION_POLLS_QUEUE: Final[bool] = False
SCAN_WORKER_ORCHESTRATION_SELECTS_JOBS: Final[bool] = False
SCAN_WORKER_ORCHESTRATION_REGISTERS_ON_STARTUP: Final[bool] = False
SCAN_WORKER_ORCHESTRATION_READS_FILES: Final[bool] = False
SCAN_WORKER_ORCHESTRATION_USES_REAL_SCANNER_DEPENDENCY: Final[bool] = False
SCAN_WORKER_ORCHESTRATION_EXPOSES_ROUTE: Final[bool] = False
SCAN_WORKER_ORCHESTRATION_APPLIES_RESULTS_VIA_F29_ONLY: Final[bool] = True
SCAN_WORKER_ORCHESTRATION_SESSION_BOUNDARIES: Final[int] = 3

# Safe error codes (all inside the F21 allow-list; normalized again by F22).
_SAFE_CODE_UNAVAILABLE: Final[str] = "scanner_unavailable"
_SAFE_CODE_OUTPUT_UNAVAILABLE: Final[str] = "scanner_output_unavailable"
_SAFE_CODE_ERROR: Final[str] = "scanner_error"


class ScanWorkerOrchestrationOutcome(StrEnum):
    SCANNER_UNAVAILABLE = "scanner_unavailable"
    SKIPPED_UNAVAILABLE = "skipped_unavailable"
    RESERVATION_REJECTED = "reservation_rejected"
    APPLIED = "applied"
    ALREADY_APPLIED = "already_applied"
    RESULT_APPLICATION_REJECTED = "result_application_rejected"


@dataclass(frozen=True, slots=True)
class ScanWorkerOrchestrationResult:
    """
    Structured, owner-safe outcome of one orchestration attempt.

    Never carries file paths, storage URIs, raw exceptions, internal database
    details, or another owner's resource existence.
    """

    outcome: ScanWorkerOrchestrationOutcome
    scanner_executable: bool
    reserved: bool
    job_id: uuid.UUID | None
    owner_user_id: uuid.UUID | None
    reservation_decision: str | None
    result_application_decision: str | None
    safe_message: str


# Test-only adapter injection seam. Production always resolves the configured
# factory. This is never part of the product-facing input surface.
AdapterFactory = Callable[[], AttachmentScannerAdapter]
SessionFactory = Callable[[], AsyncSession] | async_sessionmaker[AsyncSession]


def adapter_is_executable(info: ScannerAdapterInfo) -> bool:
    """
    Smallest capability preflight over ``adapter_info()`` only.

    Executable requires availability AVAILABLE, the MALWARE_SCAN capability
    present, and the UNAVAILABLE capability absent. Does not call the scanner.
    """
    return (
        info.availability == ScannerAvailability.AVAILABLE
        and ScannerAdapterCapability.MALWARE_SCAN in info.capabilities
        and ScannerAdapterCapability.UNAVAILABLE not in info.capabilities
    )


def _unavailable_result(
    *,
    scan_job_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> ScanWorkerOrchestrationResult:
    """Generic unavailable outcome. Reveals nothing about the supplied job."""
    return ScanWorkerOrchestrationResult(
        outcome=ScanWorkerOrchestrationOutcome.SCANNER_UNAVAILABLE,
        scanner_executable=False,
        reserved=False,
        job_id=scan_job_id,
        owner_user_id=owner_user_id,
        reservation_decision=None,
        result_application_decision=None,
        safe_message="Malware scanning is not available in this version.",
    )


def _safe_mark_error_plan(
    *,
    safe_error_code: str,
    safe_error_message: str | None = None,
) -> ScanJobUpdatePlan:
    """
    Build a persistable MARK_ERROR plan with no fabricated engine identity.

    Reuses the F22 builder (which normalizes codes/messages via F21). Used when
    the reserved attempt cannot yield a trustworthy verdict.
    """
    return build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.MARK_ERROR,
        job_status=AttachmentScanJobStatus.FAILED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_ERROR.value,
        engine_name=None,
        engine_version=None,
        safe_error_code=safe_error_code,
        safe_error_message=safe_error_message,
    )


def _plan_from_reserved_scan_result(result: object) -> ScanJobUpdatePlan:
    """
    Convert an adapter result into a persistable plan after reservation.

    Legitimate verdicts (CLEAN / MALICIOUS / SUSPICIOUS / TIMEOUT / ERROR /
    UNSUPPORTED) reuse the F17 result→plan mapping and are rebuilt as
    persistable through the F22 helper (no duplicated normalization). Any
    NOT_RUN, malformed return, or mapping failure becomes a safe persistable
    MARK_ERROR. Never fabricates CLEAN / scan_passed / an engine identity.
    """
    if not isinstance(result, ScanResultContract):
        # Malformed return type from the adapter.
        return _safe_mark_error_plan(safe_error_code=_SAFE_CODE_OUTPUT_UNAVAILABLE)

    try:
        base = build_scan_job_update_from_result(result)
    except (asyncio.CancelledError, KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        # Malformed result object (bad verdict / fields) during mapping.
        return _safe_mark_error_plan(safe_error_code=_SAFE_CODE_OUTPUT_UNAVAILABLE)

    # NOT_RUN maps to a non-persistable NO_OP; after a real reservation this is
    # an unexpected/unavailable attempt → terminalize safely as MARK_ERROR.
    if base.action is ScanWorkerAction.NO_OP or base.job_status is None:
        code = _SAFE_CODE_UNAVAILABLE
        if result.verdict is not ScannerVerdict.NOT_RUN:
            code = _SAFE_CODE_OUTPUT_UNAVAILABLE
        return _safe_mark_error_plan(safe_error_code=code)

    # Rebuild the adapter-derived mapping as an explicit persistable plan.
    return build_persistable_scan_job_update_plan(
        action=base.action,
        job_status=base.job_status,
        attachment_safety_status=base.attachment_safety_status,
        engine_name=base.engine_name,
        engine_version=base.engine_version,
        safe_error_code=base.safe_error_code,
        safe_error_message=base.safe_error_message,
        quarantine_required=base.quarantine_required,
    )


def _execute_adapter_to_plan(
    adapter: AttachmentScannerAdapter,
    snapshot: ReservedJobSnapshot,
) -> ScanJobUpdatePlan:
    """
    Boundary 2: invoke the adapter with authoritative reserved-row values only.

    No active database session/transaction/lock exists here. Process-level
    interruptions propagate. Ordinary failures become a safe MARK_ERROR plan.
    """
    try:
        raw = adapter.scan_attachment(
            evidence_id=snapshot.evidence_id,
            content_hash=snapshot.content_hash_snapshot,
            mime_type=snapshot.mime_type_snapshot,
            size_bytes=snapshot.size_bytes_snapshot,
        )
    except (asyncio.CancelledError, KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        # Ordinary operational exception from adapter invocation.
        return _safe_mark_error_plan(safe_error_code=_SAFE_CODE_ERROR)

    return _plan_from_reserved_scan_result(raw)


async def orchestrate_attachment_scan_job(
    *,
    owner_user_id: uuid.UUID,
    scan_job_id: uuid.UUID,
    expected_content_hash_snapshot: str,
    session_factory: SessionFactory = async_session_factory,
    adapter_factory: AdapterFactory = get_configured_attachment_scanner_adapter,
) -> ScanWorkerOrchestrationResult:
    """
    Orchestrate one guarded scan attempt for a single supplied job.

    Product-facing inputs are only ``owner_user_id``, ``scan_job_id`` and
    ``expected_content_hash_snapshot``. No caller-supplied evidence id, MIME,
    size, storage path, attachment bytes, snapshot metadata, or production
    adapter identity is accepted. ``adapter_factory`` is a test-only injection
    seam; production resolves the configured factory.

    Flow: adapter preflight → (if executable) F27 reservation in a short-lived
    session → adapter execution with no active session → F29 application in a
    new short-lived session. Process interruptions propagate and may leave the
    job reserved (a documented recovery/watch item).
    """
    # --- Adapter capability preflight (adapter_info only; no DB, no scan) ---
    adapter = adapter_factory()
    try:
        info = adapter.adapter_info()
    except (asyncio.CancelledError, KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        # adapter_info failed: treat as unavailable, before any reservation.
        return _unavailable_result(
            scan_job_id=scan_job_id, owner_user_id=owner_user_id
        )

    if not adapter_is_executable(info):
        # Normal production state (noop/unavailable/disabled adapter).
        return _unavailable_result(
            scan_job_id=scan_job_id, owner_user_id=owner_user_id
        )

    # --- Boundary 1: reservation transaction (F27), then close the session ---
    async with session_factory() as reservation_session:
        reservation = await reserve_attachment_scan_job_for_worker(
            reservation_session,
            job_id=scan_job_id,
            owner_user_id=owner_user_id,
            expected_content_hash_snapshot=expected_content_hash_snapshot,
        )

    if (
        reservation.decision is not ScanWorkerReservationDecision.RESERVED
        or reservation.snapshot is None
    ):
        return ScanWorkerOrchestrationResult(
            outcome=ScanWorkerOrchestrationOutcome.RESERVATION_REJECTED,
            scanner_executable=True,
            reserved=False,
            job_id=scan_job_id,
            owner_user_id=owner_user_id,
            reservation_decision=reservation.decision.value,
            result_application_decision=None,
            safe_message=reservation.safe_message,
        )

    snapshot = reservation.snapshot

    # --- Boundary 2: adapter execution with NO active DB session/txn/lock ---
    plan = _execute_adapter_to_plan(adapter, snapshot)

    # --- Boundary 3: result application through F29 only (new session) ---
    async with session_factory() as application_session:
        application = await apply_attachment_scan_worker_result(
            application_session,
            owner_user_id=owner_user_id,
            scan_job_id=scan_job_id,
            expected_content_hash_snapshot=expected_content_hash_snapshot,
            plan=plan,
        )

    if application.decision is ScanWorkerResultApplicationDecision.APPLIED:
        outcome = ScanWorkerOrchestrationOutcome.APPLIED
        safe_message = "Scan job result applied. Orchestration is not verification."
        reserved = False
    elif application.decision is ScanWorkerResultApplicationDecision.ALREADY_APPLIED:
        outcome = ScanWorkerOrchestrationOutcome.ALREADY_APPLIED
        safe_message = "Scan job result was already applied."
        reserved = False
    else:
        # Any F29 guard rejection: leave DB state unchanged; job stays reserved.
        outcome = ScanWorkerOrchestrationOutcome.RESULT_APPLICATION_REJECTED
        safe_message = (
            "Scan job result could not be applied; state left unchanged."
        )
        reserved = True

    return ScanWorkerOrchestrationResult(
        outcome=outcome,
        scanner_executable=True,
        reserved=reserved,
        job_id=scan_job_id,
        owner_user_id=owner_user_id,
        reservation_decision=reservation.decision.value,
        result_application_decision=application.decision.value,
        safe_message=safe_message,
    )


def orchestration_guard_summary() -> dict[str, object]:
    """Safe introspection for docs/tests — no side effects."""
    return {
        "guard_enabled": SCAN_WORKER_ORCHESTRATION_GUARD_ENABLED,
        "session_boundaries": SCAN_WORKER_ORCHESTRATION_SESSION_BOUNDARIES,
        "runs_worker_loop": SCAN_WORKER_ORCHESTRATION_RUNS_WORKER_LOOP,
        "polls_queue": SCAN_WORKER_ORCHESTRATION_POLLS_QUEUE,
        "selects_jobs": SCAN_WORKER_ORCHESTRATION_SELECTS_JOBS,
        "registers_on_startup": SCAN_WORKER_ORCHESTRATION_REGISTERS_ON_STARTUP,
        "reads_files": SCAN_WORKER_ORCHESTRATION_READS_FILES,
        "uses_real_scanner_dependency": (
            SCAN_WORKER_ORCHESTRATION_USES_REAL_SCANNER_DEPENDENCY
        ),
        "exposes_route": SCAN_WORKER_ORCHESTRATION_EXPOSES_ROUTE,
        "applies_results_via_f29_only": (
            SCAN_WORKER_ORCHESTRATION_APPLIES_RESULTS_VIA_F29_ONLY
        ),
        "preflight_uses_adapter_info_only": True,
        "invokes_configured_adapter_seam": True,
        "reserves_via_f27": True,
        "no_active_session_during_adapter": True,
        "calls_public_apply_scan_job_update_plan": False,
        "forces_terminal_state_on_rejection": False,
        "auto_cancels": False,
        "adds_lease_ttl_reclaim": False,
        "emits_audit": False,
        "mutates_evidence_record": False,
        "mutates_claim_record": False,
        "mutates_review_request": False,
        "is_scanning": False,
        "is_verification": False,
    }
