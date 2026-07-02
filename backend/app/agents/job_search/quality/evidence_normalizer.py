from __future__ import annotations

import re
from typing import Any

GENERIC_REPLACEMENTS = {
    "improve outcomes": "reduce errors, delays, or safety risks",
    "check the result": "verify the result using the required test or inspection record",
    "follow the correct process": "follow the approved method, standard, and inspection sequence",
    "handle the task properly": "complete the task with documented checks and traceable decisions",
}

_BANNED_FRAGMENTS = [
    "in a clear and professional way",
    "with consistent quality",
    "as required",
    "where appropriate",
    "as needed",
]


def normalize_evidence_text(text: str) -> str:
    out = (text or "").strip()
    out = re.sub(r"\.\.+", ".", out)
    out = re.sub(r"\s+\.", ".", out)
    out = re.sub(r"\.\s*,", ",", out)
    out = re.sub(r"\s+,", ",", out)
    out = re.sub(r"\s+;", ";", out)
    out = re.sub(r"\.\s*\.", ".", out)
    out = re.sub(r"\s{2,}", " ", out)
    for fragment in _BANNED_FRAGMENTS:
        out = out.replace(fragment, "")
    for src, dst in GENERIC_REPLACEMENTS.items():
        if src in out:
            out = out.replace(src, dst)
    return out.strip(" ,.;:")


def normalize_list_items(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        out = normalize_evidence_text(str(item))
        key = out.lower()
        if not out or key in seen:
            continue
        if re.search(r"\b(is th|protective d|may requir)\b$", out.lower()):
            continue
        seen.add(key)
        cleaned.append(out)
    return cleaned


def normalize_evidence_slots(slots: dict[str, Any]) -> dict[str, Any]:
    out = dict(slots)
    for key in ("direct_definition", "role_specific_example", "interview_ready_closing"):
        out[key] = normalize_evidence_text(str(out.get(key, "")))
    for key in (
        "practical_steps",
        "standards_or_regulations",
        "tools_or_documents",
        "safety_checks",
        "quality_checks",
        "common_mistakes",
    ):
        out[key] = normalize_list_items([str(x) for x in (out.get(key) or [])])
    return out
