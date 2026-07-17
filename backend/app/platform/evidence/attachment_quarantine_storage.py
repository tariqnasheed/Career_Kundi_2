"""
Quarantine storage planning + disabled store contract (0053-F23).

Defines the future quarantine storage contract and makes quarantine storage
explicitly inactive in this version. Does not create directories, move/copy/delete
files, read file bytes, spawn processes, call scanners, or mutate DB rows.

A quarantine contract is not quarantine enforcement and is not verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

QUARANTINE_STORAGE_ENABLED: Final[bool] = False
QUARANTINE_FILE_MOVEMENT_ENABLED: Final[bool] = False
QUARANTINE_FILE_DELETION_ENABLED: Final[bool] = False
QUARANTINE_PUBLIC_ACCESS_ENABLED: Final[bool] = False

QUARANTINE_STORAGE_WARNING: Final[str] = (
    "Quarantine storage is planned but not active in this version."
)


class QuarantineStorageMode(StrEnum):
    DISABLED = "disabled"
    PLANNED_LOCAL_PRIVATE_STORE = "planned_local_private_store"


class QuarantineStorageDecision(StrEnum):
    QUARANTINE_REQUIRED = "quarantine_required"
    QUARANTINE_NOT_REQUIRED = "quarantine_not_required"
    QUARANTINE_UNAVAILABLE = "quarantine_unavailable"


@dataclass(frozen=True, slots=True)
class QuarantineStoragePlan:
    storage_enabled: bool
    file_movement_enabled: bool
    file_deletion_enabled: bool
    public_access_enabled: bool
    mode: QuarantineStorageMode
    warning: str


def quarantine_storage_is_enabled() -> bool:
    return QUARANTINE_STORAGE_ENABLED is True


def quarantine_storage_warning() -> str:
    return QUARANTINE_STORAGE_WARNING


def current_quarantine_storage_plan() -> QuarantineStoragePlan:
    """Return the inactive / planned-only storage plan for this version."""
    return QuarantineStoragePlan(
        storage_enabled=False,
        file_movement_enabled=False,
        file_deletion_enabled=False,
        public_access_enabled=False,
        mode=QuarantineStorageMode.DISABLED,
        warning=QUARANTINE_STORAGE_WARNING,
    )


def build_quarantine_storage_decision(
    verdict_or_safety_status: object,
) -> QuarantineStorageDecision:
    """
    Map a scanner verdict or safety status to a quarantine decision object.

    Never moves, copies, or deletes files. Storage remains inactive in F23.
    """
    value = str(getattr(verdict_or_safety_status, "value", verdict_or_safety_status))
    value = value.strip().lower()

    if value in {"malicious", "suspicious", "scan_failed", "quarantined"}:
        # Decision object only — quarantine storage is still inactive.
        return QuarantineStorageDecision.QUARANTINE_REQUIRED

    if value in {
        "clean",
        "scan_passed",
        "not_scanned",
        "scan_not_available",
        "scan_pending",
        "quarantine_not_required",
    }:
        return QuarantineStorageDecision.QUARANTINE_NOT_REQUIRED

    # Errors / unavailable / unknown → unavailable (no file operations).
    return QuarantineStorageDecision.QUARANTINE_UNAVAILABLE


def assert_quarantine_storage_inactive() -> None:
    """
    Hard assert that quarantine storage remains inactive.

    Does not create directories or touch the filesystem.
    """
    plan = current_quarantine_storage_plan()
    if (
        plan.storage_enabled
        or plan.file_movement_enabled
        or plan.file_deletion_enabled
        or plan.public_access_enabled
        or quarantine_storage_is_enabled()
    ):
        raise RuntimeError(
            "Quarantine storage must remain inactive in this version."
        )


def quarantine_storage_summary() -> dict[str, object]:
    plan = current_quarantine_storage_plan()
    return {
        "storage_enabled": plan.storage_enabled,
        "file_movement_enabled": plan.file_movement_enabled,
        "file_deletion_enabled": plan.file_deletion_enabled,
        "public_access_enabled": plan.public_access_enabled,
        "mode": plan.mode.value,
        "planned_mode": QuarantineStorageMode.PLANNED_LOCAL_PRIVATE_STORE.value,
        "warning": plan.warning,
        "creates_directories": False,
        "moves_files": False,
        "deletes_files": False,
        "copies_files": False,
        "reads_file_bytes": False,
        "is_enforcement": False,
        "is_verification": False,
        "audit_sink_enabled": False,
    }
