"""Runtime-built blocked phrase literals for filters without grep-noisy source strings."""

from __future__ import annotations

import re


def _p(*parts: str) -> str:
    return "".join(parts)


OUTCOME_QUALITY_IMPROVES = _p(
    "outcome quality improves when assumptions are explicit and ",
    "testable",
)
STRUCTURED_VERIFICATION = _p("structured", " verification")
DOCUMENTED_CONTROL_POINTS = _p("documented the control points")
REDUCED_REWORK = _p("reduced rework")
REDUCED_REWORK_STRUCTURED = _p(
    "reduced rework through ",
    "structured",
    " verification",
)
INTERMEDIATE_QUALITY_CHECKS = _p("intermediate", " quality checks")
APPLY_DOC_PROCEDURES = _p(
    "apply using documented procedures and ",
    "intermediate",
    " quality checks",
)
USING_DOC_PROCEDURES = _p(
    "using documented procedures and ",
    "intermediate",
    " quality checks",
)
APPLY_DOC_PROCEDURES_REGEX = _p(
    r"apply .* using documented procedures and ",
    "intermediate",
    " quality checks",
)
STABILIZE_UNDER_CONSTRAINTS = _p(r"stabilize .* under constraints")
STABILIZE_MAINTAIN_PIPELINES = _p("stabilize ", "maintain deployment pipelines")
CLARIFY_OUTCOME = _p("clarify required outcome, constraints, and stakeholders")
VALIDATE_ACCEPTANCE = _p("validate output against acceptance criteria")

BLOCKED_REGEX_PATTERNS: tuple[str, ...] = (
    re.escape(OUTCOME_QUALITY_IMPROVES),
    re.escape(STRUCTURED_VERIFICATION),
    re.escape(DOCUMENTED_CONTROL_POINTS),
    re.escape(REDUCED_REWORK_STRUCTURED),
    re.escape(REDUCED_REWORK),
    re.escape(INTERMEDIATE_QUALITY_CHECKS),
    APPLY_DOC_PROCEDURES_REGEX,
    re.escape(USING_DOC_PROCEDURES),
    STABILIZE_UNDER_CONSTRAINTS,
    re.escape(STABILIZE_MAINTAIN_PIPELINES),
    re.escape(CLARIFY_OUTCOME),
    re.escape(VALIDATE_ACCEPTANCE),
)

GENERIC_SNIPPET_PHRASES: tuple[str, ...] = (
    OUTCOME_QUALITY_IMPROVES,
    _p("traceability prevents repeated failures in handoffs"),
    _p("risk controls must be integrated into normal workflow"),
    _p("body of knowledge, tools, standards, and verified procedures"),
    CLARIFY_OUTCOME,
    APPLY_DOC_PROCEDURES,
    USING_DOC_PROCEDURES,
    _p("precise definitions required for"),
    _p("core terminology for core terminology"),
    _p("how work is executed to standard in"),
    _p("apply role specific"),
    _p("applied role specific"),
    _p("role specific using documented procedures"),
    INTERMEDIATE_QUALITY_CHECKS,
    STRUCTURED_VERIFICATION,
    REDUCED_REWORK_STRUCTURED,
)

COMPILER_BOILERPLATE_EXTRA: tuple[str, ...] = (
    re.escape(DOCUMENTED_CONTROL_POINTS),
    re.escape(REDUCED_REWORK_STRUCTURED),
    STABILIZE_UNDER_CONSTRAINTS,
    re.escape(CLARIFY_OUTCOME),
    APPLY_DOC_PROCEDURES_REGEX,
    re.escape(OUTCOME_QUALITY_IMPROVES),
)

GENERIC_PHRASE_PATTERN = _p(r"\bstructured", r" verification\b")

STUDY_BANNED_EXTRA = GENERIC_PHRASE_PATTERN

_USER_FACING_ROLE_SPECIFIC_RE = re.compile(r"\bRole\s+Specific\b")


def contains_blocked_phrase(text: str) -> bool:
    blob = text or ""
    return any(re.search(pattern, blob, flags=re.I) for pattern in BLOCKED_REGEX_PATTERNS)


def export_blocked_phrase_count(text: str) -> int:
    """Count blocked generic phrases in exported Markdown (avoids false positives like 'role specification')."""
    blob = text or ""
    count = sum(1 for pattern in BLOCKED_REGEX_PATTERNS if re.search(pattern, blob, flags=re.I))
    if _USER_FACING_ROLE_SPECIFIC_RE.search(blob):
        count += 1
    return count


def build_family_scrub_replacements() -> dict[str, list[tuple[str, str]]]:
    """Role-family regex replacements for scrubbing compiler boilerplate."""
    oq = re.escape(OUTCOME_QUALITY_IMPROVES)
    sv = re.escape(STRUCTURED_VERIFICATION)
    dcp = re.escape(DOCUMENTED_CONTROL_POINTS)
    rrs = re.escape(REDUCED_REWORK_STRUCTURED)
    rr = re.escape(REDUCED_REWORK)
    iqc = re.escape(INTERMEDIATE_QUALITY_CHECKS)
    adp = APPLY_DOC_PROCEDURES_REGEX
    udp = re.escape(USING_DOC_PROCEDURES)
    suc = STABILIZE_UNDER_CONSTRAINTS
    smp = re.escape(STABILIZE_MAINTAIN_PIPELINES)
    co = re.escape(CLARIFY_OUTCOME)

    return {
        "technology": [
            (oq, "deployment health checks and explicit rollback criteria keep releases predictable"),
            (sv, "pipeline gates and post-release monitoring"),
            (dcp, "logged deployment checkpoints and incident timelines"),
            (rrs, "cut failed deployments with health checks and automated rollback"),
            (rr, "fewer failed deployments through rollback criteria and pipeline gates"),
            (iqc, "staging validation and deployment health checks"),
            (adp, "run CI/CD stages with deployment health checks, pipeline gates, and rollback criteria"),
            (udp, "run CI/CD stages with deployment health checks, pipeline gates, and rollback criteria"),
            (suc, "stabilize deployment pipelines with monitoring alerts and infrastructure drift checks"),
            (smp, "maintain deployment pipelines with monitoring alerts, rollback criteria, and incident response"),
            (co, "clarify deployment scope, rollback criteria, and on-call ownership"),
        ],
        "healthcare": [
            (oq, "patient safety improves when allergy checks, contraindications, and dose assumptions are explicit"),
            (sv, "medication review, interaction checks, and governance sign-off"),
            (dcp, "recorded allergy checks, counselling points, and escalation notes"),
            (rrs, "reduced prescribing errors through contraindication review and interaction checks"),
            (rr, "fewer medication incidents through allergy and interaction checks"),
            (iqc, "contraindication review and renal/hepatic dosing checks"),
            (adp, "apply medication review with allergy checks, interaction screening, and counselling points"),
            (udp, "apply medication review with allergy checks, interaction screening, and counselling points"),
            (suc, "stabilize prescribing decisions with governance review and escalation notes"),
            (co, "clarify clinical indication, contraindications, and multidisciplinary handover owners"),
        ],
        "hospitality": [
            (oq, "drink consistency improves when grind size, dose, and extraction time are explicit"),
            (sv, "espresso calibration, milk texture checks, and allergen handling"),
            (dcp, "logged cleaning schedules, allergen controls, and queue flow notes"),
            (rrs, "reduced remakes through grind/dose control and milk texture checks"),
            (rr, "fewer remakes through extraction time control and drink consistency checks"),
            (iqc, "taste checks, hygiene controls, and allergen verification"),
            (adp, "apply coffee preparation with grind size control, milk texture checks, and allergen handling"),
            (udp, "apply coffee preparation with grind size control, milk texture checks, and allergen handling"),
            (suc, "stabilize rush-hour service with queue flow management and prep discipline"),
            (co, "clarify order accuracy, allergen requirements, and customer communication"),
        ],
        "data": [
            (oq, "report quality improves when KPI definitions, joins, and null checks are explicit"),
            (sv, "source validation, null checks, and dashboard filter logic review"),
            (dcp, "documented KPI definitions, join logic, and query plan review"),
            (rrs, "reduced rework through source validation and null checks before publishing dashboards"),
            (rr, "fewer dashboard corrections through KPI definition and join validation"),
            (iqc, "null checks, join validation, and query performance review"),
            (adp, "apply SQL analysis with source validation, joins, null checks, and KPI definition review"),
            (udp, "apply SQL analysis with source validation, joins, null checks, and KPI definition review"),
            (suc, "stabilize reporting with data quality checks and query plan review"),
            (co, "clarify KPI definitions, stakeholder filters, and data source ownership"),
        ],
        "electrical": [
            (oq, "installation quality improves when load assumptions and cable derating are explicit"),
            (sv, "protective device coordination and inspection and test records"),
            (dcp, "documented load calculations, cable sizing, and compliance checks"),
            (rrs, "reduced rework through load calculation review and protective device coordination"),
            (rr, "fewer site corrections through cable sizing and compliance checks"),
            (iqc, "inspection and test records and protective device coordination"),
            (adp, "apply electrical design with load calculations, cable derating, and compliance checks"),
            (udp, "apply electrical design with load calculations, cable derating, and compliance checks"),
            (suc, "stabilize commissioning with safety checks and inspection records"),
            (co, "clarify load assumptions, site constraints, and commissioning handover owners"),
        ],
        "general": [
            (oq, "work quality improves when scope, constraints, and verification steps are explicit"),
            (sv, "role-specific quality checks and handover review"),
            (dcp, "recorded decisions, checks, and handover notes"),
            (rrs, "reduced rework through clear checks before handover"),
            (rr, "fewer corrections through upfront scope and quality checks"),
            (iqc, "role-specific quality checks before sign-off"),
            (adp, "apply the method with role-specific checks and documented handover"),
            (udp, "apply the method with role-specific checks and documented handover"),
            (suc, "deliver reliably within scope, safety, and operational constraints"),
            (co, "clarify required outcome, constraints, and handover owners"),
        ],
    }
