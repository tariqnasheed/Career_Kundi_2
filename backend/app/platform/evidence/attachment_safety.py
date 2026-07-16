"""
Attachment safety / malware-scan planning contracts (0053-F13).

Pure domain states and safe display text. No scanner engine, parsing, OCR,
LLM review, quarantine storage, or DB persistence in F13.

An uploaded attachment is not scanned, not reviewed, and not verified.
"""

from __future__ import annotations

from enum import StrEnum


class AttachmentSafetyStatus(StrEnum):
    SCAN_NOT_AVAILABLE = "scan_not_available"
    NOT_SCANNED = "not_scanned"
    SCAN_PENDING = "scan_pending"
    SCAN_PASSED = "scan_passed"
    SCAN_FAILED = "scan_failed"
    SCAN_ERROR = "scan_error"
    QUARANTINED = "quarantined"


_LABELS: dict[AttachmentSafetyStatus, str] = {
    AttachmentSafetyStatus.SCAN_NOT_AVAILABLE: "Scan not available",
    AttachmentSafetyStatus.NOT_SCANNED: "Not scanned",
    AttachmentSafetyStatus.SCAN_PENDING: "Scan pending",
    AttachmentSafetyStatus.SCAN_PASSED: "Scan passed",
    AttachmentSafetyStatus.SCAN_FAILED: "Scan failed",
    AttachmentSafetyStatus.SCAN_ERROR: "Scan error",
    AttachmentSafetyStatus.QUARANTINED: "Quarantined",
}

ATTACHMENT_SAFETY_WARNING = (
    "Private attachments are stored but not malware-scanned, parsed, reviewed, "
    "or verified in this version."
)

FORBIDDEN_ATTACHMENT_SAFETY_WORDING: frozenset[str] = frozenset(
    {
        "trusted file",
        "clean file",
        "safe file",
        "verified document",
        "official document",
        "proof of truth",
        "public credential",
        "wallet",
        "blockchain",
        "did",
        "ai verified",
    }
)

# F13: no scan engine exists; every attachment derives this status.
DEFAULT_ATTACHMENT_SAFETY_STATUS = AttachmentSafetyStatus.SCAN_NOT_AVAILABLE


def attachment_safety_label(status: AttachmentSafetyStatus | str) -> str:
    if isinstance(status, AttachmentSafetyStatus):
        return _LABELS[status]
    return _LABELS[AttachmentSafetyStatus(str(status))]


def attachment_safety_warning() -> str:
    return ATTACHMENT_SAFETY_WARNING


def current_attachment_safety_status() -> AttachmentSafetyStatus:
    """Derived status while no scanner exists. Does not read or write storage."""
    return DEFAULT_ATTACHMENT_SAFETY_STATUS


def attachment_safety_fields() -> dict[str, str]:
    """Response helper: status + label + warning (no DB)."""
    status = current_attachment_safety_status()
    return {
        "attachment_safety_status": status.value,
        "attachment_safety_label": attachment_safety_label(status),
        "attachment_safety_warning": attachment_safety_warning(),
    }


def all_attachment_safety_labels() -> list[str]:
    return list(_LABELS.values())
