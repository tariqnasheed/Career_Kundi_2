"""
Quarantine event/audit planning + disabled audit sink (0053-F24).

Defines future scan/quarantine audit event types and a safe metadata-only
payload contract. The audit sink is disabled: it never writes DB rows, files,
or public surfaces. Does not scan, move/delete files, or mutate trust state.

An audit contract is not audit persistence and is not verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Final
from uuid import UUID

from app.platform.evidence.attachment_scanner_runtime_policy import (
    REDACTED_PATH_MARKER,
    normalize_scanner_error_code,
    normalize_scanner_error_message,
)

QUARANTINE_AUDIT_SINK_ENABLED: Final[bool] = False
QUARANTINE_AUDIT_DB_ENABLED: Final[bool] = False
QUARANTINE_AUDIT_FILE_LOG_ENABLED: Final[bool] = False
QUARANTINE_AUDIT_PUBLIC_ACCESS_ENABLED: Final[bool] = False
RAW_FILE_PATH_ALLOWED_IN_AUDIT: Final[bool] = False
STORAGE_URI_ALLOWED_IN_AUDIT: Final[bool] = False
RAW_SCANNER_OUTPUT_ALLOWED_IN_AUDIT: Final[bool] = False

QUARANTINE_AUDIT_WARNING: Final[str] = (
    "Quarantine audit persistence is planned but not active in this version."
)

AUDIT_EVENT_VERSION: Final[str] = "1"

ALLOWED_AUDIT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "event_type",
        "event_version",
        "evidence_id",
        "scan_job_id",
        "owner_user_id",
        "actor_user_id",
        "job_status",
        "attachment_safety_status",
        "safe_error_code",
        "safe_error_message",
        "created_at",
    }
)

FORBIDDEN_AUDIT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "file_path",
        "storage_path",
        "storage_uri",
        "public_url",
        "raw_output",
        "scanner_stdout",
        "scanner_stderr",
        "file_bytes",
        "content",
        "llm_analysis",
        "verification_status",
        "support_status",
    }
)

_PATH_OR_URI_NEEDLES: Final[tuple[str, ...]] = (
    "/tmp/",
    "/var/",
    "/home/",
    "/users/",
    "evidence_files",
    "local-evidence://",
    "file://",
    "http://",
    "https://",
    ":\\",
    "\\\\",
)

_FORBIDDEN_TRUST_PHRASES: Final[tuple[str, ...]] = (
    "safe file",
    "clean file",
    "trusted file",
    "verified document",
    "official proof",
    "official document",
)


class QuarantineAuditEventType(StrEnum):
    SCAN_JOB_CREATED = "scan_job_created"
    SCAN_JOB_RESERVED = "scan_job_reserved"
    SCAN_RESULT_PLAN_BUILT = "scan_result_plan_built"
    SCAN_RESULT_PERSISTENCE_REJECTED = "scan_result_persistence_rejected"
    SCAN_RESULT_PERSISTED_TO_JOB = "scan_result_persisted_to_job"
    QUARANTINE_REQUIRED_DECISION_BUILT = "quarantine_required_decision_built"
    QUARANTINE_STORAGE_UNAVAILABLE = "quarantine_storage_unavailable"
    QUARANTINE_STORAGE_INACTIVE_CONFIRMED = "quarantine_storage_inactive_confirmed"


class QuarantineAuditMode(StrEnum):
    DISABLED = "disabled"
    PLANNED_PRIVATE_AUDIT_SINK = "planned_private_audit_sink"


@dataclass(frozen=True, slots=True)
class QuarantineAuditPlan:
    sink_enabled: bool
    db_enabled: bool
    file_log_enabled: bool
    public_access_enabled: bool
    mode: QuarantineAuditMode
    warning: str


@dataclass(frozen=True, slots=True)
class QuarantineAuditEvent:
    event_type: QuarantineAuditEventType
    event_version: str
    evidence_id: str | None
    scan_job_id: str | None
    owner_user_id: str | None
    actor_user_id: str | None
    job_status: str | None
    attachment_safety_status: str | None
    safe_error_code: str | None
    safe_error_message: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class DisabledAuditResult:
    persisted: bool
    reason: str
    event_type: str
    sink_enabled: bool


def quarantine_audit_is_enabled() -> bool:
    return QUARANTINE_AUDIT_SINK_ENABLED is True


def quarantine_audit_warning() -> str:
    return QUARANTINE_AUDIT_WARNING


def current_quarantine_audit_plan() -> QuarantineAuditPlan:
    return QuarantineAuditPlan(
        sink_enabled=False,
        db_enabled=False,
        file_log_enabled=False,
        public_access_enabled=False,
        mode=QuarantineAuditMode.DISABLED,
        warning=QUARANTINE_AUDIT_WARNING,
    )


def _as_optional_id(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    text = str(value).strip()
    return text or None


def _looks_like_path_or_uri(text: str) -> bool:
    lower = text.lower()
    for needle in _PATH_OR_URI_NEEDLES:
        if needle in lower:
            return True
    if "/Users/" in text or "/usr/" in lower or "/opt/" in lower:
        return True
    return False


def sanitize_quarantine_audit_value(value: object | None) -> str | None:
    """
    Sanitize a free-text audit field.

    Redacts filesystem paths, storage URIs, and public URLs. Rejects trust
    wording and truncates long / raw scanner-like dumps via F21 helpers.
    """
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None

    if _looks_like_path_or_uri(text):
        return REDACTED_PATH_MARKER

    lower = text.lower()
    for phrase in _FORBIDDEN_TRUST_PHRASES:
        if phrase in lower:
            return None

    if any(n in lower for n in ("stdout", "stderr", "raw_output")):
        # Raw scanner dumps are not stored in audit payloads.
        return None

    # Reuse F21 truncation / dump rejection for scanner-like messages.
    return normalize_scanner_error_message(text)


def _sanitize_status_token(value: str | None) -> str | None:
    """Allow only short status-like tokens; redact path/URI contamination."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    if _looks_like_path_or_uri(text):
        return REDACTED_PATH_MARKER
    if len(text) > 64:
        return text[:63].rstrip() + "…"
    return text


def build_quarantine_audit_event(
    *,
    event_type: QuarantineAuditEventType | str,
    evidence_id: object | None = None,
    scan_job_id: object | None = None,
    owner_user_id: object | None = None,
    actor_user_id: object | None = None,
    job_status: str | None = None,
    attachment_safety_status: str | None = None,
    safe_error_code: str | None = None,
    safe_error_message: str | None = None,
    created_at: datetime | None = None,
    **extra: Any,
) -> QuarantineAuditEvent:
    """
    Build a metadata-only audit event.

    Extra keys are rejected (not stored). Raw paths/URIs/output must not be
    passed as allowed fields; sanitizer still redacts message fields.
    """
    if extra:
        forbidden = sorted(set(extra) & FORBIDDEN_AUDIT_PAYLOAD_KEYS)
        if forbidden:
            raise ValueError(
                f"Forbidden audit payload keys: {', '.join(forbidden)}"
            )
        unknown = sorted(set(extra) - ALLOWED_AUDIT_PAYLOAD_KEYS)
        if unknown:
            raise ValueError(
                f"Unknown audit payload keys are not allowed: {', '.join(unknown)}"
            )

    if isinstance(event_type, QuarantineAuditEventType):
        et = event_type
    else:
        et = QuarantineAuditEventType(str(event_type))

    code = None
    if safe_error_code is not None:
        code = normalize_scanner_error_code(str(safe_error_code))

    when = created_at or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)

    return QuarantineAuditEvent(
        event_type=et,
        event_version=AUDIT_EVENT_VERSION,
        evidence_id=_as_optional_id(evidence_id),
        scan_job_id=_as_optional_id(scan_job_id),
        owner_user_id=_as_optional_id(owner_user_id),
        actor_user_id=_as_optional_id(actor_user_id),
        job_status=_sanitize_status_token(job_status),
        attachment_safety_status=_sanitize_status_token(attachment_safety_status),
        safe_error_code=code,
        safe_error_message=sanitize_quarantine_audit_value(safe_error_message),
        created_at=when.isoformat(),
    )


def disabled_quarantine_audit_sink(
    event: QuarantineAuditEvent,
) -> DisabledAuditResult:
    """
    Accept a safe event and refuse persistence.

    Does not write DB, files, or logs with raw payloads.
    """
    if not isinstance(event, QuarantineAuditEvent):
        raise TypeError("event must be QuarantineAuditEvent")
    # Defensive: sink remains disabled regardless of flags.
    return DisabledAuditResult(
        persisted=False,
        reason="audit_sink_disabled",
        event_type=event.event_type.value,
        sink_enabled=quarantine_audit_is_enabled(),
    )


def quarantine_audit_summary() -> dict[str, object]:
    plan = current_quarantine_audit_plan()
    return {
        "sink_enabled": plan.sink_enabled,
        "db_enabled": plan.db_enabled,
        "file_log_enabled": plan.file_log_enabled,
        "public_access_enabled": plan.public_access_enabled,
        "mode": plan.mode.value,
        "planned_mode": QuarantineAuditMode.PLANNED_PRIVATE_AUDIT_SINK.value,
        "warning": plan.warning,
        "raw_file_path_allowed": RAW_FILE_PATH_ALLOWED_IN_AUDIT,
        "storage_uri_allowed": STORAGE_URI_ALLOWED_IN_AUDIT,
        "raw_scanner_output_allowed": RAW_SCANNER_OUTPUT_ALLOWED_IN_AUDIT,
        "allowed_event_types": sorted(e.value for e in QuarantineAuditEventType),
        "allowed_payload_keys": sorted(ALLOWED_AUDIT_PAYLOAD_KEYS),
        "persists_events": False,
        "writes_files": False,
        "writes_db": False,
        "is_verification": False,
    }
