"""
agents/common/security.py
=============================
Agent-input/output security helpers — distinct from `app/core/security.py`,
which handles JWT issuance and password hashing for the HTTP auth layer.
These functions implement the agent-facing half of §3.5 Security
Architecture: input sanitization and prompt-injection detection at the
GuardrailAgent boundary, and a defensive output scan used by Reflectors.
"""

from __future__ import annotations

import re

from app.tools.llm import detect_prompt_injection

# Generous ceiling on free-text input length. Protects the token budget from
# a pathological paste (e.g. someone pasting an entire HTML page instead of
# a job description) rather than being a tight content restriction.
_MAX_INPUT_CHARS = 20_000

_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_EXCESS_WHITESPACE_PATTERN = re.compile(r"[ \t]{3,}")


def sanitize_input(text: str) -> str:
    """
    Strip control characters and raw HTML tags, collapse excessive
    whitespace, and hard-truncate to `_MAX_INPUT_CHARS`. Called on every
    piece of free-text user input (chat messages, pasted job descriptions,
    profile free-text fields) before it is ever interpolated into a prompt.
    """
    cleaned = _CONTROL_CHAR_PATTERN.sub("", text)
    cleaned = _HTML_TAG_PATTERN.sub(" ", cleaned)
    cleaned = _EXCESS_WHITESPACE_PATTERN.sub("  ", cleaned).strip()
    return cleaned[:_MAX_INPUT_CHARS]


def check_for_injection(text: str) -> list[str]:
    """
    Thin re-export of the shared prompt-injection pattern library in
    `app/tools/llm.py`, kept here so feature agent code imports all
    security-related concerns from this one module rather than reaching
    into the LLM tool layer directly.
    """
    return detect_prompt_injection(text)


_PII_PATTERNS: dict[str, re.Pattern] = {
    "ssn_like": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card_like": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
}


def scan_output_for_pii(text: str) -> list[str]:
    """
    Flag obviously sensitive patterns (SSN-shaped, credit-card-shaped
    number sequences) that should never appear in LLM-generated output.
    This is a defensive backstop for the Reflector, not a comprehensive PII
    scanner — returns the names of any matched pattern categories.
    """
    return [name for name, pattern in _PII_PATTERNS.items() if pattern.search(text)]
