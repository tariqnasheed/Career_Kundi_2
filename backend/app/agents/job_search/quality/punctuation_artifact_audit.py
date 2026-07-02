from __future__ import annotations

import re


def punctuation_artifact_count(text: str) -> int:
    if not text:
        return 0
    patterns = [
        r"\.\.+",
        r"\.\s*,",
        r"\s+\.",
        r",\s*,",
        r"\?\s*\.",
        r"!\s*\.",
    ]
    return sum(len(re.findall(p, text)) for p in patterns)


def detect_missing_terminal_punctuation(text: str) -> list[str]:
    out: list[str] = []
    trimmed = (text or "").strip()
    if not trimmed:
        return ["missing_terminal_punctuation"]
    if trimmed[-1] not in (".", "!", "?"):
        out.append("missing_terminal_punctuation")
    return out
