"""
Scanner adapter interface + no-op unavailable adapter (0053-F18 / F19).

Defines the seam a future scanner must implement. Ships only a no-op
adapter that reports unavailable / not_run. Does not read file bytes, call
network/processes, import scanner packages, or mutate DB rows.

F19 selection policy still returns no-op only (real scanner disabled).
A no-op adapter is not a scanner and is not verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from app.platform.evidence.attachment_scan_worker import (
    ScanResultContract,
    ScannerAvailability,
    ScannerVerdict,
)
from app.platform.evidence.attachment_scanner_policy import (
    CURRENT_SCANNER_ADAPTER_NAME,
    select_configured_scanner_adapter_name,
)

NOOP_ADAPTER_NAME = CURRENT_SCANNER_ADAPTER_NAME
NOOP_ADAPTER_VERSION = "0"
NOOP_ADAPTER_WARNING = "Scanner is not configured in this version."
NOOP_SAFE_ERROR_CODE = "scanner_unavailable"
NOOP_SAFE_ERROR_MESSAGE = "Scanner is not configured in this version."


class ScannerAdapterName(StrEnum):
    NOOP_UNAVAILABLE = "noop_unavailable"


class ScannerAdapterCapability(StrEnum):
    MALWARE_SCAN = "malware_scan"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ScannerAdapterInfo:
    name: str
    version: str
    availability: ScannerAvailability
    capabilities: tuple[ScannerAdapterCapability, ...]
    warning: str


@runtime_checkable
class AttachmentScannerAdapter(Protocol):
    """Future scanner seam. Implementations must not claim verification."""

    def adapter_info(self) -> ScannerAdapterInfo: ...

    def scan_attachment(
        self,
        *,
        evidence_id: object | None = None,
        content_hash: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
    ) -> ScanResultContract: ...


class NoopUnavailableScannerAdapter:
    """
    Default F18 adapter: always unavailable / not_run.

    Must not open files, call external processes or the network, or return clean/passed.
    """

    def adapter_info(self) -> ScannerAdapterInfo:
        return ScannerAdapterInfo(
            name=NOOP_ADAPTER_NAME,
            version=NOOP_ADAPTER_VERSION,
            availability=ScannerAvailability.UNAVAILABLE,
            capabilities=(ScannerAdapterCapability.UNAVAILABLE,),
            warning=NOOP_ADAPTER_WARNING,
        )

    def scan_attachment(
        self,
        *,
        evidence_id: object | None = None,
        content_hash: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
    ) -> ScanResultContract:
        # Intentionally ignore metadata; never open paths or read bytes.
        _ = (evidence_id, content_hash, mime_type, size_bytes)
        return ScanResultContract(
            scanner_name=NOOP_ADAPTER_NAME,
            scanner_version=NOOP_ADAPTER_VERSION,
            verdict=ScannerVerdict.NOT_RUN,
            safe_error_code=NOOP_SAFE_ERROR_CODE,
            safe_error_message=NOOP_SAFE_ERROR_MESSAGE,
            duration_ms=0,
            completed_at=None,
        )


def get_configured_attachment_scanner_adapter() -> AttachmentScannerAdapter:
    """
    Factory for the active attachment scanner adapter.

    F18/F19: always returns the no-op unavailable adapter. Selection policy
    may only name noop_unavailable while REAL_SCANNER_ENABLED is False.
    No env-based real scanner selection and no config changes in F19.
    """
    selected = select_configured_scanner_adapter_name()
    if selected != NOOP_ADAPTER_NAME:
        # Defensive: never construct a real adapter from this factory in F19.
        return NoopUnavailableScannerAdapter()
    return NoopUnavailableScannerAdapter()


def configured_scanner_adapter_summary() -> dict[str, object]:
    adapter = get_configured_attachment_scanner_adapter()
    info = adapter.adapter_info()
    return {
        "name": info.name,
        "version": info.version,
        "availability": info.availability.value,
        "capabilities": [c.value for c in info.capabilities],
        "warning": info.warning,
        "selected_by_policy": select_configured_scanner_adapter_name(),
        "reads_file_bytes": False,
        "calls_network_or_subprocess": False,
        "applies_results_to_database": False,
        "real_scanner_enabled": False,
    }
