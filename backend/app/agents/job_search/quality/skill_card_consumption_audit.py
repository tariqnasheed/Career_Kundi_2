from __future__ import annotations

import re
from typing import Any

_GERUND_TO_VERB = {
    "checking": "check",
    "verifying": "verify",
    "confirming": "confirm",
    "reviewing": "review",
    "documenting": "document",
    "tracking": "track",
    "identifying": "identify",
    "applying": "apply",
    "validating": "validate",
    "testing": "test",
    "inspecting": "inspect",
    "recording": "record",
    "escalating": "escalate",
    "protecting": "protect",
    "maintaining": "maintain",
    "monitoring": "monitor",
    "setting": "set",
}


def _item_matches_answer(answer_lower: str, item: str) -> bool:
    needle = item.lower().strip()
    if not needle:
        return False
    if needle in answer_lower:
        return True
    words = needle.split()
    if words and words[0] in _GERUND_TO_VERB:
        alt = f"{_GERUND_TO_VERB[words[0]]} {' '.join(words[1:])}"
        if alt in answer_lower:
            return True
    if words and f"{words[0]}ing" == words[0][: -3] + "ing":
        pass
    first = words[0] if words else ""
    if first.endswith("ing") and len(first) > 4:
        base = first[:-3]
        if f"{base} {' '.join(words[1:])}" in answer_lower:
            return True
    if re.search(r"\bsop\b", needle) and "standard operating procedure" in answer_lower:
        return True
    if "standard operating procedure" in needle and re.search(r"\bsop\b", answer_lower):
        return True
    if len(words) >= 3:
        core = " ".join(words[:4])
        if core in answer_lower:
            return True
    return False


def skill_card_consumption_score(answer: str, contract: dict[str, Any], slots: dict[str, Any]) -> float:
    expected_items: list[str] = []
    expected_items += [str(x) for x in (contract.get("required_domain_terms") or [])]
    expected_items += [str(x) for x in (slots.get("standards_or_regulations") or [])]
    expected_items += [str(x) for x in (slots.get("safety_checks") or [])]
    expected_items += [str(x) for x in (slots.get("quality_checks") or [])]
    expected_items += [str(x) for x in (slots.get("common_mistakes") or [])]
    expected = list(dict.fromkeys(x.strip() for x in expected_items if x and x.strip()))
    if not expected:
        return 0.0
    answer_lower = (answer or "").lower()
    hits = sum(1 for item in expected if _item_matches_answer(answer_lower, item))
    return round((hits / len(expected)) * 100, 1)
