"""
Attachment quarantine policy (0053-F17 / F23).

Pure policy helpers only. Quarantine handling is planned but not active.
Does not move, delete, or rewrite attachment files or DB rows.

F23: quarantine storage contract lives in attachment_quarantine_storage.py
and remains disabled.
"""

from __future__ import annotations

from enum import StrEnum

from app.platform.evidence.attachment_quarantine_storage import (
    quarantine_storage_is_enabled,
    quarantine_storage_summary,
    quarantine_storage_warning,
)
from app.platform.evidence.attachment_quarantine_audit import (
    quarantine_audit_summary,
    quarantine_audit_warning,
)

QUARANTINE_POLICY_WARNING = (
    "Quarantine handling is planned but not active in this version."
)

QUARANTINE_STORAGE_NOT_IMPLEMENTED_WARNING = (
    "Quarantine storage is not implemented in this version. "
    "No attachment files are moved or deleted by quarantine policy."
)

FORBIDDEN_QUARANTINE_WORDING: frozenset[str] = frozenset(
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

# Safe, user-facing error codes → messages (no filesystem paths, no raw output).
_SAFE_ERROR_MESSAGES: dict[str, str] = {
    "scanner_unavailable": "Malware scanning is not available in this version.",
    "timeout": "Scanning timed out. Try again later when scanning is available.",
    "error": "Scanning reported an error. The attachment was not marked as reviewed.",
    "unsupported": "This attachment type is not supported for scanning yet.",
    "malicious": "Scanner reported a concerning attachment result.",
    "suspicious": "Scanner reported a concerning attachment result.",
    "cancelled": "The scan job was cancelled.",
}


class QuarantinePolicyVerdict(StrEnum):
    """Verdicts that would require quarantine when a scanner exists."""

    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"


def quarantine_is_available() -> bool:
    """Quarantine storage / handling is not active (F17/F23)."""
    return quarantine_storage_is_enabled()


def quarantine_policy_warning() -> str:
    return QUARANTINE_POLICY_WARNING


def quarantine_storage_not_implemented_warning() -> str:
    return QUARANTINE_STORAGE_NOT_IMPLEMENTED_WARNING


def should_quarantine_scan_verdict(verdict: object) -> bool:
    """
    Return True when a future scanner verdict would require quarantine.

    Does not move or delete files. Quarantine is not active in F17/F23.
    """
    value = getattr(verdict, "value", verdict)
    return str(value) in {
        QuarantinePolicyVerdict.MALICIOUS.value,
        QuarantinePolicyVerdict.SUSPICIOUS.value,
    }


def safe_scan_error_message(code: str | None) -> str:
    """Normalize scanner/job error codes to safe user-facing text."""
    if code is None:
        return _SAFE_ERROR_MESSAGES["error"]
    key = str(code).strip().lower()
    if not key:
        return _SAFE_ERROR_MESSAGES["error"]
    # Reject path-like codes.
    if any(n in key for n in ("/", "\\", "evidence_files", "tmp", ":")):
        return _SAFE_ERROR_MESSAGES["error"]
    return _SAFE_ERROR_MESSAGES.get(key, _SAFE_ERROR_MESSAGES["error"])


def quarantine_policy_summary() -> dict[str, object]:
    storage = quarantine_storage_summary()
    audit = quarantine_audit_summary()
    return {
        "quarantine_available": quarantine_is_available(),
        "moves_or_deletes_files": False,
        "warning": quarantine_policy_warning(),
        "storage_warning": quarantine_storage_not_implemented_warning(),
        "storage_contract_warning": quarantine_storage_warning(),
        "audit_warning": quarantine_audit_warning(),
        "storage_enabled": storage["storage_enabled"],
        "storage_mode": storage["mode"],
        "audit_sink_enabled": audit["sink_enabled"],
        "quarantine_required_verdicts": sorted(
            v.value for v in QuarantinePolicyVerdict
        ),
    }
