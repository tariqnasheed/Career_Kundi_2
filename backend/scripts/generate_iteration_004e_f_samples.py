#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004E-F final regression gate samples."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import weakref
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

os.environ.setdefault("JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE", "false")
os.environ.setdefault("JOB_SEARCH_MODEL_KNOWLEDGE_PROVIDER", "disabled")

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.job_search.company_research import (
    extract_company_from_html,
    merge_company_research_into_job_snapshot,
)
from app.agents.job_search.job_posting_extractor import (
    extract_job_posting_from_html,
    merge_extraction_into_job_snapshot,
)
from app.agents.job_search.quality.final_regression_audit import (
    CANONICAL_FAILURE_METRIC_KEYS,
    DETERMINISTIC_RANDOM_ROLES,
    FIXED_CROSS_SECTOR_CASES,
    audit_generated_pack,
    pack_failure_reasons,
)
from app.agents.job_search.quality.run_manifest import (
    RunContext,
    assert_results_share_run_context,
    current_run_context,
    detect_generation_context_change,
    render_manifest_markdown_comment,
    write_run_index,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004e_f_final_regression"

JOB_HTML = """
<html><head><script type="application/ld+json">
{"@type":"JobPosting","title":"Data Analyst","description":"Build dashboards.",
 "responsibilities":["SQL dashboard creation","Daily data quality checks"],
 "tools":["Power BI","SQL"],"skills":["SQL","Python"]}
</script></head></html>
"""

ORG_HTML = """
<html><head><script type="application/ld+json">
{"@type":"Corporation","legalName":"Northline Analytics Ltd",
 "makesOffer":[{"name":"KPI dashboards"}],"knowsAbout":["Retail analytics"]}
</script></head></html>
"""


def _full_ladder_job() -> dict:
    extraction = extract_job_posting_from_html(JOB_HTML, "https://northline.example/jobs/analyst")
    research = extract_company_from_html(ORG_HTML, "https://northline.example/about")
    job = merge_extraction_into_job_snapshot(
        {
            "title": "Data Analyst",
            "company_name": "Northline Analytics",
            "description_raw": "Build dashboards and KPI reporting.",
            "responsibilities": ["SQL dashboard creation"],
            "requirements": ["Strong SQL"],
            "extracted_skills": [{"skill": "SQL"}, {"skill": "Excel"}],
        },
        extraction,
    )
    return merge_company_research_into_job_snapshot(job, research)


def _row_from_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    # Descriptive/context fields, then EVERY canonical failure counter derived
    # from the single authoritative schema. Previously this list was a
    # hand-maintained copy that silently drifted (rows lacked newer counters,
    # which is exactly how a stale ``all_clean=true`` survived — Slice 1).
    row: dict[str, Any] = {
        "sample": metrics["sample"],
        "role": metrics["role"],
        "input_type": metrics["input_type"],
        "question_count": metrics["question_count"],
        "answer_count": metrics["answer_count"],
        "study_module_count": metrics["study_module_count"],
        "coverage_score": metrics["coverage_score"],
        "source_ladder_present": metrics["source_ladder_present"],
        "export_ready": metrics["export_ready"],
    }
    for key in CANONICAL_FAILURE_METRIC_KEYS:
        row[key] = metrics.get(key, 0)
    return row


def _row_failure_reasons(row: dict[str, Any]) -> list[str]:
    # Delegate to the single canonical clean/fail derivation (§11) so this
    # generator can never drift from the audit and regression tests.
    return pack_failure_reasons(row)


def _write_markdown_artifact(path: Path, body: str, manifest: dict[str, Any]) -> None:
    """Every markdown artifact starts with a hidden run-manifest comment so
    same-run membership is provable without user-facing metadata noise."""
    path.write_text(
        f"{render_manifest_markdown_comment(manifest)}\n{body}", encoding="utf-8"
    )


def _aggregate_findings(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Totals iterate the canonical schema so a newly added failure key can
    # never be silently absent from findings (Slice 1 lineage hardening).
    totals = {
        key: sum(r.get(key, 0) for r in rows) for key in CANONICAL_FAILURE_METRIC_KEYS
    }
    failing = [
        {"sample": r["sample"], "role": r.get("role"), "reasons": _row_failure_reasons(r)}
        for r in rows
        if _row_failure_reasons(r)
    ]
    return {
        "totals": totals,
        "failing_samples": failing,
        # Derived from the complete per-sample audit (semantic + structural +
        # substantive), not just legacy counters.
        "all_clean": not failing,
    }


PART_TIME_JOB = {
    "title": "Weekend Barista",
    "description_raw": "Part-time weekend espresso shifts.",
    "responsibilities": ["Espresso preparation", "Till operation"],
    "requirements": ["Customer service"],
    "extracted_skills": [{"skill": "Coffee Preparation"}],
}


def build_work_items() -> list[dict[str, Any]]:
    """Flat ordered work list — one entry per generated pack.

    Keeping generation item-wise (instead of one monolithic function) lets any
    environment split the expensive generation across processes while the
    assembly step still stamps ONE run manifest over every artifact.
    """
    items: list[dict[str, Any]] = [
        {"kind": "cross", "case": case} for case in FIXED_CROSS_SECTOR_CASES
    ]
    items.append(
        {
            "kind": "single",
            "outfile": "sample_title_only_regression.md",
            "job": {"title": "Mystery Role"},
            "focus": [],
            "difficulty": "auto",
            "role": "Mystery Role",
            "input_type": "title_only",
            "sample": "Title only",
        }
    )
    items.append(
        {
            "kind": "single",
            "outfile": "sample_rich_source_ladder_regression.md",
            "job_factory": "full_ladder",
            "focus": ["SQL"],
            "role": "Data Analyst",
            "input_type": "rich_source_ladder",
            "sample": "Rich source ladder",
        }
    )
    items.append(
        {
            "kind": "single",
            "outfile": "sample_document_export_regression.md",
            "job_factory": "full_ladder",
            "focus": ["SQL"],
            "role": "Data Analyst",
            "input_type": "document_export",
            "sample": "Document export",
        }
    )
    items.append(
        {
            "kind": "single",
            "outfile": "sample_part_time_odd_job_input_regression.md",
            "job": PART_TIME_JOB,
            "focus": ["Coffee Preparation"],
            "role": "Weekend Barista",
            "input_type": "part_time_odd_job",
            "sample": "Part-time odd job",
        }
    )
    items.extend({"kind": "random", "case": case} for case in DETERMINISTIC_RANDOM_ROLES)
    return items


def work_item_identity(item: dict[str, Any]) -> str:
    sample = item.get("sample")
    if sample is None:
        sample = (item.get("case") or {}).get("sample")
    return f"{item['kind']}::{sample}"


def result_identity(result: Mapping[str, Any]) -> str:
    return f"{result['kind']}::{(result.get('row') or {}).get('sample')}"


def _complete_result_payload_digest(result: Mapping[str, Any]) -> str:
    """Deterministic digest of the complete publishable result payload."""
    canonical = json.dumps(
        dict(result),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class _MintedProvenance:
    run_context_ref: weakref.ReferenceType[RunContext]
    work_item_identity: str
    run_id: str
    context_digest: str
    payload_digest: str


class _GeneratedWorkResult(Mapping[str, Any]):
    """In-memory lifecycle-provenance result — minted only by ``generate_work_item``.

    Legitimacy is proven by closure-private registry membership, not caller-supplied
    fields. Identity-hashable for exact-object weak-key binding.
    """

    __slots__ = (
        "_payload",
        "_work_item_identity",
        "_run_id",
        "_context_digest",
        "__weakref__",
    )
    __hash__ = object.__hash__
    __eq__ = object.__eq__

    def __init__(
        self,
        *,
        payload: dict[str, Any],
        work_item_identity: str,
        run_id: str,
        context_digest: str,
    ) -> None:
        self._payload = payload
        self._work_item_identity = work_item_identity
        self._run_id = run_id
        self._context_digest = context_digest

    def __getitem__(self, key: str) -> Any:
        return self._payload[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._payload)

    def __len__(self) -> int:
        return len(self._payload)

    def get(self, key: str, default: Any = None) -> Any:
        return self._payload.get(key, default)

    @property
    def work_item_identity(self) -> str:
        return self._work_item_identity

    @property
    def bound_run_id(self) -> str:
        return self._run_id

    @property
    def bound_context_digest(self) -> str:
        return self._context_digest


def _build_lifecycle_bound_generation_functions() -> tuple[
    Callable[[dict[str, Any], RunContext], _GeneratedWorkResult],
    Callable[[list[Any], RunContext], None],
]:
    """Closure-private weak registry — no module-global mint path exists."""
    mint_registry: weakref.WeakKeyDictionary[_GeneratedWorkResult, _MintedProvenance] = (
        weakref.WeakKeyDictionary()
    )

    def generate_work_item(
        item: dict[str, Any], run_context: RunContext
    ) -> _GeneratedWorkResult:
        """Generate one pack under a live run context."""
        run_context.require_live_generation_capability()
        item_ident = work_item_identity(item)
        if item["kind"] in ("cross", "random"):
            case = item["case"]
            metrics = audit_generated_pack(
                case["job"],
                focus_areas=case["focus"],
                role_label=case["role"],
                input_type=case["input_type"],
                sample_name=case["sample"],
            )
            outfile = None
        else:
            job = (
                _full_ladder_job()
                if item.get("job_factory") == "full_ladder"
                else dict(item["job"])
            )
            metrics = audit_generated_pack(
                job,
                focus_areas=item["focus"],
                difficulty=item.get("difficulty", "mid"),
                role_label=item["role"],
                input_type=item["input_type"],
                sample_name=item["sample"],
            )
            outfile = item["outfile"]
        payload = {
            "kind": item["kind"],
            "outfile": outfile,
            "row": _row_from_metrics(metrics),
            "pack_markdown": metrics["pack_markdown"],
            "run_id": run_context.run_id,
            "run_context_digest": run_context.context_digest,
        }
        result = _GeneratedWorkResult(
            payload=payload,
            work_item_identity=item_ident,
            run_id=run_context.run_id,
            context_digest=run_context.context_digest,
        )
        mint_registry[result] = _MintedProvenance(
            run_context_ref=weakref.ref(run_context),
            work_item_identity=item_ident,
            run_id=run_context.run_id,
            context_digest=run_context.context_digest,
            payload_digest=_complete_result_payload_digest(result),
        )
        return result

    def assert_lifecycle_provenance(
        results: list[Any], run_context: RunContext
    ) -> None:
        """F5 — reject retroactive relabeling before any authoritative write."""
        run_context.require_live_generation_capability()
        for index, result in enumerate(results):
            if not isinstance(result, _GeneratedWorkResult):
                raise SystemExit(
                    f"generation_lifecycle_provenance_invalid: result[{index}] is not a "
                    "lifecycle-provenance result"
                )
            provenance = mint_registry.get(result)
            if provenance is None:
                raise SystemExit(
                    f"generation_lifecycle_provenance_invalid: result[{index}] was not "
                    "minted by generate_work_item"
                )
            origin_context = provenance.run_context_ref()
            if origin_context is not run_context:
                raise SystemExit(
                    f"generation_lifecycle_provenance_invalid: result[{index}] origin "
                    "RunContext mismatch"
                )
            if provenance.work_item_identity != result_identity(result):
                raise SystemExit(
                    f"generation_lifecycle_provenance_invalid: result[{index}] work-item "
                    "identity mismatch"
                )
            if provenance.run_id != run_context.run_id:
                raise SystemExit(
                    f"generation_lifecycle_provenance_invalid: result[{index}] run_id mismatch"
                )
            if provenance.context_digest != run_context.context_digest:
                raise SystemExit(
                    f"generation_lifecycle_provenance_invalid: result[{index}] "
                    "run_context_digest mismatch"
                )
            if provenance.payload_digest != _complete_result_payload_digest(result):
                raise SystemExit(
                    f"generation_lifecycle_provenance_invalid: result[{index}] "
                    "payload content mismatch"
                )

    return generate_work_item, assert_lifecycle_provenance


generate_work_item, _assert_lifecycle_provenance = _build_lifecycle_bound_generation_functions()
del _build_lifecycle_bound_generation_functions


# --- F3: result-set completeness contract -------------------------------------
#
# A stable identity per expected work item, derived from existing fields only
# (kind + unique sample name — verified unique across the whole plan). Used to
# prove the actual results cover exactly the run-start plan, with exact
# multiplicity and independent of ordering.


def compute_work_plan_digest(items: list[dict[str, Any]]) -> str:
    """Deterministic, order-independent digest of the expected work-item plan."""
    payload = "\n".join(sorted(work_item_identity(i) for i in items))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def check_result_set_completeness(
    results: list[dict[str, Any]], expected_items: list[dict[str, Any]]
) -> list[str]:
    """Return problems if actual results do not cover the expected plan exactly.

    Detects empty, missing, duplicate, and unexpected-extra identities. Order is
    irrelevant. Empty list means the run is complete.
    """
    if not results:
        return ["empty_result_set"]
    expected = Counter(work_item_identity(i) for i in expected_items)
    actual = Counter(result_identity(r) for r in results)
    problems: list[str] = []
    for ident, n in sorted((expected - actual).items()):
        problems.append(f"missing:{ident}x{n}")
    for ident, n in sorted((actual - expected).items()):
        label = "duplicate" if ident in expected else "unexpected"
        problems.append(f"{label}:{ident}x{n}")
    return problems


def assemble_and_write(
    results: list[Any],
    run_context: RunContext,
    expected_items: list[dict[str, Any]],
) -> None:
    """Write every artifact of the run, all bound to ONE run context.

    The run context was created BEFORE the first work item. Assembly (a) proves
    every work item belongs to it, (b) rechecks the repository/audit context to
    detect any change during generation (TOCTOU), and (c) writes the authoritative
    root index LAST, binding the exact bytes of every artifact.
    """
    manifest = run_context.manifest

    # F5 lifecycle provenance — BEFORE any authoritative write. Retroactive
    # relabeling via bind_result() or forged dicts must never reach publication.
    _assert_lifecycle_provenance(results, run_context)

    # F3 publication contract — BEFORE any authoritative write. A missing,
    # unbound, mismatched, partial, empty, duplicated, or extended plan/result
    # set must never reach findings aggregation (false all_clean=true).
    if expected_items is None:
        raise SystemExit("generation_plan_required")
    bound_digest = manifest.get("work_plan_digest") or ""
    if not bound_digest:
        raise SystemExit(
            "generation_plan_unbound: run context has no work_plan_digest bound at run start."
        )
    actual_digest = compute_work_plan_digest(expected_items)
    if bound_digest != actual_digest:
        raise SystemExit(
            f"generation_plan_mismatch: expected plan bound at run start "
            f"({bound_digest}) != plan presented at assembly ({actual_digest})."
        )
    problems = check_result_set_completeness(results, expected_items)
    if problems:
        raise SystemExit(f"generation_result_set_incomplete: {problems}")

    # Mixed-context rejection: refuse to relabel results from another run/state.
    assert_results_share_run_context(results, run_context)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    cross_md_parts = [r["pack_markdown"] for r in results if r["kind"] == "cross"]
    _write_markdown_artifact(
        OUTPUT_DIR / "sample_cross_sector_regression.md",
        "\n\n---\n\n".join(cross_md_parts),
        manifest,
    )
    written.append("sample_cross_sector_regression.md")
    for result in results:
        if result["kind"] == "single":
            _write_markdown_artifact(
                OUTPUT_DIR / result["outfile"], result["pack_markdown"], manifest
            )
            written.append(result["outfile"])
    random_md_parts = [r["pack_markdown"] for r in results if r["kind"] == "random"]
    _write_markdown_artifact(
        OUTPUT_DIR / "sample_deterministic_random_regression.md",
        "\n\n---\n\n".join(random_md_parts),
        manifest,
    )
    written.append("sample_deterministic_random_regression.md")

    all_rows = [r["row"] for r in results]
    random_rows = [r["row"] for r in results if r["kind"] == "random"]
    findings = _aggregate_findings(all_rows)
    (OUTPUT_DIR / "metrics.json").write_text(
        json.dumps({"manifest": manifest, "data": all_rows}, indent=2), encoding="utf-8"
    )
    written.append("metrics.json")
    (OUTPUT_DIR / "sample_final_quality_findings.json").write_text(
        json.dumps({"manifest": manifest, **findings}, indent=2), encoding="utf-8"
    )
    written.append("sample_final_quality_findings.json")

    lines = [
        render_manifest_markdown_comment(manifest),
        "# Iteration 004E-F Final Regression Gate Summary",
        "",
        f"*Captured: {manifest['generated_at']}*",
        "",
        f"*Run: `{manifest['run_id']}` — HEAD `{manifest['git_head'][:8]}`, "
        f"worktree `{manifest['dirty_worktree_fingerprint']}`, "
        f"audit schema `{manifest['audit_schema_version']}`*",
        "",
        "## Purpose",
        "",
        "Final verification/stabilization for Interview Pack Generator and Interview Study Material.",
        "Interview Pack Generator + Interview Study Material core pipeline is regression-checked.",
        "Includes 004E-E2 adaptive study-material depth and length policy checks.",
        "Includes 004E-E2.2 semantic integrity, claim integrity, and truthful regression gates.",
        "",
        "## Risk controls (004E-F)",
        "",
        "1. **Fake completion risk** — gate requires zero missing answers/study modules and clean quality metrics before claiming completion.",
        "2. **Generic content risk** — blocked-phrase scan covers answers and study material, not just question titles.",
        "3. **Thin input risk** — title-only sample must not claim fake full coverage (coverage score 0).",
        "4. **Source-ladder regression risk** — user fields, URL extraction, company research, document library, model status, and fallback statuses remain transparent.",
        "5. **Study material regression risk** — every exportable question has a dedicated module; duplicate fingerprint scan uses full module content.",
        "6. **Export regression risk** — markdown export keeps model answer and study material attached per question.",
        "7. **Frontend/backend drift risk** — no schema changes in this phase; prior 004E-E alignment preserved.",
        "8. **Security/network risk** — no new direct live fetching; samples and tests use mocked/deterministic inputs only.",
        "9. **Over-scope risk** — 004F global job search not implemented; role catalog dropdown not implemented; Final Content Library Regeneration not run.",
        "10. **Overfitting risk** — five deterministic random roles (fixed seed list) supplement ten fixed cross-sector roles.",
        "",
        "## Deferred",
        "",
        "- **004F** global job search remains deferred.",
        "- **Role catalog dropdown** remains deferred (next UI improvement before or alongside 004F planning).",
        "- **Final Content Library Regeneration** not run in this phase.",
        "",
        "## Sample metrics",
        "",
        "| Sample | Role | Input Type | Questions | Answers | Study Modules | Missing Answers | Missing Study Modules | Coverage Score | Source Ladder Present | Export Ready | Hard Max Violations | Fake URLs | Generic Hits | Silly Hits | Empty Sections | Duplicate Study Modules | Internal Label Leaks |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in all_rows:
        lines.append(
            f"| {row['sample']} | {row['role']} | {row['input_type']} | {row['question_count']} | "
            f"{row['answer_count']} | {row['study_module_count']} | {row['missing_answer_count']} | "
            f"{row['missing_study_module_count']} | {row['coverage_score']} | "
            f"{'yes' if row['source_ladder_present'] else 'no'} | "
            f"{'yes' if row['export_ready'] else 'no'} | {row.get('hard_max_violation_count', 0)} | {row['fake_url_hits']} | "
            f"{row['generic_phrase_hits']} | {row['silly_question_hits']} | {row['empty_section_count']} | "
            f"{row['duplicate_study_module_count']} | {row['internal_label_leak_count']} |"
        )

    lines.extend([
        "",
        "## Deterministic random regression samples",
        "",
        "Fixed deterministic set (seed list of 15 roles; 5 selected):",
        "",
        "- Lab Technician (science/health)",
        "- Logistics Coordinator (office/business)",
        "- HR Assistant (office/business)",
        "- Graphic Designer (creative/media)",
        "- Warehouse Picker (part-time/odd-job style)",
        "",
        "| Role | Input Type | Questions | Missing Answers | Missing Study Modules | Fake URLs | Generic Hits | Silly Hits |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in random_rows:
        lines.append(
            f"| {row['role']} | {row['input_type']} | {row['question_count']} | "
            f"{row['missing_answer_count']} | {row['missing_study_module_count']} | "
            f"{row['fake_url_hits']} | {row['generic_phrase_hits']} | {row['silly_question_hits']} |"
        )

    lines.extend([
        "",
        "## Aggregate quality findings",
        "",
        f"- All samples clean: **{findings['all_clean']}**",
        f"- Missing answers (total): **{findings['totals']['missing_answer_count']}**",
        f"- Missing study modules (total): **{findings['totals']['missing_study_module_count']}**",
        f"- Fake URLs (total): **{findings['totals']['fake_url_hits']}**",
        f"- Generic hits (total): **{findings['totals']['generic_phrase_hits']}**",
        f"- Silly hits (total): **{findings['totals']['silly_question_hits']}**",
        f"- Empty sections (total): **{findings['totals']['empty_section_count']}**",
        f"- Hard max violations (total): **{findings['totals']['hard_max_violation_count']}**",
        f"- Duplicate study modules (total): **{findings['totals']['duplicate_study_module_count']}**",
        f"- Internal label leaks (total): **{findings['totals']['internal_label_leak_count']}**",
        f"- Unsupported personal claims (total): **{findings['totals']['unsupported_personal_claim_count']}**",
        f"- Unsupported numeric claims (total): **{findings['totals']['unsupported_numeric_claim_count']}**",
        f"- Cross-domain contamination hits (total): **{findings['totals']['cross_domain_contamination_hits']}**",
        f"- Surface quality defects (total): **{findings['totals']['surface_quality_defect_count']}**",
        f"- Thin-input specificity violations (total): **{findings['totals']['thin_input_specificity_violation_count']}**",
        f"- Structure-incomplete study modules (total): **{findings['totals']['structure_incomplete_count']}**",
        f"- Substantive-depth failures (total): **{findings['totals']['substantive_depth_failure_count']}**",
        "",
        "## Failing samples (per-sample reasons)",
        "",
    ])
    if findings["failing_samples"]:
        for fs in findings["failing_samples"]:
            lines.append(f"- **{fs['sample']}** ({fs.get('role')}): {', '.join(fs['reasons'])}")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Quality gates",
        "",
        "In-generator deterministic gates (missing-content, blocked-phrase, fake-URL, silly-question, "
        "claim-integrity, surface-quality, cross-domain, structural/substantive depth) are computed by "
        "`audit_generated_pack` and reflected in the metrics above. External live-network and secret scans "
        "are NOT executed by this script and remain pending as a separate step.",
        "",
    ])
    (OUTPUT_DIR / "iteration_004e_f_summary.md").write_text("\n".join(lines), encoding="utf-8")
    written.append("iteration_004e_f_summary.md")

    # --- End-of-run TOCTOU check -------------------------------------------------
    # Recompute the live repository/audit context and compare to run start. All
    # artifacts live under project_review/ (excluded from the fingerprint), so a
    # difference means the code/audit state genuinely changed mid-run.
    changed = detect_generation_context_change(
        run_context.start_context(), current_run_context(REPO_ROOT)
    )

    # Authoritative root index written LAST, binding exact artifact bytes. If the
    # context changed, it is marked invalid (never publishable as current
    # evidence) and the run fails loudly — no silent relabel, no false clean.
    write_run_index(
        OUTPUT_DIR, manifest, written, generation_context_changed=changed or None
    )
    if changed:
        raise SystemExit(
            f"generation_context_changed during run {manifest['run_id']}: {changed}. "
            "Artifacts marked invalid; not current release evidence."
        )
    print(f"Wrote samples to {OUTPUT_DIR} (run {manifest['run_id']})")


def main() -> None:
    # Expected work-item plan captured ONCE and bound to the run identity, so
    # assembly proves the results cover exactly this plan (F3).
    items = build_work_items()
    run_context = RunContext.create(REPO_ROOT, work_plan_digest=compute_work_plan_digest(items))
    results = [generate_work_item(item, run_context) for item in items]
    assemble_and_write(results, run_context, expected_items=items)


if __name__ == "__main__":
    main()
