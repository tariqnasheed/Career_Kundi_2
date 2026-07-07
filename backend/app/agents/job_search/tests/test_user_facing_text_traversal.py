"""Recursive user-facing-text traversal tests (004E-E2.3 §14).

The audit traversal must reach legitimate, deeply-nested user-facing prose (no
silent depth cutoff), terminate on self-referential structures, and skip
metadata/provenance keys so bookkeeping is never treated as user-facing content.
"""

from __future__ import annotations

from app.agents.job_search.quality.user_facing_text import (
    NON_PROSE_KEYS,
    collect_user_facing_text,
    iter_user_facing_text,
)


def test_deeply_nested_user_facing_text_is_reached() -> None:
    """Prose nested far deeper than any old cutoff must still be audited."""
    depth = 60
    node: dict = {"leaf": "UNSUPPORTED deep claim marker"}
    for i in range(depth):
        node = {"advanced_extension": {"notes": [node], "label": f"level {i}"}}
    blob = collect_user_facing_text(node)
    assert "UNSUPPORTED deep claim marker" in blob


def test_cycle_does_not_recurse_forever() -> None:
    """A self-referential structure must terminate and still yield its prose."""
    a: dict = {"text": "cycle-safe prose"}
    b: dict = {"nested": a}
    a["back_ref"] = b  # introduce a cycle a -> b -> a
    a["self_ref"] = a

    collected = list(iter_user_facing_text(a))
    assert "cycle-safe prose" in collected


def test_list_cycle_terminates() -> None:
    items: list = ["visible list prose"]
    items.append(items)  # self-referential list
    collected = list(iter_user_facing_text(items))
    assert "visible list prose" in collected


def test_metadata_keys_are_not_user_facing() -> None:
    """Provenance / numeric bookkeeping keys must be excluded from prose scanning."""
    obj = {
        "overview": "This is genuine study prose.",
        "study_depth": "complex_scenario",
        "budget_status": "within_target",
        "actual_word_count": 512,
        "answer_source": "contract_compiler",
        "quality_audit": {"note": "internal audit metadata should not surface"},
    }
    blob = collect_user_facing_text(obj)
    assert "This is genuine study prose." in blob
    # A representative sample of excluded keys must not leak their values as prose.
    assert "complex_scenario" not in blob
    assert "within_target" not in blob
    assert "contract_compiler" not in blob
    assert "internal audit metadata should not surface" not in blob


def test_non_prose_keys_frozenset_covers_core_metadata() -> None:
    for key in ("study_depth", "budget_status", "answer_source", "quality_audit"):
        assert key in NON_PROSE_KEYS


def test_scalars_are_ignored() -> None:
    obj = {"a": 1, "b": 2.5, "c": True, "d": None, "e": "real prose"}
    collected = list(iter_user_facing_text(obj))
    assert collected == ["real prose"]
