"""Unit tests for the generation-run manifest (004E-E2.3C Slice 1).

These tests reproduce the confirmed artifact-lineage false-green class:
artifacts generated under one code/audit state being consumed as if they
represent the current state. All validation logic is exercised with injected
values (no hardcoded current SHA), per the slice test-design rule.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.agents.job_search.quality.run_manifest import (
    REASON_AUDIT_SCHEMA_CHANGED,
    REASON_DIRTY_WORKTREE_CHANGED,
    REASON_GIT_HEAD_CHANGED,
    REASON_MISSING_MANIFEST,
    STATUS_CURRENT,
    STATUS_LEGACY_UNVERIFIED,
    STATUS_STALE,
    _evidence_only_direct_parent,
    build_generation_run_manifest,
    classify_artifact_evidence,
    compute_audit_schema_version,
    compute_dirty_worktree_fingerprint,
    current_run_context,
    extract_manifest_from_markdown,
    fingerprint_from_inputs,
    is_valid_release_evidence,
    read_git_head,
    render_manifest_markdown_comment,
    runs_are_coherent,
    validate_artifact_run,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
ARTIFACT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004e_f_final_regression"

OLD_KEYS = ("missing_answer_count", "generic_phrase_hits")
NEW_KEYS = OLD_KEYS + ("generic_template_saturation_failure_count",)


def _manifest(**overrides) -> dict:
    base = {
        "manifest_version": 1,
        "run_id": "run-test-0001",
        "generated_at": "2026-07-07T00:00:00Z",
        "git_head": "a" * 40,
        "dirty_worktree_fingerprint": "f" * 16,
        "audit_schema_version": compute_audit_schema_version(NEW_KEYS),
        "metrics_schema_version": "2",
        "findings_schema_version": "2",
    }
    base.update(overrides)
    return base


def _context(**overrides) -> dict:
    ctx = {
        "git_head": "a" * 40,
        "dirty_worktree_fingerprint": "f" * 16,
        "audit_schema_version": compute_audit_schema_version(NEW_KEYS),
        "metrics_schema_version": "2",
        "findings_schema_version": "2",
    }
    ctx.update(overrides)
    return ctx


# --- Test 1 — missing manifest -------------------------------------------------

def test_missing_manifest_is_legacy_unverified_not_release_evidence() -> None:
    for legacy in (None, {}, {"data": []}, [1, 2, 3]):
        result = classify_artifact_evidence(
            legacy if isinstance(legacy, dict) else None, _context()
        )
        assert result["status"] == STATUS_LEGACY_UNVERIFIED, legacy
        assert REASON_MISSING_MANIFEST in result["reasons"]
        assert is_valid_release_evidence(result) is False


# --- Test 2 + Test 7 — audit schema drift, all_clean cannot bypass -------------

def test_audit_schema_drift_invalidates_artifact_even_if_all_clean_true() -> None:
    """Reproduces the confirmed real defect: stored all_clean=true generated
    before newer canonical failure keys existed must NOT count as current."""
    stale_manifest = _manifest(audit_schema_version=compute_audit_schema_version(OLD_KEYS))
    context = _context()  # current schema derived from NEW_KEYS

    result = classify_artifact_evidence(stale_manifest, context)
    assert result["status"] == STATUS_STALE
    assert REASON_AUDIT_SCHEMA_CHANGED in result["reasons"]

    # Negative control: a payload claiming all_clean=true changes nothing.
    payload = {"manifest": stale_manifest, "all_clean": True, "failing_samples": []}
    result2 = classify_artifact_evidence(payload.get("manifest"), context)
    assert is_valid_release_evidence(result2) is False


# --- Test 3 — dirty worktree drift ---------------------------------------------

def test_dirty_worktree_drift_with_same_head_is_stale() -> None:
    manifest = _manifest(dirty_worktree_fingerprint="1" * 16)
    context = _context(dirty_worktree_fingerprint="2" * 16)
    result = classify_artifact_evidence(manifest, context)
    assert result["status"] == STATUS_STALE
    assert REASON_DIRTY_WORKTREE_CHANGED in result["reasons"]
    assert REASON_GIT_HEAD_CHANGED not in result["reasons"]
    assert is_valid_release_evidence(result) is False


def test_git_head_change_is_stale() -> None:
    result = classify_artifact_evidence(
        _manifest(git_head="b" * 40), _context(git_head="c" * 40)
    )
    assert result["status"] == STATUS_STALE
    assert REASON_GIT_HEAD_CHANGED in result["reasons"]


# --- Test 4 — mixed run IDs ------------------------------------------------------

def test_mixed_run_ids_across_artifacts_are_detected() -> None:
    metrics_manifest = _manifest(run_id="run-A")
    findings_manifest = _manifest(run_id="run-B")
    coherent, problems = runs_are_coherent([metrics_manifest, findings_manifest])
    assert coherent is False
    assert any("run_id" in p for p in problems)


def test_missing_manifest_breaks_run_coherence() -> None:
    coherent, problems = runs_are_coherent([_manifest(), None])
    assert coherent is False
    assert any("missing" in p for p in problems)


# --- Test 5 — summary binding ----------------------------------------------------

def test_summary_manifest_comment_roundtrip_and_mismatch() -> None:
    manifest = _manifest(run_id="run-summary-1")
    comment = render_manifest_markdown_comment(manifest)
    md = comment + "\n# Some Summary\n\ncontent\n"
    extracted = extract_manifest_from_markdown(md)
    assert extracted == manifest

    other = _manifest(run_id="run-summary-2")
    coherent, problems = runs_are_coherent([manifest, other])
    assert coherent is False and problems

    assert extract_manifest_from_markdown("# no manifest here\n") is None


# --- Test 6 — coherent run --------------------------------------------------------

def test_coherent_current_run_passes_all_checks() -> None:
    manifest = _manifest()
    context = _context()
    result = classify_artifact_evidence(manifest, context)
    assert result["status"] == STATUS_CURRENT
    assert result["reasons"] == []
    assert is_valid_release_evidence(result) is True
    coherent, problems = runs_are_coherent([manifest, dict(manifest), dict(manifest)])
    assert coherent is True and problems == []


# --- Determinism / sensitivity of derived versions --------------------------------

def test_audit_schema_version_is_deterministic_and_key_sensitive() -> None:
    v1 = compute_audit_schema_version(OLD_KEYS)
    v2 = compute_audit_schema_version(OLD_KEYS)
    v3 = compute_audit_schema_version(NEW_KEYS)
    assert v1 == v2
    assert v1 != v3
    # Order matters: the canonical tuple order is part of the schema identity.
    assert compute_audit_schema_version(tuple(reversed(OLD_KEYS))) != v1


def test_fingerprint_inputs_are_order_stable() -> None:
    status_a = [" M backend/a.py", "?? backend/b.py"]
    status_b = ["?? backend/b.py", " M backend/a.py"]
    blobs_a = [("backend/a.py", "deadbeef"), ("backend/b.py", "cafef00d")]
    blobs_b = list(reversed(blobs_a))
    fp1 = fingerprint_from_inputs(status_a, blobs_a)
    fp2 = fingerprint_from_inputs(status_b, blobs_b)
    assert fp1 == fp2
    # Sensitive to tracked-modification content changes.
    assert fingerprint_from_inputs(status_a, [("backend/a.py", "00"), blobs_a[1]]) != fp1
    # Sensitive to untracked content changes.
    assert fingerprint_from_inputs(status_a, [blobs_a[0], ("backend/b.py", "00")]) != fp1
    # Sensitive to path-state changes (e.g. a deletion) even with same blobs.
    assert fingerprint_from_inputs([" D backend/x.py", *status_a], blobs_a) != fp1


def test_real_repo_fingerprint_is_deterministic() -> None:
    fp1 = compute_dirty_worktree_fingerprint(REPO_ROOT)
    fp2 = compute_dirty_worktree_fingerprint(REPO_ROOT)
    assert fp1 == fp2
    assert len(fp1) == 16
    int(fp1, 16)  # hex


def test_build_manifest_reads_real_git_state() -> None:
    manifest = build_generation_run_manifest(REPO_ROOT)
    assert len(manifest["git_head"]) == 40
    int(manifest["git_head"], 16)
    assert manifest["run_id"].startswith("run-")
    assert manifest["generated_at"].endswith("Z")
    assert manifest["manifest_version"] == 1
    assert len(manifest["dirty_worktree_fingerprint"]) == 16
    assert manifest["metrics_schema_version"]
    assert manifest["findings_schema_version"]
    # JSON-serializable by construction.
    json.dumps(manifest)


# --- Checkpoint integrity — evidence-only direct-parent compatibility ----------


def _git_env() -> dict[str, str]:
    return {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}


def _git_commit(repo: Path, message: str, env: dict[str, str]) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@test", "-c", "user.name=t", "commit", "-m", message],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )


def _init_checkpoint_repo(tmp_path: Path) -> tuple[Path, dict[str, str], str, str]:
    repo = tmp_path / "checkpoint_repo"
    repo.mkdir()
    env = _git_env()
    (repo / "backend" / "app").mkdir(parents=True)
    (repo / "project_review" / "samples" / "iteration_test").mkdir(parents=True)
    (repo / "project_review" / "00_iteration_log.md").write_text("log\n", encoding="utf-8")
    (repo / "backend" / "app" / "module.py").write_text("source v1\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "h1 source", env)
    base_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()
    return repo, env, read_git_head(repo), base_branch


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp1_exact_current_head_still_accepted() -> None:
    manifest = _manifest()
    context = _context()
    result = classify_artifact_evidence(manifest, context)
    assert result["status"] == STATUS_CURRENT
    assert result["reasons"] == []


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp2_direct_evidence_only_child_accepts_source_parent(tmp_path: Path) -> None:
    repo, env, h1, _base = _init_checkpoint_repo(tmp_path)
    manifest = build_generation_run_manifest(repo)
    assert manifest["git_head"] == h1
    sample = repo / "project_review" / "samples" / "iteration_test" / "sample.md"
    sample.write_text("# evidence\n", encoding="utf-8")
    subprocess.run(["git", "add", sample], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "h2 evidence-only", env)
    h2 = read_git_head(repo)
    assert h2 != h1
    assert _evidence_only_direct_parent(repo) == h1
    context = current_run_context(repo)
    assert h1 in context["compatible_source_git_heads"]
    result = classify_artifact_evidence(manifest, context)
    assert result["status"] == STATUS_CURRENT
    assert REASON_GIT_HEAD_CHANGED not in result["reasons"]


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp3_backend_code_child_rejected(tmp_path: Path) -> None:
    repo, env, h1, _base = _init_checkpoint_repo(tmp_path)
    manifest = build_generation_run_manifest(repo)
    (repo / "backend" / "app" / "module.py").write_text("source v2\n", encoding="utf-8")
    subprocess.run(["git", "add", "backend/app/module.py"], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "h2 backend change", env)
    assert _evidence_only_direct_parent(repo) is None
    result = classify_artifact_evidence(manifest, current_run_context(repo))
    assert result["status"] == STATUS_STALE
    assert REASON_GIT_HEAD_CHANGED in result["reasons"]


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp4_mixed_evidence_and_code_child_rejected(tmp_path: Path) -> None:
    repo, env, h1, _base = _init_checkpoint_repo(tmp_path)
    manifest = build_generation_run_manifest(repo)
    sample = repo / "project_review" / "samples" / "iteration_test" / "sample.md"
    sample.write_text("# evidence\n", encoding="utf-8")
    (repo / "backend" / "app" / "module.py").write_text("source v2\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "h2 mixed", env)
    assert _evidence_only_direct_parent(repo) is None
    result = classify_artifact_evidence(manifest, current_run_context(repo))
    assert result["status"] == STATUS_STALE
    assert REASON_GIT_HEAD_CHANGED in result["reasons"]


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp5_unrelated_project_review_document_rejected(tmp_path: Path) -> None:
    repo, env, h1, _base = _init_checkpoint_repo(tmp_path)
    manifest = build_generation_run_manifest(repo)
    (repo / "project_review" / "00_iteration_log.md").write_text("updated log\n", encoding="utf-8")
    subprocess.run(["git", "add", "project_review/00_iteration_log.md"], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "h2 iteration log", env)
    assert _evidence_only_direct_parent(repo) is None
    result = classify_artifact_evidence(manifest, current_run_context(repo))
    assert result["status"] == STATUS_STALE
    assert REASON_GIT_HEAD_CHANGED in result["reasons"]


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp6_merge_commit_rejected(tmp_path: Path) -> None:
    repo, env, h1, base = _init_checkpoint_repo(tmp_path)
    manifest = build_generation_run_manifest(repo)
    samples_dir = repo / "project_review" / "samples" / "iteration_test"
    subprocess.run(["git", "checkout", "-b", "branch-a"], cwd=repo, check=True, capture_output=True, env=env)
    samples_dir.mkdir(parents=True, exist_ok=True)
    (samples_dir / "a.md").write_text("# a\n", encoding="utf-8")
    subprocess.run(["git", "add", "project_review/samples/iteration_test/a.md"], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "branch-a evidence", env)
    subprocess.run(["git", "checkout", base], cwd=repo, check=True, capture_output=True, env=env)
    subprocess.run(["git", "checkout", "-b", "branch-b"], cwd=repo, check=True, capture_output=True, env=env)
    samples_dir.mkdir(parents=True, exist_ok=True)
    (samples_dir / "b.md").write_text("# b\n", encoding="utf-8")
    subprocess.run(["git", "add", "project_review/samples/iteration_test/b.md"], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "branch-b evidence", env)
    subprocess.run(["git", "checkout", base], cwd=repo, check=True, capture_output=True, env=env)
    subprocess.run(
        ["git", "merge", "--no-ff", "branch-a", "-m", "merge-a"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        ["git", "merge", "--no-ff", "branch-b", "-m", "merge-b"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    parents = subprocess.run(
        ["git", "log", "-1", "--format=%P", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip().split()
    assert len(parents) > 1
    assert _evidence_only_direct_parent(repo) is None
    result = classify_artifact_evidence(manifest, current_run_context(repo))
    assert result["status"] == STATUS_STALE
    assert REASON_GIT_HEAD_CHANGED in result["reasons"]


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp7_empty_child_diff_not_accepted(tmp_path: Path) -> None:
    repo, env, _h1, _base = _init_checkpoint_repo(tmp_path)
    subprocess.run(
        ["git", "-c", "user.email=t@test", "-c", "user.name=t", "commit", "--allow-empty", "-m", "empty"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    assert _evidence_only_direct_parent(repo) is None


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp8_dirty_fingerprint_still_enforced_with_compatible_head(tmp_path: Path) -> None:
    repo, env, h1, _base = _init_checkpoint_repo(tmp_path)
    manifest = build_generation_run_manifest(repo)
    sample = repo / "project_review" / "samples" / "iteration_test" / "sample.md"
    sample.write_text("# evidence\n", encoding="utf-8")
    subprocess.run(["git", "add", sample], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "h2 evidence-only", env)
    assert _evidence_only_direct_parent(repo) == h1
    (repo / "backend" / "app" / "module.py").write_text("uncommitted drift\n", encoding="utf-8")
    context = current_run_context(repo)
    assert h1 in context["compatible_source_git_heads"]
    result = classify_artifact_evidence(manifest, context)
    assert result["status"] == STATUS_STALE
    assert REASON_DIRTY_WORKTREE_CHANGED in result["reasons"]
    assert REASON_GIT_HEAD_CHANGED not in result["reasons"]


def test_cp9_existing_git_head_drift_test_remains_green() -> None:
    result = classify_artifact_evidence(
        _manifest(git_head="b" * 40), _context(git_head="c" * 40)
    )
    assert result["status"] == STATUS_STALE
    assert REASON_GIT_HEAD_CHANGED in result["reasons"]


def test_cp10_current_stored_run_remains_current_before_any_commit() -> None:
    context = current_run_context(REPO_ROOT)
    result = validate_artifact_run(ARTIFACT_DIR, context)
    assert result["status"] == STATUS_CURRENT, result
    assert result["reasons"] == []


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp11_live_source_to_evidence_rename_bypass_rejected(tmp_path: Path) -> None:
    repo, env, h1, _base = _init_checkpoint_repo(tmp_path)
    manifest = build_generation_run_manifest(repo)
    dest = repo / "project_review" / "samples" / "iteration_test" / "module.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "mv", "backend/app/module.py", str(dest.relative_to(repo))],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    _git_commit(repo, "h2 source-to-evidence mv", env)
    subprocess.run(
        ["git", "config", "diff.renames", "true"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    default_paths = subprocess.run(
        ["git", "diff", "--name-only", h1, "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip().splitlines()
    no_rename_paths = subprocess.run(
        ["git", "diff", "--no-renames", "--name-only", h1, "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip().splitlines()
    assert len(default_paths) == 1
    assert default_paths[0].endswith("project_review/samples/iteration_test/module.py")
    assert len(no_rename_paths) == 2
    assert _evidence_only_direct_parent(repo) is None
    result = classify_artifact_evidence(manifest, current_run_context(repo))
    assert result["status"] == STATUS_STALE
    assert REASON_GIT_HEAD_CHANGED in result["reasons"]


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp12_evidence_to_source_rename_rejected(tmp_path: Path) -> None:
    repo, env, h1, _base = _init_checkpoint_repo(tmp_path)
    manifest = build_generation_run_manifest(repo)
    sample = repo / "project_review" / "samples" / "iteration_test" / "sample.md"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text("# sample\n", encoding="utf-8")
    subprocess.run(["git", "add", sample], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "h1 sample", env)
    manifest = build_generation_run_manifest(repo)
    dest = repo / "backend" / "app" / "sample.md"
    subprocess.run(
        ["git", "mv", str(sample.relative_to(repo)), str(dest.relative_to(repo))],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    _git_commit(repo, "h2 evidence-to-source mv", env)
    assert _evidence_only_direct_parent(repo) is None
    result = classify_artifact_evidence(manifest, current_run_context(repo))
    assert result["status"] == STATUS_STALE
    assert REASON_GIT_HEAD_CHANGED in result["reasons"]


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp13_evidence_to_evidence_rename_accepted(tmp_path: Path) -> None:
    repo, env, h1, _base = _init_checkpoint_repo(tmp_path)
    src_dir = repo / "project_review" / "samples" / "a"
    src_dir.mkdir(parents=True)
    (src_dir / "sample.md").write_text("# sample\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True, env=env)
    _git_commit(repo, "h1 evidence", env)
    h1_evidence = read_git_head(repo)
    manifest = build_generation_run_manifest(repo)
    dest_dir = repo / "project_review" / "samples" / "b"
    dest_dir.mkdir(parents=True)
    subprocess.run(
        ["git", "mv", "project_review/samples/a/sample.md", "project_review/samples/b/sample.md"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    _git_commit(repo, "h2 evidence-to-evidence mv", env)
    assert _evidence_only_direct_parent(repo) == h1_evidence
    result = classify_artifact_evidence(manifest, current_run_context(repo))
    assert result["status"] == STATUS_CURRENT
    assert REASON_GIT_HEAD_CHANGED not in result["reasons"]


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment",
)
def test_cp14_rename_config_cannot_change_classification(tmp_path: Path) -> None:
    repo, env, h1, _base = _init_checkpoint_repo(tmp_path)
    manifest = build_generation_run_manifest(repo)
    dest = repo / "project_review" / "samples" / "iteration_test" / "module.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "mv", "backend/app/module.py", str(dest.relative_to(repo))],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    _git_commit(repo, "h2 source-to-evidence mv", env)

    def _classification_with_renames(value: str) -> dict:
        subprocess.run(
            ["git", "config", "diff.renames", value],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )
        assert _evidence_only_direct_parent(repo) is None
        return classify_artifact_evidence(manifest, current_run_context(repo))

    result_true = _classification_with_renames("true")
    result_false = _classification_with_renames("false")
    assert result_true["status"] == STATUS_STALE
    assert result_false["status"] == STATUS_STALE
    assert REASON_GIT_HEAD_CHANGED in result_true["reasons"]
    assert REASON_GIT_HEAD_CHANGED in result_false["reasons"]
