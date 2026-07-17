"""
Scanner worker dry-run planning + disabled runner contract (0053-F26).

Defines the future scanner-worker runtime shape and dry-run decision objects
describing what a future worker would do. The runner is disabled: it never
loops, reserves jobs, calls scanners, reads files, mutates DB, or emits audit.

A dry-run contract is not a worker feature and is not verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

SCAN_WORKER_ENABLED: Final[bool] = False
SCAN_WORKER_DRY_RUN_ENABLED: Final[bool] = False
SCAN_WORKER_BACKGROUND_LOOP_ENABLED: Final[bool] = False
SCAN_WORKER_STARTUP_REGISTRATION_ENABLED: Final[bool] = False
SCAN_WORKER_DB_MUTATION_ENABLED: Final[bool] = False
SCAN_WORKER_FILE_ACCESS_ENABLED: Final[bool] = False
SCAN_WORKER_SCANNER_EXECUTION_ENABLED: Final[bool] = False
SCAN_WORKER_AUDIT_EMIT_ENABLED: Final[bool] = False

SCAN_WORKER_DRY_RUN_WARNING: Final[str] = (
    "Scanner worker execution is planned but not active in this version."
)


class ScanWorkerRunnerMode(StrEnum):
    DISABLED = "disabled"
    PLANNED_DRY_RUN = "planned_dry_run"
    PLANNED_BACKGROUND_WORKER = "planned_background_worker"


class ScanWorkerDryRunDecision(StrEnum):
    NO_JOB_AVAILABLE = "no_job_available"
    WOULD_RESERVE_JOB = "would_reserve_job"
    WOULD_SKIP_NON_PENDING_JOB = "would_skip_non_pending_job"
    WOULD_SKIP_HASH_MISMATCH = "would_skip_hash_mismatch"
    WOULD_SKIP_SCANNER_UNAVAILABLE = "would_skip_scanner_unavailable"
    WOULD_REJECT_UNPERSISTABLE_PLAN = "would_reject_unpersistable_plan"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class ScanWorkerDryRunPlan:
    runner_enabled: bool
    dry_run_enabled: bool
    background_loop_enabled: bool
    startup_registration_enabled: bool
    db_mutation_enabled: bool
    file_access_enabled: bool
    scanner_execution_enabled: bool
    audit_emit_enabled: bool
    mode: ScanWorkerRunnerMode
    decision: ScanWorkerDryRunDecision
    warning: str


def scan_worker_is_enabled() -> bool:
    return SCAN_WORKER_ENABLED is True


def scan_worker_dry_run_warning() -> str:
    return SCAN_WORKER_DRY_RUN_WARNING


def current_scan_worker_dry_run_plan() -> ScanWorkerDryRunPlan:
    """Return the inactive runner plan for this version."""
    return ScanWorkerDryRunPlan(
        runner_enabled=False,
        dry_run_enabled=False,
        background_loop_enabled=False,
        startup_registration_enabled=False,
        db_mutation_enabled=False,
        file_access_enabled=False,
        scanner_execution_enabled=False,
        audit_emit_enabled=False,
        mode=ScanWorkerRunnerMode.DISABLED,
        decision=ScanWorkerDryRunDecision.DISABLED,
        warning=SCAN_WORKER_DRY_RUN_WARNING,
    )


def build_scan_worker_dry_run_decision(
    *,
    job_status: str | None = None,
    scanner_available: bool | None = None,
    plan_persistable: bool | None = None,
    hash_matches: bool | None = None,
    job_available: bool | None = None,
) -> ScanWorkerDryRunDecision:
    """
    Map explicit planning hints to a dry-run decision object.

    Does not read files, call scanners, reserve jobs, or mutate DB.
    Runner remains disabled in F26 regardless of decision value.
    """
    # Hard gate: runner/dry-run disabled → always disabled decision for
    # default/no-hint calls; explicit hypothetical hints may still describe
    # what a future approved worker would do (object only).
    if not SCAN_WORKER_ENABLED and not SCAN_WORKER_DRY_RUN_ENABLED:
        # Allow hypothetical planning when callers pass explicit hints.
        has_hint = any(
            v is not None
            for v in (
                job_status,
                scanner_available,
                plan_persistable,
                hash_matches,
                job_available,
            )
        )
        if not has_hint:
            return ScanWorkerDryRunDecision.DISABLED

    if job_available is False:
        return ScanWorkerDryRunDecision.NO_JOB_AVAILABLE

    if hash_matches is False:
        return ScanWorkerDryRunDecision.WOULD_SKIP_HASH_MISMATCH

    if scanner_available is False:
        return ScanWorkerDryRunDecision.WOULD_SKIP_SCANNER_UNAVAILABLE

    if plan_persistable is False:
        return ScanWorkerDryRunDecision.WOULD_REJECT_UNPERSISTABLE_PLAN

    if job_status is not None:
        status = str(job_status).strip().lower()
        if status in {"queued", "scan_pending", "pending"}:
            return ScanWorkerDryRunDecision.WOULD_RESERVE_JOB
        if status in {"reserved", "completed", "failed", "cancelled"}:
            return ScanWorkerDryRunDecision.WOULD_SKIP_NON_PENDING_JOB

    if job_available is True:
        return ScanWorkerDryRunDecision.WOULD_RESERVE_JOB

    return ScanWorkerDryRunDecision.DISABLED


def assert_scan_worker_runner_disabled() -> None:
    """
    Hard assert that the scanner worker runner remains inactive.

    Does not create routes, files, DB rows, or background tasks.
    """
    plan = current_scan_worker_dry_run_plan()
    if (
        plan.runner_enabled
        or plan.dry_run_enabled
        or plan.background_loop_enabled
        or plan.startup_registration_enabled
        or plan.db_mutation_enabled
        or plan.file_access_enabled
        or plan.scanner_execution_enabled
        or plan.audit_emit_enabled
        or scan_worker_is_enabled()
    ):
        raise RuntimeError(
            "Scanner worker runner must remain disabled in this version."
        )


def scan_worker_dry_run_summary() -> dict[str, object]:
    plan = current_scan_worker_dry_run_plan()
    return {
        "runner_enabled": plan.runner_enabled,
        "dry_run_enabled": plan.dry_run_enabled,
        "background_loop_enabled": plan.background_loop_enabled,
        "startup_registration_enabled": plan.startup_registration_enabled,
        "db_mutation_enabled": plan.db_mutation_enabled,
        "file_access_enabled": plan.file_access_enabled,
        "scanner_execution_enabled": plan.scanner_execution_enabled,
        "audit_emit_enabled": plan.audit_emit_enabled,
        "mode": plan.mode.value,
        "planned_mode": ScanWorkerRunnerMode.PLANNED_DRY_RUN.value,
        "decision": plan.decision.value,
        "warning": plan.warning,
        "calls_apply_scan_job_update_plan": False,
        "calls_scanner_adapter": False,
        "reads_file_bytes": False,
        "mutates_attachment_scan_job": False,
        "mutates_evidence_record": False,
        "mutates_claim_record": False,
        "mutates_review_request": False,
        "registers_on_startup": False,
        "runs_background_loop": False,
        "is_worker_feature": False,
        "is_verification": False,
    }
