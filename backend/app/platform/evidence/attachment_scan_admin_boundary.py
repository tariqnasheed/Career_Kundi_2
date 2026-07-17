"""
Scan/quarantine admin boundary planning + disabled surface (0053-F25).

Defines the future admin/operations boundary for scan jobs, quarantine
decisions, and audit review: planned safe actions, explicit forbidden powers,
and a disabled admin surface. Does not add routes, UI, workflows, DB writes,
scanner execution, quarantine enforcement, or trust-state mutation.

An admin boundary contract is not an admin feature and is not verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

SCAN_ADMIN_SURFACE_ENABLED: Final[bool] = False
SCAN_ADMIN_API_ENABLED: Final[bool] = False
SCAN_ADMIN_UI_ENABLED: Final[bool] = False
SCAN_ADMIN_CAN_FORCE_SCAN: Final[bool] = False
SCAN_ADMIN_CAN_MARK_SAFE: Final[bool] = False
SCAN_ADMIN_CAN_MARK_CLEAN: Final[bool] = False
SCAN_ADMIN_CAN_VERIFY_DOCUMENT: Final[bool] = False
SCAN_ADMIN_CAN_VERIFY_CLAIM: Final[bool] = False
SCAN_ADMIN_CAN_RELEASE_QUARANTINE: Final[bool] = False
SCAN_ADMIN_CAN_DELETE_ATTACHMENT: Final[bool] = False
SCAN_ADMIN_CAN_VIEW_RAW_FILE_PATH: Final[bool] = False
SCAN_ADMIN_CAN_VIEW_STORAGE_URI: Final[bool] = False
SCAN_ADMIN_CAN_VIEW_RAW_SCANNER_OUTPUT: Final[bool] = False

SCAN_ADMIN_BOUNDARY_WARNING: Final[str] = (
    "Scan/quarantine admin controls are planned but not active in this version."
)


class ScanAdminSurfaceMode(StrEnum):
    DISABLED = "disabled"
    PLANNED_INTERNAL_OPERATIONS = "planned_internal_operations"


class ScanAdminRole(StrEnum):
    NONE = "none"
    PLANNED_SECURITY_OPERATOR = "planned_security_operator"
    PLANNED_TRUST_REVIEWER = "planned_trust_reviewer"


class ScanAdminFutureAction(StrEnum):
    VIEW_SCAN_JOB_SUMMARY = "view_scan_job_summary"
    VIEW_SAFE_AUDIT_EVENT = "view_safe_audit_event"
    REQUEST_RESCAN = "request_rescan"
    ACKNOWLEDGE_QUARANTINE_REQUIRED = "acknowledge_quarantine_required"
    MARK_SCAN_JOB_REVIEWED = "mark_scan_job_reviewed"


class ScanAdminForbiddenAction(StrEnum):
    MARK_FILE_SAFE = "mark_file_safe"
    MARK_FILE_CLEAN = "mark_file_clean"
    VERIFY_DOCUMENT = "verify_document"
    VERIFY_CLAIM = "verify_claim"
    PUBLISH_FILE = "publish_file"
    EXPOSE_STORAGE_URI = "expose_storage_uri"
    EXPOSE_RAW_SCANNER_OUTPUT = "expose_raw_scanner_output"
    OVERRIDE_CLAIM_STATUS = "override_claim_status"
    OVERRIDE_REVIEW_STATE = "override_review_state"
    RELEASE_QUARANTINE = "release_quarantine"
    DELETE_ATTACHMENT_AS_QUARANTINE = "delete_attachment_as_quarantine"


@dataclass(frozen=True, slots=True)
class ScanAdminBoundaryPlan:
    surface_enabled: bool
    api_enabled: bool
    ui_enabled: bool
    mode: ScanAdminSurfaceMode
    warning: str


def scan_admin_surface_is_enabled() -> bool:
    return SCAN_ADMIN_SURFACE_ENABLED is True


def scan_admin_boundary_warning() -> str:
    return SCAN_ADMIN_BOUNDARY_WARNING


def current_scan_admin_boundary_plan() -> ScanAdminBoundaryPlan:
    return ScanAdminBoundaryPlan(
        surface_enabled=False,
        api_enabled=False,
        ui_enabled=False,
        mode=ScanAdminSurfaceMode.DISABLED,
        warning=SCAN_ADMIN_BOUNDARY_WARNING,
    )


def planned_scan_admin_actions() -> tuple[str, ...]:
    """Future safe operational visibility actions (not implemented in F25)."""
    return tuple(action.value for action in ScanAdminFutureAction)


def forbidden_scan_admin_actions() -> tuple[str, ...]:
    """Powers that must never be granted through scan/quarantine tooling."""
    return tuple(action.value for action in ScanAdminForbiddenAction)


def assert_scan_admin_surface_disabled() -> None:
    """
    Hard assert that admin surface remains inactive.

    Does not create routes, files, or DB rows.
    """
    plan = current_scan_admin_boundary_plan()
    if (
        plan.surface_enabled
        or plan.api_enabled
        or plan.ui_enabled
        or scan_admin_surface_is_enabled()
        or SCAN_ADMIN_CAN_FORCE_SCAN
        or SCAN_ADMIN_CAN_MARK_SAFE
        or SCAN_ADMIN_CAN_MARK_CLEAN
        or SCAN_ADMIN_CAN_VERIFY_DOCUMENT
        or SCAN_ADMIN_CAN_VERIFY_CLAIM
        or SCAN_ADMIN_CAN_RELEASE_QUARANTINE
        or SCAN_ADMIN_CAN_DELETE_ATTACHMENT
        or SCAN_ADMIN_CAN_VIEW_RAW_FILE_PATH
        or SCAN_ADMIN_CAN_VIEW_STORAGE_URI
        or SCAN_ADMIN_CAN_VIEW_RAW_SCANNER_OUTPUT
    ):
        raise RuntimeError(
            "Scan/quarantine admin surface must remain disabled in this version."
        )


def scan_admin_boundary_summary() -> dict[str, object]:
    plan = current_scan_admin_boundary_plan()
    planned = planned_scan_admin_actions()
    forbidden = forbidden_scan_admin_actions()
    return {
        "surface_enabled": plan.surface_enabled,
        "api_enabled": plan.api_enabled,
        "ui_enabled": plan.ui_enabled,
        "mode": plan.mode.value,
        "planned_mode": ScanAdminSurfaceMode.PLANNED_INTERNAL_OPERATIONS.value,
        "active_role": ScanAdminRole.NONE.value,
        "planned_roles": [
            ScanAdminRole.PLANNED_SECURITY_OPERATOR.value,
            ScanAdminRole.PLANNED_TRUST_REVIEWER.value,
        ],
        "warning": plan.warning,
        "planned_actions": list(planned),
        "forbidden_actions": list(forbidden),
        "can_force_scan": SCAN_ADMIN_CAN_FORCE_SCAN,
        "can_mark_safe": SCAN_ADMIN_CAN_MARK_SAFE,
        "can_mark_clean": SCAN_ADMIN_CAN_MARK_CLEAN,
        "can_verify_document": SCAN_ADMIN_CAN_VERIFY_DOCUMENT,
        "can_verify_claim": SCAN_ADMIN_CAN_VERIFY_CLAIM,
        "can_release_quarantine": SCAN_ADMIN_CAN_RELEASE_QUARANTINE,
        "can_delete_attachment": SCAN_ADMIN_CAN_DELETE_ATTACHMENT,
        "can_view_raw_file_path": SCAN_ADMIN_CAN_VIEW_RAW_FILE_PATH,
        "can_view_storage_uri": SCAN_ADMIN_CAN_VIEW_STORAGE_URI,
        "can_view_raw_scanner_output": SCAN_ADMIN_CAN_VIEW_RAW_SCANNER_OUTPUT,
        "mutates_evidence_record": False,
        "mutates_claim_record": False,
        "mutates_review_request": False,
        "has_mutation_powers": False,
        "worker_controls_enabled": False,
        "is_admin_feature": False,
        "is_verification": False,
    }
