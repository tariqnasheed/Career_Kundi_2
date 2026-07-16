"""
Local scanner integration policy (0053-F19).

Planning/specification helpers only. Does not enable a real scanner, install
dependencies, call subprocess/network, read file bytes, or mutate DB rows.

A scanner integration plan is not scanning and is not verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# ---------------------------------------------------------------------------
# Current product boundary (F19): real scanning remains disabled.
# Do not add env/config toggles that enable a real scanner in this slice.
# ---------------------------------------------------------------------------

REAL_SCANNER_ENABLED: Final[bool] = False
CURRENT_SCANNER_ADAPTER_NAME: Final[str] = "noop_unavailable"
# F20 scaffold name only — never selected while REAL_SCANNER_ENABLED is False.
DISABLED_LOCAL_SCANNER_ADAPTER_NAME: Final[str] = "local_process_disabled"
FUTURE_SCANNER_ADAPTER_FAMILY: Final[str] = "local_process_scanner"
EXTERNAL_SCANNER_APIS_ALLOWED: Final[bool] = False
FILE_PARSING_ALLOWED_FOR_MALWARE_SCAN: Final[bool] = False
LLM_FILE_REVIEW_ALLOWED: Final[bool] = False
OCR_ALLOWED_FOR_MALWARE_SCAN: Final[bool] = False

# Future local-process scanner bounds (documentation constants; not wired).
FUTURE_SCAN_TIMEOUT_SECONDS_DEFAULT: Final[int] = 30
FUTURE_SCAN_TIMEOUT_SECONDS_MAX: Final[int] = 120

# Fields a future approved worker may update on AttachmentScanJob only.
FUTURE_ALLOWED_SCAN_JOB_UPDATE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "job_status",
        "attachment_safety_status",
        "engine_name",
        "engine_version",
        "safe_error_code",
        "safe_error_message",
        "started_at",
        "completed_at",
        "attempt_count",
    }
)

# Must never be mutated by a scan worker.
FUTURE_FORBIDDEN_MUTATION_TARGETS: Final[frozenset[str]] = frozenset(
    {
        "EvidenceRecord.support_status",
        "EvidenceRecord.trust_fields",
        "ClaimRecord.support_status",
        "ClaimRecord.verification_status",
        "ReviewRequest.review_state",
        "Passport.verification_status",
        "public_sharing_state",
    }
)

FORBIDDEN_SCANNER_POLICY_WORDING: Final[frozenset[str]] = frozenset(
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


@dataclass(frozen=True, slots=True)
class ScannerIntegrationPolicySummary:
    real_scanner_enabled: bool
    current_adapter_name: str
    future_adapter_family: str
    external_scanner_apis_allowed: bool
    file_parsing_allowed_for_malware_scan: bool
    llm_file_review_allowed: bool
    ocr_allowed_for_malware_scan: bool
    future_timeout_seconds_default: int
    applies_results_to_database: bool
    is_verification: bool
    warning: str


def real_scanner_is_enabled() -> bool:
    """F19: always False. No env override."""
    return REAL_SCANNER_ENABLED


def current_scanner_adapter_name() -> str:
    return CURRENT_SCANNER_ADAPTER_NAME


def future_scanner_adapter_family() -> str:
    return FUTURE_SCANNER_ADAPTER_FAMILY


def external_scanner_apis_allowed() -> bool:
    return EXTERNAL_SCANNER_APIS_ALLOWED


def file_parsing_allowed_for_malware_scan() -> bool:
    return FILE_PARSING_ALLOWED_FOR_MALWARE_SCAN


def llm_file_review_allowed() -> bool:
    return LLM_FILE_REVIEW_ALLOWED


def ocr_allowed_for_malware_scan() -> bool:
    return OCR_ALLOWED_FOR_MALWARE_SCAN


def select_configured_scanner_adapter_name() -> str:
    """
    Adapter selection policy.

    F19 (and until a separately approved enablement slice): always no-op.
    Even if REAL_SCANNER_ENABLED were flipped later, selection must still go
    through an approved adapter factory — this helper never enables scanning.
    """
    if not REAL_SCANNER_ENABLED:
        return CURRENT_SCANNER_ADAPTER_NAME
    # Defensive: F19 keeps REAL_SCANNER_ENABLED False; never select a real
    # adapter from this planning module alone.
    return CURRENT_SCANNER_ADAPTER_NAME


def scanner_integration_policy_summary() -> ScannerIntegrationPolicySummary:
    return ScannerIntegrationPolicySummary(
        real_scanner_enabled=REAL_SCANNER_ENABLED,
        current_adapter_name=CURRENT_SCANNER_ADAPTER_NAME,
        future_adapter_family=FUTURE_SCANNER_ADAPTER_FAMILY,
        external_scanner_apis_allowed=EXTERNAL_SCANNER_APIS_ALLOWED,
        file_parsing_allowed_for_malware_scan=FILE_PARSING_ALLOWED_FOR_MALWARE_SCAN,
        llm_file_review_allowed=LLM_FILE_REVIEW_ALLOWED,
        ocr_allowed_for_malware_scan=OCR_ALLOWED_FOR_MALWARE_SCAN,
        future_timeout_seconds_default=FUTURE_SCAN_TIMEOUT_SECONDS_DEFAULT,
        applies_results_to_database=False,
        is_verification=False,
        warning=(
            "Local scanner integration is planned only. "
            "Real scanning is disabled; the no-op adapter remains active. "
            "A scan plan is not verification."
        ),
    )


def future_local_scanner_requirements() -> tuple[str, ...]:
    """Documented requirements for a later approved local scanner adapter."""
    return (
        "Accept only storage-managed paths from the private evidence storage service.",
        "Verify path containment under the evidence storage root before any scan.",
        "Run with a bounded timeout; treat timeout as scan_error / not clean.",
        "Normalize scanner output into safe error codes; never expose raw scanner output.",
        "Never log raw file bytes or raw filesystem paths to users or public APIs.",
        "Never mutate ClaimRecord, EvidenceRecord trust fields, ReviewRequest, or Passport verification.",
        "Only update AttachmentScanJob rows through a separately approved worker.",
        "Refuse to scan when attachment metadata/hash differs from the job snapshot.",
        "Never use network / cloud scanner APIs under the current product boundary.",
        "Never parse, OCR, or LLM-review documents as part of malware scanning.",
        "Never mark claims or Passports verified based on scan results.",
        "Never publish or publicly share scanned files.",
        "Keep public UI wording conservative (scan_not_available until approved exposure).",
    )


def future_scan_job_fields_may_update() -> frozenset[str]:
    return FUTURE_ALLOWED_SCAN_JOB_UPDATE_FIELDS


def future_mutation_targets_forbidden() -> frozenset[str]:
    return FUTURE_FORBIDDEN_MUTATION_TARGETS
