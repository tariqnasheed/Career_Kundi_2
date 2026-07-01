"""
agents/common/reflector.py
==============================
`BaseReflectorAgent`: the quality gate every Executor's output passes
through before reaching the user. Implements the 11 rejection criteria
from §3.6 as deterministic CODE checks — citation-integrity checking,
generic-boilerplate phrase detection, unsupported-claim heuristics, and
confidence scoring — rather than relying solely on the LLM to police its
own output.

This is defense-in-depth alongside the prompt-level instructions in
`prompts.py`: an LLM can ignore instructions in its system prompt, but it
cannot talk its way past a regex that checks whether a `[7]` citation
marker actually corresponds to one of the 3 sources it was given.

Feature-specific Reflectors subclass `BaseReflectorAgent` and override
`domain_checks()` for structural checks unique to that feature's output
schema (e.g. the CV Reflector checking every bullet traces back to a real
`WorkExperience` entry; the Roadmap Reflector checking every resource has a
real, non-empty URL).
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.common.base import BaseAgent

# Phrases that signal generic/templated language rather than input-specific
# content (§3.6 rejection criterion 3, "generic boilerplate"). Deliberately
# conservative — a false positive here just triggers one extra, cheap
# revision round rather than wrongly blocking good output.
GENERIC_PHRASES = [
    "results-driven professional",
    "team player",
    "fast-paced environment",
    "synergy",
    "wear many hats",
    "go-getter",
    "self-starter who thrives",
    "passionate about leveraging",
    "dynamic individual",
    "proven track record of success",
    "detail-oriented professional",
    "excellent communication skills",
]

_CITATION_MARKER_PATTERN = re.compile(r"\[(\d+)\]")


def check_citation_integrity(text: str, num_available_citations: int) -> list[str]:
    """
    Rejection criterion 2: every `[n]` marker in the text must reference a
    citation that actually exists in the numbered context handed to the
    Executor. A `[7]` marker when only 3 citations were retrieved is a
    fabricated / out-of-range citation and is rejected outright.
    """
    referenced = {int(n) for n in _CITATION_MARKER_PATTERN.findall(text)}
    out_of_range = sorted(n for n in referenced if n < 1 or n > num_available_citations)
    if out_of_range:
        return [f"References citation marker(s) {out_of_range} that don't exist in the retrieved context."]
    return []


def check_generic_language(text: str) -> list[str]:
    """Rejection criterion 3: flag known generic-boilerplate phrases verbatim."""
    lowered = text.lower()
    return [f"Contains generic boilerplate phrase: '{phrase}'" for phrase in GENERIC_PHRASES if phrase in lowered]


def check_unsupported_claims(text: str, num_available_citations: int) -> list[str]:
    """
    Rejection criterion 1 (heuristic half): flags sentences containing a
    specific number/statistic with NO citation marker anywhere in them as
    potentially unsupported factual claims worth a revision pass. This is
    a heuristic, not exhaustive — it pairs with `check_citation_integrity`
    for the structural half of the same rejection criterion. Capped at 5
    reported issues per pass so revision feedback stays readable.
    """
    if num_available_citations == 0:
        return []
    issues = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        has_number = bool(re.search(r"\b\d+(\.\d+)?%?\b", sentence))
        has_citation = bool(_CITATION_MARKER_PATTERN.search(sentence))
        if has_number and not has_citation and len(sentence) > 40:
            issues.append(f"Sentence has a number but no citation: '{sentence.strip()[:100]}'")
    return issues[:5]


def compute_confidence_score(
    *,
    num_issues: int,
    num_citations: int,
    is_grounded_search_hit: bool,
    revision_count: int,
) -> float:
    """
    Blend several signals into a single 0.0-1.0 confidence score surfaced
    to the user alongside generated content (§2 "Confidence Scoring"):
    fewer issues and more citations raise confidence; each revision round
    needed lowers it slightly (the first draft wasn't solid); independent
    search-grounding confirmation (live mode only) raises it further.
    """
    score = 1.0
    score -= min(0.5, num_issues * 0.12)
    score += min(0.15, num_citations * 0.03)
    score -= revision_count * 0.05
    if is_grounded_search_hit:
        score += 0.1
    return round(max(0.0, min(1.0, score)), 2)


class BaseReflectorAgent(BaseAgent):
    """
    Generic Reflector. Runs the shared checks above against
    `state[self.output_field]` (flattened to text via `render_for_review`),
    merges in any `domain_checks()` issues from the subclass, computes a
    confidence score, and decides whether another revision round is
    warranted.
    """

    name = "ReflectorAgent"
    output_field: str = "draft_output"
    max_revisions: int = 3

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get(self.output_field)
        citations = state.get("citations", [])
        revision_count = state.get("revision_count", 0)

        text = self.render_for_review(draft)
        issues: list[str] = []
        issues += check_citation_integrity(text, len(citations))
        issues += check_generic_language(text)
        issues += check_unsupported_claims(text, len(citations))
        issues += await self.domain_checks(state, draft)

        confidence = compute_confidence_score(
            num_issues=len(issues),
            num_citations=len(citations),
            is_grounded_search_hit=bool(state.get("search_grounded")),
            revision_count=revision_count,
        )

        passed = len(issues) == 0
        can_revise = revision_count < self.max_revisions
        should_revise = (not passed) and can_revise
        # After exhausting revision rounds we stop looping forever, but we
        # do NOT silently call it "passed" — `reflection_forced_accept`
        # tells the route layer / UI to surface a low-confidence warning
        # rather than presenting a still-flawed draft as fully verified.
        forced_accept = (not passed) and not can_revise

        if issues:
            self.logger.warning(
                "reflector_found_issues",
                issues=issues,
                will_revise=should_revise,
                forced_accept=forced_accept,
                revision_count=revision_count,
                confidence=confidence,
            )

        return {
            "reflection_passed": passed or forced_accept,
            "reflection_forced_accept": forced_accept,
            "reflection_issues": issues,
            "confidence_score": confidence,
            "revision_count": revision_count + (1 if should_revise else 0),
            "_should_revise": should_revise,
        }

    def render_for_review(self, draft: Any) -> str:
        """
        Flatten the draft output into plain text for the text-based checks
        above. Override this if `draft` isn't a simple string or a flat
        dict of string/number values (e.g. nested lists of interview
        questions) — see each feature's own Reflector for examples.
        """
        if isinstance(draft, str):
            return draft
        if isinstance(draft, dict):
            return " ".join(str(v) for v in draft.values() if isinstance(v, (str, int, float)))
        if isinstance(draft, list):
            return " ".join(self.render_for_review(item) for item in draft)
        return str(draft)

    async def domain_checks(self, state: dict[str, Any], draft: Any) -> list[str]:
        """Override in feature-specific subclasses for structural checks unique to that feature's output schema."""
        return []
