"""Adaptive study-material depth and length policy (Iteration 004E-E2).

Deterministic only — no model calls. Target ranges are guidance, not quotas.
Interview answer limits remain separate (see answer_length_policy).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

StudyDepth = Literal[
    "simple_factual",
    "hr_behavioral",
    "standard_technical",
    "practical_workflow",
    "complex_scenario",
    "advanced_multi_step",
]

ComplexityLevel = Literal["low", "moderate", "high", "very_high"]

BudgetStatus = Literal[
    "concise_complete",
    "within_target",
    "above_target_but_allowed",
    "hard_limit_exceeded",
    "structure_incomplete",
]

_DEPTH_LABELS: dict[str, str] = {
    "simple_factual": "Simple factual",
    "hr_behavioral": "HR / behavioral",
    "standard_technical": "Standard technical",
    "practical_workflow": "Practical workflow",
    "complex_scenario": "Complex scenario",
    "advanced_multi_step": "Advanced multi-step",
}


@dataclass(frozen=True)
class StudyMaterialBudget:
    study_depth: StudyDepth
    target_min_words: int
    target_max_words: int
    hard_max_words: int
    complexity_level: ComplexityLevel


@dataclass
class StudyMaterialComplexitySignals:
    category: str = ""
    question_type: str = ""
    source_item_count: int = 0
    source_type_count: int = 0
    responsibility_signals: int = 0
    tool_signals: int = 0
    seniority_signals: int = 0
    scenario_signals: int = 0
    safety_signals: int = 0
    compliance_signals: int = 0
    regulation_signals: int = 0
    calculation_signals: int = 0
    troubleshooting_signals: int = 0
    system_design_signals: int = 0
    multi_step_signals: int = 0
    behavioral_signals: int = 0
    hr_signals: int = 0
    simple_factual_signals: int = 0
    job_thin: bool = False
    document_library_rich: bool = False
    company_context: bool = False
    weighted_score: int = 0
    matched_signals: list[str] = field(default_factory=list)


_BUDGETS: dict[StudyDepth, StudyMaterialBudget] = {
    "simple_factual": StudyMaterialBudget("simple_factual", 100, 250, 350, "low"),
    "hr_behavioral": StudyMaterialBudget("hr_behavioral", 150, 350, 450, "low"),
    "standard_technical": StudyMaterialBudget("standard_technical", 300, 700, 850, "moderate"),
    "practical_workflow": StudyMaterialBudget("practical_workflow", 400, 800, 950, "high"),
    "complex_scenario": StudyMaterialBudget("complex_scenario", 500, 1000, 1100, "high"),
    "advanced_multi_step": StudyMaterialBudget("advanced_multi_step", 700, 1200, 1200, "very_high"),
}

_CONTENT_TEXT_KEYS = (
    "core_idea",
    "what_this_question_tests",
    "beginner_explanation",
    "intermediate_explanation",
    "advanced_explanation",
    "interview_application",
    "practical_example",
    "worked_example",
    "practical_workflow",
    "advanced_nuance",
    "decision_points_summary",
    "compact_explanation",
    "behavioral_response_structure",
    "system_framing",
    "trade_off_analysis",
    "scenario_framing",
    "outcome_evaluation",
    "workflow_objective",
    "web_or_company_source_insight",
    "document_library_insight",
    "saved_material_insight",
    "model_insight",
    "overview",
)

_CONTENT_LIST_KEYS = (
    "key_principles",
    "step_by_step_method",
    "step_by_step_breakdown",
    "common_mistakes",
    "likely_follow_ups",
    "decision_points",
    "key_definitions",
    "workflow_checkpoints",
    "failure_modes",
    "escalation_triggers",
    "competing_constraints",
    "decision_branches",
    "verification_steps",
    "assumptions_and_dependencies",
    "staged_reasoning",
    "alternative_paths",
    "validation_and_monitoring",
    "technical_mechanisms",
    "common_misconceptions",
)

# Depth contract: required pedagogical elements (not word counts).
_DEPTH_CONTRACT: dict[StudyDepth, list[str]] = {
    "simple_factual": [
        "core_idea",
        "what_this_question_tests",
        "compact_explanation",
        "key_principles",
    ],
    "hr_behavioral": [
        "what_this_question_tests",
        "behavioral_response_structure",
        "common_mistakes",
        "interview_application",
    ],
    "standard_technical": [
        "core_idea",
        "what_this_question_tests",
        "technical_mechanisms",
        "common_misconceptions",
        "interview_application",
    ],
    "practical_workflow": [
        "workflow_objective",
        "step_by_step_method",
        "workflow_checkpoints",
        "failure_modes",
        "escalation_triggers",
    ],
    "complex_scenario": [
        "scenario_framing",
        "competing_constraints",
        "decision_branches",
        "verification_steps",
        "outcome_evaluation",
    ],
    "advanced_multi_step": [
        "system_framing",
        "assumptions_and_dependencies",
        "staged_reasoning",
        "trade_off_analysis",
        "validation_and_monitoring",
    ],
}

# §9: thin / title-only input preserves the semantic *category* but is legitimately
# shaped into a compact, conservative module (deep scenario/workflow richness cannot
# be grounded without source material and must not be invented). Such a module is
# therefore evaluated against the compact contract it is designed to fulfil, not the
# full deep contract — this scales the "target length within a semantically
# appropriate range" (§9) rather than lowering the deep floor to game metrics (§16).
_THIN_DEPTH_CONTRACT: list[str] = [
    "what_this_question_tests",
    "compact_explanation",
    "key_principles",
    "common_mistakes",
    "interview_application",
]

# Shallow depths should stay well below hard max (ceiling is emergency only).
_SHALLOW_TARGET_CEILING_RATIO = 0.72
_THIN_INPUT_WORD_CEILING = 220

_SENIOR_MARKERS = ("senior", "lead", "principal", "head of", "chief", "architect", "staff")
_SCENARIO_MARKERS = ("scenario", "case study", "what would you do if", "hypothetical", "incident")
_SAFETY_MARKERS = ("safety-critical", "patient safety", "hazard", "risk assessment", "safe isolation")
_COMPLIANCE_MARKERS = ("compliance", "governance", "audit", "haccp", "safeguarding")
_REGULATION_MARKERS = ("regulation", "standard", "bs ", "iso ", "legislation", "prescribing")
_CALC_MARKERS = ("calculate", "calculation", "dose", "sizing", "load calculation")
_TROUBLESHOOT_MARKERS = ("troubleshoot", "diagnose", "debug", "root cause", "fault finding")
_SYSTEM_DESIGN_MARKERS = (
    "system design",
    "architecture",
    "trade-off",
    "trade off",
    "multi-domain",
    "integration design",
    "scalability",
)
_MULTI_STEP_MARKERS = ("step by step", "multi-stage", "first you", "then you", "workflow", "pipeline")
_TOOL_MARKERS = ("tool", "platform", "software", "using ", "configure", "deploy")
_BEHAVIORAL_MARKERS = ("tell me about a time", "describe a situation", "give an example", "star")
_HR_MARKERS = ("why this role", "why us", "motivat", "strength", "weakness", "teamwork", "conflict")
_SIMPLE_MARKERS = ("what is ", "what are ", "define ", "explain what", "basic role")
# Role-fit / motivation phrasings that keep a question semantically motivation/HR
# even when it also mentions standards/compliance/safety words (§9/§10).
_MOTIVATION_MARKERS = (
    "excites you",
    "why do you want",
    "why are you interested",
    "interested in this role",
    "interested in working",
    "fit for this",
    "a good fit",
    "your experience help",
    "experience help",
    "want to work here",
    "want to join",
    "contribute to",
    "drawn to",
    "attracts you",
    "career goal",
    "development direction",
    "what do you know about",
)
_MOTIVATION_FIT_ARCHETYPES = frozenset({"motivation", "company_research", "behavioral", "hr"})
_INCOMPATIBLE_MOTIVATION_DEPTHS = frozenset(
    {"standard_technical", "practical_workflow", "complex_scenario", "advanced_multi_step"}
)


def question_has_motivation_fit_archetype(question: dict[str, Any]) -> bool:
    """Match answer-routing archetype detection for motivation/HR semantics."""
    from app.agents.job_search.knowledge.content_engine import _question_archetype

    category = question.get("category") or ""
    archetype = _question_archetype(question.get("question") or "", category, question)
    return archetype in _MOTIVATION_FIT_ARCHETYPES


def question_has_role_fit_study_archetype(
    question: dict[str, Any], job: dict[str, Any] | None = None
) -> bool:
    """Pure motivation/company-fit questions whose study module must teach fit, not workflow."""
    from app.agents.job_search.knowledge.question_obligations import (
        get_question_obligation_profile,
        is_role_fit_study_profile,
    )

    profile = get_question_obligation_profile(question, job)
    return is_role_fit_study_profile(profile)


def question_has_hybrid_obligation_study(question: dict[str, Any], job: dict[str, Any]) -> bool:
    from app.agents.job_search.knowledge.question_obligations import get_question_obligation_profile

    profile = get_question_obligation_profile(question, job)
    return profile.is_hybrid and not question_has_role_fit_study_archetype(question, job)


def _role_fit_context(job: dict[str, Any]) -> tuple[str, str]:
    role = job.get("title") or "this role"
    # Neutral fallback — never claim a posting "listed duties" it did not
    # actually capture (Defect Class E).
    resp = (job.get("responsibilities") or ["the core work of the role"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    return role, str(resp or "the core work of the role")


def build_role_fit_apply_steps(question: dict[str, Any], job: dict[str, Any]) -> list[str]:
    role, resp = _role_fit_context(job)
    return [
        f"Quote one responsibility from the {role} posting that genuinely interests you.",
        "Explain why that duty connects to your strengths or development goals — use real experience only if you have it.",
        f"Name how you could contribute in work centred on {resp.lower()} from the first months.",
    ]


def build_role_fit_interview_application(question: dict[str, Any], job: dict[str, Any]) -> str:
    role, resp = _role_fit_context(job)
    return (
        f"Keep your answer focused on why this {role} posting attracts you: cite specific duties "
        f"such as {resp.lower()}, connect them to genuine interests or skills you want to deepen, "
        f"and state what you hope to contribute — not a technical procedure."
    )


_MOTIVATION_STUDY_ANCHORS = (
    "interested in this",
    "why you want",
    "motivated",
    "attracts you",
    "drawn to",
    "fit for",
    "contribute",
    "posting centres",
    "posting centers",
    "why this role",
    "genuinely interests",
    "hope to contribute",
)
_TECH_PROCEDURE_DOMINANCE_MARKERS = (
    "confirm safe isolation",
    "demand factor",
    "design current",
    "interpret calculation",
    "establish the connected load",
    "validation checkpoint",
    "checks you would run",
    "your method, checks",
    "state the goal, your method",
    "validation checks and expected outcome",
)


def motivation_study_application_blob(study: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("step_by_step_method", "worked_example", "practical_example", "interview_application"):
        value = study.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value if item)
        elif value:
            parts.append(str(value))
    return " ".join(parts).lower()


def shape_hybrid_obligation_study_application(
    study: dict[str, Any],
    question: dict[str, Any],
    job: dict[str, Any],
) -> dict[str, Any]:
    """Teach each required hybrid obligation without collapsing to generic STAR only."""
    from app.agents.job_search.knowledge.question_obligations import Obligation, get_question_obligation_profile

    profile = get_question_obligation_profile(question, job)
    out = dict(study)
    obs = set(profile.obligations)
    apply_steps: list[str] = []
    if Obligation.MOTIVATION_FIT.value in obs or Obligation.COMPANY_FIT.value in obs:
        apply_steps.extend(build_role_fit_apply_steps(question, job))
    if Obligation.TECHNICAL_METHOD.value in obs:
        skill = question.get("mapped_skill") or question.get("skill_tag") or _role_fit_context(job)[1]
        apply_steps.append(f"Explain your {skill} method with concrete checks before handoff.")
        apply_steps.append("Name one realistic failure mode your checks would catch.")
    if Obligation.CONTRIBUTION.value in obs:
        apply_steps.append("State what you would contribute in the first months with realistic scope.")
    if Obligation.STRENGTHS.value in obs:
        apply_steps.append("Name two relevant strengths and tie each to a posting duty.")
    if Obligation.SCENARIO_REASONING.value in obs:
        apply_steps.append("Walk through how you would handle the stated constraints and escalation path.")
    out["step_by_step_method"] = apply_steps[:6]
    out["interview_application"] = (
        "Cover every part of the question: "
        + ", ".join(o.replace("_", " ") for o in profile.obligations if o in obs)
        + ". Do not answer with motivation alone when the question also asks for method or contribution."
    )
    out["behavioral_response_structure"] = (
        "Use a short structure per obligation: motivation/fit, then method/contribution/scenario as asked."
    )
    return out


def is_question_study_alignment_failure(question: dict[str, Any]) -> bool:
    """True when study application surfaces fail obligation contract."""
    from app.agents.job_search.quality.question_obligation_coverage_audit import (
        evaluate_study_obligation_coverage,
    )

    job = question.get("_audit_job")
    if question_has_hybrid_obligation_study(question, job or {}):
        return not evaluate_study_obligation_coverage(question, job)["passed"]
    if not question_has_role_fit_study_archetype(question):
        return False
    blob = motivation_study_application_blob(question.get("study_material") or {})
    if not blob.strip():
        return True
    has_anchor = any(anchor in blob for anchor in _MOTIVATION_STUDY_ANCHORS)
    tech_dominant = any(marker in blob for marker in _TECH_PROCEDURE_DOMINANCE_MARKERS)
    return (not has_anchor) or tech_dominant


def shape_role_fit_study_application(
    study: dict[str, Any],
    question: dict[str, Any],
    job: dict[str, Any],
) -> dict[str, Any]:
    """Strip technical workflow leakage and install motivation/fit application guidance."""
    out = dict(study)
    for key in (
        "worked_example",
        "practical_example",
        "step_by_step_breakdown",
        "technical_mechanisms",
        "key_terms",
        "skill_explanations",
        "practical_workflow",
        "beginner_explanation",
        "intermediate_explanation",
        "advanced_explanation",
    ):
        out.pop(key, None)
    out["step_by_step_method"] = build_role_fit_apply_steps(question, job)
    out["interview_application"] = build_role_fit_interview_application(question, job)
    return out


def is_intent_depth_mismatch(question: dict[str, Any]) -> bool:
    """True when pure motivation intent resolves to incompatible technical study depth."""
    from app.agents.job_search.knowledge.question_obligations import (
        Obligation,
        get_question_obligation_profile,
        is_pure_motivation_profile,
    )

    profile = get_question_obligation_profile(question)
    if Obligation.MOTIVATION_FIT.value not in profile.obligations:
        return False
    if not is_pure_motivation_profile(profile):
        return False
    depth = (question.get("study_material") or {}).get("study_depth")
    return depth in _INCOMPATIBLE_MOTIVATION_DEPTHS
# Signals that a question genuinely asks for case/scenario analysis (so it may be a
# real complex scenario rather than a motivation/fit question).
_SCENARIO_REQUEST_MARKERS = (
    "walk through",
    "scenario",
    "case study",
    "a case where",
    "handle a situation where",
    "what would you do if",
    "step through",
)


def count_words(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def _blob(question: dict[str, Any]) -> str:
    return " ".join(
        [
            str(question.get("question") or ""),
            str(question.get("skill_tag") or ""),
            str(question.get("category") or ""),
            str(question.get("question_type") or ""),
        ]
    ).lower()


def is_job_thin(job: dict[str, Any]) -> bool:
    if job.get("job_posting_extraction") or job.get("company_research"):
        return False
    if (job.get("responsibilities") or []) or (job.get("requirements") or []):
        return False
    if (job.get("extracted_skills") or []) or (job.get("description_raw") or "").strip():
        return False
    return bool((job.get("title") or "").strip())


def collect_complexity_signals(question: dict[str, Any], job: dict[str, Any]) -> StudyMaterialComplexitySignals:
    qtext = _blob(question)
    signals = StudyMaterialComplexitySignals(
        category=(question.get("category") or "").lower(),
        question_type=(question.get("question_type") or "").lower(),
        source_item_count=len(question.get("question_source_items") or []),
        source_type_count=len(question.get("question_source_types") or []),
        job_thin=is_job_thin(job),
    )
    study = question.get("study_material") or {}
    if study.get("document_library_insight") or study.get("saved_material_insight"):
        signals.document_library_rich = True
    if question.get("question_source_types") and (
        "company_research" in (question.get("question_source_types") or [])
        or "user_company_profile" in (question.get("question_source_types") or [])
    ):
        signals.company_context = True

    def _mark(attr: str, label: str, patterns: tuple[str, ...], weight: int = 1) -> None:
        hits = sum(1 for p in patterns if p in qtext)
        if hits:
            setattr(signals, attr, getattr(signals, attr) + hits * weight)
            signals.matched_signals.append(label)

    _mark("behavioral_signals", "behavioral", _BEHAVIORAL_MARKERS, 2)
    _mark("hr_signals", "hr", _HR_MARKERS, 2)
    _mark("simple_factual_signals", "simple_factual", _SIMPLE_MARKERS, 2)
    _mark("scenario_signals", "scenario", _SCENARIO_MARKERS, 2)
    _mark("safety_signals", "safety", _SAFETY_MARKERS, 2)
    _mark("compliance_signals", "compliance", _COMPLIANCE_MARKERS, 2)
    _mark("regulation_signals", "regulation", _REGULATION_MARKERS, 2)
    _mark("calculation_signals", "calculation", _CALC_MARKERS, 2)
    _mark("troubleshooting_signals", "troubleshooting", _TROUBLESHOOT_MARKERS, 2)
    _mark("system_design_signals", "system_design", _SYSTEM_DESIGN_MARKERS, 3)
    _mark("multi_step_signals", "multi_step", _MULTI_STEP_MARKERS, 1)
    _mark("tool_signals", "tool", _TOOL_MARKERS, 1)

    title = (job.get("title") or "").lower()
    if any(m in title for m in _SENIOR_MARKERS):
        signals.seniority_signals += 2
        signals.matched_signals.append("senior_title")

    if signals.category in {"hr", "behavioral", "motivation"}:
        signals.hr_signals += 2
        signals.behavioral_signals += 1
    if signals.category in {"technical", "role_specific"}:
        signals.tool_signals += 1
    if signals.question_type in {"tool_usage", "tool", "responsibility"}:
        signals.tool_signals += 2
        signals.responsibility_signals += 1

    if signals.source_item_count >= 2:
        signals.matched_signals.append("multiple_sources")
    if signals.source_item_count >= 4:
        signals.weighted_score += 1

    signals.responsibility_signals += min(2, signals.source_item_count // 2)
    signals.weighted_score = (
        signals.behavioral_signals
        + signals.hr_signals
        + signals.simple_factual_signals
        + signals.scenario_signals
        + signals.safety_signals
        + signals.compliance_signals
        + signals.regulation_signals
        + signals.calculation_signals
        + signals.troubleshooting_signals
        + signals.system_design_signals * 2
        + signals.multi_step_signals
        + signals.tool_signals
        + signals.seniority_signals
        + min(3, signals.source_item_count)
        + (2 if signals.document_library_rich else 0)
        + (1 if signals.company_context else 0)
    )
    return signals


def classify_study_material_depth(
    question: dict[str, Any],
    job: dict[str, Any],
    signals: StudyMaterialComplexitySignals | None = None,
) -> StudyDepth:
    sig = signals or collect_complexity_signals(question, job)
    qtext = _blob(question)

    def _hybrid_technical_for_depth(profile) -> bool:
        obs = set(profile.obligations)
        category = (question.get("category") or "").lower()
        qtype = (question.get("question_type") or "").lower()
        if category == "behavioral" or qtype == "behavioral":
            return Obligation.TECHNICAL_METHOD.value in obs
        return (
            Obligation.TECHNICAL_METHOD.value in obs
            or Obligation.SCENARIO_REASONING.value in obs
        )

    # Advanced: needs strong multi-signal evidence, not title alone.
    advanced_score = (
        sig.system_design_signals * 3
        + sig.multi_step_signals
        + sig.seniority_signals
        + sig.troubleshooting_signals
        + min(2, sig.source_item_count // 3)
    )
    if advanced_score >= 8 and sig.system_design_signals >= 1 and not sig.job_thin:
        return "advanced_multi_step"
    if advanced_score >= 10 and sig.seniority_signals >= 2 and sig.troubleshooting_signals >= 1:
        return "advanced_multi_step"

    # Motivation / role-fit dominance (§9 Problem A): a motivation/fit/behavioral
    # question stays hr_behavioral even when it mentions standards / protocol /
    # compliance / safety, UNLESS it genuinely asks for case/scenario analysis.
    # Hybrid obligation questions with technical method or scenario keep technical depth.
    from app.agents.job_search.knowledge.question_obligations import Obligation, get_question_obligation_profile

    profile = get_question_obligation_profile(question, job)
    hybrid_technical = _hybrid_technical_for_depth(profile)
    motivation_dominant = (
        not hybrid_technical
        and (
            sig.category in {"hr", "behavioral", "motivation"}
            or sig.question_type == "motivation"
            or sig.hr_signals >= 2
            or sig.behavioral_signals >= 2
            or any(m in qtext for m in _MOTIVATION_MARKERS)
            or question_has_motivation_fit_archetype(question)
        )
    )
    genuine_scenario_request = (
        sig.scenario_signals >= 1
        or sig.system_design_signals >= 1
        or any(m in qtext for m in _SCENARIO_REQUEST_MARKERS)
    )
    if motivation_dominant and not genuine_scenario_request:
        return "hr_behavioral"

    # Complex scenario: safety/regulation with scenario context — not weak behavioral safety mention.
    complex_score = (
        sig.scenario_signals * 2
        + sig.safety_signals
        + sig.compliance_signals
        + sig.regulation_signals
        + sig.calculation_signals
    )
    if complex_score >= 4 and (sig.scenario_signals >= 1 or sig.safety_signals >= 2):
        if not (sig.behavioral_signals >= 2 and sig.safety_signals == 1 and sig.scenario_signals == 0):
            return "complex_scenario"
    if sig.regulation_signals >= 2 and (sig.compliance_signals >= 1 or sig.safety_signals >= 1):
        return "complex_scenario"

    # Practical workflow / troubleshooting
    workflow_score = sig.tool_signals + sig.troubleshooting_signals + sig.multi_step_signals
    if workflow_score >= 3 or sig.question_type in {"tool_usage", "tool"}:
        return "practical_workflow"
    if "workflow" in qtext or "how would you use" in qtext or "how do you" in qtext:
        if sig.tool_signals >= 1 or sig.troubleshooting_signals >= 1:
            return "practical_workflow"

    # HR / behavioral — but not hybrid obligation questions that also need technical depth.
    profile = get_question_obligation_profile(question, job)
    hybrid_technical = _hybrid_technical_for_depth(profile)
    if sig.behavioral_signals >= 2 or sig.hr_signals >= 2 or sig.category in {"hr", "behavioral", "motivation"}:
        if not hybrid_technical:
            return "hr_behavioral"

    # Simple factual / definitional — before generic technical category bump
    if sig.simple_factual_signals >= 1 and not sig.scenario_signals and not sig.system_design_signals:
        if sig.troubleshooting_signals == 0 and "architecture" not in qtext:
            return "simple_factual"

    # Standard technical — only when not clearly simple definitional
    if sig.simple_factual_signals >= 1 and sig.tool_signals == 0 and sig.scenario_signals == 0:
        return "simple_factual"
    if sig.category in {"technical", "role_specific"} or sig.tool_signals >= 1:
        return "standard_technical"
    if sig.source_item_count >= 2 and not sig.job_thin:
        return "standard_technical"

    # Simple factual default — especially title-only, but preserve behavioral semantics.
    if sig.category in {"behavioral", "hr", "motivation"} and (
        sig.behavioral_signals >= 2 or sig.hr_signals >= 2
    ):
        return "hr_behavioral"
    if sig.simple_factual_signals >= 1 or sig.job_thin:
        return "simple_factual"

    return "standard_technical"


def resolve_study_material_budget(
    question: dict[str, Any],
    job: dict[str, Any],
    *,
    signals: StudyMaterialComplexitySignals | None = None,
    depth: StudyDepth | None = None,
) -> StudyMaterialBudget:
    sig = signals or collect_complexity_signals(question, job)
    resolved_depth = depth or classify_study_material_depth(question, job, sig)
    budget = _BUDGETS[resolved_depth]

    # Thin inputs stay conservative in length/specificity, but must NOT rewrite the
    # semantic category (§9 Problem B). Behavioral/motivation (hr_behavioral) is
    # already conservative and must stay behavioral rather than collapse to factual;
    # a genuine scenario must not collapse to factual either. Only ungrounded deep
    # *technical* depth (advanced/practical) is stepped down when there is no evidence
    # to support fabricated multi-step/tool detail.
    _SEMANTIC_PRESERVE = {"hr_behavioral", "simple_factual", "complex_scenario"}
    if is_thin_conservative_input(sig):
        if resolved_depth not in _SEMANTIC_PRESERVE:
            resolved_depth = "standard_technical"
        budget = _BUDGETS[resolved_depth]

    # Title-only cap for ungrounded deep *technical* depth: do not fabricate advanced
    # multi-step / practical-workflow detail without grounded evidence. Behavioral,
    # motivation, and genuine scenario semantics are preserved (only their length and
    # specificity tighten via the conservative budget/complexity below).
    if sig.job_thin and resolved_depth in {"advanced_multi_step", "practical_workflow"}:
        if sig.source_item_count < 2 and not sig.document_library_rich:
            resolved_depth = "standard_technical"
            budget = _BUDGETS[resolved_depth]

    complexity: ComplexityLevel = budget.complexity_level
    if sig.weighted_score >= 12:
        complexity = "very_high"
    elif sig.weighted_score >= 8:
        complexity = "high"
    elif sig.weighted_score >= 4:
        complexity = "moderate"
    else:
        complexity = "low"

    return StudyMaterialBudget(
        study_depth=resolved_depth,
        target_min_words=budget.target_min_words,
        target_max_words=budget.target_max_words,
        hard_max_words=budget.hard_max_words,
        complexity_level=complexity,
    )


def study_module_word_count(study: dict[str, Any], *, include_extension: bool = True, for_hard_max: bool = False) -> int:
    exclude = {"model_insight"} if for_hard_max else set()
    total = 0
    for key in _CONTENT_TEXT_KEYS:
        if key in exclude:
            continue
        total += count_words(str(study.get(key) or ""))
    for key in _CONTENT_LIST_KEYS:
        value = study.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    total += count_words(item)
                elif isinstance(item, dict):
                    total += count_words(str(item.get("definition") or item.get("term") or ""))
    if include_extension:
        ext = study.get("advanced_extension")
        if isinstance(ext, dict):
            total += study_module_word_count(ext, include_extension=False)
    return total


def study_module_core_word_count(study: dict[str, Any], *, for_hard_max: bool = False) -> int:
    return study_module_word_count(study, include_extension=False, for_hard_max=for_hard_max)


def _hard_max_word_count(study: dict[str, Any]) -> int:
    return study_module_core_word_count(study, for_hard_max=True)


def is_thin_conservative_input(signals: StudyMaterialComplexitySignals) -> bool:
    """Title-only or zero-source inputs with low evidence richness."""
    if signals.document_library_rich or signals.company_context:
        return False
    if signals.job_thin:
        return True
    return signals.source_item_count == 0 and signals.weighted_score <= 3


def _element_present(study: dict[str, Any], element: str) -> bool:
    value = study.get(element)
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len([v for v in value if str(v).strip()]) > 0
    return bool(value)


def _generic_substance_blob(text: str) -> bool:
    lowered = (text or "").lower().strip()
    if len(lowered.split()) > 15:
        return False
    exact_generic = {
        "verify quality and monitor performance",
        "define success metrics and alert thresholds",
    }
    return lowered in exact_generic


def _is_substantive_element(element: str, study: dict[str, Any], depth: StudyDepth) -> bool:
    if not _element_present(study, element):
        return False
    value = study.get(element)
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
        if not items:
            return False
        if element in {"step_by_step_method", "staged_reasoning", "decision_branches"}:
            return len(items) >= 2 and all(len(item.split()) >= 6 for item in items[:2])
        if element in {"workflow_checkpoints", "failure_modes", "verification_steps"}:
            return len(items) >= 2 and all(len(item.split()) >= 5 for item in items[:2])
        if element in {"competing_constraints", "assumptions_and_dependencies"}:
            return len(items) >= 2
        return all(len(item.split()) >= 4 for item in items[:2])
    text = str(value).strip()
    words = text.split()
    if _generic_substance_blob(text):
        return False
    min_words = 8
    if depth in {"advanced_multi_step", "complex_scenario", "practical_workflow"}:
        min_words = 12
    if element in {"trade_off_analysis", "scenario_framing", "system_framing", "workflow_objective"}:
        min_words = 14
    return len(words) >= min_words


def _backfill_depth_contract_fields(
    study: dict[str, Any],
    depth: StudyDepth,
    *,
    role: str,
    focus: str,
) -> dict[str, Any]:
    """Ensure required contract keys exist so export/regression empty-section scans stay truthful."""
    out = dict(study)
    required = list(_DEPTH_CONTRACT.get(depth, []))
    for key in ("core_idea", "what_this_question_tests"):
        if key not in required:
            required.append(key)

    fillers: dict[str, Any] = {
        "core_idea": str(
            out.get("compact_explanation")
            or out.get("beginner_explanation")
            or f"Core concept for {focus} in {role} work."
        ).strip(),
        "what_this_question_tests": (
            f"Applied understanding of {focus} in realistic {role} interview context."
        ),
        "compact_explanation": str(out.get("core_idea") or f"Concise explanation of {focus}."),
        "key_principles": [
            f"Apply {focus} with documented checks.",
            f"Communicate assumptions clearly in {role} work.",
        ],
        "behavioral_response_structure": (
            "Structure with STAR: Situation, Task, Action, Result with evidence you can support."
        ),
        "common_mistakes": [f"Vague claims about {focus} without checks or evidence."],
        "interview_application": f"Use one relevant, supportable example from {role} practice.",
        "technical_mechanisms": [f"How {focus} works and which parts must be verified."],
        "common_misconceptions": [
            f"Treating {focus} as a checklist instead of a quality-controlled process."
        ],
        "workflow_objective": f"Complete {focus} reliably with traceable checkpoints.",
        "step_by_step_method": [
            f"Confirm objective and constraints for {focus}.",
            f"Execute with intermediate validation checkpoints.",
        ],
        "workflow_checkpoints": [
            f"Pre-check inputs for {focus}.",
            f"Validate output before handoff.",
        ],
        "failure_modes": [f"Skipping validation for {focus}.", "Unclear handoff criteria."],
        "escalation_triggers": ["Checkpoint failure", "Unresolved risk threshold breach"],
        "scenario_framing": f"A realistic {role} scenario involving {focus} with competing constraints.",
        "competing_constraints": ["Quality versus deadline pressure", "Safety or compliance versus speed"],
        "decision_branches": [
            "If evidence is incomplete, pause and gather verification before proceeding.",
            "If risk threshold is exceeded, escalate with documented rationale.",
        ],
        "verification_steps": [
            f"Cross-check {focus} output against the standard the task requires.",
            "Confirm stakeholder sign-off.",
        ],
        "outcome_evaluation": (
            f"Judge whether {focus} delivery met quality, timing, and communication goals."
        ),
        "system_framing": (
            f"System boundary for {focus} across people, process, and tooling in {role} work."
        ),
        "assumptions_and_dependencies": ["Stable inputs", "Clear ownership for checkpoints"],
        "staged_reasoning": [
            f"Frame the problem and constraints for {focus}.",
            f"Implement with staged validation before final handoff.",
        ],
        "trade_off_analysis": (
            f"Compare speed versus rigor for {focus}, noting consequences of each choice."
        ),
        "validation_and_monitoring": (
            f"Validate {focus} with explicit checks and monitor for failure signals after release."
        ),
    }
    for el in required:
        if not _element_present(out, el) and el in fillers:
            out[el] = fillers[el]
    return out


def evaluate_depth_contract(study: dict[str, Any], depth: StudyDepth) -> dict[str, Any]:
    # A conservative thin module (semantic depth preserved, content compacted per §9)
    # is judged against the compact contract with a shallow substantive bar, since it
    # cannot ground deep scenario/workflow richness without inventing facts.
    if bool(study.get("thin_input_conservative")):
        required = list(_THIN_DEPTH_CONTRACT)
        substantive_depth: StudyDepth = "simple_factual"
    else:
        required = list(_DEPTH_CONTRACT.get(depth, []))
        substantive_depth = depth
    present = [el for el in required if _element_present(study, el)]
    substantive = [el for el in required if _is_substantive_element(el, study, substantive_depth)]
    weak = [el for el in present if el not in substantive]
    missing = [el for el in required if el not in present]
    coverage = round(len(present) / len(required), 2) if required else 1.0
    substantive_coverage = round(len(substantive) / len(required), 2) if required else 1.0
    return {
        "depth_contract_required_elements": required,
        "depth_contract_present_elements": present,
        "depth_contract_substantive_elements": substantive,
        "depth_contract_weak_elements": weak,
        "depth_contract_missing_elements": missing,
        "depth_contract_coverage": coverage,
        "substantive_contract_coverage": substantive_coverage,
    }


def _focus_label(question: dict[str, Any], job: dict[str, Any], signals: StudyMaterialComplexitySignals) -> str:
    return str(
        question.get("skill_tag")
        or (signals.matched_signals[0] if signals.matched_signals else None)
        or job.get("title")
        or "the topic"
    )


def _merge_explanations(study: dict[str, Any]) -> str:
    parts = [
        str(study.get("beginner_explanation") or ""),
        str(study.get("intermediate_explanation") or ""),
        str(study.get("advanced_explanation") or ""),
        str(study.get("core_idea") or ""),
    ]
    merged = " ".join(p.strip() for p in parts if p.strip())
    return _trim_text_to_words(merged, 90) if merged else ""


def shape_study_module_by_depth(
    study: dict[str, Any],
    question: dict[str, Any],
    job: dict[str, Any],
    budget: StudyMaterialBudget,
    signals: StudyMaterialComplexitySignals,
) -> dict[str, Any]:
    """Reshape study content to match depth pedagogical contract — not just metadata."""
    out = dict(study)
    role = job.get("title") or "this role"
    focus = _focus_label(question, job, signals)
    thin = is_thin_conservative_input(signals)
    depth = budget.study_depth

    if thin:
        out["thin_input_conservative"] = True
        # Thin inputs: strip unsupported richness and keep guidance compact.
        for key in (
            "document_library_insight",
            "saved_material_insight",
            "web_or_company_source_insight",
            "practical_workflow",
            "advanced_nuance",
            "decision_points_summary",
            "system_framing",
            "trade_off_analysis",
            "scenario_framing",
        ):
            out.pop(key, None)
        out["compact_explanation"] = _trim_text_to_words(
            _merge_explanations(out)
            or f"With only a role title available, explain {focus} using cautious, general professional guidance "
            f"without inventing employer-specific facts.",
            70,
        )
        out.pop("beginner_explanation", None)
        out.pop("intermediate_explanation", None)
        out.pop("advanced_explanation", None)
        out["what_this_question_tests"] = _trim_text_to_words(
            str(out.get("what_this_question_tests") or f"What baseline readiness for {role} can be assessed from limited input."),
            45,
        )
        out["key_principles"] = _dedupe_preserve(_ensure_list(out.get("key_principles")))[:2]
        out["common_mistakes"] = _dedupe_preserve(_ensure_list(out.get("common_mistakes")))[:2]
        out["interview_application"] = _trim_text_to_words(
            str(out.get("interview_application") or f"Keep answers honest about limited context for {role}."),
            35,
        )
        if not out.get("core_idea"):
            out["core_idea"] = _trim_text_to_words(
                str(out.get("compact_explanation") or f"Baseline guidance for {role} with limited source context."),
                50,
            )
        out["step_by_step_method"] = []
        return out

    if depth == "simple_factual":
        out["compact_explanation"] = _merge_explanations(out) or str(out.get("core_idea") or "")
        out.pop("beginner_explanation", None)
        out.pop("intermediate_explanation", None)
        out.pop("advanced_explanation", None)
        out.pop("practical_workflow", None)
        out.pop("decision_points_summary", None)
        out["key_principles"] = _dedupe_preserve(_ensure_list(out.get("key_principles")))[:2]
        out["common_mistakes"] = _dedupe_preserve(_ensure_list(out.get("common_mistakes")))[:2]
        out["step_by_step_method"] = []
        if not out.get("practical_example"):
            out["practical_example"] = _trim_text_to_words(
                f"A compact {role} example showing how {focus} appears in everyday work.", 25
            )
        return out

    if depth == "hr_behavioral":
        out["behavioral_response_structure"] = (
            "Structure with STAR: Situation (context), Task (your responsibility), "
            "Action (specific steps you took), Result (the outcome and what you learned — "
            "include numbers only if you genuinely have them, never invented ones)."
        )
        if question_has_hybrid_obligation_study(question, job):
            out = shape_hybrid_obligation_study_application(out, question, job)
            return out
        if question_has_role_fit_study_archetype(question):
            out = shape_role_fit_study_application(out, question, job)
            out["behavioral_response_structure"] = (
                "Use a short, honest structure: what in the posting attracts you, how that "
                "connects to genuine strengths or development goals, and what you hope to "
                "contribute in the first months."
            )
            out["common_mistakes"] = _dedupe_preserve(_ensure_list(out.get("common_mistakes")))[:3]
            return out
        out.pop("beginner_explanation", None)
        out.pop("intermediate_explanation", None)
        out.pop("advanced_explanation", None)
        out.pop("practical_workflow", None)
        out.pop("step_by_step_method", None)
        out["common_mistakes"] = _dedupe_preserve(_ensure_list(out.get("common_mistakes")))[:3]
        out["interview_application"] = _trim_text_to_words(
            str(out.get("interview_application") or f"Select one relevant {role} example with clear evidence."),
            40,
        )
        return out

    if depth == "standard_technical":
        out["technical_mechanisms"] = _dedupe_preserve(
            [m for m in _ensure_list(out.get("technical_mechanisms")) if len(m.split()) >= 4]
            or [p for p in _ensure_list(out.get("key_principles")) if len(p.split()) >= 4]
            or [
                f"How {focus} works in {role} practice and which components interact to produce the result.",
                f"The inputs {focus} depends on and the checks that confirm each step is correct.",
            ]
        )[:4]
        out["common_misconceptions"] = _dedupe_preserve(
            _ensure_list(out.get("common_misconceptions"))
            or _ensure_list(out.get("common_mistakes"))
        )[:3]
        if not out.get("practical_example"):
            out["practical_example"] = (
                f"Interpret {focus} in a realistic {role} task: inputs, checks, and expected output."
            )
        return out

    if depth == "practical_workflow":
        out["workflow_objective"] = (
            f"Complete {focus} for {role} by confirming scope and constraints, executing the "
            f"method with intermediate validation, and verifying the output meets the standard "
            f"the task requires before a documented handoff."
        )
        steps = [s for s in _dedupe_preserve(_ensure_list(out.get("step_by_step_method"))) if len(s.split()) >= 6]
        if len(steps) < 4:
            steps = [
                f"Confirm the objective, scope, inputs, and constraints for the {focus} task.",
                f"Prepare the tools, data, and pre-checks {focus} needs before you start.",
                f"Execute the {focus} method, recording an intermediate validation checkpoint at each stage.",
                f"Verify the {focus} output meets the standard the task requires and capture evidence for handoff.",
                f"Escalate promptly if a checkpoint fails or a risk threshold for {focus} is exceeded.",
            ]
        out["step_by_step_method"] = steps[:5]
        out["workflow_checkpoints"] = _collect_min_items(
            [c for c in _ensure_list(out.get("workflow_checkpoints")) if len(c.split()) >= 5],
            [
                f"Confirm inputs and preconditions for {focus} are validated before execution begins.",
                f"Record an intermediate quality check partway through the {focus} workflow.",
                f"Verify the final {focus} output against explicit sign-off checks before handoff.",
            ],
            minimum=2,
        )[:4]
        out["failure_modes"] = _collect_min_items(
            [f for f in _ensure_list(out.get("failure_modes")) if len(f.split()) >= 5],
            [f for f in _ensure_list(out.get("common_mistakes")) if len(f.split()) >= 5],
            [
                f"Skipping validation checkpoints for {focus} before final sign-off.",
                f"Unclear handoff criteria that let {focus} defects reach the next stage.",
            ],
            minimum=2,
        )[:3]
        out["escalation_triggers"] = _collect_min_items(
            [e for e in _ensure_list(out.get("escalation_triggers")) if len(e.split()) >= 5],
            [
                f"A safety or compliance threshold relevant to {focus} has been breached.",
                f"A {focus} checkpoint fails repeatedly after one documented corrective attempt.",
            ],
            minimum=2,
        )[:3]
        out["practical_workflow"] = (
            f"Workflow for {focus}: define objective, prepare inputs, execute with staged checkpoints, "
            f"verify against criteria, and escalate when checks fail."
        )
        return out

    if depth == "complex_scenario":
        out["scenario_framing"] = (
            f"Frame the {focus} scenario for {role}: name the stakeholders involved, the constraints "
            f"in play, the risks to manage, and what a good outcome actually looks like."
        )
        out["competing_constraints"] = _collect_min_items(
            [c for c in _ensure_list(out.get("competing_constraints")) if len(c.split()) >= 4],
            [
                f"Safety or compliance requirements that limit how {focus} can be done.",
                "Time and resource limits pushing against thorough checks.",
                "Stakeholder expectations that conflict with each other.",
            ],
            minimum=2,
        )[:4]
        out["decision_branches"] = _collect_min_items(
            [d for d in _ensure_list(out.get("decision_branches")) if len(d.split()) >= 6],
            [d for d in _ensure_list(out.get("decision_points")) if len(d.split()) >= 6],
            [
                f"If risk to {focus} is high, pause and escalate before proceeding further.",
                "If information is incomplete, gather the critical facts before committing to a path.",
                "If constraints conflict, make the trade-off explicit and record the rationale.",
            ],
            minimum=2,
        )[:4]
        out["verification_steps"] = _collect_min_items(
            [v for v in _ensure_list(out.get("verification_steps")) if len(v.split()) >= 5],
            [
                f"Confirm the {focus} assumptions against the evidence actually available.",
                "Validate the relevant controls both before and after the decision.",
            ],
            minimum=2,
        )[:4]
        out["outcome_evaluation"] = _trim_text_to_words(
            str(out.get("outcome_evaluation"))
            if len(str(out.get("outcome_evaluation") or "").split()) >= 12
            else (
                f"Evaluate whether the {focus} outcome met quality, safety, and timing goals for {role}, "
                f"and note any residual risk plus the follow-up actions required."
            ),
            45,
        )
        out["decision_points_summary"] = (
            f"Interviewers expect explicit trade-off reasoning on {focus}, not a single generic answer."
        )
        return out

    if depth == "advanced_multi_step":
        out["system_framing"] = (
            f"Describe the {focus} system boundary for {role}: the main components, the interfaces "
            f"between them, the data that flows through, and the blast radius when a part fails."
        )
        out["assumptions_and_dependencies"] = _collect_min_items(
            [a for a in _ensure_list(out.get("assumptions_and_dependencies")) if len(a.split()) >= 4],
            [
                f"State the load, latency, and reliability assumptions behind the {focus} design explicitly.",
                "List the upstream and downstream dependencies that could break the design.",
            ],
            minimum=2,
        )[:4]
        out["staged_reasoning"] = _collect_min_items(
            [s for s in _ensure_list(out.get("staged_reasoning")) if len(s.split()) >= 6],
            [s for s in _ensure_list(out.get("step_by_step_method")) if len(s.split()) >= 6],
            [
                f"Stage 1: define the requirements and constraints that shape the {focus} design.",
                "Stage 2: propose two or three architecture options with their trade-offs.",
                "Stage 3: select a design and define how you will validate it.",
                "Stage 4: plan the rollout, monitoring, and a clear rollback path.",
            ],
            minimum=2,
        )[:5]
        out["trade_off_analysis"] = _trim_text_to_words(
            str(out.get("trade_off_analysis"))
            if len(str(out.get("trade_off_analysis") or "").split()) >= 14
            else (
                f"Compare the {focus} options across cost, reliability, security, and operability, then "
                f"state which trade-off you would accept given the constraints and explain why."
            ),
            55,
        )
        out["validation_and_monitoring"] = _collect_min_items(
            [v for v in _ensure_list(out.get("validation_and_monitoring")) if len(v.split()) >= 5],
            [
                f"Define the success metrics and review thresholds for the {focus} design.",
                "Plan a phased rollout with a clear, tested back-out plan.",
            ],
            minimum=2,
        )[:4]
        out["alternative_paths"] = _collect_min_items(
            [a for a in _ensure_list(out.get("alternative_paths")) if len(a.split()) >= 5],
            [
                f"Document a lower-complexity {focus} fallback to use if constraints tighten.",
                "Note when to defer scope or split delivery across phases.",
            ],
            minimum=2,
        )[:3]
        if not out.get("advanced_explanation"):
            out["advanced_explanation"] = (
                f"Advanced {role} judgment on {focus} means anticipating second-order effects, dependency "
                f"failures, and the governance needed to keep the system safe under change."
            )
        return out

    return out


def _ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if v and str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _apply_shallow_economy(out: dict[str, Any], budget: StudyMaterialBudget) -> dict[str, Any]:
    """Keep simple/HR modules economical — hard max is not a target."""
    if budget.study_depth not in {"simple_factual", "hr_behavioral"}:
        return out
    ceiling = int(budget.hard_max_words * _SHALLOW_TARGET_CEILING_RATIO)
    soft_cap = min(budget.target_max_words, ceiling)
    trim_keys = (
        "overview",
        "core_idea",
        "compact_explanation",
        "what_this_question_tests",
        "interview_application",
        "behavioral_response_structure",
        "beginner_explanation",
        "intermediate_explanation",
        "advanced_explanation",
    )
    source_types = set(out.get("source_types_used") or [])
    guard = 0
    while study_module_core_word_count(out) > soft_cap and guard < 35:
        guard += 1
        removed = False
        for key in ("document_library_insight", "saved_material_insight", "web_or_company_source_insight", "practical_example", "practical_workflow"):
            if key in {"document_library_insight", "saved_material_insight"} and "document_library" in source_types:
                continue
            if out.pop(key, None) is not None:
                removed = True
                break
        if not removed:
            for list_key in ("likely_follow_ups", "key_principles", "common_mistakes", "step_by_step_method"):
                items = _ensure_list(out.get(list_key))
                if len(items) > 1:
                    out[list_key] = items[: max(1, len(items) - 1)]
                    removed = True
                    break
        if not removed:
            over = study_module_core_word_count(out) - soft_cap
            step = 12 if over < 40 else min(60, max(20, over // 4))
            for key in trim_keys:
                text = str(out.get(key) or "")
                if text and count_words(text) > 15:
                    out[key] = _trim_text_to_words(text, max(12, count_words(text) - step))
                    removed = True
                    break
        if not removed:
            break
    return out


def _apply_thin_word_ceiling(out: dict[str, Any]) -> dict[str, Any]:
    trim_keys = (
        "overview",
        "core_idea",
        "compact_explanation",
        "what_this_question_tests",
        "interview_application",
    )
    guard = 0
    while study_module_core_word_count(out) > _THIN_INPUT_WORD_CEILING and guard < 30:
        guard += 1
        removed = False
        for key in ("practical_example", "likely_follow_ups", "document_library_insight", "saved_material_insight"):
            if out.pop(key, None) is not None:
                removed = True
                break
        if not removed:
            for list_key in ("key_principles", "common_mistakes"):
                items = _ensure_list(out.get(list_key))
                if len(items) > 1:
                    out[list_key] = items[:1]
                    removed = True
                    break
        if not removed:
            over = study_module_core_word_count(out) - _THIN_INPUT_WORD_CEILING
            step = 8 if over < 25 else min(40, max(15, over // 3))
            for key in trim_keys:
                text = str(out.get(key) or "")
                if text and count_words(text) > 10:
                    trimmed = _trim_text_to_words(text, max(8, count_words(text) - step))
                    if trimmed.strip():
                        out[key] = trimmed
                        removed = True
                        break
        if not removed:
            break
    return out


def evaluate_budget_status(
    actual_words: int,
    budget: StudyMaterialBudget,
    *,
    contract_coverage: float = 1.0,
    substantive_coverage: float = 1.0,
    thin_conservative: bool = False,
    integrity_clean: bool = True,
) -> BudgetStatus:
    if actual_words > budget.hard_max_words:
        return "hard_limit_exceeded"
    if actual_words > budget.target_max_words:
        return "above_target_but_allowed"
    if actual_words >= budget.target_min_words:
        return "within_target"
    if not integrity_clean:
        return "structure_incomplete"
    # Below target minimum: allow concise_complete only with substantive structural evidence.
    min_ratio = actual_words / max(1, budget.target_min_words)
    coverage_floor = 0.55 if thin_conservative else 0.65
    substantive_floor = 0.75 if thin_conservative else 0.85
    deep_depths = {"advanced_multi_step", "complex_scenario", "practical_workflow"}
    if budget.study_depth in deep_depths:
        coverage_floor = 0.75
        substantive_floor = 0.9
    if substantive_coverage < substantive_floor:
        return "structure_incomplete"
    if min_ratio < 0.45:
        if substantive_coverage >= max(substantive_floor, 0.95):
            return "concise_complete"
        return "structure_incomplete"
    if budget.study_depth in deep_depths:
        if substantive_coverage >= substantive_floor and contract_coverage >= coverage_floor:
            return "concise_complete"
        return "structure_incomplete"
    if substantive_coverage >= substantive_floor and contract_coverage >= coverage_floor:
        return "concise_complete"
    if min_ratio >= 0.55 and substantive_coverage >= 0.7:
        return "concise_complete"
    return "structure_incomplete"


def _concise_complete_reason(
    actual_words: int,
    budget: StudyMaterialBudget,
    contract: dict[str, Any],
    thin_conservative: bool,
) -> str:
    if thin_conservative:
        return "Thin input conservative module: compact guidance with required elements present."
    if actual_words < budget.target_min_words:
        missing = set(contract.get("depth_contract_required_elements", [])) - set(
            contract.get("depth_contract_present_elements", [])
        )
        if missing:
            return f"Below target range but core depth elements present; optional sections omitted ({', '.join(sorted(missing)[:2])})."
        return "Below target range with complete required depth structure; no padding added."
    return "Within adaptive depth expectations."


def _human_budget_reason(signals: StudyMaterialComplexitySignals, depth: StudyDepth) -> str:
    parts: list[str] = []
    if depth == "advanced_multi_step":
        parts.append("Multi-step or system-design question")
    elif depth == "complex_scenario":
        parts.append("Scenario, safety, or regulation context")
    elif depth == "practical_workflow":
        parts.append("Practical workflow or troubleshooting focus")
    elif depth == "standard_technical":
        parts.append("Standard technical or conceptual focus")
    elif depth == "hr_behavioral":
        parts.append("HR or behavioral evidence question")
    else:
        parts.append("Introductory or factual focus")
    if signals.tool_signals:
        parts.append("with tool context")
    if signals.safety_signals or signals.compliance_signals:
        parts.append("with safety or compliance context")
    if signals.job_thin:
        parts.append("on thin job input")
    return ". ".join(parts[:2]) + "."


def _dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = re.sub(r"\s+", " ", item.lower().strip())[:80]
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _collect_min_items(*candidate_lists: list[str], minimum: int = 2) -> list[str]:
    """Accumulate (deduped) list items across fallbacks until at least ``minimum`` exist.

    Fixes the short-circuit defect where a skill-native list survives filtering with a
    single item (truthy) and therefore never backfills from the generic fallbacks,
    leaving a required deep-depth element non-substantive (needs >= 2 items). Skill-native
    items are still preferred because they are listed first; fallbacks only top up.
    """
    collected: list[str] = []
    for candidate in candidate_lists:
        for item in candidate:
            collected.append(item)
        collected = _dedupe_preserve(collected)
        if len(collected) >= minimum:
            break
    return collected


def _trim_text_to_words(text: str, max_words: int) -> str:
    """Soft shaping trim — prefer sentence boundaries when over budget."""
    return _trim_text_for_hard_limit(text, max_words)


def _trim_text_for_hard_limit(text: str, target_words: int) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    if count_words(cleaned) <= target_words:
        return cleaned
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    if len(sentences) > 1:
        while sentences and count_words(" ".join(sentences)) > target_words:
            sentences.pop()
        if sentences:
            return " ".join(sentences).strip()
    clauses = re.split(r"(?<=[;,])\s+", cleaned)
    if len(clauses) > 1:
        while clauses and count_words(" ".join(clauses)) > target_words:
            clauses.pop()
        if clauses:
            return " ".join(clauses).strip()
    # Single unbreakable unit — drop rather than arbitrary word-array clipping.
    return ""


def _compress_study_module(study: dict[str, Any], budget: StudyMaterialBudget) -> dict[str, Any]:
    """Remove redundancy and compress non-essential sections — never mid-sentence chop."""
    out = dict(study)

    core = str(out.get("core_idea") or "")
    for key in ("beginner_explanation", "intermediate_explanation", "advanced_explanation"):
        val = str(out.get(key) or "")
        if val and core and val.strip() == core.strip():
            out.pop(key, None)

    for list_key in ("key_principles", "common_mistakes", "step_by_step_method", "likely_follow_ups"):
        if list_key in out and isinstance(out[list_key], list):
            out[list_key] = _dedupe_preserve([str(x) for x in out[list_key]])[:5]

    trim_plan = (
        ("advanced_explanation", 40, 30),
        ("intermediate_explanation", 50, 25),
        ("beginner_explanation", 45, 20),
        ("practical_workflow", 30, 20),
        ("advanced_nuance", 0, 0),
        ("decision_points_summary", 0, 0),
        ("web_or_company_source_insight", 25, 15),
        ("document_library_insight", 25, 15),
        ("what_this_question_tests", 35, 15),
    )

    guard = 0
    while _hard_max_word_count(out) > budget.hard_max_words and guard < 40:
        guard += 1
        progressed = False
        for key, floor, step in trim_plan:
            if _hard_max_word_count(out) <= budget.hard_max_words:
                break
            if key in ("advanced_nuance", "decision_points_summary"):
                if out.get(key):
                    out.pop(key, None)
                    progressed = True
                continue
            text = str(out.get(key) or "")
            if text and count_words(text) > floor:
                out[key] = _trim_text_to_words(text, max(floor, count_words(text) - step))
                progressed = True
        if not progressed:
            for list_key in ("common_mistakes", "key_principles", "step_by_step_method"):
                items = out.get(list_key) or []
                if len(items) > 2:
                    out[list_key] = items[:2]
                    progressed = True
                    break
        if not progressed:
            break

    return out


def _force_under_hard_max(study: dict[str, Any], budget: StudyMaterialBudget) -> dict[str, Any]:
    """Last-resort trim: remove optional fields, then trim longest text fields by whole sentences."""
    out = dict(study)
    optional_keys = (
        "advanced_nuance",
        "decision_points_summary",
        "practical_workflow",
        "web_or_company_source_insight",
        "document_library_insight",
        "saved_material_insight",
        "model_insight",
    )
    for key in optional_keys:
        if _hard_max_word_count(out) <= budget.hard_max_words:
            break
        out.pop(key, None)

    text_keys = [k for k in _CONTENT_TEXT_KEYS if out.get(k)]
    guard = 0
    while _hard_max_word_count(out) > budget.hard_max_words and guard < 60:
        guard += 1
        longest_key = max(text_keys, key=lambda k: count_words(str(out.get(k) or "")), default=None)
        if not longest_key:
            break
        text = str(out.get(longest_key) or "")
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) > 1:
            out[longest_key] = " ".join(sentences[:-1]).strip()
        else:
            out.pop(longest_key, None)
        text_keys = [k for k in _CONTENT_TEXT_KEYS if out.get(k)]
    return out


def _split_advanced_extension(study: dict[str, Any], budget: StudyMaterialBudget) -> dict[str, Any]:
    """Move overflow into optional advanced_extension when core still exceeds hard max."""
    if budget.study_depth != "advanced_multi_step":
        return study
    if _hard_max_word_count(study) <= budget.hard_max_words:
        return study

    out = dict(study)
    extension: dict[str, Any] = {}
    for key in ("advanced_nuance", "decision_points", "practical_workflow"):
        if out.get(key):
            extension[key] = out.pop(key)

    adv = str(out.get("advanced_explanation") or "")
    if adv and count_words(adv) > 80:
        sentences = re.split(r"(?<=[.!?])\s+", adv)
        if len(sentences) > 1:
            split_idx = max(1, len(sentences) // 2)
            out["advanced_explanation"] = " ".join(sentences[:split_idx]).strip()
            extension["advanced_explanation"] = " ".join(sentences[split_idx:]).strip()
        else:
            out.pop("advanced_explanation", None)

    if extension and _hard_max_word_count(out) <= budget.hard_max_words:
        out["advanced_extension"] = extension
    return out


def apply_adaptive_study_budget(
    study: dict[str, Any],
    question: dict[str, Any],
    job: dict[str, Any],
) -> dict[str, Any]:
    """Classify, shape by depth contract, measure, compress, and attach budget metadata."""
    signals = collect_complexity_signals(question, job)
    budget = resolve_study_material_budget(question, job, signals=signals)
    thin = is_thin_conservative_input(signals)

    out = shape_study_module_by_depth(study, question, job, budget, signals)
    if thin:
        out = _apply_thin_word_ceiling(out)
    else:
        out = _apply_shallow_economy(out, budget)

    # Compress only when above hard max (ceiling, not target).
    if _hard_max_word_count(out) > budget.hard_max_words:
        out = _compress_study_module(out, budget)
    out = _split_advanced_extension(out, budget)
    for _ in range(3):
        if _hard_max_word_count(out) <= budget.hard_max_words:
            break
        out = _compress_study_module(out, budget)
    if _hard_max_word_count(out) > budget.hard_max_words:
        out = _force_under_hard_max(out, budget)

    if thin:
        out = _apply_thin_word_ceiling(out)
    role_title = job.get("title") or ""
    from app.agents.job_search.quality.surface_quality_guard import fix_surface_quality_defects

    for key in _CONTENT_TEXT_KEYS:
        value = out.get(key)
        if isinstance(value, str):
            out[key] = fix_surface_quality_defects(value, role=role_title)
        elif isinstance(value, list):
            out[key] = [
                fix_surface_quality_defects(str(item), role=role_title)
                for item in value
                if str(item).strip()
            ]
    out = _backfill_depth_contract_fields(
        out,
        budget.study_depth,
        role=role_title,
        focus=_focus_label(question, job, signals),
    )
    if _hard_max_word_count(out) > budget.hard_max_words:
        out = _compress_study_module(out, budget)
        if _hard_max_word_count(out) > budget.hard_max_words:
            out = _force_under_hard_max(out, budget)
    contract = evaluate_depth_contract(out, budget.study_depth)
    actual = study_module_core_word_count(out)
    hard_actual = _hard_max_word_count(out)
    integrity_blob = " ".join(
        str(out.get(key) or "")
        for key in _CONTENT_TEXT_KEYS
        if out.get(key)
    )
    from app.agents.job_search.quality.claim_integrity import audit_claim_integrity
    from app.agents.job_search.quality.surface_quality_guard import audit_surface_quality

    claim_audit = audit_claim_integrity(integrity_blob, job)
    surface_audit = audit_surface_quality(integrity_blob, role=job.get("title") or "")
    integrity_clean = (
        claim_audit["unsupported_personal_claim_count"] == 0
        and claim_audit["unsupported_numeric_claim_count"] == 0
        and claim_audit["thin_input_specificity_violation_count"] == 0
        and surface_audit["total_surface_quality_defects"] == 0
    )
    status = evaluate_budget_status(
        actual,
        budget,
        contract_coverage=float(contract["depth_contract_coverage"]),
        substantive_coverage=float(contract["substantive_contract_coverage"]),
        thin_conservative=thin,
        integrity_clean=integrity_clean,
    )
    if hard_actual > budget.hard_max_words:
        status = "hard_limit_exceeded"

    out["study_depth"] = budget.study_depth
    out["study_depth_label"] = _DEPTH_LABELS[budget.study_depth]
    out["study_complexity_level"] = budget.complexity_level
    out["target_min_words"] = budget.target_min_words
    out["target_max_words"] = budget.target_max_words
    out["hard_max_words"] = budget.hard_max_words
    out["actual_word_count"] = actual
    out["budget_status"] = status
    out["budget_reason"] = _human_budget_reason(signals, budget.study_depth)
    out["concise_complete_reason"] = _concise_complete_reason(actual, budget, contract, thin)
    out["complexity_signals"] = list(dict.fromkeys(signals.matched_signals))[:8]
    out["thin_input_conservative"] = thin
    out["unsupported_personal_claim_count"] = claim_audit["unsupported_personal_claim_count"]
    out["unsupported_numeric_claim_count"] = claim_audit["unsupported_numeric_claim_count"]
    out["thin_input_specificity_violation_count"] = claim_audit["thin_input_specificity_violation_count"]
    out["surface_quality_defect_count"] = surface_audit["total_surface_quality_defects"]
    out.update(contract)
    return out


def hard_max_violation_count(study: dict[str, Any]) -> int:
    hard_max = study.get("hard_max_words")
    if hard_max is None:
        return 0
    actual = _hard_max_word_count(study)
    try:
        return 1 if actual > int(hard_max) else 0
    except (TypeError, ValueError):
        return 0


def enforce_study_hard_max_after_export_touchup(
    study: dict[str, Any],
    question: dict[str, Any],
    job: dict[str, Any],
) -> dict[str, Any]:
    """Re-compress if post-budget export touch-ups pushed a module over its hard max."""
    hard_max = study.get("hard_max_words")
    if hard_max is None:
        return study
    signals = collect_complexity_signals(question, job)
    budget = resolve_study_material_budget(question, job, signals=signals)
    out = dict(study)
    preserved = {
        key: out[key]
        for key in (
            "source_status",
            "fallback_status",
            "source_items_used",
            "source_types_used",
            "source_priority_used",
        )
        if key in out
    }
    model_insight = out.get("model_insight")
    for _ in range(3):
        if _hard_max_word_count(out) <= int(hard_max):
            break
        out = _compress_study_module(out, budget)
    if _hard_max_word_count(out) > int(hard_max):
        out = _force_under_hard_max(out, budget)
    out.update(preserved)
    if model_insight:
        out["model_insight"] = model_insight
    # Thin inputs must stay conservative in LENGTH even though their semantic depth is
    # preserved (§9): downstream export touch-ups can add fields (key_definitions,
    # model_insight, ...) after the budget-time ceiling ran, so re-apply the thin word
    # ceiling on the final assembled content. This tightens length only — it never
    # changes the study_depth category.
    if bool(out.get("thin_input_conservative")):
        out = _apply_thin_word_ceiling(out)
    actual = study_module_core_word_count(out)
    out["actual_word_count"] = actual
    # Canonical truthful refresh: this runs AFTER the recursive claim/surface
    # sanitiser, so it is the last point at which the module content matches what a
    # user can ever see. The initial status computed inside apply_adaptive_study_budget
    # audited pre-sanitisation content, so a defect that the sanitiser later removed
    # could leave a stale `structure_incomplete`. Re-derive the whole status from the
    # final content (contract coverage + a fresh integrity audit) using the single
    # canonical evaluator so tests, generators, and reports agree on the same truth.
    from app.agents.job_search.quality.claim_integrity import audit_claim_integrity
    from app.agents.job_search.quality.surface_quality_guard import audit_surface_quality

    contract = evaluate_depth_contract(out, budget.study_depth)
    integrity_blob = " ".join(
        str(out.get(key) or "") for key in _CONTENT_TEXT_KEYS if out.get(key)
    )
    claim_audit = audit_claim_integrity(integrity_blob, job)
    surface_audit = audit_surface_quality(integrity_blob, role=job.get("title") or "")
    integrity_clean = (
        claim_audit["unsupported_personal_claim_count"] == 0
        and claim_audit["unsupported_numeric_claim_count"] == 0
        and claim_audit["thin_input_specificity_violation_count"] == 0
        and surface_audit["total_surface_quality_defects"] == 0
    )
    thin = bool(out.get("thin_input_conservative"))
    status = evaluate_budget_status(
        actual,
        budget,
        contract_coverage=float(contract["depth_contract_coverage"]),
        substantive_coverage=float(contract["substantive_contract_coverage"]),
        thin_conservative=thin,
        integrity_clean=integrity_clean,
    )
    if _hard_max_word_count(out) > int(hard_max):
        status = "hard_limit_exceeded"
    out["budget_status"] = status
    out["unsupported_personal_claim_count"] = claim_audit["unsupported_personal_claim_count"]
    out["unsupported_numeric_claim_count"] = claim_audit["unsupported_numeric_claim_count"]
    out["thin_input_specificity_violation_count"] = claim_audit[
        "thin_input_specificity_violation_count"
    ]
    out["surface_quality_defect_count"] = surface_audit["total_surface_quality_defects"]
    out.update(contract)
    return out
