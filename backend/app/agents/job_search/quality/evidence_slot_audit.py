from __future__ import annotations

import re
from typing import Any
from app.agents.job_search.quality.domain_contamination_audit import has_domain_contamination

BAD_SLOT_PATTERNS = [
    r"clear steps",
    r"clear checks",
    r"clear notes",
    r"consistent quality",
    r"acceptance criteria",
    r"benchmark check",
    r"documentation review",
    r"sign-off note",
    r"work log",
    r"verify output",
    r"set the goal",
    r"run the task",
    r"quality steady",
    r"generic wording",
    r"missing final verification",
]

INTERNAL_QA_TERMS = (
    "generic wording",
    "missing final verification",
    "acceptance criteria",
    "benchmark check",
    "documentation review",
)


def _clean_text(text: str) -> str:
    out = text or ""
    for p in BAD_SLOT_PATTERNS:
        out = re.sub(p, "", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out).strip(" ,.;:")
    return out


def sanitize_evidence_slots(slots: dict[str, Any]) -> dict[str, Any]:
    clean = dict(slots)
    for key in ("direct_definition", "role_specific_example", "interview_ready_closing"):
        clean[key] = _clean_text(str(clean.get(key, "")))

    for key in ("practical_steps", "standards_or_regulations", "tools_or_documents", "safety_checks", "quality_checks", "common_mistakes"):
        values = [str(v) for v in (clean.get(key) or [])]
        values = [_clean_text(v) for v in values]
        values = [v for v in values if v and not any(t in v.lower() for t in INTERNAL_QA_TERMS)]
        clean[key] = list(dict.fromkeys(values))
    return clean


def audit_evidence_slots(slots: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    blob = " ".join(
        [str(slots.get("direct_definition", "")), str(slots.get("role_specific_example", ""))]
        + [str(x) for k in ("practical_steps", "standards_or_regulations", "tools_or_documents", "safety_checks", "quality_checks", "common_mistakes") for x in (slots.get(k) or [])]
    )
    if any(re.search(p, blob, re.I) for p in BAD_SLOT_PATTERNS):
        failures.append("bad_slot_pattern")
    if len((slots.get("role_specific_example") or "").split()) < 25:
        failures.append("weak_role_example")
    if len(slots.get("practical_steps") or []) < 4:
        failures.append("weak_practical_steps")
    if len(slots.get("standards_or_regulations") or []) < 1:
        failures.append("missing_standard")
    if len(slots.get("safety_checks") or []) < 2:
        failures.append("weak_safety_checks")
    required_terms = [str(t).lower() for t in contract.get("required_domain_terms", []) if t]
    slot_blob = blob.lower()
    term_hits = sum(1 for t in required_terms if t in slot_blob)
    if required_terms and term_hits < min(3, len(required_terms)):
        failures.append("missing_skill_card_terms")
    if has_domain_contamination(blob, contract.get("role_family", "default")):
        failures.append("slot_domain_contamination")
    return failures
