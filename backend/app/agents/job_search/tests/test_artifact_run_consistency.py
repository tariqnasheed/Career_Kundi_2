"""Stored-artifact run consistency — the authoritative machine oracle
(004E-E2.3C Slice 1 + Prompt 2 artifact-integrity expansion).

Replaces the hand-written ``jobsearch_report.md`` prose as machine truth:
release evidence is the manifest-bound machine-readable artifact set under
``project_review/samples/iteration_004e_f_final_regression``.

Pre-slice these tests FAIL against the stored artifacts, reproducing the
confirmed lineage defect: ``metrics.json`` is a bare list, findings claim
``all_clean=true``, and neither carries any binding to the code/audit state
that produced them. After manifest wiring + one regeneration they pass, and
they fail again whenever the stored evidence goes stale (HEAD change, dirty
worktree change, or canonical audit-key change).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from app.agents.job_search.quality.final_regression_audit import (
    CANONICAL_FAILURE_METRIC_KEYS,
)
from app.agents.job_search.quality.run_manifest import (
    REASON_ARTIFACT_HASH_MISMATCH,
    REASON_GENERATION_CONTEXT_CHANGED,
    REASON_INVALID_ARTIFACT_INDEX,
    REASON_MIXED_RUN,
    ROOT_INDEX_FILENAME,
    STATUS_ARTIFACT_HASH_MISMATCH,
    STATUS_CURRENT,
    STATUS_GENERATION_CONTEXT_CHANGED,
    STATUS_MIXED_RUN,
    STATUS_STALE,
    classify_artifact_evidence,
    compute_audit_schema_version,
    compute_dirty_worktree_fingerprint,
    current_run_context,
    extract_manifest_from_markdown,
    is_valid_release_evidence,
    render_manifest_markdown_comment,
    runs_are_coherent,
    validate_artifact_run,
    write_run_index,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
ARTIFACT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004e_f_final_regression"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"
FINDINGS_PATH = ARTIFACT_DIR / "sample_final_quality_findings.json"
SUMMARY_PATH = ARTIFACT_DIR / "iteration_004e_f_summary.md"

# Authoritative artifact set — mirrors ``written`` in
# ``backend/scripts/generate_iteration_004e_f_samples.py::assemble_and_write``.
# ``run_manifest.json`` is written LAST but deliberately excluded from indexing
# (root index must not hash itself).
AUTHORITATIVE_ARTIFACTS: frozenset[str] = frozenset(
    {
        "metrics.json",
        "sample_final_quality_findings.json",
        "iteration_004e_f_summary.md",
        "sample_cross_sector_regression.md",
        "sample_deterministic_random_regression.md",
        "sample_document_export_regression.md",
        "sample_part_time_odd_job_input_regression.md",
        "sample_rich_source_ladder_regression.md",
        "sample_title_only_regression.md",
    }
)

SAMPLE_MARKDOWN_FILES = tuple(
    sorted(p for p in AUTHORITATIVE_ARTIFACTS if p.endswith(".md") and p != "iteration_004e_f_summary.md")
)

# Representative artifacts receive all three byte-mutation variants; every
# other indexed artifact receives one append mutation (smallest sufficient matrix).
REPRESENTATIVE_ARTIFACTS: frozenset[str] = frozenset(
    {
        "metrics.json",
        "sample_final_quality_findings.json",
        "sample_cross_sector_regression.md",
        "iteration_004e_f_summary.md",
    }
)
BYTE_MUTATION_VARIANTS = ("append", "replace", "truncate")

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@lru_cache(maxsize=1)
def _context() -> dict:
    """Current code/audit context, computed once per test session (the dirty
    worktree fingerprint costs one git status/diff walk)."""
    return current_run_context(REPO_ROOT)


def _load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_of(payload: object) -> dict | None:
    if isinstance(payload, dict):
        manifest = payload.get("manifest")
        if isinstance(manifest, dict):
            return manifest
    return None


def _load_root_index(artifact_dir: Path) -> dict:
    path = artifact_dir / ROOT_INDEX_FILENAME
    assert path.exists(), f"missing root index at {path}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), "root index must be a JSON object"
    return payload


def _context_from_manifest(manifest: dict) -> dict:
    return {
        "git_head": manifest["git_head"],
        "dirty_worktree_fingerprint": manifest["dirty_worktree_fingerprint"],
        "audit_schema_version": manifest["audit_schema_version"],
        "metrics_schema_version": manifest["metrics_schema_version"],
        "findings_schema_version": manifest["findings_schema_version"],
        "document_library_fingerprint": manifest.get("document_library_fingerprint", ""),
    }


def _write_root_index(
    run_dir: Path,
    manifest: dict,
    *,
    artifacts: object,
) -> None:
    (run_dir / ROOT_INDEX_FILENAME).write_text(
        json.dumps({"manifest": manifest, "artifacts": artifacts}, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _invalid_index_result(result: dict) -> None:
    assert result["status"] == STATUS_STALE
    assert REASON_INVALID_ARTIFACT_INDEX in result["reasons"]
    assert result["status"] != STATUS_CURRENT
    assert not is_valid_release_evidence(result)


def _copy_coherent_run(tmp_path: Path) -> Path:
    dest = tmp_path / "coherent_run"
    shutil.copytree(ARTIFACT_DIR, dest)
    return dest


def _mutate_bytes(data: bytes, variant: str) -> bytes:
    if variant == "append":
        return data + b"\n"
    if variant == "replace":
        for index, byte in enumerate(data):
            if 32 <= byte <= 126:
                mutated = bytearray(data)
                mutated[index] = byte ^ 1
                return bytes(mutated)
        return data + b" "
    if variant == "truncate":
        return data[:-1] if data else data
    raise ValueError(f"unknown mutation variant: {variant!r}")


def _mutate_file(path: Path, variant: str) -> None:
    path.write_bytes(_mutate_bytes(path.read_bytes(), variant))


def _tamper_matrix() -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for rel in sorted(AUTHORITATIVE_ARTIFACTS):
        variants = BYTE_MUTATION_VARIANTS if rel in REPRESENTATIVE_ARTIFACTS else ("append",)
        for variant in variants:
            cases.append((rel, variant))
    return cases


# --- Slice 1 baseline (stored artifact currency) --------------------------------


def test_stored_metrics_and_findings_carry_run_manifests() -> None:
    """Test 1 (real artifact): legacy bare payloads are not release evidence."""
    metrics_manifest = _manifest_of(_load_json(METRICS_PATH))
    findings_manifest = _manifest_of(_load_json(FINDINGS_PATH))
    context = _context()

    for name, manifest in (("metrics.json", metrics_manifest), ("findings", findings_manifest)):
        result = classify_artifact_evidence(manifest, context)
        assert is_valid_release_evidence(result), (
            f"{name} is not valid current release evidence: status={result['status']} "
            f"reasons={result['reasons']}. Regenerate iteration_004e_f samples via "
            f"backend/scripts/generate_iteration_004e_f_samples.py after code/audit changes."
        )


def test_stored_artifacts_share_one_generation_run() -> None:
    """Tests 4+5+6 (real artifacts): metrics, findings, and summary must be
    demonstrably from the same run."""
    metrics_manifest = _manifest_of(_load_json(METRICS_PATH))
    findings_manifest = _manifest_of(_load_json(FINDINGS_PATH))
    summary_manifest = extract_manifest_from_markdown(
        SUMMARY_PATH.read_text(encoding="utf-8")
    )
    coherent, problems = runs_are_coherent(
        [metrics_manifest, findings_manifest, summary_manifest]
    )
    assert coherent, f"mixed/missing run binding across stored artifacts: {problems}"


def test_stored_sample_markdown_files_reference_the_same_run() -> None:
    metrics_manifest = _manifest_of(_load_json(METRICS_PATH))
    assert metrics_manifest, "metrics.json has no manifest; regenerate samples"
    manifests = [metrics_manifest]
    for name in SAMPLE_MARKDOWN_FILES:
        path = ARTIFACT_DIR / name
        if not path.exists():
            continue
        manifest = extract_manifest_from_markdown(path.read_text(encoding="utf-8"))
        assert manifest is not None, f"{name} carries no run binding"
        manifests.append(manifest)
    coherent, problems = runs_are_coherent(manifests)
    assert coherent, f"sample markdown files belong to a different run: {problems}"


def test_stored_all_clean_cannot_bypass_audit_schema_currency() -> None:
    """Test 7 (real artifact): a stored ``all_clean=true`` produced under an
    older canonical failure-key schema must never be accepted as current."""
    payload = _load_json(FINDINGS_PATH)
    assert isinstance(payload, dict)
    manifest = _manifest_of(payload)
    result = classify_artifact_evidence(manifest, _context())

    if payload.get("all_clean") is True:
        assert result["status"] == STATUS_CURRENT and is_valid_release_evidence(result), (
            "stored findings claim all_clean=true but are NOT bound to the current "
            f"code/audit state (status={result['status']}, reasons={result['reasons']}); "
            "stale clean evidence must not masquerade as current truth."
        )
    # Whether clean or failing, the manifest must reflect today's canonical keys.
    assert manifest is not None, "findings carry no manifest"
    assert manifest.get("audit_schema_version") == compute_audit_schema_version(
        CANONICAL_FAILURE_METRIC_KEYS
    ), "findings were generated under a different canonical failure-key schema"


def test_stored_metrics_rows_contain_all_canonical_failure_keys() -> None:
    """Rows missing newer counters were exactly how stale all_clean survived:
    the aggregate could not see failures for keys that did not exist yet."""
    payload = _load_json(METRICS_PATH)
    rows = payload.get("data") if isinstance(payload, dict) else payload
    assert isinstance(rows, list) and rows, "metrics.json has no data rows"
    for row in rows:
        missing = [k for k in CANONICAL_FAILURE_METRIC_KEYS if k not in row]
        assert not missing, (
            f"sample '{row.get('sample')}' lacks canonical audit counters {missing}; "
            "metrics were generated before the current audit schema."
        )


def test_legacy_unmanifested_artifact_fixture_is_rejected(tmp_path: Path) -> None:
    """Deterministic negative control that does not depend on stored files."""
    legacy = tmp_path / "legacy_metrics.json"
    legacy.write_text(json.dumps([{"sample": "X", "all_clean": True}]), encoding="utf-8")
    payload = json.loads(legacy.read_text(encoding="utf-8"))
    manifest = _manifest_of(payload)
    result = classify_artifact_evidence(manifest, _context())
    assert not is_valid_release_evidence(result)
    assert result["status"] != STATUS_CURRENT


def test_audit_schema_version_defaults_to_live_canonical_keys() -> None:
    assert compute_audit_schema_version() == compute_audit_schema_version(
        CANONICAL_FAILURE_METRIC_KEYS
    )


# --- Prompt 2 Task A — stored root-index integration ----------------------------


def test_stored_run_manifest_json_exists() -> None:
    assert (ARTIFACT_DIR / ROOT_INDEX_FILENAME).is_file()


def test_stored_root_index_is_structurally_valid() -> None:
    index = _load_root_index(ARTIFACT_DIR)
    manifest = index.get("manifest")
    artifacts = index.get("artifacts")
    assert isinstance(manifest, dict) and manifest.get("run_id"), "root manifest missing run_id"
    assert isinstance(artifacts, dict) and artifacts, "root index has no artifacts section"
    assert index.get("generation_context_changed") in (None, []), (
        "stored run must not be marked generation_context_changed"
    )


def test_stored_root_index_paths_are_normalized_relative() -> None:
    index = _load_root_index(ARTIFACT_DIR)
    for rel in index["artifacts"]:
        assert not rel.startswith("/"), f"indexed path must be relative: {rel!r}"
        assert "\\" not in rel, f"indexed path must use forward slashes: {rel!r}"
        assert rel == rel.lstrip("/")


def test_stored_root_index_sha256_values_have_expected_form() -> None:
    index = _load_root_index(ARTIFACT_DIR)
    for rel, meta in index["artifacts"].items():
        sha = (meta or {}).get("sha256")
        assert isinstance(sha, str) and SHA256_RE.fullmatch(sha), (
            f"{rel}: sha256 has unexpected form {sha!r}"
        )


def test_stored_root_index_every_indexed_file_exists() -> None:
    index = _load_root_index(ARTIFACT_DIR)
    for rel in index["artifacts"]:
        assert (ARTIFACT_DIR / rel).is_file(), f"indexed artifact missing on disk: {rel}"


def test_stored_run_validates_as_current_via_root_index(tmp_path: Path) -> None:
    """Prove the stored byte set + root index are internally coherent.

    Uses the manifest's own generation context (not live ``_context()``) so the
    test does not depend on worktree drift since artifact capture — that
    currency binding is covered separately by the Slice-1 stored-currency tests.
    """
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    result = validate_artifact_run(run_dir, _context_from_manifest(index["manifest"]))
    assert result["status"] == STATUS_CURRENT, result
    assert result["reasons"] == []


# --- Prompt 2 Task B — exact authoritative artifact coverage ------------------


def test_indexed_authoritative_set_equals_generator_written_set() -> None:
    """Indexed authoritative set must equal the generator's ``written`` list.

    ``run_manifest.json`` is intentionally non-authoritative: it is the root
    index itself and is excluded from its own ``artifacts`` map to prevent
    circular self-hashing.
    """
    index = _load_root_index(ARTIFACT_DIR)
    indexed = frozenset(index["artifacts"].keys())
    assert indexed == AUTHORITATIVE_ARTIFACTS
    assert ROOT_INDEX_FILENAME not in indexed


def test_stored_directory_has_no_unindexed_authoritative_surprises() -> None:
    """Every non-root file in the artifact directory must be indexed."""
    on_disk = {
        p.name
        for p in ARTIFACT_DIR.iterdir()
        if p.is_file() and p.name != ROOT_INDEX_FILENAME
    }
    assert on_disk == set(AUTHORITATIVE_ARTIFACTS), (
        f"unindexed or unexpected files: {on_disk ^ AUTHORITATIVE_ARTIFACTS}"
    )


# --- Prompt 2 Task J — root index self-exclusion ------------------------------


def test_root_index_never_indexes_itself_on_stored_run() -> None:
    index = _load_root_index(ARTIFACT_DIR)
    assert ROOT_INDEX_FILENAME not in index.get("artifacts", {})


def test_root_index_self_exclusion_enforced_on_synthetic_fixture(tmp_path: Path) -> None:
    """Circularity prevention is executable, not merely implementation-assumed."""
    manifest = _load_root_index(ARTIFACT_DIR)["manifest"]
    (tmp_path / "metrics.json").write_text(
        json.dumps({"manifest": manifest, "data": []}), encoding="utf-8"
    )
    write_run_index(
        tmp_path,
        manifest,
        ["metrics.json", ROOT_INDEX_FILENAME],  # deliberate self-reference attempt
    )
    index = _load_root_index(tmp_path)
    assert ROOT_INDEX_FILENAME not in index["artifacts"]
    assert "metrics.json" in index["artifacts"]


# --- Prompt 2 Tasks C+D — per-artifact tamper permutations --------------------


@pytest.mark.parametrize("rel_path,variant", _tamper_matrix())
def test_indexed_artifact_byte_tamper_detected(
    tmp_path: Path, rel_path: str, variant: str
) -> None:
    run_dir = _copy_coherent_run(tmp_path)
    _mutate_file(run_dir / rel_path, variant)
    index = _load_root_index(run_dir)
    result = validate_artifact_run(run_dir, _context_from_manifest(index["manifest"]))
    assert result["status"] == STATUS_ARTIFACT_HASH_MISMATCH, (
        f"{rel_path}/{variant}: expected hash mismatch, got {result}"
    )
    assert REASON_ARTIFACT_HASH_MISMATCH in result["reasons"]
    assert rel_path in result.get("artifacts", [])


# --- Prompt 2 Task E — same-run file swap -------------------------------------


def test_same_run_markdown_swap_fails_path_to_bytes_binding(tmp_path: Path) -> None:
    run_dir = _copy_coherent_run(tmp_path)
    path_a = run_dir / "sample_cross_sector_regression.md"
    path_b = run_dir / "sample_title_only_regression.md"
    bytes_a = path_a.read_bytes()
    bytes_b = path_b.read_bytes()
    path_a.write_bytes(bytes_b)
    path_b.write_bytes(bytes_a)
    result = validate_artifact_run(run_dir, _context_from_manifest(_load_root_index(run_dir)["manifest"]))
    assert result["status"] == STATUS_ARTIFACT_HASH_MISMATCH
    swapped = set(result.get("artifacts", []))
    assert {"sample_cross_sector_regression.md", "sample_title_only_regression.md"} <= swapped


# --- Prompt 2 Task F — copied manifest comment --------------------------------


def test_copied_manifest_comment_with_foreign_body_fails(tmp_path: Path) -> None:
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    manifest = index["manifest"]
    target = run_dir / "sample_cross_sector_regression.md"
    target.write_text(
        render_manifest_markdown_comment(manifest) + "\nforeign body not from this run\n",
        encoding="utf-8",
    )
    result = validate_artifact_run(run_dir, _context_from_manifest(manifest))
    assert result["status"] == STATUS_ARTIFACT_HASH_MISMATCH
    assert "sample_cross_sector_regression.md" in result.get("artifacts", [])


# --- Prompt 2 Task G — mixed-run branch reachability --------------------------


def test_mixed_run_branch_reached_with_valid_byte_hashes(tmp_path: Path) -> None:
    """Root manifest from run A, one embedded artifact from run B — hashes
    recomputed so byte-integrity checking does not mask the mixed-run branch."""
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    manifest_a = index["manifest"]
    manifest_b = dict(manifest_a)
    manifest_b["run_id"] = str(manifest_a["run_id"]) + "-foreign"

    foreign_md = run_dir / "sample_cross_sector_regression.md"
    foreign_md.write_text(
        render_manifest_markdown_comment(manifest_b) + "\n# pack from foreign run\n",
        encoding="utf-8",
    )
    write_run_index(run_dir, manifest_a, AUTHORITATIVE_ARTIFACTS)

    result = validate_artifact_run(run_dir, _context_from_manifest(manifest_a))
    assert result["status"] == STATUS_MIXED_RUN, (
        f"expected mixed_run branch, got {result['status']!r} — "
        "hash check may have masked mixed-run detection"
    )
    assert REASON_MIXED_RUN in result["reasons"]
    assert result.get("problems")


# --- Prompt 2 Task H — generation_context_changed integration -----------------


def test_generation_context_changed_prioritized_on_stored_run_copy(tmp_path: Path) -> None:
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    index["generation_context_changed"] = [REASON_GENERATION_CONTEXT_CHANGED]
    (run_dir / ROOT_INDEX_FILENAME).write_text(
        json.dumps(index, indent=2, sort_keys=True), encoding="utf-8"
    )
    result = validate_artifact_run(run_dir, _context())
    assert result["status"] == STATUS_GENERATION_CONTEXT_CHANGED
    assert result["status"] not in (STATUS_CURRENT, STATUS_STALE)


# --- Prompt 2 Task I — failure-priority semantics -----------------------------


def test_failure_priority_context_changed_beats_artifact_mismatch(tmp_path: Path) -> None:
    """Case 1: context changed + artifact mismatch ⇒ generation_context_changed."""
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    index["generation_context_changed"] = ["git_head_changed"]
    (run_dir / ROOT_INDEX_FILENAME).write_text(
        json.dumps(index, indent=2, sort_keys=True), encoding="utf-8"
    )
    _mutate_file(run_dir / "metrics.json", "append")
    result = validate_artifact_run(run_dir, _context_from_manifest(index["manifest"]))
    assert result["status"] == STATUS_GENERATION_CONTEXT_CHANGED


def test_failure_priority_hash_mismatch_beats_mixed_embedded_run(tmp_path: Path) -> None:
    """Case 2: no context change + byte mismatch + mixed embedded ⇒ hash mismatch."""
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    manifest_a = index["manifest"]
    manifest_b = dict(manifest_a)
    manifest_b["run_id"] = str(manifest_a["run_id"]) + "-foreign"

    foreign_md = run_dir / "sample_document_export_regression.md"
    foreign_md.write_text(
        render_manifest_markdown_comment(manifest_b) + "\n# foreign\n",
        encoding="utf-8",
    )
    _mutate_file(run_dir / "metrics.json", "append")
    result = validate_artifact_run(run_dir, _context_from_manifest(manifest_a))
    assert result["status"] == STATUS_ARTIFACT_HASH_MISMATCH


def test_failure_priority_mixed_run_when_hashes_valid(tmp_path: Path) -> None:
    """Case 3: hashes valid + mixed embedded run ⇒ mixed_run."""
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    manifest_a = index["manifest"]
    manifest_b = dict(manifest_a)
    manifest_b["run_id"] = str(manifest_a["run_id"]) + "-foreign"

    foreign_md = run_dir / "sample_part_time_odd_job_input_regression.md"
    foreign_md.write_text(
        render_manifest_markdown_comment(manifest_b) + "\n# foreign\n",
        encoding="utf-8",
    )
    write_run_index(run_dir, manifest_a, AUTHORITATIVE_ARTIFACTS)
    result = validate_artifact_run(run_dir, _context_from_manifest(manifest_a))
    assert result["status"] == STATUS_MIXED_RUN


# --- F4 — reject empty / invalid authoritative artifact index -----------------


def test_f4_t1_empty_artifacts_map_rejected(tmp_path: Path) -> None:
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    _write_root_index(run_dir, index["manifest"], artifacts={})
    result = validate_artifact_run(run_dir, _context_from_manifest(index["manifest"]))
    _invalid_index_result(result)


def test_f4_t2_missing_artifacts_field_rejected(tmp_path: Path) -> None:
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    (run_dir / ROOT_INDEX_FILENAME).write_text(
        json.dumps({"manifest": index["manifest"]}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    result = validate_artifact_run(run_dir, _context_from_manifest(index["manifest"]))
    _invalid_index_result(result)


@pytest.mark.parametrize(
    "artifacts",
    [
        [],
        "not-a-map",
        None,
    ],
)
def test_f4_t3_artifacts_wrong_type_rejected(
    tmp_path: Path, artifacts: object
) -> None:
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    _write_root_index(run_dir, index["manifest"], artifacts=artifacts)
    result = validate_artifact_run(run_dir, _context_from_manifest(index["manifest"]))
    _invalid_index_result(result)


def test_f4_t4_non_empty_valid_artifact_map_still_passes(tmp_path: Path) -> None:
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    result = validate_artifact_run(run_dir, _context_from_manifest(index["manifest"]))
    assert result["status"] == STATUS_CURRENT
    assert is_valid_release_evidence(result)


def test_f4_t5_tamper_detection_unchanged(tmp_path: Path) -> None:
    run_dir = _copy_coherent_run(tmp_path)
    _mutate_file(run_dir / "metrics.json", "append")
    index = _load_root_index(run_dir)
    result = validate_artifact_run(run_dir, _context_from_manifest(index["manifest"]))
    assert result["status"] == STATUS_ARTIFACT_HASH_MISMATCH
    assert REASON_ARTIFACT_HASH_MISMATCH in result["reasons"]


def test_f4_t6_current_manifest_cannot_mask_invalid_index(tmp_path: Path) -> None:
    """Negative control: context-matching manifest + empty artifacts ≠ current."""
    run_dir = _copy_coherent_run(tmp_path)
    index = _load_root_index(run_dir)
    manifest = index["manifest"]
    _write_root_index(run_dir, manifest, artifacts={})
    result = validate_artifact_run(run_dir, _context_from_manifest(manifest))
    _invalid_index_result(result)


def test_f4_stored_run_has_non_empty_artifact_map() -> None:
    index = _load_root_index(ARTIFACT_DIR)
    artifacts = index.get("artifacts")
    assert isinstance(artifacts, dict) and artifacts, "stored run must index authoritative artifacts"


def test_f4_stored_run_validates_as_current() -> None:
    index = _load_root_index(ARTIFACT_DIR)
    result = validate_artifact_run(ARTIFACT_DIR, _context())
    assert result["status"] == STATUS_CURRENT, result


# --- Prompt 2 Task K (optional) — disposable git repo index sensitivity -------


@pytest.mark.skipif(
    subprocess.run(
        ["git", "init"],
        capture_output=True,
        cwd="/tmp",
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    ).returncode
    != 0,
    reason="git init unavailable in this environment (sandbox or missing git)",
)
def test_disposable_git_repo_staged_index_affects_fingerprint(tmp_path: Path) -> None:
    """Lightweight integration proof that staged/index state affects fingerprint.

    Runs only inside pytest ``tmp_path``; never stages anything in CareerKundi.
    Skipped when ``git init`` is unavailable (e.g. restricted sandbox).
    """
    repo = tmp_path / "mini_repo"
    repo.mkdir()
    tracked = repo / "src.py"
    tracked.write_text("baseline\n", encoding="utf-8")
    env = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, env=env)
    subprocess.run(
        ["git", "-c", "user.email=t@test", "-c", "user.name=t", "add", "src.py"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@test", "-c", "user.name=t", "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )

    tracked.write_text("working-tree-edit\n", encoding="utf-8")
    fp_modified_unstaged = compute_dirty_worktree_fingerprint(repo)

    subprocess.run(
        ["git", "-c", "user.email=t@test", "-c", "user.name=t", "add", "src.py"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    fp_modified_staged = compute_dirty_worktree_fingerprint(repo)

    assert fp_modified_unstaged != fp_modified_staged
