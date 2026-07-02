from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.question_intent import detect_question_intent
from app.agents.job_search.quality.question_intent_alignment_audit import audit_question_intent_alignment

ABSOLUTE_MAX_WORDS = 500
WARN_SHORT_WORDS = 150

PREFERRED_RANGES: dict[str, tuple[int, int]] = {
    "terminology_definition": (160, 300),
    "principles_workflow": (160, 300),
    "general_explain": (160, 300),
    "scenario_case": (220, 400),
    "production_issue_metrics": (220, 400),
    "calculation_or_diagnostic": (250, 450),
    "peer_teaching": (250, 450),
}


def answer_word_count(answer: str) -> int:
    return len((answer or "").split())


def is_repetitive_or_padded(answer: str) -> bool:
    paras = [p.strip().lower() for p in re.split(r"\n\s*\n", (answer or "").strip()) if p.strip()]
    if len(paras) < 2:
        return False
    for i in range(1, len(paras)):
        if paras[i] == paras[i - 1] and len(paras[i].split()) > 30:
            return True
    blob = " ".join(paras)
    if blob.count("for compliance") > 2 or blob.count("i would evidence") > 2:
        return True
    return False


def audit_answer_length(
    answer: str,
    question: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    words = answer_word_count(answer)
    intent = detect_question_intent(
        str((question or {}).get("question") or ""),
        (question or {}).get("question_type"),
        category=(question or {}).get("category"),
    )

    if words > ABSOLUTE_MAX_WORDS:
        errors.append(
            f"answer exceeds absolute maximum (expected <= {ABSOLUTE_MAX_WORDS} words, actual {words})"
        )

    if words < WARN_SHORT_WORDS and question:
        intent_audit = audit_question_intent_alignment(answer, question)
        if not intent_audit["passed"]:
            errors.append(
                f"short answer below {WARN_SHORT_WORDS} words and fails intent alignment "
                f"(actual {words} words): {intent_audit['errors'][:1]}"
            )
        else:
            warnings.append(
                f"answer below {WARN_SHORT_WORDS} words but passes intent alignment (actual {words})"
            )

    pref = PREFERRED_RANGES.get(intent)
    if pref and words > pref[1] and words <= ABSOLUTE_MAX_WORDS:
        if is_repetitive_or_padded(answer):
            warnings.append(
                f"answer above preferred range for {intent} ({pref[0]}-{pref[1]} words) "
                f"and appears repetitive (actual {words})"
            )

    return {
        "passed": not errors,
        "word_count": words,
        "intent": intent,
        "errors": errors,
        "warnings": warnings,
    }


def compress_over_limit(answer: str, *, max_words: int = ABSOLUTE_MAX_WORDS) -> str:
    """Trim only when above absolute max; preserve opening and closing paragraphs."""
    text = (answer or "").strip()
    words = text.split()
    if len(words) <= max_words:
        return text

    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paras) >= 3:
        # Compress middle compliance/safety repetition first.
        middle = paras[1:-1]
        compressed_middle: list[str] = []
        seen: set[str] = set()
        for para in middle:
            key = para.lower()[:80]
            if key in seen and ("for compliance" in para.lower() or "i would evidence" in para.lower()):
                continue
            seen.add(key)
            compressed_middle.append(para)
        paras = [paras[0], *compressed_middle, paras[-1]]
        text = "\n\n".join(paras)
        words = text.split()

    if len(words) > max_words:
        trimmed = " ".join(words[:max_words]).rstrip(" ,;:") + "."
        return trimmed
    return text


def collect_length_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    over_500: list[dict[str, str]] = []
    under_150: list[dict[str, str]] = []
    max_len = 0
    for rec in records:
        words = int(rec.get("word_count") or 0)
        max_len = max(max_len, words)
        if words > ABSOLUTE_MAX_WORDS:
            over_500.append(
                {
                    "role": rec.get("role", ""),
                    "question": (rec.get("question") or "")[:90],
                }
            )
        if words < WARN_SHORT_WORDS:
            under_150.append(
                {
                    "role": rec.get("role", ""),
                    "question": (rec.get("question") or "")[:90],
                    "intent_aligned": bool(rec.get("intent_aligned")),
                }
            )
    return {
        "max_answer_length": max_len,
        "answers_over_500_count": len(over_500),
        "answers_below_150_count": len(under_150),
        "over_500_records": over_500,
        "under_150_records": under_150,
    }
