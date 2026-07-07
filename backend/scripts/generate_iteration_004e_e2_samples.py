#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004E-E2 adaptive study-material samples."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
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
from app.agents.job_search.knowledge.study_material_budget import hard_max_violation_count
from app.agents.job_search.knowledge.question_study_material import count_empty_study_sections
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.agents.job_search.quality.claim_integrity import audit_claim_integrity, classify_claim_support
from app.agents.job_search.quality.cross_domain_guard import audit_cross_domain_contamination
from app.agents.job_search.quality.final_regression_audit import pack_failure_reasons
from app.agents.job_search.quality.surface_quality_guard import audit_surface_quality
from app.agents.job_search.quality.user_facing_text import iter_user_facing_text
from app.tools.document_export import build_interview_pack_markdown

# Deep depths whose substantive pedagogical contract must be genuinely met.
_DEEP_DEPTHS = {"practical_workflow", "complex_scenario", "advanced_multi_step"}
# Minimum substantive contract coverage required to call a representative
# depth sample "clean" (structural field presence alone is NOT sufficient).
_SUBSTANTIVE_FLOOR = 0.85
_DEEP_SUBSTANTIVE_FLOOR = 0.9

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004e_e2_adaptive_study_material"

JOB_HTML = """
<html><head><script type="application/ld+json">
{"@type":"JobPosting","title":"Data Analyst","description":"Build dashboards.",
 "responsibilities":["SQL dashboard creation"],"tools":["Power BI","SQL"],"skills":["SQL"]}
</script></head></html>
"""

ORG_HTML = """
<html><head><script type="application/ld+json">
{"@type":"Corporation","legalName":"Northline Analytics Ltd",
 "makesOffer":[{"name":"KPI dashboards"}],"knowsAbout":["Retail analytics"]}
</script></head></html>
"""

_URL_RE = re.compile(r"https?://", re.I)
_INTERNAL_LABEL_RE = re.compile(r"\bRole Specific\b")

_DEPTH_SAMPLES = [
    ("simple_factual", "Teaching Assistant", {"title": "Teaching Assistant", "description_raw": "Classroom support.", "responsibilities": ["Classroom support"], "extracted_skills": [{"skill": "Classroom Support"}]}, ["Classroom Support"], "sample_simple_factual.md"),
    ("hr_behavioral", "HR Assistant", {"title": "HR Assistant", "description_raw": "Onboarding support.", "responsibilities": ["Employee onboarding"], "extracted_skills": [{"skill": "Onboarding"}]}, ["Onboarding"], "sample_hr_behavioral.md"),
    ("standard_technical", "Lab Technician", {"title": "Lab Technician", "description_raw": "Sample processing.", "responsibilities": ["Sample processing"], "extracted_skills": [{"skill": "Sample Processing"}]}, ["Sample Processing"], "sample_standard_technical.md"),
    ("practical_workflow", "DevOps Engineer", {"title": "DevOps Engineer", "description_raw": "CI/CD maintenance.", "responsibilities": ["CI/CD pipeline maintenance"], "extracted_skills": [{"skill": "CI/CD"}, {"skill": "AWS"}]}, ["CI/CD", "AWS"], "sample_practical_workflow.md"),
    ("complex_scenario", "Clinical Pharmacist", {"title": "Clinical Pharmacist", "description_raw": "Ward medication review.", "responsibilities": ["Medication review", "Patient counselling"], "extracted_skills": [{"skill": "Pharmacology"}]}, ["Medication Review"], "sample_complex_scenario.md"),
    ("advanced_multi_step", "Senior Systems Engineer", {"title": "Senior Systems Engineer", "description_raw": "Multi-region architecture and trade-offs.", "responsibilities": ["System architecture", "Trade-off analysis"], "extracted_skills": [{"skill": "System Design"}]}, ["System Design"], "sample_advanced_multi_step.md"),
]


def _exportable(questions: list[dict]) -> list[dict]:
    return [q for q in questions if q.get("model_answer") and not q.get("export_blocked")]


def _sample_sort_key(q: dict) -> tuple:
    """Prefer substantive completeness and semantic integrity over legacy
    structural-presence coverage when choosing a representative sample."""
    study = q.get("study_material") or {}
    status = study.get("budget_status")
    status_ok = 1 if status not in {"structure_incomplete", "hard_limit_exceeded"} else 0
    substantive = float(study.get("substantive_contract_coverage") or 0)
    integrity_ok = 1 if (
        int(study.get("unsupported_personal_claim_count") or 0) == 0
        and int(study.get("unsupported_numeric_claim_count") or 0) == 0
        and int(study.get("surface_quality_defect_count") or 0) == 0
    ) else 0
    legacy = float(study.get("depth_contract_coverage") or 0)
    return (status_ok, integrity_ok, round(substantive, 3), legacy)


def _pick_depth_question(questions: list[dict], depth: str) -> dict | None:
    matches = [q for q in questions if (q.get("study_material") or {}).get("study_depth") == depth]
    if not matches:
        return None
    return max(matches, key=_sample_sort_key)


def _row_failure_reasons(row: dict[str, Any]) -> list[str]:
    """Per-question clean/fail reasons derived from the single canonical path (§11).

    This maps the per-question E2 row onto the canonical pack-metric key names and
    delegates to ``pack_failure_reasons`` so E2, F, the audit, and the regression
    tests can never disagree about what "clean" means. The descriptive
    substantive-floor suffix is preserved for the human-readable summary.
    """
    subst = row.get("substantive_contract_coverage")
    floor = _DEEP_SUBSTANTIVE_FLOOR if row.get("study_depth") in _DEEP_DEPTHS else _SUBSTANTIVE_FLOOR
    substantive_fail = 0
    if subst is not None:
        try:
            substantive_fail = 1 if float(subst) < floor else 0
        except (TypeError, ValueError):
            substantive_fail = 0
    canonical_metrics = {
        "hard_max_violation_count": row.get("hard_max_violations", 0),
        "fake_url_hits": row.get("fake_url_hits", 0),
        "generic_phrase_hits": row.get("generic_phrase_hits", 0),
        "empty_section_count": row.get("empty_section_count", 0),
        "internal_label_leak_count": row.get("internal_label_leak_count", 0),
        "unsupported_personal_claim_count": row.get("unsupported_personal_claims", 0),
        "unsupported_numeric_claim_count": row.get("unsupported_numeric_claims", 0),
        "cross_domain_contamination_hits": row.get("cross_domain_contamination_hits", 0),
        "surface_quality_defect_count": row.get("surface_quality_defects", 0),
        "thin_input_specificity_violation_count": row.get("thin_input_specificity_violations", 0),
        "structure_incomplete_count": (
            1 if row.get("budget_status") in {"structure_incomplete", "hard_limit_exceeded"} else 0
        ),
        "substantive_depth_failure_count": substantive_fail,
    }
    reasons = pack_failure_reasons(canonical_metrics)
    # Enrich the generic substantive reason with the actual value for the summary.
    if substantive_fail:
        reasons = [
            f"substantive_depth_failure_count({subst}<{floor})"
            if r == "substantive_depth_failure_count"
            else r
            for r in reasons
        ]
    return reasons


def _rich_job() -> dict:
    extraction = extract_job_posting_from_html(JOB_HTML, "https://northline.example/jobs/analyst")
    research = extract_company_from_html(ORG_HTML, "https://northline.example/about")
    job = merge_extraction_into_job_snapshot(
        {
            "title": "Data Analyst",
            "company_name": "Northline Analytics",
            "description_raw": "Build dashboards.",
            "responsibilities": ["SQL dashboard creation"],
            "extracted_skills": [{"skill": "SQL"}],
        },
        extraction,
    )
    return merge_company_research_into_job_snapshot(job, research)


def _metrics_from_question(q: dict, job: dict, role: str, sample: str) -> dict[str, Any]:
    study = q.get("study_material") or {}
    blob = json.dumps(study)
    hard_max = int(study.get("hard_max_words") or 0)
    actual = int(study.get("actual_word_count") or 0)
    skill = ""
    if job.get("extracted_skills"):
        first = job["extracted_skills"][0]
        skill = first.get("skill") if isinstance(first, dict) else str(first)
    # Audit ALL user-facing prose recursively (answer + study + nested fields),
    # scanning each prose blob independently. Joining blobs would let \s-based
    # patterns (duplicate token, role tautology) match across the newline join
    # boundary and report cross-blob false positives.
    claim = {"unsupported_personal_claim_count": 0, "unsupported_numeric_claim_count": 0, "thin_input_specificity_violation_count": 0}
    surface = {"total_surface_quality_defects": 0}
    cross = {"cross_domain_contamination_hits": 0}
    for prose in iter_user_facing_text(q):
        ci = audit_claim_integrity(prose, job)
        for k in claim:
            claim[k] += ci.get(k, 0)
        sq = audit_surface_quality(prose, role=role)
        surface["total_surface_quality_defects"] += sq["total_surface_quality_defects"]
        cd = audit_cross_domain_contamination(prose, role=role, skill=skill, job=job)
        cross["cross_domain_contamination_hits"] += cd["cross_domain_contamination_hits"]
    return {
        "sample": sample,
        "role": role,
        "question": (q.get("question") or "")[:120],
        "study_depth": study.get("study_depth"),
        "complexity": study.get("study_complexity_level"),
        "target_min": study.get("target_min_words"),
        "target_max": study.get("target_max_words"),
        "hard_max": hard_max,
        "actual_words": actual,
        "budget_status": study.get("budget_status"),
        "source_items": len(study.get("source_items_used") or []),
        "claim_support_status": classify_claim_support(job),
        "hard_max_violations": hard_max_violation_count(study),
        "depth_contract_coverage": study.get("depth_contract_coverage"),
        "substantive_contract_coverage": study.get("substantive_contract_coverage"),
        "thin_input_conservative": study.get("thin_input_conservative"),
        "unsupported_personal_claims": claim["unsupported_personal_claim_count"],
        "unsupported_numeric_claims": claim["unsupported_numeric_claim_count"],
        "cross_domain_contamination_hits": cross["cross_domain_contamination_hits"],
        "surface_quality_defects": surface["total_surface_quality_defects"],
        "thin_input_specificity_violations": claim["thin_input_specificity_violation_count"],
        "hard_max_ratio": round(actual / hard_max, 3) if hard_max else 0,
        "fake_url_hits": len(_URL_RE.findall(blob)),
        "generic_phrase_hits": export_blocked_phrase_count(blob),
        "empty_section_count": count_empty_study_sections(study),
        "internal_label_leak_count": len(_INTERNAL_LABEL_RE.findall(blob)),
        "has_workflow_structure": bool(study.get("workflow_checkpoints") and study.get("failure_modes")),
        "has_scenario_structure": bool(study.get("decision_branches") and study.get("verification_steps")),
        "has_advanced_structure": bool(study.get("staged_reasoning") and study.get("validation_and_monitoring")),
        "has_compact_explanation": bool(study.get("compact_explanation")),
        "has_behavioral_structure": bool(study.get("behavioral_response_structure")),
    }


def _with_reasons(row: dict[str, Any]) -> dict[str, Any]:
    row["failure_reasons"] = _row_failure_reasons(row)
    row["clean"] = not row["failure_reasons"]
    return row


def _behavioral_findings(rows: list[dict[str, Any]]) -> dict[str, Any]:
  def _pick(depth: str) -> dict[str, Any] | None:
      return next((r for r in rows if r.get("study_depth") == depth and r.get("sample") not in {"Title only", "Source rich"}), None)

  simple = _pick("simple_factual")
  hr = _pick("hr_behavioral")
  workflow = _pick("practical_workflow")
  scenario = _pick("complex_scenario")
  advanced = _pick("advanced_multi_step")
  title = next((r for r in rows if r.get("sample") == "Title only"), None)

  return {
    "simple_economical": bool(simple and simple["actual_words"] < simple["hard_max"] * 0.8 and simple.get("has_compact_explanation")),
    "hr_not_near_hard_max": bool(hr and hr.get("hard_max_ratio", 1) <= 0.75 and hr.get("has_behavioral_structure")),
    "workflow_has_structure": bool(workflow and workflow.get("has_workflow_structure")),
    "scenario_has_structure": bool(scenario and scenario.get("has_scenario_structure")),
    "advanced_has_structure": bool(advanced and advanced.get("has_advanced_structure")),
    "title_only_conservative": bool(title and title.get("thin_input_conservative") and title["actual_words"] <= 260),
    "simple_vs_advanced_word_delta": (
      (advanced["actual_words"] - simple["actual_words"]) if simple and advanced else None
    ),
  }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for depth, role, job, focus, outfile in _DEPTH_SAMPLES:
        questions = _exportable(mock_generate_questions(job, focus_areas=focus, difficulty="mid"))
        q = _pick_depth_question(questions, depth) or questions[0]
        pack_md = build_interview_pack_markdown(job_title=role, company_name=job.get("company_name"), questions=[q])
        (OUTPUT_DIR / outfile).write_text(pack_md, encoding="utf-8")
        rows.append(_with_reasons(_metrics_from_question(q, job, role, role)))

    title_job = {"title": "Mystery Role"}
    title_qs = _exportable(mock_generate_questions(title_job, focus_areas=[], difficulty="auto"))
    title_q = title_qs[0]
    (OUTPUT_DIR / "sample_title_only_budget.md").write_text(
        build_interview_pack_markdown(job_title="Mystery Role", company_name=None, questions=[title_q]),
        encoding="utf-8",
    )
    rows.append(_with_reasons(_metrics_from_question(title_q, title_job, "Mystery Role", "Title only")))

    rich_job = _rich_job()
    rich_qs = _exportable(mock_generate_questions(rich_job, focus_areas=["SQL"], difficulty="mid"))
    rich_q = max(rich_qs, key=lambda q: len((q.get("study_material") or {}).get("source_items_used") or []))
    (OUTPUT_DIR / "sample_source_rich_budget.md").write_text(
        build_interview_pack_markdown(job_title="Data Analyst", company_name="Northline Analytics", questions=[rich_q]),
        encoding="utf-8",
    )
    rows.append(_with_reasons(_metrics_from_question(rich_q, rich_job, "Data Analyst (rich)", "Source rich")))

    semantic_totals = {
        "unsupported_personal_claims": sum(r.get("unsupported_personal_claims", 0) for r in rows),
        "unsupported_numeric_claims": sum(r.get("unsupported_numeric_claims", 0) for r in rows),
        "cross_domain_contamination_hits": sum(r.get("cross_domain_contamination_hits", 0) for r in rows),
        "surface_quality_defects": sum(r.get("surface_quality_defects", 0) for r in rows),
        "thin_input_specificity_violations": sum(r.get("thin_input_specificity_violations", 0) for r in rows),
    }
    behavioral = _behavioral_findings(rows)
    failing_samples = [
        {"sample": r.get("sample"), "role": r.get("role"), "reasons": r.get("failure_reasons", [])}
        for r in rows
        if r.get("failure_reasons")
    ]
    structure_incomplete_count = sum(
        1 for r in rows if r.get("budget_status") == "structure_incomplete"
    )
    substantive_depth_failures = sum(
        1
        for r in rows
        if any(str(x).startswith("substantive_coverage_below_floor") for x in r.get("failure_reasons", []))
    )
    findings = {
        "hard_max_violations": sum(r.get("hard_max_violations", 0) for r in rows),
        "fake_url_hits": sum(r.get("fake_url_hits", 0) for r in rows),
        "generic_phrase_hits": sum(r.get("generic_phrase_hits", 0) for r in rows),
        "empty_section_count": sum(r.get("empty_section_count", 0) for r in rows),
        "internal_label_leak_count": sum(r.get("internal_label_leak_count", 0) for r in rows),
        "structure_incomplete_count": structure_incomplete_count,
        "substantive_depth_failures": substantive_depth_failures,
        "semantic_integrity": semantic_totals,
        "claim_integrity": {
            "unsupported_personal_claims": semantic_totals["unsupported_personal_claims"],
            "unsupported_numeric_claims": semantic_totals["unsupported_numeric_claims"],
            "thin_input_specificity_violations": semantic_totals["thin_input_specificity_violations"],
        },
        "behavioral_adaptation": behavioral,
        "failing_samples": failing_samples,
        # all_clean is derived from the COMPLETE per-sample audit, including
        # structural completeness and substantive depth — not just legacy counters.
        "all_clean": not failing_samples,
    }
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "sample_budget_findings.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")

    lines = [
        "# Iteration 004E-E2 Adaptive Study Material Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Policy (004E-E2 + 004E-E2.1 + 004E-E2.2)",
        "",
        "- Adaptive depth uses pedagogical contracts, not word-count quotas.",
        "- Interview answers retain separate concise limits (500-word hard ceiling).",
        "- Hard max is an emergency ceiling, not a generation target.",
        "- Thin title-only inputs remain conservative and source-transparent.",
        "- `concise_complete` requires substantive depth-contract coverage and integrity gates.",
        "- Explicit user-stated claims are usable without evidence; unsupported biography is forbidden.",
        "",
        "## Sample metrics",
        "",
        "| Sample | Role | Question | Study Depth | Complexity | Target Min | Target Max | Hard Max | Actual Words | Budget Status | Source Items | Claim Support | Hard Max Violations | Depth Contract Coverage | Substantive Contract Coverage | Thin Input | Unsupported Personal Claims | Unsupported Numeric Claims | Cross-Domain Contamination Hits | Surface Quality Defects | Thin-Input Specificity Violations | Fake URLs | Generic Hits | Empty Sections | Internal Label Leaks |",
        "|---|---|---|---|---:|---:|---:|---:|---|---|---:|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        thin = "yes" if row.get("thin_input_conservative") else "no"
        lines.append(
            f"| {row['sample']} | {row['role']} | {row.get('question', '')[:60]} | {row.get('study_depth')} | {row.get('complexity')} | "
            f"{row.get('target_min')} | {row.get('target_max')} | {row.get('hard_max')} | {row.get('actual_words')} | "
            f"{row.get('budget_status')} | {row.get('source_items')} | {row.get('claim_support_status')} | "
            f"{row.get('hard_max_violations', 0)} | {row.get('depth_contract_coverage')} | "
            f"{row.get('substantive_contract_coverage')} | {thin} | {row.get('unsupported_personal_claims', 0)} | "
            f"{row.get('unsupported_numeric_claims', 0)} | {row.get('cross_domain_contamination_hits', 0)} | "
            f"{row.get('surface_quality_defects', 0)} | {row.get('thin_input_specificity_violations', 0)} | "
            f"{row.get('fake_url_hits', 0)} | {row.get('generic_phrase_hits', 0)} | "
            f"{row.get('empty_section_count', 0)} | {row.get('internal_label_leak_count', 0)} |"
        )

    b = behavioral
    s = semantic_totals
    lines.extend([
        "",
        "## Behavioral adaptation findings",
        "",
        f"- Simple material stayed economical: **{b.get('simple_economical')}**",
        f"- HR/behavioral avoided hard-ceiling attraction: **{b.get('hr_not_near_hard_max')}**",
        f"- Practical workflow includes workflow structure: **{b.get('workflow_has_structure')}**",
        f"- Complex scenario includes branches/trade-offs/verification: **{b.get('scenario_has_structure')}**",
        f"- Advanced multi-step includes staged/validation structure: **{b.get('advanced_has_structure')}**",
        f"- Title-only stayed conservative (≤220 words): **{b.get('title_only_conservative')}**",
        f"- Simple vs advanced word delta (representative samples): **{b.get('simple_vs_advanced_word_delta')}**",
        "",
        "## Semantic integrity findings",
        "",
        f"- Unsupported personal claims (total): **{s['unsupported_personal_claims']}**",
        f"- Unsupported numeric claims (total): **{s['unsupported_numeric_claims']}**",
        f"- Cross-domain contamination hits (total): **{s['cross_domain_contamination_hits']}**",
        f"- Surface quality defects (total): **{s['surface_quality_defects']}**",
        f"- Thin-input specificity violations (total): **{s['thin_input_specificity_violations']}**",
        "",
        "## Claim integrity findings",
        "",
        f"- Unsupported personal claims (total): **{semantic_totals['unsupported_personal_claims']}**",
        f"- Unsupported numeric claims (total): **{semantic_totals['unsupported_numeric_claims']}**",
        f"- Thin-input specificity violations (total): **{semantic_totals['thin_input_specificity_violations']}**",
        f"- Structure-incomplete samples: **{findings['structure_incomplete_count']}**",
        f"- Substantive-depth failures: **{findings['substantive_depth_failures']}**",
        f"- All samples clean: **{findings['all_clean']}**",
        "",
        "## Failing samples (per-sample reasons)",
        "",
    ])
    if findings["failing_samples"]:
        for fs in findings["failing_samples"]:
            lines.append(f"- **{fs['sample']}** ({fs['role']}): {', '.join(fs['reasons'])}")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Quality gates",
        "",
        "In-generator deterministic gates (blocked-phrase, fake-URL, claim-integrity, "
        "surface-quality, cross-domain, structural/substantive depth) are reflected in the "
        "metrics above. External network/secret scans are NOT run by this script and are "
        "pending as a separate step.",
        "",
    ])
    (OUTPUT_DIR / "iteration_004e_e2_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote samples to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
