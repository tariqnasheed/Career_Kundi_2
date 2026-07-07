"""Generation-run manifest: artifact lineage + staleness detection
(004E-E2.3C Slice 1).

Every regression-artifact generation run builds ONE manifest and stamps it
into every output (metrics JSON, findings JSON, summary markdown, sample
markdown packs). Consumers use :func:`classify_artifact_evidence` and
:func:`runs_are_coherent` so that:

* artifacts with no manifest are ``legacy_unverified`` — never current
  release evidence;
* artifacts from a different Git HEAD, a different dirty-worktree state, or
  a different canonical audit-key schema are ``stale`` — even when they
  claim ``all_clean = true``;
* metrics/findings/summary/sample files from different runs are detected as
  a mixed run.

Design constraints honoured here:
* read-only with respect to Git — no ``add``/``stash``/``reset``; the
  fingerprint uses only ``status``/``diff``/``hash-object`` (no ``-w``);
* one small authoritative module — no competing manifest builders;
* deterministic — no wall-clock or ordering dependence in any fingerprint.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

MANIFEST_VERSION = 1
MANIFEST_KEY = "manifest"

# Root artifact index written LAST for every generation run. It binds the exact
# SHA-256 of every authoritative artifact's final bytes, so a post-generation
# edit (even one that keeps run_id/HEAD/fingerprint intact) is detectable.
#
# TRUST BOUNDARY (documented honestly): the artifact index detects stale,
# accidental, swapped, or uncoordinated post-generation modifications of any
# indexed artifact. It is NOT a cryptographic authenticity proof: an actor who
# can rewrite BOTH an artifact and this root index (recomputing the SHA-256)
# can produce an internally-consistent forged run. Integrity here means
# tamper-evidence for uncoordinated edits, not attestation against a coordinated
# rewrite. Cryptographic signing/attestation is intentionally out of scope.
ROOT_INDEX_FILENAME = "run_manifest.json"

# Explicit shape versions for the two machine-readable artifacts. Version 1 is
# the historical bare shape (metrics = bare list; findings = bare totals dict
# with no manifest). Bump when the serialized shape changes incompatibly.
METRICS_SCHEMA_VERSION = "2"
FINDINGS_SCHEMA_VERSION = "2"

STATUS_CURRENT = "current"
STATUS_STALE = "stale"
STATUS_LEGACY_UNVERIFIED = "legacy_unverified"
# Slice 1.1 statuses (artifact-integrity + lifecycle):
STATUS_MIXED_RUN = "mixed_run"
STATUS_GENERATION_CONTEXT_CHANGED = "generation_context_changed"
STATUS_ARTIFACT_HASH_MISMATCH = "artifact_hash_mismatch"

REASON_MISSING_MANIFEST = "missing_manifest"
REASON_GIT_HEAD_CHANGED = "git_head_changed"
REASON_DIRTY_WORKTREE_CHANGED = "dirty_worktree_changed"
REASON_AUDIT_SCHEMA_CHANGED = "audit_schema_changed"
REASON_METRICS_SCHEMA_CHANGED = "metrics_schema_changed"
REASON_FINDINGS_SCHEMA_CHANGED = "findings_schema_changed"
REASON_ARTIFACT_HASH_MISMATCH = "artifact_hash_mismatch"
REASON_GENERATION_CONTEXT_CHANGED = "generation_context_changed"
REASON_MIXED_RUN = "mixed_run"
REASON_DOCUMENT_LIBRARY_CHANGED = "document_library_changed"
REASON_INVALID_ARTIFACT_INDEX = "invalid_artifact_index"

# Repository-state fields whose change DURING a run is a TOCTOU violation.
_GENERATION_CONTEXT_FIELDS: tuple[tuple[str, str], ...] = (
    ("git_head", REASON_GIT_HEAD_CHANGED),
    ("dirty_worktree_fingerprint", REASON_DIRTY_WORKTREE_CHANGED),
    ("audit_schema_version", REASON_AUDIT_SCHEMA_CHANGED),
    ("document_library_fingerprint", REASON_DOCUMENT_LIBRARY_CHANGED),
)

# --- Document-library input-state scope (Finding F1) --------------------------
#
# The 004E-F generation call graph reads documents/indexes/ (role matching) and
# the matched interview-pack's json/md content (saved questions/study). PDFs and
# the exports/ and source_materials/ sibling dirs are NOT consumed at generation
# time (verified by runtime tracing), so they are deliberately excluded — both
# to avoid over-hashing the personal document tree and to keep possibly-sensitive
# material out of scope. Only these subdirs and file types participate.
_DOC_LIBRARY_INCLUDED_SUBDIRS: tuple[str, ...] = ("indexes", "interview_packs")
_DOC_LIBRARY_CONSUMED_SUFFIXES: tuple[str, ...] = (".json", ".md")


class GenerationContextChanged(RuntimeError):
    """Raised when repository/audit context changes between run start and end."""


class MixedRunContext(RuntimeError):
    """Raised when work-item results are not all bound to one run context."""

# --- Dirty-worktree fingerprint scope -----------------------------------------
#
# INCLUDED: every tracked modification (staged or unstaged, content-level via
# `git diff HEAD`) and every untracked file's content blob hash — i.e. the
# code/config state that determines generation semantics.
#
# EXCLUDED (documented limitation): generated/narrative outputs that the run
# itself writes or that do not affect generation semantics. Without excluding
# the artifact output directory, writing the artifacts would invalidate their
# own manifest (self-referential staleness).
_FINGERPRINT_EXCLUDE_PREFIXES: tuple[str, ...] = (
    "project_review/",   # generated regression artifacts (self-exclusion)
    "documents/",        # generated document exports / source material store
    "jobsearch_report.md",  # narrative-only report (Decision C)
    "report.md",
    "audit.md",
)
_FINGERPRINT_EXCLUDE_BASENAMES: frozenset[str] = frozenset(
    {".DS_Store", ".env", "__pycache__", ".pytest_cache", ".venv", "node_modules", "dist"}
)
# Narrow evidence-only commit scope for checkpoint-integrity compatibility.
# Only paths under these prefixes may change in a direct child commit whose
# parent HEAD is accepted as a compatible source for stored artifact manifests.
_EVIDENCE_ONLY_COMMIT_PREFIXES: tuple[str, ...] = (
    "project_review/samples/",
)
# Untracked files larger than this are fingerprinted by (path, size) only, so
# the computation stays bounded on pathological worktrees.
_MAX_UNTRACKED_CONTENT_BYTES = 2 * 1024 * 1024

_MANIFEST_COMMENT_RE = re.compile(
    r"<!--\s*careerkundi-run-manifest\s+(\{.*?\})\s*-->", re.S
)


def _git(repo_root: Path | str, *args: str) -> str:
    """Run a read-only git command and return stdout as text."""
    out = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout


def read_git_head(repo_root: Path | str) -> str:
    return _git(repo_root, "rev-parse", "HEAD").strip()


def _path_is_evidence_only_commit_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return any(normalized.startswith(prefix) for prefix in _EVIDENCE_ONLY_COMMIT_PREFIXES)


def _evidence_only_direct_parent(repo_root: Path | str) -> str | None:
    """Return the direct parent HEAD when current HEAD is an evidence-only child.

    Accepts only a single-parent commit whose entire changed-path set is non-empty
    and confined to :data:`_EVIDENCE_ONLY_COMMIT_PREFIXES`. Merge commits, empty
    diffs, mixed evidence/code commits, and non-evidence project_review paths
    return ``None``.
    """
    repo_root = Path(repo_root)
    try:
        parents_raw = _git(repo_root, "log", "-1", "--format=%P", "HEAD").strip()
    except subprocess.CalledProcessError:
        return None
    if not parents_raw:
        return None
    parents = parents_raw.split()
    if len(parents) != 1:
        return None
    parent = parents[0]
    try:
        changed_raw = _git(
            repo_root,
            "diff",
            "--no-renames",
            "--name-only",
            parent,
            "HEAD",
        )
    except subprocess.CalledProcessError:
        return None
    changed = [line.strip() for line in changed_raw.splitlines() if line.strip()]
    if not changed:
        return None
    if not all(_path_is_evidence_only_commit_path(path) for path in changed):
        return None
    return parent


def _git_head_is_compatible(manifest: dict[str, Any], context: dict[str, Any]) -> bool:
    manifest_head = manifest.get("git_head")
    context_head = context.get("git_head")
    if manifest_head == context_head:
        return True
    compatible = context.get("compatible_source_git_heads")
    if compatible and manifest_head in compatible:
        return True
    return False


def _path_excluded(path: str) -> bool:
    if any(path.startswith(prefix) for prefix in _FINGERPRINT_EXCLUDE_PREFIXES):
        return True
    parts = path.split("/")
    return any(part in _FINGERPRINT_EXCLUDE_BASENAMES for part in parts)


def fingerprint_from_inputs(
    status_lines: Iterable[str],
    content_blobs: Iterable[tuple[str, str]],
    index_lines: Iterable[str] = (),
) -> str:
    """Deterministic, order-stable hash over normalized worktree-state inputs.

    Pure function so staleness logic is unit-testable without a git fixture.

    ``index_lines`` carries the exact staged/index state (``git diff-index
    --cached HEAD`` raw lines, which embed the index blob SHA). This closes the
    gap where two worktrees with identical CONTENT but different STAGED index
    blobs would otherwise fingerprint identically. Omitting it is backward
    compatible: the section is present but empty.
    """
    hasher = hashlib.sha256()
    for line in sorted(str(s) for s in status_lines):
        hasher.update(line.encode("utf-8"))
        hasher.update(b"\n")
    hasher.update(b"--content--\n")
    for path, blob in sorted((str(p), str(b)) for p, b in content_blobs):
        hasher.update(f"{path}\x00{blob}\n".encode("utf-8"))
    hasher.update(b"--index--\n")
    for line in sorted(str(s) for s in index_lines):
        hasher.update(line.encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()[:16]


def _staged_index_lines(repo_root: Path) -> list[str]:
    """Read-only exact staged/index state (no ``git add``).

    ``git diff-index --cached HEAD`` reports index-vs-HEAD with the index blob
    SHA in each raw line, so it captures the precise staged content. Excluded
    paths are filtered with the same policy as the worktree scan. On an
    unborn/detached HEAD it degrades to empty rather than crashing generation.
    """
    try:
        raw = _git(repo_root, "diff-index", "--cached", "--no-renames", "HEAD")
    except subprocess.CalledProcessError:
        return []
    lines: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        # Format: ":<m1> <m2> <sha1> <sha2> <status>\t<path>"
        path = line.split("\t", 1)[1].strip().strip('"') if "\t" in line else ""
        if path and _path_excluded(path):
            continue
        lines.append(line)
    return lines


def compute_dirty_worktree_fingerprint(repo_root: Path | str) -> str:
    """Fingerprint the uncommitted worktree state (same HEAD, different
    uncommitted changes ⇒ different fingerprint).

    Inputs (all read-only, one tree walk + one batched content hash):
    * sorted ``git status --porcelain -uall --no-renames`` lines — captures
      which paths are added/modified/deleted/untracked/staged;
    * ``git hash-object`` (no ``-w``: computes blob SHAs, writes nothing)
      over the worktree CONTENT of every modified/added tracked file and
      every untracked file — captures what changed, not just that it changed.

    Both input sets are filtered through the documented exclusion list above.
    Deleted or unreadable paths contribute a deterministic marker instead of
    content; files above the size bound contribute ``size:<n>`` so the
    computation stays bounded (documented honest compromise).
    """
    repo_root = Path(repo_root)
    status_raw = _git(repo_root, "status", "--porcelain=v1", "-uall", "--no-renames")
    status_lines: list[str] = []
    paths_to_hash: list[str] = []
    for line in status_raw.splitlines():
        if not line.strip():
            continue
        code, path = line[:2], line[3:].strip().strip('"')
        if _path_excluded(path):
            continue
        status_lines.append(line)
        if "D" not in code:  # deletions are captured by the status line itself
            paths_to_hash.append(path)

    content_blobs: list[tuple[str, str]] = []
    small: list[str] = []
    for path in paths_to_hash:
        full = repo_root / path
        try:
            size = full.stat().st_size
        except OSError:
            content_blobs.append((path, "unreadable"))
            continue
        if size > _MAX_UNTRACKED_CONTENT_BYTES:
            content_blobs.append((path, f"size:{size}"))
        else:
            small.append(path)
    if small:
        hashes = _git(repo_root, "hash-object", "--", *small).split()
        content_blobs.extend(zip(small, hashes))

    return fingerprint_from_inputs(
        status_lines, content_blobs, index_lines=_staged_index_lines(repo_root)
    )


def compute_audit_schema_version(keys: Sequence[str] | None = None) -> str:
    """Stable hash of the ordered canonical failure-key schema.

    Defaults to the live ``CANONICAL_FAILURE_METRIC_KEYS`` so the version can
    never be forgotten when keys change — adding/removing/reordering a
    canonical key automatically invalidates previously generated artifacts.
    """
    if keys is None:
        from app.agents.job_search.quality.final_regression_audit import (
            CANONICAL_FAILURE_METRIC_KEYS,
        )

        keys = CANONICAL_FAILURE_METRIC_KEYS
    payload = "\n".join(str(k) for k in keys)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _resolved_documents_root(documents_root: Path | str | None) -> Path | None:
    if documents_root is not None:
        return Path(documents_root)
    try:
        from app.core.config import settings

        return Path(settings.resolved_documents_root)
    except Exception:
        return None


def compute_document_library_fingerprint(documents_root: Path | str | None = None) -> str:
    """Stable digest of the generation-relevant document-library state.

    Binds only what the generation call graph actually consumes: the retrieval
    ``indexes/`` and the ``interview_packs/`` json/md content (saved
    questions/study). PDFs and non-consumed sibling dirs (``exports/``,
    ``source_materials/``) are excluded, so editing an unrelated / private
    document does not invalidate evidence and no over-hashing of the personal
    tree occurs.

    Path-INDEPENDENT: identity is the relevant corpus state — sorted RELATIVE
    paths + exact file bytes — NOT the machine-specific absolute location. An
    identical corpus copied to a different root (e.g. a sandbox vs a Mac
    ``/var/folders/...`` temp) fingerprints identically; only corpus content /
    additions / removals / relative-path renames change it. The effective root
    is used to LOCATE files but is never hashed or stored.

    Privacy: only SHA-256 digests and relative role-pack paths feed the hash;
    no document CONTENTS and no absolute path are ever returned or stored.
    """
    root = _resolved_documents_root(documents_root)
    hasher = hashlib.sha256()
    if not root or not root.exists():
        hasher.update(b"no_library\n")
        return hasher.hexdigest()[:16]

    entries: list[tuple[str, str]] = []
    for sub in _DOC_LIBRARY_INCLUDED_SUBDIRS:
        base = root / sub
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in _DOC_LIBRARY_CONSUMED_SUFFIXES:
                continue
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                digest = "unreadable"
            entries.append((path.relative_to(root).as_posix(), digest))
    hasher.update(b"--library--\n")
    for rel, digest in sorted(entries):
        hasher.update(f"{rel}\x00{digest}\n".encode("utf-8"))
    return hasher.hexdigest()[:16]


def _new_run_id(now: datetime) -> str:
    return f"run-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def build_generation_run_manifest(
    repo_root: Path | str,
    *,
    run_id: str | None = None,
    generated_at: datetime | None = None,
    canonical_keys: Sequence[str] | None = None,
    document_library_fingerprint: str | None = None,
    work_plan_digest: str | None = None,
) -> dict[str, Any]:
    """Build the single manifest for one generation run.

    Call once per run and reuse the returned dict for every artifact — the
    run_id must be identical across all outputs of the run.

    ``work_plan_digest`` binds the expected work-item plan captured at run start
    (F3), so assembly can prove the results cover exactly that plan and cannot be
    reconstructed into a different expected set.
    """
    now = generated_at or datetime.now(timezone.utc)
    return {
        "manifest_version": MANIFEST_VERSION,
        "run_id": run_id or _new_run_id(now),
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": read_git_head(repo_root),
        "dirty_worktree_fingerprint": compute_dirty_worktree_fingerprint(repo_root),
        "audit_schema_version": compute_audit_schema_version(canonical_keys),
        "metrics_schema_version": METRICS_SCHEMA_VERSION,
        "findings_schema_version": FINDINGS_SCHEMA_VERSION,
        "document_library_fingerprint": (
            document_library_fingerprint
            if document_library_fingerprint is not None
            else compute_document_library_fingerprint()
        ),
        "work_plan_digest": work_plan_digest or "",
    }


def current_run_context(
    repo_root: Path | str, canonical_keys: Sequence[str] | None = None
) -> dict[str, Any]:
    """The current code/audit state an artifact manifest is validated against."""
    repo_root = Path(repo_root)
    compatible_source_git_heads: list[str] = []
    parent = _evidence_only_direct_parent(repo_root)
    if parent is not None:
        compatible_source_git_heads.append(parent)
    return {
        "git_head": read_git_head(repo_root),
        "compatible_source_git_heads": compatible_source_git_heads,
        "dirty_worktree_fingerprint": compute_dirty_worktree_fingerprint(repo_root),
        "audit_schema_version": compute_audit_schema_version(canonical_keys),
        "metrics_schema_version": METRICS_SCHEMA_VERSION,
        "findings_schema_version": FINDINGS_SCHEMA_VERSION,
        "document_library_fingerprint": compute_document_library_fingerprint(),
    }


def classify_artifact_evidence(
    manifest: dict[str, Any] | None, context: dict[str, Any]
) -> dict[str, Any]:
    """Classify one artifact manifest against the current context.

    Returns ``{"status": ..., "reasons": [...]}`` where status is one of
    ``current`` / ``stale`` / ``legacy_unverified``. Only ``current`` may be
    treated as release evidence (see :func:`is_valid_release_evidence`).
    ``all_clean = true`` inside an artifact payload has NO influence here —
    that is the negative control for the historical false-green class.
    """
    if not isinstance(manifest, dict) or not manifest.get("run_id"):
        return {"status": STATUS_LEGACY_UNVERIFIED, "reasons": [REASON_MISSING_MANIFEST]}

    reasons: list[str] = []
    if context.get("git_head") is not None and not _git_head_is_compatible(manifest, context):
        reasons.append(REASON_GIT_HEAD_CHANGED)
    checks = (
        ("dirty_worktree_fingerprint", REASON_DIRTY_WORKTREE_CHANGED),
        ("audit_schema_version", REASON_AUDIT_SCHEMA_CHANGED),
        ("metrics_schema_version", REASON_METRICS_SCHEMA_CHANGED),
        ("findings_schema_version", REASON_FINDINGS_SCHEMA_CHANGED),
        ("document_library_fingerprint", REASON_DOCUMENT_LIBRARY_CHANGED),
    )
    for field, reason in checks:
        expected = context.get(field)
        if expected is not None and manifest.get(field) != expected:
            reasons.append(reason)

    return {"status": STATUS_STALE if reasons else STATUS_CURRENT, "reasons": reasons}


def is_valid_release_evidence(classification: dict[str, Any]) -> bool:
    return classification.get("status") == STATUS_CURRENT


def runs_are_coherent(
    manifests: Sequence[dict[str, Any] | None],
) -> tuple[bool, list[str]]:
    """True only when every artifact carries a manifest and all share one run_id."""
    problems: list[str] = []
    run_ids: set[str] = set()
    for index, manifest in enumerate(manifests):
        if not isinstance(manifest, dict) or not manifest.get("run_id"):
            problems.append(f"artifact[{index}]: missing run manifest")
            continue
        run_ids.add(str(manifest["run_id"]))
    if len(run_ids) > 1:
        problems.append(f"run_id mismatch across artifacts: {sorted(run_ids)}")
    return (not problems, problems)


def render_manifest_markdown_comment(manifest: dict[str, Any]) -> str:
    """Hidden, single-line HTML comment binding a markdown artifact to its run.

    Chosen over visible metadata so interview-pack samples carry no
    user-facing noise; markdown renderers do not display HTML comments.
    """
    return f"<!-- careerkundi-run-manifest {json.dumps(manifest, sort_keys=True)} -->"


def extract_manifest_from_markdown(text: str) -> dict[str, Any] | None:
    match = _MANIFEST_COMMENT_RE.search(text or "")
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except (TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


# --- Slice 1.1: immutable run context created BEFORE the first work item -------


def context_digest_of(manifest: dict[str, Any]) -> str:
    """Stable digest of the COMPLETE authoritative manifest.

    Two run contexts are identical only when their complete manifests are
    identical. Deriving the digest from the whole manifest (via deterministic
    canonical JSON) instead of a hand-maintained field list means any future
    authoritative manifest field automatically participates in run identity and
    can never silently escape it. Key insertion order is irrelevant
    (``sort_keys=True``); only the manifest's semantic content matters.
    """
    canonical = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:16]


@dataclass(frozen=True)
class RunContext:
    """Immutable identity of ONE generation run, created before any work item.

    The manifest is stored as a canonical JSON string (the immutable core), so a
    frozen ``RunContext`` cannot have its identity mutated after creation. The
    ``manifest`` property returns a fresh dict each access; the ``context_digest``
    is bound at creation and never recomputed from mutable state.

    Only contexts created via :meth:`create` carry a private in-memory generation
    capability. Reconstructed contexts from :meth:`from_manifest` are read/validation
    only and cannot authorize generation or publication.
    """

    manifest_json: str
    context_digest: str
    repo_root: str = ""
    _generation_capability: object | None = field(
        default=None, init=False, repr=False, compare=False
    )

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any], *, repo_root: str = "") -> "RunContext":
        """Reconstruct a non-generation-authoritative context from a stored manifest."""
        manifest_json = json.dumps(manifest, sort_keys=True)
        return cls(
            manifest_json=manifest_json,
            context_digest=context_digest_of(manifest),
            repo_root=str(repo_root),
        )

    @classmethod
    def create(
        cls,
        repo_root: Path | str,
        *,
        run_id: str | None = None,
        generated_at: datetime | None = None,
        canonical_keys: Sequence[str] | None = None,
        work_plan_digest: str | None = None,
    ) -> "RunContext":
        """Capture the run manifest ONCE, before the first work item is generated."""
        manifest = build_generation_run_manifest(
            repo_root,
            run_id=run_id,
            generated_at=generated_at,
            canonical_keys=canonical_keys,
            work_plan_digest=work_plan_digest,
        )
        manifest_json = json.dumps(manifest, sort_keys=True)
        ctx = cls(
            manifest_json=manifest_json,
            context_digest=context_digest_of(manifest),
            repo_root=str(repo_root),
        )
        object.__setattr__(ctx, "_generation_capability", object())
        return ctx

    @property
    def manifest(self) -> dict[str, Any]:
        return json.loads(self.manifest_json)

    @property
    def run_id(self) -> str:
        return str(self.manifest["run_id"])

    @property
    def has_live_generation_capability(self) -> bool:
        return self._generation_capability is not None

    def require_live_generation_capability(self) -> None:
        """Validate liveness. Does not return the private capability token."""
        if self._generation_capability is None:
            raise SystemExit(
                "generation_context_not_live: RunContext was reconstructed from "
                "manifest and cannot authorize generation."
            )

    def start_context(self) -> dict[str, Any]:
        """The repository/audit context captured at run start."""
        m = self.manifest
        return {
            "git_head": m["git_head"],
            "dirty_worktree_fingerprint": m["dirty_worktree_fingerprint"],
            "audit_schema_version": m["audit_schema_version"],
            "metrics_schema_version": m["metrics_schema_version"],
            "findings_schema_version": m["findings_schema_version"],
            "document_library_fingerprint": m.get("document_library_fingerprint"),
        }

    def bind_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Copy ``run_id`` and ``run_context_digest`` onto a plain dict.

        This is a label-copy helper for low-level coherence tests only. It does
        NOT create lifecycle-provenance results and must never be accepted by
        authoritative publication (``assemble_and_write``).
        """
        out = dict(result)
        out["run_id"] = self.run_id
        out["run_context_digest"] = self.context_digest
        return out


def results_share_run_context(
    results: Sequence[dict[str, Any]], run_context: RunContext
) -> tuple[bool, list[str]]:
    """True only when every result is bound to exactly ``run_context``.

    Rejects a result missing its binding, a result from a different run_id, and
    — critically — a result whose run_id matches but whose context digest was
    computed under a different repository state.
    """
    problems: list[str] = []
    for index, result in enumerate(results):
        run_id = result.get("run_id")
        digest = result.get("run_context_digest")
        if not run_id or not digest:
            problems.append(f"result[{index}]: missing run-context binding")
            continue
        if run_id != run_context.run_id:
            problems.append(
                f"result[{index}]: run_id {run_id!r} != {run_context.run_id!r}"
            )
        if digest != run_context.context_digest:
            problems.append(f"result[{index}]: run-context digest mismatch")
    return (not problems, problems)


def assert_results_share_run_context(
    results: Sequence[dict[str, Any]], run_context: RunContext
) -> None:
    ok, problems = results_share_run_context(results, run_context)
    if not ok:
        raise MixedRunContext("; ".join(problems))


def detect_generation_context_change(
    start_context: dict[str, Any], end_context: dict[str, Any]
) -> list[str]:
    """Reasons the repository/audit context changed between run start and end."""
    reasons: list[str] = []
    for field, reason in _GENERATION_CONTEXT_FIELDS:
        if start_context.get(field) != end_context.get(field):
            reasons.append(reason)
    return reasons


# --- Slice 1.1: artifact-byte integrity root ----------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path | str) -> str:
    return sha256_bytes(Path(path).read_bytes())


def build_artifact_index(
    output_dir: Path | str,
    manifest: dict[str, Any],
    relative_paths: Iterable[str],
    *,
    generation_context_changed: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Root index binding the exact SHA-256 of every authoritative artifact.

    ``relative_paths`` must NOT include the root index file itself (no
    self-hash). Paths are normalized and deterministically ordered.
    """
    output_dir = Path(output_dir)
    artifacts: dict[str, Any] = {}
    for rel in sorted({str(p).replace("\\", "/").lstrip("/") for p in relative_paths}):
        if rel == ROOT_INDEX_FILENAME:
            continue  # circularity guard
        artifacts[rel] = {"sha256": sha256_file(output_dir / rel)}
    index: dict[str, Any] = {"manifest": manifest, "artifacts": artifacts}
    if generation_context_changed:
        index["generation_context_changed"] = list(generation_context_changed)
    return index


def write_run_index(
    output_dir: Path | str,
    manifest: dict[str, Any],
    relative_paths: Iterable[str],
    *,
    generation_context_changed: Sequence[str] | None = None,
) -> Path:
    """Write the authoritative root index LAST (after all other artifacts)."""
    index = build_artifact_index(
        output_dir,
        manifest,
        relative_paths,
        generation_context_changed=generation_context_changed,
    )
    path = Path(output_dir) / ROOT_INDEX_FILENAME
    path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _embedded_manifests(output_dir: Path, relative_paths: Iterable[str]) -> list[dict | None]:
    """Every artifact's own embedded manifest (JSON payload or markdown comment)."""
    out: list[dict | None] = []
    for rel in relative_paths:
        path = Path(output_dir) / rel
        if not path.exists():
            out.append(None)
            continue
        text = path.read_text(encoding="utf-8")
        if rel.endswith(".json"):
            try:
                payload = json.loads(text)
            except ValueError:
                out.append(None)
                continue
            out.append(payload.get("manifest") if isinstance(payload, dict) else None)
        elif rel.endswith(".md"):
            out.append(extract_manifest_from_markdown(text))
    return out


def _invalid_artifact_index_result() -> dict[str, Any]:
    """Structural root-index failure — empty or malformed ``artifacts`` map."""
    return {"status": STATUS_STALE, "reasons": [REASON_INVALID_ARTIFACT_INDEX]}


def validate_artifact_run(
    output_dir: Path | str, context: dict[str, Any]
) -> dict[str, Any]:
    """Authoritative validator for a stored generation run.

    Priority of failure signals (most specific first):
      * ``legacy_unverified`` — no authoritative root index;
      * ``generation_context_changed`` — the run itself recorded a TOCTOU change;
      * ``stale`` / ``invalid_artifact_index`` — root index ``artifacts`` map is
        missing, wrong type, or empty (no authoritative artifacts to verify);
      * ``artifact_hash_mismatch`` — an indexed artifact's bytes changed;
      * ``mixed_run`` — an artifact's embedded manifest belongs to another run;
      * ``stale`` / ``current`` — manifest vs the current code/audit context.
    """
    output_dir = Path(output_dir)
    index_path = output_dir / ROOT_INDEX_FILENAME
    if not index_path.exists():
        return {"status": STATUS_LEGACY_UNVERIFIED, "reasons": [REASON_MISSING_MANIFEST]}
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {"status": STATUS_LEGACY_UNVERIFIED, "reasons": [REASON_MISSING_MANIFEST]}

    manifest = index.get("manifest") if isinstance(index, dict) else None
    if not isinstance(manifest, dict) or not manifest.get("run_id"):
        return {"status": STATUS_LEGACY_UNVERIFIED, "reasons": [REASON_MISSING_MANIFEST]}

    if index.get("generation_context_changed"):
        return {
            "status": STATUS_GENERATION_CONTEXT_CHANGED,
            "reasons": [REASON_GENERATION_CONTEXT_CHANGED],
            "detail": list(index.get("generation_context_changed") or []),
        }

    artifacts = index.get("artifacts") if isinstance(index, dict) else None
    if not isinstance(artifacts, dict) or not artifacts:
        return _invalid_artifact_index_result()

    # Exact artifact-byte integrity (tamper detection).
    mismatches: list[str] = []
    for rel, meta in sorted(artifacts.items()):
        fpath = output_dir / rel
        if not fpath.exists() or sha256_file(fpath) != (meta or {}).get("sha256"):
            mismatches.append(rel)
    if mismatches:
        return {
            "status": STATUS_ARTIFACT_HASH_MISMATCH,
            "reasons": [REASON_ARTIFACT_HASH_MISMATCH],
            "artifacts": mismatches,
        }

    # Cross-artifact run coherence (mixed run detection).
    coherent, problems = runs_are_coherent([manifest, *_embedded_manifests(output_dir, artifacts.keys())])
    if not coherent:
        return {"status": STATUS_MIXED_RUN, "reasons": [REASON_MIXED_RUN], "problems": problems}

    # Currency against the live code/audit context.
    return classify_artifact_evidence(manifest, context)
