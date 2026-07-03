from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.answer_builders import GENERIC_CLOSING_PHRASE
from app.agents.job_search.quality.compiler_boilerplate_audit import contains_universal_boilerplate
from app.agents.job_search.quality.blocked_phrase_guard import (
    DOCUMENTED_CONTROL_POINTS,
    REDUCED_REWORK_STRUCTURED,
)
from app.agents.job_search.quality.example_quality_audit import validate_example_quality
from app.agents.job_search.quality.expert_naturalness_audit import (
    contains_formulaic_spoken_labels,
    expert_naturalness_failures,
)
from app.agents.job_search.quality.key_term_quality_audit import (
    invalid_key_term_count_in_answer,
    invalid_key_terms,
)
from app.agents.job_search.quality.punctuation_artifact_audit import detect_missing_terminal_punctuation

EMPTY_SLOT_PATTERNS = [
    r"For compliance,\s*I check\s+and verify",
    r"I check\s*,?\s*and verify",
    r"against\s+and applicable standards",
    r"check\s+and verify using",
]
_GENERIC_SURFACE_FRAGMENTS = (
    DOCUMENTED_CONTROL_POINTS,
    REDUCED_REWORK_STRUCTURED,
    "complaint rate decreased materially",
)
_TRUNCATED_ENDINGS = ("and", "or", "with", "into", "for", "to", "from", "because", "while")


def _detect_empty_rendered_slots(answer: str) -> list[str]:
    if any(re.search(p, answer, re.I) for p in EMPTY_SLOT_PATTERNS):
        return ["empty_compliance_slot"]
    return []


def _detect_truncated_sentences(answer: str) -> list[str]:
    failures: list[str] = []
    trimmed = (answer or "").strip()
    if not trimmed:
        return ["truncated_example"]
    lower = trimmed.lower()
    if lower.endswith(_TRUNCATED_ENDINGS):
        failures.append("truncated_example")
    if re.search(r"\b\d+\s*A\s+main\.?$", trimmed, re.I):
        failures.append("truncated_example")
    if re.search(r"\b\d+\s*V\s*$", trimmed, re.I):
        failures.append("truncated_example")
    if re.search(r"\b\d+\s*mA\s*$", trimmed, re.I):
        failures.append("truncated_example")
    return failures


def _looks_complete_without_terminal_punctuation(answer: str) -> bool:
    text = (answer or "").strip()
    if not text:
        return False
    last = text.split()[-1].lower().rstrip(",;:")
    if last in _TRUNCATED_ENDINGS:
        return False
    if re.search(r"\b\d+\s*A\s+main$", text, re.I):
        return False
    if re.search(r"\b\d+\s*V$", text, re.I):
        return False
    if re.search(r"\b\d+\s*mA$", text, re.I):
        return False
    return True


def ensure_final_terminal_punctuation(answer: str) -> tuple[str, bool]:
    text = (answer or "").rstrip()
    if not text:
        return text, False
    if text.endswith((".", "!", "?")):
        return text, True
    if _looks_complete_without_terminal_punctuation(text):
        return text + ".", True
    return text, False


def _detect_paragraph_merge(answer: str, question: dict[str, Any]) -> list[str]:
    qtype = question.get("question_type") or ""
    compiler_only = {"explain", "explain_to_peer", "scenario", "complex_problem", "terminology", "principles", "calculation", "procedure"}
    if qtype in compiler_only and answer.count("\n\n") < 2:
        return ["paragraph_merge_detected"]
    return []


def _detect_invalid_key_terms(answer: str, contract: dict[str, Any]) -> list[str]:
    required = [str(t) for t in (contract.get("required_domain_terms") or []) if t]
    if invalid_key_terms(required):
        return ["invalid_key_term"]
    return ["invalid_key_term"] if invalid_key_term_count_in_answer(answer) > 0 else []


def _detect_generic_surface_fragments(answer: str) -> list[str]:
    lowered = (answer or "").lower()
    if any(f in lowered for f in _GENERIC_SURFACE_FRAGMENTS):
        return ["generic_surface_fragment"]
    return []


def _detect_sentence_fragment(answer: str) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", (answer or "").strip()) if s.strip()]
    if sentences and len(sentences[-1].split()) < 6 and not sentences[-1].endswith((".", "!", "?")):
        return ["sentence_fragment"]
    return []


def _detect_improper_example_capitalization(answer: str) -> list[str]:
    if re.search(r"For example,\s+(During|On|When|In)\b", answer or ""):
        return ["improper_example_capitalization"]
    return []


def _detect_generic_repeated_closing(answer: str) -> list[str]:
    if GENERIC_CLOSING_PHRASE.lower() in (answer or "").lower():
        return ["generic_repeated_closing"]
    return []


def _detect_universal_boilerplate(answer: str) -> list[str]:
    return ["universal_boilerplate_detected"] if contains_universal_boilerplate(answer) else []


def _detect_formulaic_spoken_labels(answer: str) -> list[str]:
    return ["formulaic_spoken_label"] if contains_formulaic_spoken_labels(answer) else []


def _detect_expert_naturalness(
    answer: str,
    question: dict[str, Any],
    contract: dict[str, Any],
) -> list[str]:
    slots = question.get("evidence_slots") or {}
    return expert_naturalness_failures(answer, contract, slots)


def validate_final_surface(answer: str, question: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    failures += _detect_universal_boilerplate(answer)
    failures += _detect_formulaic_spoken_labels(answer)
    failures += _detect_expert_naturalness(answer, question, contract)
    failures += detect_missing_terminal_punctuation(answer)
    failures += _detect_empty_rendered_slots(answer)
    failures += _detect_truncated_sentences(answer)
    failures += _detect_paragraph_merge(answer, question)
    failures += _detect_invalid_key_terms(answer, contract)
    failures += _detect_generic_surface_fragments(answer)
    failures += _detect_improper_example_capitalization(answer)
    failures += _detect_generic_repeated_closing(answer)
    failures += _detect_sentence_fragment(answer)
    example = question.get("quality_audit", {}).get("role_specific_example", "")
    if not example:
        for marker in ("For example,", "Role example:"):
            if marker in answer:
                idx = answer.find(marker)
                example = answer[idx:]
                break
    if example:
        failures += validate_example_quality(example, contract.get("required_domain_terms", []))
    return list(dict.fromkeys(failures))
