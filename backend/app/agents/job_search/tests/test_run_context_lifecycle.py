"""Run-context lifecycle, TOCTOU protection, and artifact-byte integrity
(004E-E2.3C Slice 1.1 / Prompt 1).

These tests reproduce the two confirmed lineage gaps left by Slice 1:

* GAP A — run identity was created at ASSEMBLY time (after every work item was
  generated), so the manifest could describe assembly-time repository state
  rather than generation-time state (a TOCTOU defect);
* GAP B — a matching run_id / manifest did NOT bind the exact artifact bytes, so
  an output file could be edited after generation while keeping run_id, HEAD,
  worktree fingerprint, and audit schema unchanged.

All lifecycle logic is exercised with injected values so nothing depends on a
hardcoded current SHA or on staging anything in git.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agents.job_search.quality.run_manifest import (
    REASON_ARTIFACT_HASH_MISMATCH,
    REASON_AUDIT_SCHEMA_CHANGED,
    REASON_DIRTY_WORKTREE_CHANGED,
    REASON_GIT_HEAD_CHANGED,
    ROOT_INDEX_FILENAME,
    STATUS_ARTIFACT_HASH_MISMATCH,
    STATUS_CURRENT,
    STATUS_GENERATION_CONTEXT_CHANGED,
    STATUS_LEGACY_UNVERIFIED,
    STATUS_MIXED_RUN,
    RunContext,
    build_generation_run_manifest,
    compute_audit_schema_version,
    context_digest_of,
    detect_generation_context_change,
    fingerprint_from_inputs,
    render_manifest_markdown_comment,
    results_share_run_context,
    validate_artifact_run,
    write_run_index,
)

REPO_ROOT = Path(__file__).resolve().parents[5]

_KEYS = ("missing_answer_count", "generic_phrase_hits")


def _manifest(**overrides) -> dict:
    base = {
        "manifest_version": 1,
        "run_id": "run-fixed-0001",
        "generated_at": "2026-07-07T00:00:00Z",
        "git_head": "a" * 40,
        "dirty_worktree_fingerprint": "f" * 16,
        "audit_schema_version": compute_audit_schema_version(_KEYS),
        "metrics_schema_version": "2",
        "findings_schema_version": "2",
    }
    base.update(overrides)
    return base


def _run_context(**overrides) -> RunContext:
    return RunContext.from_manifest(_manifest(**overrides), repo_root=str(REPO_ROOT))


# --- T1 — run context exists BEFORE the first work item ------------------------

def test_t1_run_context_created_before_first_work_item() -> None:
    """The run identity must be constructible independently, before any work is
    generated, and must be immutable and self-consistent."""
    ctx = RunContext.create(REPO_ROOT, run_id="run-lifecycle-1")
    assert ctx.run_id == "run-lifecycle-1"
    # Immutable: frozen dataclass rejects field reassignment.
    with pytest.raises(Exception):
        ctx.context_digest = "tampered"  # type: ignore[misc]
    # Digest is derived from the manifest identity and is stable.
    assert ctx.context_digest == context_digest_of(ctx.manifest)
    # A freshly built manifest (no work generated yet) already carries the digest.
    bound = ctx.bind_result({"kind": "cross"})
    assert bound["run_id"] == "run-lifecycle-1"
    assert bound["run_context_digest"] == ctx.context_digest


# --- T2 — mixed work-item contexts rejected ------------------------------------

def test_t2_mixed_work_item_contexts_are_rejected() -> None:
    ctx_x = _run_context(run_id="run-X")
    ctx_y = _run_context(run_id="run-Y", git_head="b" * 40)
    result_a = ctx_x.bind_result({"kind": "a"})
    result_b = ctx_y.bind_result({"kind": "b"})
    ok, problems = results_share_run_context([result_a, result_b], ctx_x)
    assert ok is False
    assert problems


# --- T3 — same run_id, different context digest ---------------------------------

def test_t3_same_run_id_different_context_digest_is_rejected() -> None:
    ctx = _run_context(run_id="run-shared")
    good = ctx.bind_result({"kind": "a"})
    # Same run_id, but the context digest was computed under a different repo
    # state (different HEAD) — must be rejected even though run_id matches.
    forged = dict(good)
    forged["run_context_digest"] = context_digest_of(_manifest(run_id="run-shared", git_head="c" * 40))
    ok, problems = results_share_run_context([good, forged], ctx)
    assert ok is False
    assert any("digest" in p.lower() for p in problems)


# --- T4 — repository changed during generation (TOCTOU) -------------------------

def test_t4_repository_change_during_generation_is_detected() -> None:
    start = {
        "git_head": "a" * 40,
        "dirty_worktree_fingerprint": "1" * 16,
        "audit_schema_version": "s1",
    }
    end_same = dict(start)
    assert detect_generation_context_change(start, end_same) == []

    end_dirty = {**start, "dirty_worktree_fingerprint": "2" * 16}
    assert REASON_DIRTY_WORKTREE_CHANGED in detect_generation_context_change(start, end_dirty)

    end_head = {**start, "git_head": "b" * 40}
    assert REASON_GIT_HEAD_CHANGED in detect_generation_context_change(start, end_head)

    end_schema = {**start, "audit_schema_version": "s2"}
    assert REASON_AUDIT_SCHEMA_CHANGED in detect_generation_context_change(start, end_schema)


def test_t4b_context_changed_run_index_validates_as_generation_context_changed(tmp_path: Path) -> None:
    manifest = _manifest()
    (tmp_path / "metrics.json").write_text(
        json.dumps({"manifest": manifest, "data": []}), encoding="utf-8"
    )
    write_run_index(
        tmp_path, manifest, ["metrics.json"], generation_context_changed=[REASON_GIT_HEAD_CHANGED]
    )
    result = validate_artifact_run(tmp_path, _context_from(manifest))
    assert result["status"] == STATUS_GENERATION_CONTEXT_CHANGED


# --- T5 — metrics tamper (run_id preserved) ------------------------------------

def _context_from(manifest: dict) -> dict:
    return {
        "git_head": manifest["git_head"],
        "dirty_worktree_fingerprint": manifest["dirty_worktree_fingerprint"],
        "audit_schema_version": manifest["audit_schema_version"],
        "metrics_schema_version": manifest["metrics_schema_version"],
        "findings_schema_version": manifest["findings_schema_version"],
    }


def _write_run(tmp_path: Path, manifest: dict) -> None:
    (tmp_path / "metrics.json").write_text(
        json.dumps({"manifest": manifest, "data": [{"sample": "X"}]}), encoding="utf-8"
    )
    (tmp_path / "sample_final_quality_findings.json").write_text(
        json.dumps({"manifest": manifest, "all_clean": True}), encoding="utf-8"
    )
    (tmp_path / "sample_cross_sector_regression.md").write_text(
        render_manifest_markdown_comment(manifest) + "\n# pack\n", encoding="utf-8"
    )
    write_run_index(
        tmp_path,
        manifest,
        [
            "metrics.json",
            "sample_final_quality_findings.json",
            "sample_cross_sector_regression.md",
        ],
    )


def test_t5_metrics_tamper_after_generation_is_detected(tmp_path: Path) -> None:
    manifest = _manifest()
    _write_run(tmp_path, manifest)
    # Baseline: untouched run is current.
    assert validate_artifact_run(tmp_path, _context_from(manifest))["status"] == STATUS_CURRENT
    # Edit metrics bytes while PRESERVING the embedded run_id/manifest.
    payload = json.loads((tmp_path / "metrics.json").read_text())
    payload["data"].append({"sample": "SMUGGLED"})
    (tmp_path / "metrics.json").write_text(json.dumps(payload), encoding="utf-8")
    result = validate_artifact_run(tmp_path, _context_from(manifest))
    assert result["status"] == STATUS_ARTIFACT_HASH_MISMATCH
    assert REASON_ARTIFACT_HASH_MISMATCH in result["reasons"]


# --- T6 — findings tamper -------------------------------------------------------

def test_t6_findings_tamper_after_generation_is_detected(tmp_path: Path) -> None:
    manifest = _manifest()
    _write_run(tmp_path, manifest)
    payload = json.loads((tmp_path / "sample_final_quality_findings.json").read_text())
    payload["all_clean"] = False  # flip a single value
    (tmp_path / "sample_final_quality_findings.json").write_text(
        json.dumps({"manifest": manifest, **payload}), encoding="utf-8"
    )
    result = validate_artifact_run(tmp_path, _context_from(manifest))
    assert result["status"] == STATUS_ARTIFACT_HASH_MISMATCH


# --- T7 — same-run-looking markdown swap ----------------------------------------

def test_t7_same_run_markdown_swap_fails_hash(tmp_path: Path) -> None:
    manifest = _manifest()
    _write_run(tmp_path, manifest)
    # Replace the markdown pack with DIFFERENT content that still carries the
    # exact same run manifest comment (so run_id/coherence still "match").
    (tmp_path / "sample_cross_sector_regression.md").write_text(
        render_manifest_markdown_comment(manifest) + "\n# a totally different pack\n",
        encoding="utf-8",
    )
    result = validate_artifact_run(tmp_path, _context_from(manifest))
    assert result["status"] == STATUS_ARTIFACT_HASH_MISMATCH


# --- T8 — copied manifest comment cannot authenticate foreign content -----------

def test_t8_copied_manifest_comment_does_not_authenticate_foreign_file(tmp_path: Path) -> None:
    manifest = _manifest()
    _write_run(tmp_path, manifest)
    # A foreign file that merely copied the manifest comment but is NOT in the
    # authoritative artifact index must not become release evidence: the index
    # binds an exact byte set, and editing an indexed file breaks its hash.
    (tmp_path / "sample_cross_sector_regression.md").write_text(
        render_manifest_markdown_comment(manifest) + "\nforged body copied from elsewhere\n",
        encoding="utf-8",
    )
    result = validate_artifact_run(tmp_path, _context_from(manifest))
    assert result["status"] != STATUS_CURRENT


# --- T9 — coherent untouched run ------------------------------------------------

def test_t9_coherent_untouched_run_is_current(tmp_path: Path) -> None:
    manifest = _manifest()
    _write_run(tmp_path, manifest)
    result = validate_artifact_run(tmp_path, _context_from(manifest))
    assert result["status"] == STATUS_CURRENT
    assert result["reasons"] == []


def test_t9b_mixed_run_index_detected(tmp_path: Path) -> None:
    manifest = _manifest(run_id="run-real")
    foreign = _manifest(run_id="run-foreign")
    (tmp_path / "metrics.json").write_text(
        json.dumps({"manifest": manifest, "data": []}), encoding="utf-8"
    )
    # A markdown artifact whose embedded manifest belongs to a DIFFERENT run.
    (tmp_path / "sample_cross_sector_regression.md").write_text(
        render_manifest_markdown_comment(foreign) + "\n# pack\n", encoding="utf-8"
    )
    write_run_index(tmp_path, manifest, ["metrics.json", "sample_cross_sector_regression.md"])
    result = validate_artifact_run(tmp_path, _context_from(manifest))
    assert result["status"] == STATUS_MIXED_RUN


def test_t9c_missing_root_index_is_legacy_unverified(tmp_path: Path) -> None:
    (tmp_path / "metrics.json").write_text(json.dumps({"data": []}), encoding="utf-8")
    result = validate_artifact_run(tmp_path, _context_from(_manifest()))
    assert result["status"] == STATUS_LEGACY_UNVERIFIED


# --- T10 — index/staged-state semantics ----------------------------------------

def test_t10_fingerprint_is_sensitive_to_index_state() -> None:
    status = [" M backend/a.py"]
    blobs = [("backend/a.py", "deadbeef")]
    # Same worktree status + content, but DIFFERENT staged/index blob state must
    # produce a different fingerprint (the gap the current worktree-only content
    # hash missed).
    fp_idx_a = fingerprint_from_inputs(status, blobs, index_lines=[":100644 100644 aaa bbb M\tbackend/a.py"])
    fp_idx_b = fingerprint_from_inputs(status, blobs, index_lines=[":100644 100644 aaa ccc M\tbackend/a.py"])
    assert fp_idx_a != fp_idx_b
    # Backward compatible: omitting index_lines still works and is deterministic.
    assert fingerprint_from_inputs(status, blobs) == fingerprint_from_inputs(status, blobs)


# --- T11 CORRECTED (Prompt 3 / F1) ---------------------------------------------
#
# The original T11 asserted the generator SCRIPT performs no file IO and
# concluded the documents/ exclusion was "honest". That premise was wrong: the
# generator delegates to ``audit_generated_pack``, whose call graph reads the
# document library (see test_document_library_binding.py::test_t6...). The
# document-library state is now bound via ``document_library_fingerprint``; the
# runtime dependency + binding are proven in that dedicated module, so this
# stale string-scan is intentionally removed here rather than asserting a false
# "no document input" claim.


def test_manifest_build_still_reads_real_git_state() -> None:
    manifest = build_generation_run_manifest(REPO_ROOT)
    assert len(manifest["git_head"]) == 40
    assert len(manifest["dirty_worktree_fingerprint"]) == 16


# --- Prompt 1 correction — context digest covers the COMPLETE manifest ----------


class TestContextDigestCompleteness:
    """The context digest must be derived from the complete authoritative
    manifest, so no future authoritative field can silently escape run identity."""

    def test_c1_key_insertion_order_does_not_change_digest(self) -> None:
        ordered = _manifest()
        shuffled = {k: ordered[k] for k in reversed(list(ordered))}
        assert shuffled != ordered or list(shuffled) != list(ordered)
        assert context_digest_of(ordered) == context_digest_of(shuffled)

    def test_c2_generated_at_change_changes_digest(self) -> None:
        base = _manifest()
        other = _manifest(generated_at="2099-01-01T00:00:00Z")
        assert context_digest_of(base) != context_digest_of(other)

    def test_c3_manifest_version_change_changes_digest(self) -> None:
        base = _manifest()
        other = _manifest(manifest_version=999)
        assert context_digest_of(base) != context_digest_of(other)

    def test_c4_future_authoritative_field_changes_digest(self) -> None:
        """The critical invariant: a NEW manifest field not in any hand-written
        digest list must still alter the context identity."""
        base = _manifest()
        future = _manifest()
        future["some_future_authoritative_field"] = "v1"
        assert context_digest_of(base) != context_digest_of(future)
        # And a change to that new field's value also changes the digest.
        future_v2 = dict(future)
        future_v2["some_future_authoritative_field"] = "v2"
        assert context_digest_of(future) != context_digest_of(future_v2)

    def test_c5_mixed_context_rejection_still_works(self) -> None:
        ctx_x = _run_context(run_id="run-X")
        ctx_y = _run_context(run_id="run-Y", git_head="b" * 40)
        results = [ctx_x.bind_result({"i": 0}), ctx_y.bind_result({"i": 1})]
        ok, problems = results_share_run_context(results, ctx_x)
        assert ok is False and problems

    def test_c6_coherent_run_still_passes(self) -> None:
        ctx = _run_context(run_id="run-coherent")
        results = [ctx.bind_result({"i": i}) for i in range(3)]
        ok, problems = results_share_run_context(results, ctx)
        assert ok is True and problems == []
        # RunContext self-consistency: stored digest == recomputed complete digest.
        assert ctx.context_digest == context_digest_of(ctx.manifest)


# --- F5 — lifecycle provenance / retroactive binding bypass --------------------


def _f5_item(kind: str, sample: str) -> dict:
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
    return {
        "kind": kind,
        "sample": sample,
        "outfile": f"{sample}.md",
        "job": {"title": sample},
        "focus": [],
        "role": sample,
        "input_type": "x",
    }


def _f5_plan() -> list[dict]:
    return [_f5_item("cross", "A"), _f5_item("random", "R")]


def _f5_synthetic_audit(*_args: object, **kwargs: object) -> dict:
    sample = str(kwargs.get("sample_name") or "X")
    return {
        "sample": sample,
        "role": str(kwargs.get("role_label") or sample),
        "input_type": str(kwargs.get("input_type") or "x"),
        "question_count": 1,
        "answer_count": 1,
        "study_module_count": 1,
        "coverage_score": 1.0,
        "source_ladder_present": False,
        "export_ready": True,
        "pack_markdown": f"# {sample}\n",
        "missing_answer_count": 0,
        "missing_study_module_count": 0,
        "hard_max_violation_count": 0,
        "fake_url_hits": 0,
        "generic_phrase_hits": 0,
        "silly_question_hits": 0,
        "empty_section_count": 0,
        "duplicate_study_module_count": 0,
        "internal_label_leak_count": 0,
        "unsupported_personal_claim_count": 0,
        "unsupported_numeric_claim_count": 0,
        "cross_domain_contamination_hits": 0,
        "surface_quality_defect_count": 0,
        "thin_input_specificity_violation_count": 0,
        "structure_incomplete_count": 0,
        "substantive_depth_failure_count": 0,
    }


def _f5_no_authoritative_artifacts(tmp_path: Path) -> None:
    assert not (tmp_path / "run_manifest.json").exists()
    assert not (tmp_path / "sample_final_quality_findings.json").exists()
    assert not (tmp_path / "metrics.json").exists()


def test_f5_t1_retroactive_bind_result_bypass_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    raw = [
        {
            "kind": it["kind"],
            "outfile": None,
            "row": {"sample": it["case"]["sample"]},
            "pack_markdown": "# raw\n",
        }
        for it in plan
    ]
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-bypass", work_plan_digest=gen.compute_work_plan_digest(plan))
    retro = [ctx.bind_result(r) for r in raw]
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write(retro, ctx, expected_items=plan)
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_t2_forged_plain_dict_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-forged", work_plan_digest=gen.compute_work_plan_digest(plan))
    forged = {
        "kind": "cross",
        "outfile": None,
        "row": {"sample": "A"},
        "pack_markdown": "# forged\n",
        "run_id": ctx.run_id,
        "run_context_digest": ctx.context_digest,
    }
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([forged], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_t3_legitimate_generation_accepted(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-good", work_plan_digest=gen.compute_work_plan_digest(plan))
    results = [gen.generate_work_item(item, ctx) for item in plan]
    gen.assemble_and_write(results, ctx, expected_items=plan)
    assert (tmp_path / "run_manifest.json").exists()
    assert (tmp_path / "sample_final_quality_findings.json").exists()
    assert (tmp_path / "metrics.json").exists()


def test_f5_t4_old_context_result_rejected_under_new_context(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx_old = RunContext.create(REPO_ROOT, run_id="run-f5-old", work_plan_digest=gen.compute_work_plan_digest(plan))
    results = [gen.generate_work_item(item, ctx_old) for item in plan]
    ctx_new = RunContext.create(REPO_ROOT, run_id="run-f5-new", work_plan_digest=gen.compute_work_plan_digest(plan))
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write(results, ctx_new, expected_items=plan)
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_t5_reconstructed_context_rejected_for_generation() -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    live = RunContext.create(REPO_ROOT, run_id="run-f5-live")
    reconstructed = RunContext.from_manifest(live.manifest)
    with pytest.raises(SystemExit, match="generation_context_not_live"):
        gen.generate_work_item(_f5_plan()[0], reconstructed)


def test_f5_t6_mixed_legitimate_and_forged_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-mix", work_plan_digest=gen.compute_work_plan_digest(plan))
    genuine = gen.generate_work_item(plan[0], ctx)
    forged = {
        "kind": "random",
        "outfile": None,
        "row": {"sample": "R"},
        "pack_markdown": "# forged\n",
        "run_id": ctx.run_id,
        "run_context_digest": ctx.context_digest,
    }
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([genuine, forged], ctx, expected_items=plan)
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_t7_reconstructed_context_cannot_impersonate_live() -> None:
    live = RunContext.create(REPO_ROOT, run_id="run-f5-impersonate")
    reconstructed = RunContext.from_manifest(live.manifest)
    assert reconstructed.context_digest == live.context_digest
    assert live.has_live_generation_capability
    assert not reconstructed.has_live_generation_capability
    assert not hasattr(live, "generation_capability")


def test_f5_t8_capability_not_serialized(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-serial", work_plan_digest=gen.compute_work_plan_digest(plan))
    results = [gen.generate_work_item(item, ctx) for item in plan]
    gen.assemble_and_write(results, ctx, expected_items=plan)
    assert "_generation_capability" not in ctx.manifest_json
    assert not hasattr(gen, "_MINT_REGISTRY")
    assert not hasattr(gen, "_register_minted_result")
    for name in ("run_manifest.json", "metrics.json", "sample_cross_sector_regression.md"):
        text = (tmp_path / name).read_text(encoding="utf-8")
        assert "_generation_capability" not in text
        assert "_MintedProvenance" not in text


# --- F5 Correction 1 — caller-forgeable authority closure ---------------------


def test_f5_c1_public_accessor_forgery_regression(tmp_path: Path, monkeypatch) -> None:
    """No ordinary API exposes capability; manual wrap cannot publish."""
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    raw = [
        {
            "kind": it["kind"],
            "outfile": None,
            "row": {"sample": it["case"]["sample"]},
            "pack_markdown": "# raw\n",
        }
        for it in plan
    ]
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-c1", work_plan_digest=gen.compute_work_plan_digest(plan))
    assert not hasattr(ctx, "generation_capability")
    forged = gen._GeneratedWorkResult(
        payload={
            "kind": "cross",
            "outfile": None,
            "row": {"sample": "A"},
            "pack_markdown": "# forged\n",
            "run_id": ctx.run_id,
            "run_context_digest": ctx.context_digest,
        },
        work_item_identity="cross::A",
        run_id=ctx.run_id,
        context_digest=ctx.context_digest,
    )
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([forged], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_c2_manual_generated_work_result_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-c2", work_plan_digest=gen.compute_work_plan_digest(plan))
    item = plan[0]
    sample = item["case"]["sample"]
    forged = gen._GeneratedWorkResult(
        payload={
            "kind": "cross",
            "outfile": None,
            "row": {"sample": sample},
            "pack_markdown": "# forged\n",
            "run_id": ctx.run_id,
            "run_context_digest": ctx.context_digest,
        },
        work_item_identity=gen.work_item_identity(item),
        run_id=ctx.run_id,
        context_digest=ctx.context_digest,
    )
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([forged], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_c3_runcontext_capability_constructor_injection_blocked() -> None:
    with pytest.raises(TypeError):
        RunContext(
            manifest_json="{}",
            context_digest="abc",
            _generation_capability=object(),
        )


def test_f5_c4_reconstructed_context_remains_non_live() -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    live = RunContext.create(REPO_ROOT, run_id="run-f5-c4")
    reconstructed = RunContext.from_manifest(live.manifest)
    with pytest.raises(SystemExit, match="generation_context_not_live"):
        gen.generate_work_item(_f5_plan()[0], reconstructed)


def test_f5_c5_legitimate_lifecycle_accepted(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-c5", work_plan_digest=gen.compute_work_plan_digest(plan))
    results = [gen.generate_work_item(item, ctx) for item in plan]
    gen.assemble_and_write(results, ctx, expected_items=plan)
    assert (tmp_path / "run_manifest.json").exists()


def test_f5_c6_foreign_context_exact_object_rejection(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx_old = RunContext.create(REPO_ROOT, run_id="run-f5-c6-old", work_plan_digest=gen.compute_work_plan_digest(plan))
    results = [gen.generate_work_item(item, ctx_old) for item in plan]
    ctx_new = RunContext.create(REPO_ROOT, run_id="run-f5-c6-new", work_plan_digest=gen.compute_work_plan_digest(plan))
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write(results, ctx_new, expected_items=plan)
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_c7_manual_correct_class_mixed_with_genuine_rejected(
    tmp_path: Path, monkeypatch
) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-c7", work_plan_digest=gen.compute_work_plan_digest(plan))
    genuine = gen.generate_work_item(plan[0], ctx)
    forged = gen._GeneratedWorkResult(
        payload={
            "kind": "random",
            "outfile": None,
            "row": {"sample": "R"},
            "pack_markdown": "# forged\n",
            "run_id": ctx.run_id,
            "run_context_digest": ctx.context_digest,
        },
        work_item_identity="random::R",
        run_id=ctx.run_id,
        context_digest=ctx.context_digest,
    )
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([genuine, forged], ctx, expected_items=plan)
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_c8_late_context_bind_result_bypass_remains_rejected(
    tmp_path: Path, monkeypatch
) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    raw = [
        {
            "kind": it["kind"],
            "outfile": None,
            "row": {"sample": it["case"]["sample"]},
            "pack_markdown": "# raw\n",
        }
        for it in plan
    ]
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-c8", work_plan_digest=gen.compute_work_plan_digest(plan))
    retro = [ctx.bind_result(r) for r in raw]
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write(retro, ctx, expected_items=plan)
    _f5_no_authoritative_artifacts(tmp_path)


# --- F5 Correction 2 — closure-private weak registry --------------------------


def test_f5_d1_posthoc_registration_bypass_closed(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    assert not hasattr(gen, "_register_minted_result")
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-d1", work_plan_digest=gen.compute_work_plan_digest(plan))
    forged = gen._GeneratedWorkResult(
        payload={
            "kind": "cross",
            "outfile": None,
            "row": {"sample": "A"},
            "pack_markdown": "# forged\n",
            "run_id": ctx.run_id,
            "run_context_digest": ctx.context_digest,
        },
        work_item_identity="cross::A",
        run_id=ctx.run_id,
        context_digest=ctx.context_digest,
    )
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([forged], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_d2_no_module_global_mint_registry() -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    assert not hasattr(gen, "_MINT_REGISTRY")
    assert not hasattr(gen, "_register_minted_result")
    assert not hasattr(gen, "mint_registry")
    assert not hasattr(gen, "register_minted_result")


def test_f5_d3_manual_correct_class_result_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-d3", work_plan_digest=gen.compute_work_plan_digest(plan))
    item = plan[0]
    forged = gen._GeneratedWorkResult(
        payload={
            "kind": "cross",
            "outfile": None,
            "row": {"sample": item["case"]["sample"]},
            "pack_markdown": "# forged\n",
            "run_id": ctx.run_id,
            "run_context_digest": ctx.context_digest,
        },
        work_item_identity=gen.work_item_identity(item),
        run_id=ctx.run_id,
        context_digest=ctx.context_digest,
    )
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([forged], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_d4_legitimate_generation_accepted(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-d4", work_plan_digest=gen.compute_work_plan_digest(plan))
    results = [gen.generate_work_item(item, ctx) for item in plan]
    gen.assemble_and_write(results, ctx, expected_items=plan)
    assert (tmp_path / "run_manifest.json").exists()


def test_f5_d5_foreign_context_rejected_by_exact_object_identity(
    tmp_path: Path, monkeypatch
) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx_old = RunContext.create(REPO_ROOT, run_id="run-f5-d5-old", work_plan_digest=gen.compute_work_plan_digest(plan))
    results = [gen.generate_work_item(item, ctx_old) for item in plan]
    ctx_new = RunContext.create(REPO_ROOT, run_id="run-f5-d5-new", work_plan_digest=gen.compute_work_plan_digest(plan))
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write(results, ctx_new, expected_items=plan)
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_d6_payload_identical_different_result_object_rejected(
    tmp_path: Path, monkeypatch
) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-d6", work_plan_digest=gen.compute_work_plan_digest(plan))
    genuine = gen.generate_work_item(plan[0], ctx)
    twin = gen._GeneratedWorkResult(
        payload=dict(genuine._payload),
        work_item_identity=genuine.work_item_identity,
        run_id=genuine.bound_run_id,
        context_digest=genuine.bound_context_digest,
    )
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([twin], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_d7_weak_registry_does_not_retain_dead_result(monkeypatch) -> None:
    import gc
    import weakref

    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-d7", work_plan_digest=gen.compute_work_plan_digest(plan))
    result = gen.generate_work_item(plan[0], ctx)
    result_ref = weakref.ref(result)
    del result
    gc.collect()
    assert result_ref() is None


def test_f5_d8_provenance_does_not_retain_dead_context(monkeypatch) -> None:
    import gc
    import weakref

    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-d8", work_plan_digest=gen.compute_work_plan_digest(plan))
    result = gen.generate_work_item(plan[0], ctx)
    ctx_ref = weakref.ref(ctx)
    del ctx
    gc.collect()
    assert ctx_ref() is None
    assert result is not None


def test_f5_d9_public_work_identity_mutation_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-d9", work_plan_digest=gen.compute_work_plan_digest(plan))
    result = gen.generate_work_item(plan[0], ctx)
    result._payload["row"]["sample"] = "MUTATED"
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([result], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_d10_bind_result_bypass_remains_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    raw = [
        {
            "kind": it["kind"],
            "outfile": None,
            "row": {"sample": it["case"]["sample"]},
            "pack_markdown": "# raw\n",
        }
        for it in plan
    ]
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-d10", work_plan_digest=gen.compute_work_plan_digest(plan))
    retro = [ctx.bind_result(r) for r in raw]
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write(retro, ctx, expected_items=plan)
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_weakkey_dictionary_compatible_with_generated_work_result() -> None:
    import weakref

    import scripts.generate_iteration_004e_f_samples as gen

    registry: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
    obj = gen._GeneratedWorkResult(
        payload={"kind": "cross", "outfile": None, "row": {"sample": "A"}, "pack_markdown": "#"},
        work_item_identity="cross::A",
        run_id="run-x",
        context_digest="abc",
    )
    registry[obj] = "ok"
    assert registry.get(obj) == "ok"


# --- F5 Correction 3 — complete-payload digest binding ------------------------


def test_f5_e1_live_payload_substitution_bypass_rejected(
    tmp_path: Path, monkeypatch
) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    item = plan[0]
    sample = item["case"]["sample"]
    old_precontext_payload = {
        "kind": item["kind"],
        "outfile": None,
        "row": {"sample": sample},
        "pack_markdown": "# OLD PRE-CONTEXT WORK\n",
    }
    ctx = RunContext.create(
        REPO_ROOT,
        run_id="run-f5-e1",
        work_plan_digest=gen.compute_work_plan_digest(plan),
    )
    result = gen.generate_work_item(item, ctx)
    assert result["pack_markdown"] == f"# {sample}\n"
    result._payload.clear()
    result._payload.update(
        {
            **old_precontext_payload,
            "run_id": ctx.run_id,
            "run_context_digest": ctx.context_digest,
        }
    )
    assert result["pack_markdown"] == "# OLD PRE-CONTEXT WORK\n"
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([result], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)
    assert not (tmp_path / "sample_cross_sector_regression.md").exists()


def test_f5_e2_pack_markdown_mutation_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-e2", work_plan_digest=gen.compute_work_plan_digest(plan))
    result = gen.generate_work_item(plan[0], ctx)
    result._payload["pack_markdown"] = "# mutated\n"
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([result], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_e3_nested_row_mutation_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-e3", work_plan_digest=gen.compute_work_plan_digest(plan))
    result = gen.generate_work_item(plan[0], ctx)
    result._payload["row"]["question_count"] = 999
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([result], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_e4_payload_identity_preserving_replacement_rejected(
    tmp_path: Path, monkeypatch
) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    item = plan[0]
    sample = item["case"]["sample"]
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-e4", work_plan_digest=gen.compute_work_plan_digest(plan))
    result = gen.generate_work_item(item, ctx)
    result._payload.clear()
    result._payload.update(
        {
            "kind": item["kind"],
            "outfile": None,
            "row": {"sample": sample, "question_count": 0},
            "pack_markdown": "# different generated body\n",
            "run_id": ctx.run_id,
            "run_context_digest": ctx.context_digest,
        }
    )
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([result], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_e5_legitimate_unchanged_result_accepted(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-e5", work_plan_digest=gen.compute_work_plan_digest(plan))
    results = [gen.generate_work_item(item, ctx) for item in plan]
    gen.assemble_and_write(results, ctx, expected_items=plan)
    assert (tmp_path / "run_manifest.json").exists()


def test_f5_e6_complete_digest_is_order_independent() -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    first = {
        "kind": "cross",
        "outfile": None,
        "row": {"sample": "A", "question_count": 1},
        "pack_markdown": "# A\n",
        "run_id": "run-x",
        "run_context_digest": "abc",
    }
    second = {
        "run_context_digest": "abc",
        "run_id": "run-x",
        "pack_markdown": "# A\n",
        "row": {"question_count": 1, "sample": "A"},
        "outfile": None,
        "kind": "cross",
    }
    assert gen._complete_result_payload_digest(first) == gen._complete_result_payload_digest(
        second
    )


def test_f5_e7_extra_payload_field_mutation_rejected(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-e7", work_plan_digest=gen.compute_work_plan_digest(plan))
    result = gen.generate_work_item(plan[0], ctx)
    result._payload["future_publishable_field"] = "injected"
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([result], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_e8_payload_digest_not_serialized_as_authority(
    tmp_path: Path, monkeypatch
) -> None:
    import json

    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-e8", work_plan_digest=gen.compute_work_plan_digest(plan))
    results = [gen.generate_work_item(item, ctx) for item in plan]
    minted_digest = gen._complete_result_payload_digest(results[0])
    gen.assemble_and_write(results, ctx, expected_items=plan)
    for name in (
        "run_manifest.json",
        "metrics.json",
        "sample_final_quality_findings.json",
        "sample_cross_sector_regression.md",
    ):
        text = (tmp_path / name).read_text(encoding="utf-8")
        assert "payload_digest" not in text
        assert "_MintedProvenance" not in text
        assert minted_digest not in text
    findings = json.loads((tmp_path / "sample_final_quality_findings.json").read_text())
    assert "payload_digest" not in json.dumps(findings)


def test_f5_e9_posthoc_helper_bypass_remains_closed(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    assert not hasattr(gen, "_register_minted_result")
    assert not hasattr(gen, "_MINT_REGISTRY")
    plan = _f5_plan()
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-e9", work_plan_digest=gen.compute_work_plan_digest(plan))
    forged = gen._GeneratedWorkResult(
        payload={
            "kind": "cross",
            "outfile": None,
            "row": {"sample": "A"},
            "pack_markdown": "# forged\n",
            "run_id": ctx.run_id,
            "run_context_digest": ctx.context_digest,
        },
        work_item_identity="cross::A",
        run_id=ctx.run_id,
        context_digest=ctx.context_digest,
    )
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write([forged], ctx, expected_items=plan[:1])
    _f5_no_authoritative_artifacts(tmp_path)


def test_f5_e10_bind_result_bypass_remains_closed(tmp_path: Path, monkeypatch) -> None:
    import scripts.generate_iteration_004e_f_samples as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "audit_generated_pack", _f5_synthetic_audit)
    plan = _f5_plan()
    raw = [
        {
            "kind": it["kind"],
            "outfile": None,
            "row": {"sample": it["case"]["sample"]},
            "pack_markdown": "# raw\n",
        }
        for it in plan
    ]
    ctx = RunContext.create(REPO_ROOT, run_id="run-f5-e10", work_plan_digest=gen.compute_work_plan_digest(plan))
    retro = [ctx.bind_result(r) for r in raw]
    with pytest.raises(SystemExit, match="generation_lifecycle_provenance_invalid"):
        gen.assemble_and_write(retro, ctx, expected_items=plan)
    _f5_no_authoritative_artifacts(tmp_path)
