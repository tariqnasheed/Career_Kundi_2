"""
Local scanner runtime safety contract (0053-F21).

Defines how a future local scanner runtime must be invoked: no shell, no
network scanners, bounded timeout, safe output normalization, disabled by
default. Does not execute commands, spawn processes, read files, or mutate DB.

A runtime contract is not scanner execution and is not verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

LOCAL_SCANNER_RUNTIME_ENABLED: Final[bool] = False
ALLOW_SHELL_EXECUTION: Final[bool] = False
ALLOW_NETWORK_SCANNER: Final[bool] = False
ALLOW_RAW_SCANNER_OUTPUT_TO_USER: Final[bool] = False
ALLOW_FILE_PARSING_FOR_SCAN: Final[bool] = False
ALLOW_LLM_REVIEW_FOR_SCAN: Final[bool] = False
ALLOW_OCR_FOR_SCAN: Final[bool] = False

DEFAULT_SCANNER_TIMEOUT_SECONDS: Final[int] = 30
MAX_SCANNER_TIMEOUT_SECONDS: Final[int] = 120
MAX_SAFE_MESSAGE_LENGTH: Final[int] = 240
REDACTED_PATH_MARKER: Final[str] = "[redacted-path]"

# F21: empty — do not imply an active scanner binary.
ALLOWED_SCANNER_BINARY_NAMES: Final[tuple[str, ...]] = ()

DEFAULT_SAFE_ERROR_CODE: Final[str] = "scanner_output_unavailable"
DEFAULT_SAFE_ERROR_MESSAGE: Final[str] = (
    "Scanner result is unavailable in this version."
)

ALLOWED_SAFE_ERROR_CODES: Final[frozenset[str]] = frozenset(
    {
        "scanner_unavailable",
        "local_scanner_disabled",
        "scanner_timeout",
        "scanner_error",
        "scanner_unsupported",
        "scanner_output_unavailable",
    }
)

_PATH_LEAK_NEEDLES: Final[tuple[str, ...]] = (
    "/tmp/",
    "/var/",
    "/home/",
    "/users/",
    "evidence_files",
    "local-evidence://",
    "file://",
    ":\\",
    "\\\\",
)


class ScannerRuntimeMode(StrEnum):
    DISABLED = "disabled"
    LOCAL_PROCESS_PLANNED = "local_process_planned"


@dataclass(frozen=True, slots=True)
class ScannerCommandPolicy:
    runtime_enabled: bool
    shell_allowed: bool
    network_allowed: bool
    timeout_seconds: int
    max_timeout_seconds: int
    allowed_binary_names: tuple[str, ...]
    mode: ScannerRuntimeMode
    warning: str


@dataclass(frozen=True, slots=True)
class ScannerOutputPolicy:
    expose_raw_output_to_user: bool
    max_safe_message_length: int
    redacted_path_marker: str
    allowed_safe_error_codes: frozenset[str]
    default_safe_error_message: str


def scanner_runtime_is_enabled() -> bool:
    """F21: always False. No env/config override."""
    return LOCAL_SCANNER_RUNTIME_ENABLED


def current_scanner_runtime_policy() -> ScannerCommandPolicy:
    return ScannerCommandPolicy(
        runtime_enabled=LOCAL_SCANNER_RUNTIME_ENABLED,
        shell_allowed=ALLOW_SHELL_EXECUTION,
        network_allowed=ALLOW_NETWORK_SCANNER,
        timeout_seconds=DEFAULT_SCANNER_TIMEOUT_SECONDS,
        max_timeout_seconds=MAX_SCANNER_TIMEOUT_SECONDS,
        allowed_binary_names=ALLOWED_SCANNER_BINARY_NAMES,
        mode=(
            ScannerRuntimeMode.LOCAL_PROCESS_PLANNED
            if LOCAL_SCANNER_RUNTIME_ENABLED
            else ScannerRuntimeMode.DISABLED
        ),
        warning=(
            "Local scanner runtime is disabled. "
            "Shell and network scanner execution are not allowed. "
            "A runtime contract is not scanner execution."
        ),
    )


def current_scanner_output_policy() -> ScannerOutputPolicy:
    return ScannerOutputPolicy(
        expose_raw_output_to_user=ALLOW_RAW_SCANNER_OUTPUT_TO_USER,
        max_safe_message_length=MAX_SAFE_MESSAGE_LENGTH,
        redacted_path_marker=REDACTED_PATH_MARKER,
        allowed_safe_error_codes=ALLOWED_SAFE_ERROR_CODES,
        default_safe_error_message=DEFAULT_SAFE_ERROR_MESSAGE,
    )


def normalize_scanner_error_code(value: str | None) -> str:
    if value is None:
        return DEFAULT_SAFE_ERROR_CODE
    code = " ".join(str(value).split()).lower().replace(" ", "_")
    if not code:
        return DEFAULT_SAFE_ERROR_CODE
    if code in ALLOWED_SAFE_ERROR_CODES:
        return code
    return DEFAULT_SAFE_ERROR_CODE


def _contains_path_or_storage_leak(text: str) -> bool:
    lower = text.lower()
    for needle in _PATH_LEAK_NEEDLES:
        if needle in lower:
            return True
    # Absolute unix-style path segments (conservative).
    if "/Users/" in text or "/usr/" in lower or "/opt/" in lower:
        return True
    return False


def normalize_scanner_error_message(value: str | None) -> str:
    if value is None:
        return DEFAULT_SAFE_ERROR_MESSAGE
    text = " ".join(str(value).split())
    if not text:
        return DEFAULT_SAFE_ERROR_MESSAGE
    if _contains_path_or_storage_leak(text):
        return DEFAULT_SAFE_ERROR_MESSAGE
    lower = text.lower()
    for phrase in (
        "safe file",
        "clean file",
        "trusted file",
        "verified document",
        "official document",
        "protected by scan",
    ):
        if phrase in lower:
            return DEFAULT_SAFE_ERROR_MESSAGE
    if len(text) > MAX_SAFE_MESSAGE_LENGTH:
        return text[: MAX_SAFE_MESSAGE_LENGTH - 1].rstrip() + "…"
    return text


def redact_scanner_output_for_user(value: str | None) -> str:
    """
    User-facing redaction helper. F21 never exposes raw scanner dumps.
    """
    if ALLOW_RAW_SCANNER_OUTPUT_TO_USER:
        # Defensive: flag is False in F21; still never return raw dumps.
        return normalize_scanner_error_message(value)
    if value is None or not str(value).strip():
        return DEFAULT_SAFE_ERROR_MESSAGE
    if _contains_path_or_storage_leak(str(value)):
        return DEFAULT_SAFE_ERROR_MESSAGE
    return normalize_scanner_error_message(value)


def scanner_runtime_policy_summary() -> dict[str, object]:
    command = current_scanner_runtime_policy()
    output = current_scanner_output_policy()
    return {
        "runtime_enabled": command.runtime_enabled,
        "mode": command.mode.value,
        "shell_allowed": command.shell_allowed,
        "network_allowed": command.network_allowed,
        "timeout_seconds": command.timeout_seconds,
        "max_timeout_seconds": command.max_timeout_seconds,
        "allowed_binary_names": list(command.allowed_binary_names),
        "expose_raw_output_to_user": output.expose_raw_output_to_user,
        "file_parsing_for_scan": ALLOW_FILE_PARSING_FOR_SCAN,
        "llm_review_for_scan": ALLOW_LLM_REVIEW_FOR_SCAN,
        "ocr_for_scan": ALLOW_OCR_FOR_SCAN,
        "executes_commands": False,
        "reads_file_bytes": False,
        "is_verification": False,
        "warning": command.warning,
    }
