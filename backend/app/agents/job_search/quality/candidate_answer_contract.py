"""Unified candidate-answer quality contract (JOB-INT-R1 §12).

One place that answers the question "does this text read like a real candidate
speaking in an interview?" — used two ways:

* ``candidate_voice_violations`` / ``study_material_violations`` are the
  assertions the JOB-INT-R1 tests run against every generation path (live
  Ollama, deterministic fallback, mock, finalizer, compiler) so a regression on
  ANY path is caught, not just the one that happened to be exercised.
* ``enforce_candidate_voice`` is a conservative runtime safety-net wired into
  the finalizer: it repairs the few unambiguous coaching/second-person leaks
  (mostly relevant to raw LLM output) without touching substance.

The contract is deliberately about *voice and honesty*, not domain depth —
domain density, contamination, study depth, etc. already have their own audits.
"""

from __future__ import annotations

import re

# Coaching / meta phrasing that must never appear in a spoken model answer.
COACHING_PHRASES: tuple[str, ...] = (
    "you should say",
    "you should",
    "the candidate should",
    "a strong answer",
    "strong answer would",
    "strong answer could",
    "interviewers look for",
    "interviewers are looking",
    "interviewers reward",
    "interviewers want",
    "use the star method",
    "structured with star",
    "this answer succeeds because",
    "in this role context",
    "how to answer",
    "the way to answer",
    "as your anchor",
    "rehearse aloud",
    "practice guidance",
)

# First-person → second-person leaks (candidate speech should never say these).
SECOND_PERSON_LEAKS: tuple[str, ...] = (
    "you could",
    "you would want",
    "you'd want",
    "you need to explain",
    "you can explain",
)

# The authoring persona must never surface in the answer itself.
PERSONA_LEAKS: tuple[str, ...] = (
    "phd-level scholar",
    "phd scholar",
    "world's foremost expert",
    "master teacher",
    "foremost expert in the room",
)

# Unfilled template placeholders.
PLACEHOLDER_MARKERS: tuple[str, ...] = (
    "[specific",
    "[measurable",
    "[company",
    "[insert",
    "[role",
    "[name]",
)

# Robotic STAR scaffolding labels.
STAR_LABELS: tuple[str, ...] = (
    "**situation:**",
    "**task:**",
    "**action:**",
    "**result:**",
)

_FIRST_PERSON_RE = re.compile(r"\b(i|i'd|i'll|i'm|i've|my|me|myself)\b", re.I)
_WORD_RE = re.compile(r"\b\w+\b")


def candidate_voice_violations(
    text: str,
    *,
    role: str = "",
    question: str = "",
    category: str = "",
    min_words: int = 45,
) -> list[str]:
    """Return the list of candidate-voice contract violations for ``text``.

    Empty list == the answer reads like a real candidate speaking. Callers can
    assert ``candidate_voice_violations(...) == []``.
    """
    problems: list[str] = []
    body = (text or "").strip()
    if not body:
        return ["empty_answer"]

    low = body.lower()
    words = _WORD_RE.findall(body)
    if len(words) < min_words:
        problems.append(f"too_short:{len(words)}w")

    if not _FIRST_PERSON_RE.search(body):
        problems.append("not_first_person")

    for phrase in COACHING_PHRASES:
        if phrase in low:
            problems.append(f"coaching:{phrase}")
    for phrase in SECOND_PERSON_LEAKS:
        if phrase in low:
            problems.append(f"second_person:{phrase}")
    for phrase in PERSONA_LEAKS:
        if phrase in low:
            problems.append(f"persona_leak:{phrase}")
    for marker in PLACEHOLDER_MARKERS:
        if marker in low:
            problems.append(f"placeholder:{marker}")
    for label in STAR_LABELS:
        if label in low:
            problems.append(f"star_label:{label}")

    # Second-person density: an occasional "you" is fine (e.g. addressing the
    # interviewer), but an answer dominated by "you/your" reads as coaching.
    you_count = len(re.findall(r"\byou\b|\byour\b", low))
    i_count = len(re.findall(r"\bi\b|\bmy\b|\bi'd\b|\bi'll\b|\bi'm\b", low))
    if you_count >= 3 and you_count > i_count:
        problems.append(f"second_person_dominant:you={you_count},i={i_count}")

    return problems


def role_specificity_ok(text: str, *, role: str = "", anchors: list[str] | None = None) -> bool:
    """True when the answer references the role or at least one provided anchor
    (a responsibility / skill / stream keyword)."""
    low = (text or "").lower()
    if role and role.lower() in low:
        return True
    for anchor in anchors or []:
        a = str(anchor or "").strip().lower()
        if a and a in low:
            return True
    return False


def study_material_violations(study: dict, *, question: str = "") -> list[str]:
    """Return study-material contract violations (§10)."""
    problems: list[str] = []
    if not isinstance(study, dict) or not study:
        return ["empty_study_material"]

    overview = str(study.get("overview") or "").strip()
    what_tests = str(study.get("what_this_question_tests") or "").strip()
    if not overview and not what_tests:
        problems.append("no_overview_or_what_tests")

    # Must teach something concrete: definitions OR key concepts OR a method.
    has_concepts = any(
        study.get(k)
        for k in (
            "definitions",
            "key_concepts",
            "key_principles",
            "step_by_step_method",
            "step_by_step_breakdown",
        )
    )
    if not has_concepts:
        problems.append("no_definitions_or_concepts_or_method")

    return problems


# ---------------------------------------------------------------------------
# Conservative runtime repair (safety net for raw LLM output).
# ---------------------------------------------------------------------------

_COACHING_PREAMBLE_RE = re.compile(
    r"^\s*A strong answer[^.]*\.\s*(Use the question[^.]*\.\s*)?",
    re.I,
)
_SECOND_PERSON_FIXES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bYou could\b"), "I could"),
    (re.compile(r"\byou could\b"), "I could"),
    (re.compile(r"\bYou would\b"), "I would"),
    (re.compile(r"\byou would\b"), "I would"),
    (re.compile(r"\bYou should\b"), "I would"),
    (re.compile(r"\byou should\b"), "I would"),
)


def enforce_candidate_voice(text: str) -> str:
    """Repair unambiguous coaching/second-person leaks in a *model answer*.

    Intentionally minimal: strips a leading "A strong answer… Use the question…"
    coaching preamble and flips clearly-second-person modal statements to first
    person. It never rewrites substance and is a no-op on already-clean answers.
    Only ever apply this to the spoken model answer, not to study material.
    """
    body = (text or "").strip()
    if not body:
        return body
    body = _COACHING_PREAMBLE_RE.sub("", body).strip()
    # Drop robotic STAR labels but keep the sentence that follows them.
    body = re.sub(r"\*\*(Situation|Task|Action|Result|Practice guidance):\*\*\s*", "", body, flags=re.I)
    for pattern, repl in _SECOND_PERSON_FIXES:
        body = pattern.sub(repl, body)
    body = re.sub(r"\s{2,}", " ", body).strip()
    return body
