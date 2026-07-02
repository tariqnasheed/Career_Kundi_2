"""Final surface text normalization for interview-pack prose."""

from __future__ import annotations

import re
from typing import Any


def _joined_token(*parts: str) -> str:
    return "".join(parts)


def _joined_word_pattern(token: str) -> str:
    return rf"\b{re.escape(token)}\b"


# Known joined-word artifacts observed in generated packs.
_JOINED_WORD_FIXES: tuple[tuple[str, str], ...] = (
    (r"\bsystemsand\b", "systems and"),
    (r"\bproductionsystems\b", "production systems"),
    (r"\bmilksteaming\b", "milk steaming"),
    (r"\bstrongfit\b", "strong fit"),
    (r"\bdrinkconsistency\b", "drink consistency"),
    (r"\bespressopreparation\b", "espresso preparation"),
    (r"\bloadcalculations\b", "load calculations"),
    (r"\bcablesizing\b", "cable sizing"),
    (r"\bdataquality\b", "data quality"),
    (r"\boperationaldata\b", "operational data"),
    (r"\bsitecoordination\b", "site coordination"),
    (r"\bqueryperformance\b", "query performance"),
    (r"\bincidentresponse\b", "incident response"),
    (r"\bmedicationreview\b", "medication review"),
    (r"\bstakeholderreporting\b", "stakeholder reporting"),
    (r"\ballergencontrol\b", "allergen control"),
    (r"\brushperiods\b", "rush periods"),
    (r"\binfrastructureautomation\b", "infrastructure automation"),
    (
        _joined_word_pattern(_joined_token("deterministic", "mode")),
        "deterministic mode",
    ),
    (
        _joined_word_pattern(_joined_token("deterministic", "generation", "mode")),
        "deterministic generation mode",
    ),
    (
        _joined_word_pattern(_joined_token("not_configured", "in")),
        "not configured in",
    ),
    (
        _joined_word_pattern(_joined_token("available_not_used", "when")),
        "available_not_used when",
    ),
    (
        _joined_word_pattern(_joined_token("local", "fallback")),
        "local fallback",
    ),
    (
        _joined_word_pattern(_joined_token("source", "ladderis")),
        "source ladder is",
    ),
    (
        _joined_word_pattern(_joined_token("source", " ", "ladderis")),
        "source ladder is",
    ),
)

_PLACEHOLDER_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        r"\[state your actual notice[^\]]*\]",
        "I would discuss my notice period honestly and align my start date with the employer's onboarding plan",
    ),
    (
        r"\[full-time\s*/\s*contract\s*/\s*hybrid\]",
        "the working pattern described in the job specification",
    ),
    (r"\[insert[^\]]*\]", ""),
    (r"\[specific example\]", ""),
    (r"\[company name\]", "the organisation"),
    (r"\[notice period\]", "my agreed notice period"),
)

_PLACEHOLDER_PATTERNS: tuple[str, ...] = (
    r"\[state your[^\]]*\]",
    r"\[full-time[^\]]*\]",
    r"\[insert[^\]]*\]",
    r"\[notice period[^\]]*\]",
    r"\[company name[^\]]*\]",
    r"\[specific example[^\]]*\]",
    r"\[tbd\]",
    r"\[todo[^\]]*\]",
    r"\[\.\.\.\]",
)


def truncate_at_word(text: str, max_len: int, *, ellipsis: str = "…") -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    if max_len <= len(ellipsis):
        return ellipsis[:max_len]
    budget = max_len - len(ellipsis)
    cut = text[:budget].rsplit(" ", 1)[0].strip()
    if not cut:
        cut = text[:budget].strip()
    return cut.rstrip(".,;:") + ellipsis


def strip_unresolved_placeholders(text: str) -> str:
    out = (text or "").strip()
    for pattern, replacement in _PLACEHOLDER_REPLACEMENTS:
        out = re.sub(pattern, replacement, out, flags=re.I)
    for pattern in _PLACEHOLDER_PATTERNS:
        out = re.sub(pattern, "", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    return out.strip()


def normalize_surface_text(text: str) -> str:
    out = (text or "").strip()
    if not out:
        return out
    out = re.sub(r"\.\.+", ".", out)
    out = re.sub(r"\s+\.", ".", out)
    out = re.sub(r"\.\s*,", ",", out)
    out = re.sub(r"\s+,", ",", out)
    out = re.sub(r",([A-Za-z])", r", \1", out)
    out = re.sub(r"\.([A-Za-z])", r". \1", out)
    for pattern, replacement in _JOINED_WORD_FIXES:
        out = re.sub(pattern, replacement, out, flags=re.I)
    out = re.sub(r"\.\s+(json|md|pdf|txt)\b", r".\1", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out)
    out = strip_unresolved_placeholders(out)
    return out.strip()


def has_unresolved_placeholders(text: str) -> bool:
    blob = text or ""
    return any(re.search(pattern, blob, flags=re.I) for pattern in _PLACEHOLDER_PATTERNS)


def find_joined_word_artifacts(text: str) -> list[str]:
    lowered = (text or "").lower()
    hits: list[str] = []
    for pattern, _ in _JOINED_WORD_FIXES:
        token = pattern.replace(r"\b", "").strip()
        if re.search(pattern, lowered, flags=re.I):
            hits.append(token)
    # Heuristic: long tokens without spaces that look like two words joined.
    for match in re.finditer(r"\b[a-z]{14,}\b", lowered):
        word = match.group(0)
        if word in hits:
            continue
        for split in range(4, len(word) - 3):
            left, right = word[:split], word[split:]
            if left in _COMMON_WORDS and right in _COMMON_WORDS:
                hits.append(word)
                break
    return sorted(set(hits))


def normalize_study_material_dict(study: dict[str, Any]) -> dict[str, Any]:
    out = dict(study or {})
    for key, value in list(out.items()):
        if isinstance(value, str):
            out[key] = normalize_surface_text(value)
        elif isinstance(value, list):
            out[key] = [
                normalize_surface_text(str(v)) if isinstance(v, str) else v for v in value
            ]
        elif isinstance(value, dict):
            out[key] = {k: normalize_surface_text(str(v)) if isinstance(v, str) else v for k, v in value.items()}
    return out


_COMMON_WORDS = frozenset(
    {
        "systems", "production", "milk", "steaming", "strong", "fit", "data", "quality",
        "load", "calculations", "cable", "sizing", "medication", "review", "incident",
        "response", "drink", "consistency", "espresso", "preparation", "query", "performance",
        "operational", "site", "coordination", "stakeholder", "reporting", "allergen",
        "control", "rush", "periods", "infrastructure", "automation", "and",
        "deterministic", "mode", "generation", "configured", "ladder",
    }
)
