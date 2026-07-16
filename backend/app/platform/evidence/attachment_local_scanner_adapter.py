"""
Disabled local process scanner adapter skeleton (0053-F20).

Documents how a future local-process scanner would fit AttachmentScannerAdapter.
Does not scan, open files, spawn processes, call the network, import scanner
packages, or mutate DB rows.

This scaffold is not an active scanner and is not verification.
The configured factory must continue to return NoopUnavailableScannerAdapter.
"""

from __future__ import annotations

from app.platform.evidence.attachment_scan_worker import (
    ScanResultContract,
    ScannerAvailability,
    ScannerVerdict,
)
from app.platform.evidence.attachment_scanner_adapter import (
    ScannerAdapterCapability,
    ScannerAdapterInfo,
)

DISABLED_LOCAL_ADAPTER_NAME = "local_process_disabled"
DISABLED_LOCAL_ADAPTER_VERSION = "0"
DISABLED_LOCAL_ADAPTER_WARNING = (
    "Local scanner adapter is defined but disabled in this version."
)
DISABLED_LOCAL_SAFE_ERROR_CODE = "local_scanner_disabled"
DISABLED_LOCAL_SAFE_ERROR_MESSAGE = "Local scanner is disabled in this version."


class DisabledLocalProcessScannerAdapter:
    """
    Disabled skeleton for FUTURE_SCANNER_ADAPTER_FAMILY=local_process_scanner.

    Must remain unavailable / not_run. Must not open paths, read bytes, or
    execute external processes. Not selected by the active factory in F20.
    """

    def adapter_info(self) -> ScannerAdapterInfo:
        return ScannerAdapterInfo(
            name=DISABLED_LOCAL_ADAPTER_NAME,
            version=DISABLED_LOCAL_ADAPTER_VERSION,
            availability=ScannerAvailability.UNAVAILABLE,
            # Intended future capability family, but availability stays unavailable.
            capabilities=(
                ScannerAdapterCapability.MALWARE_SCAN,
                ScannerAdapterCapability.UNAVAILABLE,
            ),
            warning=DISABLED_LOCAL_ADAPTER_WARNING,
        )

    def scan_attachment(
        self,
        *,
        evidence_id: object | None = None,
        content_hash: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
    ) -> ScanResultContract:
        # Ignore metadata only; never open paths, storage URIs, or file bytes.
        _ = (evidence_id, content_hash, mime_type, size_bytes)
        return ScanResultContract(
            scanner_name=DISABLED_LOCAL_ADAPTER_NAME,
            scanner_version=DISABLED_LOCAL_ADAPTER_VERSION,
            verdict=ScannerVerdict.NOT_RUN,
            safe_error_code=DISABLED_LOCAL_SAFE_ERROR_CODE,
            safe_error_message=DISABLED_LOCAL_SAFE_ERROR_MESSAGE,
            duration_ms=0,
            completed_at=None,
        )


def disabled_local_scanner_adapter_summary() -> dict[str, object]:
    adapter = DisabledLocalProcessScannerAdapter()
    info = adapter.adapter_info()
    return {
        "name": info.name,
        "version": info.version,
        "availability": info.availability.value,
        "capabilities": [c.value for c in info.capabilities],
        "warning": info.warning,
        "selected_by_factory": False,
        "implementation_disabled": True,
        "reads_file_bytes": False,
        "calls_network_or_subprocess": False,
        "applies_results_to_database": False,
        "is_verification": False,
    }
