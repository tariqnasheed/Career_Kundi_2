"""Final interview-pack + study-material regression audit helpers (Iteration 004E-F)."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.agents.job_search.knowledge.question_study_material import (
    count_empty_study_sections,
    study_module_fingerprint,
)
from app.agents.job_search.knowledge.study_material_budget import hard_max_violation_count
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.knowledge.source_ladder import build_source_ladder_status
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.agents.job_search.quality.silly_question_guard import is_silly_question
from app.core.config import settings
from app.agents.job_search.quality.claim_integrity import audit_pack_claim_integrity
from app.agents.job_search.quality.cross_domain_guard import audit_cross_domain_contamination
from app.agents.job_search.quality.surface_quality_guard import audit_pack_surface_quality
from app.agents.job_search.quality.user_facing_text import iter_user_facing_text
from app.tools.document_export import build_interview_pack_markdown

_URL_RE = re.compile(r"https?://", re.I)
_INTERNAL_LABEL_RE = re.compile(r"\bRole Specific\b")
_PLACEHOLDER_URL_RE = re.compile(r"fake-url|example\.invalid|placeholder-url", re.I)

# Fixed cross-sector regression roles (deterministic).
FIXED_CROSS_SECTOR_CASES: list[dict[str, Any]] = [
    {
        "sample": "Data Analyst",
        "role": "Data Analyst",
        "input_type": "rich_description",
        "focus": ["SQL", "Dashboarding"],
        "job": {
            "title": "Data Analyst",
            "company_name": "Acme Analytics",
            "description_raw": "SQL dashboards, KPI reporting, and stakeholder communication.",
            "responsibilities": ["SQL dashboard creation", "Data quality checks"],
            "requirements": ["SQL", "Excel", "Stakeholder communication"],
            "extracted_skills": [{"skill": "SQL"}, {"skill": "Excel"}, {"skill": "Dashboarding"}],
        },
    },
    {
        "sample": "Electrical Engineer",
        "role": "Electrical Engineer",
        "input_type": "rich_responsibilities_tools",
        "focus": ["Cable Sizing", "Load Calculations"],
        "job": {
            "title": "Electrical Engineer",
            "description_raw": "LV distribution, cable sizing, and commissioning.",
            "responsibilities": ["Load calculations", "Cable sizing", "Testing and commissioning"],
            "requirements": ["Electrical installation", "Standards compliance"],
            "extracted_skills": [{"skill": "Cable Sizing"}, {"skill": "Load Calculations"}, {"skill": "Commissioning"}],
        },
    },
    {
        "sample": "Clinical Pharmacist",
        "role": "Clinical Pharmacist",
        "input_type": "rich_healthcare",
        "focus": ["Medication Review", "Pharmacology"],
        "job": {
            "title": "Clinical Pharmacist",
            "description_raw": "Medication review and prescribing safety in hospital wards.",
            "responsibilities": ["Medication review", "Patient counselling", "Clinical governance"],
            "requirements": ["Pharmacology", "Prescribing safety"],
            "extracted_skills": [{"skill": "Pharmacology"}, {"skill": "Medication Review"}, {"skill": "Clinical Governance"}],
        },
    },
    {
        "sample": "Barista",
        "role": "Barista",
        "input_type": "document_library",
        "focus": ["Coffee Preparation", "HACCP"],
        "job": {
            "title": "Barista",
            "company_name": "Harbour Cafe",
            "description_raw": "Espresso preparation and rush-hour service.",
            "responsibilities": ["Espresso preparation", "HACCP hygiene controls"],
            "requirements": ["Coffee preparation", "Customer service"],
            "extracted_skills": [{"skill": "Coffee Preparation"}, {"skill": "HACCP"}],
        },
    },
    {
        "sample": "Teaching Assistant",
        "role": "Teaching Assistant",
        "input_type": "education",
        "focus": ["Classroom Support", "Safeguarding"],
        "job": {
            "title": "Teaching Assistant",
            "description_raw": "Support classroom learning and pupil safeguarding.",
            "responsibilities": ["Classroom support", "Learning differentiation", "Safeguarding awareness"],
            "requirements": ["Communication", "Safeguarding"],
            "extracted_skills": [{"skill": "Classroom Support"}, {"skill": "Safeguarding"}],
        },
    },
    {
        "sample": "Financial Analyst",
        "role": "Financial Analyst",
        "input_type": "finance",
        "focus": ["Financial Modelling", "Excel"],
        "job": {
            "title": "Financial Analyst",
            "description_raw": "Forecasting, variance analysis, and board reporting.",
            "responsibilities": ["Financial modelling", "Variance analysis", "Board reporting"],
            "requirements": ["Excel", "Financial modelling"],
            "extracted_skills": [{"skill": "Financial Modelling"}, {"skill": "Excel"}],
        },
    },
    {
        "sample": "DevOps Engineer",
        "role": "DevOps Engineer",
        "input_type": "technical",
        "focus": ["AWS", "CI/CD"],
        "job": {
            "title": "DevOps Engineer",
            "description_raw": "AWS infrastructure automation and CI/CD pipelines.",
            "responsibilities": ["CI/CD pipeline maintenance", "Infrastructure automation"],
            "requirements": ["AWS", "Docker", "Kubernetes"],
            "extracted_skills": [{"skill": "AWS"}, {"skill": "CI/CD"}, {"skill": "Docker"}],
        },
    },
    {
        "sample": "MEP Site Engineer",
        "role": "MEP Site Engineer",
        "input_type": "construction",
        "focus": ["MEP Coordination", "Site Supervision"],
        "job": {
            "title": "MEP Site Engineer",
            "description_raw": "Coordinate mechanical, electrical, and plumbing packages on site.",
            "responsibilities": ["MEP coordination", "Site supervision", "Snagging and handover"],
            "requirements": ["MEP systems", "Site coordination"],
            "extracted_skills": [{"skill": "MEP Coordination"}, {"skill": "Site Supervision"}],
        },
    },
    {
        "sample": "Social Media Creator",
        "role": "Social Media Creator",
        "input_type": "creative_odd_job",
        "focus": ["Content Planning", "Video Editing"],
        "job": {
            "title": "Social Media Creator",
            "description_raw": "Short-form video content and brand storytelling.",
            "responsibilities": ["Content planning", "Video editing", "Community engagement"],
            "requirements": ["Video editing", "Content strategy"],
            "extracted_skills": [{"skill": "Video Editing"}, {"skill": "Content Planning"}],
        },
    },
    {
        "sample": "Delivery Driver",
        "role": "Delivery Driver",
        "input_type": "part_time_odd_job",
        "focus": ["Route Planning", "Customer Service"],
        "job": {
            "title": "Delivery Driver",
            "description_raw": "Last-mile delivery and customer handoffs.",
            "responsibilities": ["Route planning", "Safe driving", "Proof of delivery"],
            "requirements": ["Driving licence", "Customer service"],
            "extracted_skills": [{"skill": "Route Planning"}, {"skill": "Customer Service"}],
        },
    },
]

DETERMINISTIC_RANDOM_ROLES: list[dict[str, Any]] = [
    {
        "sample": "Lab Technician",
        "role": "Lab Technician",
        "input_type": "science",
        "focus": ["Sample Processing", "Lab Safety"],
        "job": {
            "title": "Lab Technician",
            "description_raw": "Process lab samples and maintain safety records.",
            "responsibilities": ["Sample processing", "Equipment calibration", "Lab safety checks"],
            "requirements": ["Lab safety", "Sample handling"],
            "extracted_skills": [{"skill": "Sample Processing"}, {"skill": "Lab Safety"}],
        },
    },
    {
        "sample": "Logistics Coordinator",
        "role": "Logistics Coordinator",
        "input_type": "office_business",
        "focus": ["Inventory Control", "Scheduling"],
        "job": {
            "title": "Logistics Coordinator",
            "description_raw": "Coordinate inbound/outbound shipments and inventory.",
            "responsibilities": ["Shipment scheduling", "Inventory control", "Carrier coordination"],
            "requirements": ["Scheduling", "Inventory control"],
            "extracted_skills": [{"skill": "Inventory Control"}, {"skill": "Scheduling"}],
        },
    },
    {
        "sample": "HR Assistant",
        "role": "HR Assistant",
        "input_type": "office_business",
        "focus": ["Onboarding", "HR Administration"],
        "job": {
            "title": "HR Assistant",
            "description_raw": "Support onboarding, records, and employee queries.",
            "responsibilities": ["Employee onboarding", "HR records", "Query triage"],
            "requirements": ["HR administration", "Communication"],
            "extracted_skills": [{"skill": "Onboarding"}, {"skill": "HR Administration"}],
        },
    },
    {
        "sample": "Graphic Designer",
        "role": "Graphic Designer",
        "input_type": "creative",
        "focus": ["Brand Design", "Adobe Creative Suite"],
        "job": {
            "title": "Graphic Designer",
            "description_raw": "Brand assets, social creatives, and campaign visuals.",
            "responsibilities": ["Brand design", "Campaign visuals", "Client revisions"],
            "requirements": ["Adobe Creative Suite", "Brand design"],
            "extracted_skills": [{"skill": "Brand Design"}, {"skill": "Adobe Creative Suite"}],
        },
    },
    {
        "sample": "Warehouse Picker",
        "role": "Warehouse Picker",
        "input_type": "part_time_odd_job",
        "focus": ["Order Picking", "Stock Control"],
        "job": {
            "title": "Warehouse Picker",
            "description_raw": "Pick and pack orders accurately during peak shifts.",
            "responsibilities": ["Order picking", "Stock rotation", "Packing accuracy"],
            "requirements": ["Order picking", "Attention to detail"],
            "extracted_skills": [{"skill": "Order Picking"}, {"skill": "Stock Control"}],
        },
    },
]


def exportable_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [q for q in questions if q.get("model_answer") and not q.get("export_blocked")]


def audit_intent_depth_consistency(questions: list[dict[str, Any]]) -> dict[str, int]:
    """Detect motivation/HR intent paired with incompatible technical study depth."""
    from app.agents.job_search.knowledge.study_material_budget import is_intent_depth_mismatch

    return {
        "intent_depth_mismatch_count": sum(
            1 for q in questions if is_intent_depth_mismatch(q)
        )
    }


def audit_question_study_alignment(questions: list[dict[str, Any]], job: dict[str, Any] | None = None) -> dict[str, int]:
    """Detect role-fit questions whose study application still teaches technical workflow."""
    from app.agents.job_search.knowledge.study_material_budget import is_question_study_alignment_failure

    if job:
        questions = [{**q, "_audit_job": job} for q in questions]
    return {
        "question_study_alignment_failure_count": sum(
            1 for q in questions if is_question_study_alignment_failure(q)
        )
    }


def _content_blob(questions: list[dict[str, Any]], pack_md: str = "") -> str:
    parts = [pack_md]
    for q in questions:
        parts.append(q.get("question") or "")
        parts.append(q.get("model_answer") or "")
        study = q.get("study_material") or {}
        for value in study.values():
            if isinstance(value, str):
                parts.append(value)
            elif isinstance(value, list):
                parts.extend(str(v) for v in value if v)
            elif isinstance(value, dict):
                parts.append(str(value))
    return " ".join(parts)


def audit_generated_pack(
    job: dict[str, Any],
    *,
    focus_areas: list[str],
    difficulty: str = "mid",
    role_label: str | None = None,
    input_type: str = "rich",
    sample_name: str | None = None,
) -> dict[str, Any]:
    """Generate a pack and return deterministic regression metrics.

    Each audited pack simulates an INDEPENDENT production request, so the global
    cross-role fingerprint registry is cleared first. Without this, auditing many
    packs in sequence lets one pack's fingerprints perturb the next (extra
    "In this role-specific case" suffixes, shifted dedupe), making saturation and
    other artifact metrics order-dependent rather than a true per-pack signal.
    """
    from app.agents.job_search import mock_data as _mock_data

    _mock_data._GLOBAL_QUESTION_FINGERPRINTS.clear()
    questions = mock_generate_questions(job, focus_areas=focus_areas, difficulty=difficulty)
    exportable = exportable_questions(questions)
    pack_md = build_interview_pack_markdown(
        job_title=job.get("title") or role_label or "Role",
        company_name=job.get("company_name"),
        questions=exportable,
    )
    blob = _content_blob(exportable, pack_md)
    studies = [q.get("study_material") or {} for q in exportable]
    fingerprints = [
        study_module_fingerprint(s, q.get("question") or "") for q, s in zip(exportable, studies)
    ]
    dup_count = sum(c - 1 for c in Counter(fingerprints).values() if c > 1)
    missing_answers = sum(1 for q in exportable if not (q.get("model_answer") or "").strip())
    missing_study = sum(1 for q in exportable if not (q.get("study_material") or {}))
    empty_sections = sum(count_empty_study_sections(s) for s in studies)
    hard_max_violations = sum(hard_max_violation_count(s) for s in studies)
    missing_study_depth = sum(1 for s in studies if not s.get("study_depth"))
    _DEEP = {"practical_workflow", "complex_scenario", "advanced_multi_step"}
    structure_incomplete = sum(
        1 for s in studies if s.get("budget_status") in {"structure_incomplete", "hard_limit_exceeded"}
    )
    substantive_depth_failures = 0
    for s in studies:
        cov = s.get("substantive_contract_coverage")
        if cov is None:
            continue
        floor = 0.9 if s.get("study_depth") in _DEEP else 0.85
        try:
            if float(cov) < floor:
                substantive_depth_failures += 1
        except (TypeError, ValueError):
            pass
    answers_over_limit = sum(
        1 for q in exportable if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS
    )
    silly_hits = sum(1 for q in exportable if is_silly_question(q.get("question", "")))
    audit = job.get("coverage_audit") or {}
    ladder = (job.get("source_ladder") or {}).get("source_status") or build_source_ladder_status(job)
    export_ready = "### Study material" in pack_md and "### Model answer" in pack_md
    per_question_export = pack_md.count("### Study material") >= max(1, len(exportable))
    role = role_label or job.get("title") or "Role"
    claim_metrics = audit_pack_claim_integrity(exportable, job)
    surface_metrics = audit_pack_surface_quality(exportable, role=role)
    cross_domain_hits = 0
    for q in exportable:
        blob = "\n".join(iter_user_facing_text(q))
        cross_domain_hits += audit_cross_domain_contamination(
            blob,
            role=role,
            skill=str(q.get("skill_tag") or ""),
            job=job,
        )["cross_domain_contamination_hits"]
    intent_depth_metrics = audit_intent_depth_consistency(exportable)
    study_alignment_metrics = audit_question_study_alignment(exportable, job)
    from app.agents.job_search.quality.question_obligation_coverage_audit import audit_question_obligations

    obligation_metrics = audit_question_obligations(exportable, job)

    # Artifact-level false-green hardening audits (Defect Classes B, D, F).
    from app.agents.job_search.quality.cross_skill_alignment_audit import (
        audit_cross_skill_answer_alignment,
    )
    from app.agents.job_search.quality.template_saturation_audit import audit_template_saturation
    from app.agents.job_search.quality.terminology_integrity_audit import (
        audit_terminology_integrity,
    )

    terminology_metrics = audit_terminology_integrity(exportable)
    cross_skill_metrics = audit_cross_skill_answer_alignment(exportable, job)
    _pack_skills = list(focus_areas or []) + [
        str(s.get("skill") if isinstance(s, dict) else s)
        for s in (job.get("extracted_skills") or [])
    ]
    template_metrics = audit_template_saturation(exportable, role=role, skills=_pack_skills)

    return {
        "sample": sample_name or role_label or job.get("title"),
        "role": role_label or job.get("title"),
        "input_type": input_type,
        "question_count": len(exportable),
        "answer_count": len(exportable) - missing_answers,
        "study_module_count": len(studies) - missing_study,
        "missing_answer_count": missing_answers,
        "missing_study_module_count": missing_study,
        "coverage_score": audit.get("coverage_score", "N/A"),
        "source_ladder_present": bool(ladder),
        "export_ready": export_ready and per_question_export,
        "fake_url_hits": len(_URL_RE.findall(blob)) + len(_PLACEHOLDER_URL_RE.findall(blob)),
        "generic_phrase_hits": export_blocked_phrase_count(blob),
        "silly_question_hits": silly_hits,
        "empty_section_count": empty_sections,
        "hard_max_violation_count": hard_max_violations,
        "missing_study_depth_count": missing_study_depth,
        "answers_over_limit_count": answers_over_limit,
        "duplicate_study_module_count": dup_count,
        "internal_label_leak_count": len(_INTERNAL_LABEL_RE.findall(blob)),
        "unsupported_personal_claim_count": claim_metrics["unsupported_personal_claim_count"],
        "unsupported_numeric_claim_count": claim_metrics["unsupported_numeric_claim_count"],
        "thin_input_specificity_violation_count": claim_metrics["thin_input_specificity_violation_count"],
        "cross_domain_contamination_hits": cross_domain_hits,
        "surface_quality_defect_count": surface_metrics["total_surface_quality_defects"],
        "structure_incomplete_count": structure_incomplete,
        "substantive_depth_failure_count": substantive_depth_failures,
        "intent_depth_mismatch_count": intent_depth_metrics["intent_depth_mismatch_count"],
        "question_study_alignment_failure_count": study_alignment_metrics[
            "question_study_alignment_failure_count"
        ],
        "terminology_integrity_failure_count": terminology_metrics[
            "terminology_integrity_failure_count"
        ],
        "cross_skill_answer_contamination_failure_count": cross_skill_metrics[
            "cross_skill_answer_contamination_failure_count"
        ],
        "generic_template_saturation_failure_count": template_metrics[
            "generic_template_saturation_failure_count"
        ],
        **obligation_metrics,
        "model_knowledge_disabled": not settings.job_search_enable_model_knowledge,
        "questions": exportable,
        "pack_markdown": pack_md,
        "job": job,
    }


# --- Canonical clean/fail derivation (§11) --------------------------------
#
# This is the SINGLE authoritative list of numeric metric keys whose non-zero
# value means a pack is not clean. Tests, sample generators, and report writers
# MUST derive "clean" from `pack_failure_reasons` / `metrics_are_clean` below so
# they can never drift into independent, weaker definitions.
CANONICAL_FAILURE_METRIC_KEYS: tuple[str, ...] = (
    "missing_answer_count",
    "missing_study_module_count",
    "fake_url_hits",
    "generic_phrase_hits",
    "silly_question_hits",
    "empty_section_count",
    "hard_max_violation_count",
    "missing_study_depth_count",
    "answers_over_limit_count",
    "duplicate_study_module_count",
    "internal_label_leak_count",
    "unsupported_personal_claim_count",
    "unsupported_numeric_claim_count",
    "cross_domain_contamination_hits",
    "surface_quality_defect_count",
    "thin_input_specificity_violation_count",
    "structure_incomplete_count",
    "substantive_depth_failure_count",
    "intent_depth_mismatch_count",
    "question_study_alignment_failure_count",
    "synthetic_overload_failure_count",
    "answer_obligation_coverage_failure_count",
    "study_obligation_coverage_failure_count",
    "pure_motivation_technical_dominance_failure_count",
    # Artifact-level false-green hardening (Defect Classes B, D, F).
    "terminology_integrity_failure_count",
    "cross_skill_answer_contamination_failure_count",
    "generic_template_saturation_failure_count",
)


def pack_failure_reasons(
    metrics: dict[str, Any], *, allow_thin_coverage: bool = False
) -> list[str]:
    """Return the canonical list of reasons a pack is not clean (empty == clean).

    This is the one derivation consumed by ``metrics_are_clean`` (below), the
    E2/F sample generators, and the regression tests. Adding a new final-gate
    field here immediately, consistently tightens every consumer.
    """
    reasons: list[str] = []
    for key in CANONICAL_FAILURE_METRIC_KEYS:
        value = metrics.get(key, 0) or 0
        try:
            if int(value) != 0:
                reasons.append(key)
        except (TypeError, ValueError):
            if value:
                reasons.append(key)
    if not metrics.get("source_ladder_present", True):
        reasons.append("source_ladder_missing")
    if not metrics.get("export_ready", True):
        reasons.append("not_export_ready")
    if metrics.get("question_count", 1) < 1:
        reasons.append("no_questions")
    if allow_thin_coverage:
        score = metrics.get("coverage_score", 0)
        if score not in (0, "N/A", "0") and score not in (None, ""):
            try:
                if int(score) > 0:
                    reasons.append("thin_coverage_nonzero")
            except (TypeError, ValueError):
                pass
    return reasons


def metrics_are_clean(metrics: dict[str, Any], *, allow_thin_coverage: bool = False) -> bool:
    return not pack_failure_reasons(metrics, allow_thin_coverage=allow_thin_coverage)
