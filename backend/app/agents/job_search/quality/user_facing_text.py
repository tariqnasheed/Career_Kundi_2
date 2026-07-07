"""Shared recursive iterator over user-facing prose (Iteration 004E-E2.2 corrective).

Audits and sanitizers must inspect ALL user-facing text — including strings nested
in lists, tuples, and dicts (e.g. advanced_extension) — not just top-level fields.
This keeps a single definition of "what counts as user-facing prose" so the claim,
surface-quality, and cross-domain guards stay consistent.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from typing import Any

# Keys whose values are metadata / provenance / numeric bookkeeping, not user-facing
# prose. Scanning them creates noise (or false positives) so they are skipped.
NON_PROSE_KEYS: frozenset[str] = frozenset(
    {
        "question_id",
        "question_type",
        "category",
        "skill_tag",
        "role_family",
        "answer_source",
        "study_depth",
        "study_depth_label",
        "study_complexity_level",
        "complexity_signals",
        "budget_status",
        "budget_reason",
        "concise_complete_reason",
        "target_min_words",
        "target_max_words",
        "hard_max_words",
        "actual_word_count",
        "hard_max_ratio",
        "estimated_reading_time_minutes",
        "source_items_used",
        "source_types_used",
        "source_priority_used",
        "source_status",
        "fallback_status",
        "model_knowledge",
        "question_source_types",
        "study_sources",
        "coverage_audit",
        "source_ladder",
        "job_posting_extraction",
        "company_research",
        "depth_contract_required_elements",
        "depth_contract_present_elements",
        "depth_contract_substantive_elements",
        "depth_contract_weak_elements",
        "depth_contract_missing_elements",
        "depth_contract_coverage",
        "substantive_contract_coverage",
        "unsupported_personal_claim_count",
        "unsupported_numeric_claim_count",
        "thin_input_specificity_violation_count",
        "surface_quality_defect_count",
        "cross_domain_contamination_hits",
        "thin_input_conservative",
        "quality_audit",
        "claim_support_status",
        "rewritten_for_claim_integrity",
    }
)


# Safety ceiling on the total number of container nodes visited in a single
# traversal. This is a defence against pathological / adversarial structures, not
# a semantic depth cutoff: real study modules contain well under a few thousand
# nodes, so legitimate deeply-nested user-facing prose is never silently dropped.
MAX_CONTAINER_NODES = 100_000


def iter_user_facing_text(
    obj: Any,
    *,
    skip_keys: frozenset[str] = NON_PROSE_KEYS,
) -> Iterator[str]:
    """Yield every user-facing prose string found recursively inside ``obj``.

    Strings, and strings nested inside lists/tuples/dicts (including deeply nested
    extension structures), are yielded. Dict keys listed in ``skip_keys`` are not
    descended into. Numbers/booleans/None are ignored.

    Traversal is cycle-aware (tracks visited container object identities) so it is
    safe against self-referential structures without imposing an arbitrary depth
    cutoff that could silently omit legitimate, deeply-nested user-facing prose.
    """
    visited: set[int] = set()
    node_budget = [MAX_CONTAINER_NODES]

    def _walk(node: Any) -> Iterator[str]:
        if isinstance(node, str):
            text = node.strip()
            if text:
                yield text
            return
        # Scalars (int/float/bool/None/bytes) are not user-facing prose.
        if isinstance(node, (bytes, bytearray)) or not isinstance(
            node, (Mapping, list, tuple, Sequence)
        ):
            return

        # Cycle guard: never descend into the same container twice.
        ident = id(node)
        if ident in visited:
            return
        if node_budget[0] <= 0:
            return
        visited.add(ident)
        node_budget[0] -= 1

        if isinstance(node, Mapping):
            for key, value in node.items():
                if isinstance(key, str) and key in skip_keys:
                    continue
                yield from _walk(value)
            return
        for item in node:
            yield from _walk(item)

    yield from _walk(obj)


def collect_user_facing_text(obj: Any, *, skip_keys: frozenset[str] = NON_PROSE_KEYS) -> str:
    """Join all user-facing prose from ``obj`` into a single blob for scanning."""
    return "\n".join(iter_user_facing_text(obj, skip_keys=skip_keys))
