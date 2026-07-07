"""Generation result-set completeness contract (004E-E2.3C Prompt 3 — F3).

Assembly previously validated only run-context coherence
(``assert_results_share_run_context``), so a partial / empty / duplicated result
set could still reach ``_aggregate_findings`` and publish a false
``all_clean = true``. These tests pin the completeness invariant:

    actual result identities == expected run-start plan identities
    (exact multiplicity, order-independent)

and prove an incomplete run cannot publish authoritative findings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[4]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from scripts.generate_iteration_004e_f_samples import (  # noqa: E402
    OUTPUT_DIR as REAL_OUTPUT_DIR,
    assemble_and_write,
    build_work_items,
    check_result_set_completeness,
    compute_work_plan_digest,
    result_identity,
    work_item_identity,
)
from app.agents.job_search.quality.run_manifest import RunContext  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[5]


def _item(kind: str, sample: str) -> dict:
    if kind in ("cross", "random"):
        return {
            "kind": kind,
            "case": {
                "sample": sample,
                "role": sample,
                "focus": [],
                "input_type": "x",
                "job": {"title": sample},
            },
        }
    return {"kind": kind, "sample": sample, "outfile": f"{sample}.md", "job": {"title": sample}, "focus": [], "role": sample, "input_type": "x"}


def _result(kind: str, sample: str) -> dict:
    return {"kind": kind, "outfile": None, "row": {"sample": sample}, "pack_markdown": "# p"}


_PLAN = [_item("cross", "A"), _item("cross", "B"), _item("single", "T"), _item("random", "R")]


def _complete_results() -> list[dict]:
    return [_result("cross", "A"), _result("cross", "B"), _result("single", "T"), _result("random", "R")]


_ROW_COUNTER_KEYS = (
    "question_count", "answer_count", "study_module_count", "coverage_score",
    "source_ladder_present", "export_ready", "missing_answer_count",
    "missing_study_module_count", "hard_max_violation_count", "fake_url_hits",
    "generic_phrase_hits", "silly_question_hits", "empty_section_count",
    "duplicate_study_module_count", "internal_label_leak_count",
    "unsupported_personal_claim_count", "unsupported_numeric_claim_count",
    "cross_domain_contamination_hits", "surface_quality_defect_count",
    "thin_input_specificity_violation_count", "structure_incomplete_count",
    "substantive_depth_failure_count",
)


def _synthetic_audit_metrics(*_args: object, **kwargs: object) -> dict:
    sample = str(kwargs.get("sample_name") or "X")
    role = str(kwargs.get("role_label") or sample)
    input_type = str(kwargs.get("input_type") or "x")
    metrics = {
        "sample": sample,
        "role": role,
        "input_type": input_type,
        "question_count": 1,
        "answer_count": 1,
        "study_module_count": 1,
        "coverage_score": 1.0,
        "source_ladder_present": False,
        "export_ready": True,
        "pack_markdown": f"# {sample}\n",
    }
    metrics.update({k: 0 for k in _ROW_COUNTER_KEYS if k not in metrics})
    return metrics


def _patch_synthetic_audit(monkeypatch, gen) -> None:
    monkeypatch.setattr(gen, "audit_generated_pack", _synthetic_audit_metrics)


def _generate_plan_results(gen, ctx: RunContext, plan: list[dict]) -> list:
    return [gen.generate_work_item(item, ctx) for item in plan]


# --- identity sanity ------------------------------------------------------------

def test_identity_matches_between_item_and_result() -> None:
    for it in _PLAN:
        sample = it.get("sample") or it["case"]["sample"]
        assert work_item_identity(it) == result_identity(_result(it["kind"], sample))


# --- T1 — empty result set ------------------------------------------------------

def test_t1_empty_result_set_rejected() -> None:
    problems = check_result_set_completeness([], _PLAN)
    assert problems and any("empty" in p for p in problems)


# --- T2 — one missing -----------------------------------------------------------

def test_t2_one_missing_rejected() -> None:
    results = _complete_results()[:-1]  # drop the random result
    problems = check_result_set_completeness(results, _PLAN)
    assert any("missing" in p for p in problems)


# --- T3 — multiple missing ------------------------------------------------------

def test_t3_multiple_missing_rejected() -> None:
    problems = check_result_set_completeness(_complete_results()[:1], _PLAN)
    assert sum("missing" in p for p in problems) >= 2


# --- T4 — duplicate identity ----------------------------------------------------

def test_t4_duplicate_identity_rejected() -> None:
    results = _complete_results() + [_result("cross", "A")]  # duplicate A
    problems = check_result_set_completeness(results, _PLAN)
    assert any("duplicate" in p or "unexpected" in p for p in problems)


# --- T5 — unexpected extra identity ---------------------------------------------

def test_t5_unexpected_extra_identity_rejected() -> None:
    results = _complete_results() + [_result("cross", "GHOST")]
    problems = check_result_set_completeness(results, _PLAN)
    assert any("GHOST" in p for p in problems)


# --- T6 — complete but reordered ------------------------------------------------

def test_t6_reordered_complete_passes() -> None:
    results = list(reversed(_complete_results()))
    assert check_result_set_completeness(results, _PLAN) == []


# --- T7 — exact complete --------------------------------------------------------

def test_t7_exact_complete_passes() -> None:
    assert check_result_set_completeness(_complete_results(), _PLAN) == []


# --- T8 — chunk loss ------------------------------------------------------------

def test_t8_chunk_loss_detected() -> None:
    """Simulate 3 batches; drop batch 2 entirely."""
    batch1 = [_result("cross", "A")]
    batch3 = [_result("random", "R")]
    combined = batch1 + batch3  # batch2 ([B, T]) lost
    problems = check_result_set_completeness(combined, _PLAN)
    assert any("missing" in p for p in problems)


# --- T9 — false-clean negative control (incomplete cannot publish) --------------

def test_t9_incomplete_run_cannot_publish_findings(tmp_path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    _patch_synthetic_audit(monkeypatch, gen)
    plan = list(_PLAN)
    ctx = RunContext.create(REPO_ROOT, run_id="run-f3-neg", work_plan_digest=compute_work_plan_digest(plan))
    partial = _generate_plan_results(gen, ctx, plan[:2])
    with pytest.raises(SystemExit, match="generation_result_set_incomplete"):
        gen.assemble_and_write(partial, ctx, expected_items=plan)
    assert not (tmp_path / "sample_final_quality_findings.json").exists()
    assert not (tmp_path / "run_manifest.json").exists()


def test_t9b_complete_run_publishes(tmp_path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    _patch_synthetic_audit(monkeypatch, gen)
    plan = [_item("cross", "A"), _item("cross", "B"), _item("random", "R")]
    ctx = RunContext.create(REPO_ROOT, run_id="run-f3-pos", work_plan_digest=compute_work_plan_digest(plan))
    results = _generate_plan_results(gen, ctx, plan)
    gen.assemble_and_write(results, ctx, expected_items=plan)
    assert (tmp_path / "sample_final_quality_findings.json").exists()
    assert (tmp_path / "run_manifest.json").exists()


# --- T10 — plan digest stability (order-independent) ----------------------------

def test_t10_plan_digest_is_order_independent_and_content_sensitive() -> None:
    d1 = compute_work_plan_digest(_PLAN)
    d2 = compute_work_plan_digest(list(reversed(_PLAN)))
    assert d1 == d2
    assert compute_work_plan_digest(_PLAN[:-1]) != d1  # missing item -> different plan


# --- T13 — stored regenerated run proves complete row coverage ------------------

def test_t13_stored_metrics_row_count_matches_plan() -> None:
    metrics_path = (
        REPO_ROOT / "project_review" / "samples" / "iteration_004e_f_final_regression" / "metrics.json"
    )
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    rows = payload["data"] if isinstance(payload, dict) else payload
    expected = build_work_items()
    assert len(rows) == len(expected), (len(rows), len(expected))
    identities = [f"{r.get('input_type')}::{r['sample']}" for r in rows]
    assert len(identities) == len(set(identities)), "stored metrics have duplicate sample rows"


# --- F3 narrow hardening — publication API bypass guards -----------------------


def _assembly_output_dir(tmp_path, monkeypatch):
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    return gen


def _minimal_publish_plan() -> list[dict]:
    return [_item("cross", "A"), _item("random", "R")]


def test_f3_t1_missing_expected_plan_argument_rejected(tmp_path, monkeypatch) -> None:
    """Omitting expected_items must not reach publication."""
    gen = _assembly_output_dir(tmp_path, monkeypatch)
    _patch_synthetic_audit(monkeypatch, gen)
    plan = _minimal_publish_plan()
    ctx = RunContext.create(
        REPO_ROOT, run_id="run-f3-no-plan", work_plan_digest=compute_work_plan_digest(plan)
    )
    results = _generate_plan_results(gen, ctx, plan)
    with pytest.raises(TypeError):
        gen.assemble_and_write(results, ctx)
    assert not (tmp_path / "run_manifest.json").exists()
    assert not (tmp_path / "sample_final_quality_findings.json").exists()


def test_f3_t2_explicit_none_expected_plan_rejected(tmp_path, monkeypatch) -> None:
    gen = _assembly_output_dir(tmp_path, monkeypatch)
    _patch_synthetic_audit(monkeypatch, gen)
    plan = _minimal_publish_plan()
    ctx = RunContext.create(
        REPO_ROOT, run_id="run-f3-none", work_plan_digest=compute_work_plan_digest(plan)
    )
    results = _generate_plan_results(gen, ctx, plan)
    with pytest.raises(SystemExit, match="generation_plan_required"):
        gen.assemble_and_write(results, ctx, expected_items=None)
    assert not (tmp_path / "run_manifest.json").exists()
    assert not (tmp_path / "sample_final_quality_findings.json").exists()


def test_f3_t3_missing_bound_work_plan_digest_rejected(tmp_path, monkeypatch) -> None:
    gen = _assembly_output_dir(tmp_path, monkeypatch)
    _patch_synthetic_audit(monkeypatch, gen)
    plan = _minimal_publish_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f3-unbound")
    assert not ctx.manifest.get("work_plan_digest")
    results = _generate_plan_results(gen, ctx, plan)
    with pytest.raises(SystemExit, match="generation_plan_unbound"):
        gen.assemble_and_write(results, ctx, expected_items=plan)
    assert not (tmp_path / "run_manifest.json").exists()
    assert not (tmp_path / "sample_final_quality_findings.json").exists()


def test_f3_t4_matching_bound_plan_still_passes(tmp_path, monkeypatch) -> None:
    """Positive control: bound digest + complete results still publish."""
    gen = _assembly_output_dir(tmp_path, monkeypatch)
    _patch_synthetic_audit(monkeypatch, gen)
    plan = _minimal_publish_plan()
    ctx = RunContext.create(
        REPO_ROOT, run_id="run-f3-match", work_plan_digest=compute_work_plan_digest(plan)
    )
    results = _generate_plan_results(gen, ctx, plan)
    gen.assemble_and_write(results, ctx, expected_items=plan)
    assert (tmp_path / "sample_final_quality_findings.json").exists()
    assert (tmp_path / "run_manifest.json").exists()


def test_f3_t5_mismatched_bound_plan_still_fails(tmp_path, monkeypatch) -> None:
    gen = _assembly_output_dir(tmp_path, monkeypatch)
    _patch_synthetic_audit(monkeypatch, gen)
    plan_a = _minimal_publish_plan()
    plan_b = plan_a + [_item("cross", "GHOST")]
    ctx = RunContext.create(
        REPO_ROOT, run_id="run-f3-mismatch", work_plan_digest=compute_work_plan_digest(plan_a)
    )
    results = _generate_plan_results(gen, ctx, plan_b)
    with pytest.raises(SystemExit, match="generation_plan_mismatch"):
        gen.assemble_and_write(results, ctx, expected_items=plan_b)
    assert not (tmp_path / "run_manifest.json").exists()
    assert not (tmp_path / "sample_final_quality_findings.json").exists()
