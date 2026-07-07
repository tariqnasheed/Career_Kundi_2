from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.agents.job_search.knowledge.question_intent import (
    INTENT_CALCULATION,
    INTENT_GENERAL,
    INTENT_PEER,
    INTENT_PRINCIPLES,
    INTENT_PRODUCTION,
    INTENT_SCENARIO,
    INTENT_TERMINOLOGY,
    detect_question_intent,
)
from app.agents.job_search.quality.surface_text_normalize import truncate_at_word

MIN_EXPERT_ANSWER_WORDS = 150
TARGET_EXPERT_ANSWER_WORDS = 220
MAX_EXPERT_ANSWER_WORDS = 500

_VERB_TO_GERUND = {
    "check": "checking",
    "verify": "verifying",
    "confirm": "confirming",
    "review": "reviewing",
    "document": "documenting",
    "track": "tracking",
    "identify": "identifying",
    "align": "aligning",
    "apply": "applying",
    "validate": "validating",
    "test": "testing",
    "inspect": "inspecting",
    "record": "recording",
    "escalate": "escalating",
    "protect": "protecting",
    "maintain": "maintaining",
    "avoid": "avoiding",
    "set": "setting",
    "monitor": "monitoring",
    # Skill-native workflow verbs (from expert `how_it_works` and skill-anchored steps).
    "establish": "establishing",
    "account": "accounting",
    "calculate": "calculating",
    "select": "selecting",
    "size": "sizing",
    "determine": "determining",
    "measure": "measuring",
    "plan": "planning",
    "design": "designing",
    "assess": "assessing",
    "estimate": "estimating",
    "compare": "comparing",
    "balance": "balancing",
    "allow": "allowing",
    "total": "totalling",
    "convert": "converting",
    "clarify": "clarifying",
    "prepare": "preparing",
    "execute": "executing",
    "evaluate": "evaluating",
    "install": "installing",
    "define": "defining",
    "build": "building",
    "run": "running",
    "gather": "gathering",
}


def clean_step(step: str) -> str:
    text = (step or "").strip().rstrip(".")
    text = re.sub(r"^\d+[\).\s-]+", "", text)
    return text.strip()


def to_gerund(phrase: str) -> str:
    words = phrase.split()
    if not words:
        return phrase
    first = words[0].lower().rstrip(",")
    if first in _VERB_TO_GERUND:
        words[0] = _VERB_TO_GERUND[first]
        return " ".join(words)
    return phrase


def to_spoken_step(phrase: str) -> str:
    text = clean_step(phrase)
    if not text:
        return ""
    words = text.split()
    first = words[0].lower().rstrip(",")
    if first in _VERB_TO_GERUND:
        return to_gerund(text)
    return f"reviewing {text.lower()}"


def to_workflow_step(phrase: str) -> tuple[str, str]:
    text = clean_step(phrase)
    if not text:
        return "", ""
    words = text.split()
    first = words[0].lower().rstrip(",")
    if first in _VERB_TO_GERUND:
        gerund = f"{_VERB_TO_GERUND[first]} {' '.join(words[1:])}"
        return gerund, text.lower()
    lower = text.lower()
    return f"reviewing {lower}", f"review {lower}"


def normalize_check_phrase(check: str) -> str:
    return to_spoken_step(check)


def human_join(items: list[str]) -> str:
    cleaned = [i.strip().rstrip(".") for i in items if i and i.strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0].lower()
    if len(cleaned) == 2:
        return f"{cleaned[0].lower()} and {cleaned[1].lower()}"
    return ", ".join(i.lower() for i in cleaned[:-1]) + f", and {cleaned[-1].lower()}"


def _expand_abbreviations(text: str) -> str:
    out = text
    out = re.sub(r"\bSOPs\b", "standard operating procedures (SOPs)", out, flags=re.I)
    out = re.sub(r"\bSOP\b", "standard operating procedure (SOP)", out, flags=re.I)
    return out


COMPLIANCE_EVIDENCE_BY_FAMILY: dict[str, str] = {
    "legal": "primary-source review, advice records, conflict screening, and documented assumptions",
    "technology": "access records, deployment logs, monitoring evidence, rollback proof, and secrets controls",
    "science_laboratory": "SOP records, calibration certificates, chain-of-custody notes, contamination logs, and QC sign-off",
    "education": "learning-outcome mapping, assessment records, safeguarding notes, and integrity review",
    "operations": "KPI records, bottleneck analysis, SOP audit trails, corrective-action logs, and shift handover notes",
    "healthcare": "patient-safety records, prescribing checks, monitoring notes, and escalation documentation",
    "electrical": "isolation records, test certificates, inspection evidence, and compliance sign-off",
    "architecture": "drawing revision logs, specification records, coordination notes, and compliance review",
    "public_administration": "policy records, audit trails, escalation notes, and decision documentation",
    "hospitality": "hygiene records, allergen controls, service timing logs, and quality checks",
    "data": "query logs, data-quality checks, lineage notes, and validation records",
    "human_resources": "case files, policy version records, investigation notes, and confidentiality controls",
    "mechanical_engineering": "calculation records, inspection evidence, safety margins, and test certificates",
    "finance": "reconciliation records, control checks, assumption logs, and reporting evidence",
    "project_management": "risk logs, change records, stakeholder notes, and decision rationale",
    "default": "source checks, records, review notes, and escalation where needed",
}


def render_compliance_naturally(
    standards: list[str],
    checks: list[str],
    *,
    safety_checks: list[str] | None = None,
    workflow_steps: list[str] | None = None,
    role_family: str = "default",
) -> str:
    _ = checks, safety_checks, workflow_steps
    evidence_text = COMPLIANCE_EVIDENCE_BY_FAMILY.get(role_family) or COMPLIANCE_EVIDENCE_BY_FAMILY["default"]

    named = [s for s in standards if _is_named_standard(s)]
    if named:
        return (
            f"For compliance, I would rely on {human_join(named[:3])}. "
            f"I would evidence the work through {evidence_text}."
        )
    if standards:
        # Only non-identifying placeholders were available (e.g. "applicable
        # standards"). Do NOT pretend to rely on a named standard (Defect Class
        # G) — make the gap explicit instead of hallucinating one.
        return (
            "No specific governing standard was specified for this work in the available information, "
            "so I would confirm which standard or documented procedure applies before proceeding, and "
            f"evidence the work through {evidence_text}."
        )
    return f"I would evidence the work through {evidence_text}."


# Real, identifying standards carry a code, number, or recognised scheme name.
# Generic words like "applicable standards" / "default standards" do not satisfy
# an explicit standard obligation (Defect Class G).
_NAMED_STANDARD_TOKENS: tuple[str, ...] = (
    "iso", "bs ", "iec", "en ", "astm", "din", "gdpr", "haccp", "osha", "nice",
    "ifrs", "gaap", "coshh", "reach", "sox", "hipaa", "pci", "nist", "gmp", "glp",
    "nec", "nfpa", "cdm", "sop", "bnf",
)


def _is_named_standard(standard: str) -> bool:
    s = (standard or "").strip()
    if not s:
        return False
    low = s.lower()
    if any(ch.isdigit() for ch in s):  # e.g. ISO 15189, BS 7671
        return True
    return any(tok in low for tok in _NAMED_STANDARD_TOKENS)


def render_spoken_workflow(steps: list[str], max_steps: int = 4) -> str:
    cleaned = [to_workflow_step(s) for s in steps if s]
    cleaned = [c for c in cleaned[:max_steps] if c[0]]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return f"I would start by {cleaned[0][0]}."
    if len(cleaned) == 2:
        return f"I would start by {cleaned[0][0]}. Then I would {cleaned[1][1]}."
    if len(cleaned) == 3:
        return (
            f"I would start by {cleaned[0][0]}. "
            f"Then I would {cleaned[1][1]}. "
            f"Before closing the task, I would {cleaned[2][1]}."
        )
    return (
        f"I would start by {cleaned[0][0]}. "
        f"Then I would {cleaned[1][1]}. "
        f"After that, I would {cleaned[2][1]}. "
        f"Before closing the task, I would {cleaned[3][1]}."
    )


def render_safety_naturally(safety_checks: list[str]) -> str:
    checks = [to_workflow_step(c)[1] for c in safety_checks[:3] if c and to_workflow_step(c)[1]]
    if not checks:
        return ""
    if len(checks) == 1:
        return f"I would also {checks[0]}."
    return f"I would also {human_join(checks)}."


def render_domain_anchor(terms: list[str]) -> str:
    picked = [t.strip() for t in terms[:4] if t and t.strip()]
    if len(picked) < 2:
        return ""
    return f"This work relies on {human_join(picked)}."


def expand_answer_if_short(answer: str, slots: dict[str, Any]) -> str:
    words = answer.split()
    if len(words) >= MIN_EXPERT_ANSWER_WORDS:
        return _expand_abbreviations(answer)
    paras = [p.strip() for p in answer.split("\n\n") if p.strip()]
    domain_anchor = render_domain_anchor(slots.get("tools_or_documents", []))
    if domain_anchor and domain_anchor.lower() not in answer.lower() and paras:
        paras[0] = f"{paras[0].rstrip('.')}. {domain_anchor}"
    mistake = str(slots.get("common_mistakes", [""])[0]).rstrip(".")
    if mistake and len(words) < 120 and mistake.lower()[:25] not in answer.lower():
        target = min(2, len(paras) - 1) if len(paras) > 1 else 0
        paras[target] = f"{paras[target].rstrip('.')}. A common mistake is {mistake.lower()}."
    out = "\n\n".join(paras)
    if len(out.split()) < 100:
        closing = slots.get("interview_ready_closing") or ""
        if closing and closing.lower() not in out.lower():
            out = f"{out}\n\n{closing}"
    return _expand_abbreviations(out)


GENERIC_CLOSING_PHRASE = "I would explain my method clearly and show how my checks protect quality and safety"

INTENT_CLOSINGS: dict[tuple[str, str], str] = {
    ("technology", INTENT_PEER): (
        "In an interview, I would show that I can balance reliable releases, least-privilege access, observability, and fast recovery."
    ),
    ("technology", INTENT_GENERAL): (
        "In an interview, I would show that I can deliver reliable releases with observable pipelines, least-privilege access, and tested rollback plans."
    ),
    # NOTE: data-family closings are intentionally NOT overridden here. A single
    # family-level closing forced every data sub-skill (Python/Excel/Dashboarding)
    # to close as SQL (Defect Class D). The skill-aware closing selected in
    # evidence_slot_builder._pick_closing is used instead, so the closing stays
    # aligned to the question's primary skill.
    ("hospitality", INTENT_TERMINOLOGY): (
        "In an interview, I would show that I understand consistency, hygiene, allergens, and service speed under pressure."
    ),
    ("healthcare", INTENT_SCENARIO): (
        "In an interview, I would show that I can connect pharmacology decisions to patient safety, monitoring, and documented escalation."
    ),
    ("legal", INTENT_TERMINOLOGY): (
        "In an interview, I would show that I can turn legal research into defensible advice grounded in primary authority."
    ),
    ("operations", INTENT_PRODUCTION): (
        "In an interview, I would show that I can improve flow with measured root-cause fixes and sustained process controls."
    ),
    ("operations", INTENT_PRINCIPLES): (
        "In an interview, I would show that I can improve flow with measured root-cause fixes and sustained process controls."
    ),
}

PEER_TEACHING_TRADEOFFS: dict[str, str] = {
    "technology": (
        "For a junior engineer, I would keep the explanation practical: permissions first, then deployment path, then monitoring and rollback. "
        "In production you trade deployment speed against control — faster pipelines improve throughput but need stronger release gates; "
        "least privilege improves security but can slow ad-hoc debugging unless break-glass access is documented. "
        "I watch deployment failure rate, MTTR, alarm coverage, and rollback time as measurable quality signals."
    ),
    "data": (
        "I would explain that good SQL starts with understanding the data model and the business question, not jumping to a query. "
        "You trade query flexibility against performance — wider selects are easier to write but cost more I/O; "
        "aggressive indexing speeds reads but can slow writes. "
        "I track query runtime, logical reads, data freshness, and error rate on production dashboards."
    ),
    "default": (
        "I would explain the concept in plain language first, then show where it fails in real work. "
        "Every method involves trade-offs between speed, control, and risk, so I name the quality signal I would monitor after changes."
    ),
}


def pick_intent_closing(role_family: str, intent: str, fallback: str) -> str:
    return INTENT_CLOSINGS.get((role_family, intent)) or fallback


def normalize_example_sentence(example: str) -> str:
    ex = (example or "").strip()
    if not ex:
        return ""
    if ex.lower().startswith("for example"):
        prefix = "For example,"
        body = ex[len("for example") :].lstrip(" ,")
    else:
        prefix = "For example,"
        body = ex
    body = body.rstrip(".")
    if body and body[0].isupper():
        body = body[0].lower() + body[1:]
    return f"{prefix} {body}."


def _format_example(example: str) -> str:
    return normalize_example_sentence(example)


def render_term_definitions(terms: list[dict[str, Any]], skill: str, role: str) -> str:
    lines = [f"In {role} work, the essential {skill} terms are practical safety and consistency controls.\n"]
    for term in terms[:6]:
        name = str(term.get("term") or "").strip()
        definition = str(term.get("definition") or "").strip().rstrip(".")
        if not name:
            continue
        lines.append(f"* **{name}** means {definition}.")
    return "\n".join(lines)


def _compliance_body(contract: dict[str, Any], slots: dict[str, Any]) -> str:
    role_family = str(contract.get("role_family") or "default")
    compliance = render_compliance_naturally(
        slots.get("standards_or_regulations", []),
        slots.get("quality_checks", []),
        safety_checks=slots.get("safety_checks", []),
        workflow_steps=slots.get("practical_steps", []),
        role_family=role_family,
    )
    safety = render_safety_naturally(slots.get("safety_checks", []))
    parts = [compliance]
    if safety and safety.lower() not in (compliance or "").lower():
        parts.append(safety)
    return " ".join(p for p in parts if p)


def _diagnostic_core_answer(calc: dict[str, Any], skill: str) -> str:
    prompt = str(calc.get("prompt") or "").lower()
    if "select *" in prompt and "index" in prompt:
        return (
            "An index seek on user_id can locate matching rows quickly, but SELECT * still performs poorly because the database must fetch every column for each matched row. "
            "That usually means a key lookup to the heap or clustered index (bookmark lookup), which adds I/O beyond the index seek itself. "
            "Extra columns increase memory use, network transfer, and buffer churn, so cache efficiency drops. "
            "If the index is not covering, the optimiser still has to visit the base table for non-key columns. "
            "I would select only needed columns, add or use a covering index where justified, inspect the execution plan, and compare logical reads or runtime before and after."
        )
    answer = str(calc.get("answer") or "").strip()
    steps = [str(s).strip() for s in (calc.get("steps") or []) if s]
    if answer and steps:
        return f"{answer} {' '.join(steps[:2]).rstrip('.')}."
    if answer:
        return answer if answer.endswith(".") else answer + "."
    return (
        f"For {skill}, I would state the measurable relationship first, show the calculation or diagnostic logic, "
        f"then compare the result against the acceptable limit before acting."
    )


def build_terminology_definition_answer(contract: dict[str, Any], slots: dict[str, Any]) -> str:
    skill = str(contract.get("mapped_skill") or "General")
    role = str(contract.get("role") or "Professional")
    role_family = str(contract.get("role_family") or "default")
    terms = list(slots.get("terminology_terms") or [])
    definitions = render_term_definitions(terms, skill, role)
    steps = slots.get("practical_steps") or []
    first_step = to_spoken_step(str(steps[0])) if steps else "following the documented workflow"
    application = (
        f"I would apply these terms by {first_step.rstrip('.')} "
        f"and using each definition as a control point during real {skill} work."
    )
    compliance = _compliance_body(contract, slots)
    mistake = str(slots.get("common_mistakes", ["Skipping required checks."])[0]).rstrip(".")
    closing = pick_intent_closing(role_family, INTENT_TERMINOLOGY, slots["interview_ready_closing"])
    answer = (
        f"{definitions}\n\n{application}\n\n"
        f"{compliance} A common mistake is {mistake.lower()}.\n\n{closing}"
    )
    return expand_answer_if_short(answer, slots)


def build_calculation_or_diagnostic_answer(contract: dict[str, Any], slots: dict[str, Any]) -> str:
    skill = str(contract.get("mapped_skill") or "General")
    role_family = str(contract.get("role_family") or "default")
    calc = slots.get("calculation_pack") or {}
    diagnostic = _diagnostic_core_answer(calc, skill)
    workflow = render_spoken_workflow(slots.get("practical_steps", []))
    compliance = _compliance_body(contract, slots)
    mistake = str(slots.get("common_mistakes", ["Joining tables without understanding cardinality."])[0]).rstrip(".")
    if role_family == "data" and not slots.get("family_workflow_is_foreign"):
        example = (
            "Illustrative example: on a revenue dashboard, a data analyst could identify many-to-many joins "
            "inflating aggregation totals, validate data quality on source freshness, inspect the execution plan "
            "for query performance, and compare runtime before and after the change."
        )
    else:
        example = _format_example(slots.get("role_specific_example", ""))
    closing = pick_intent_closing(role_family, INTENT_CALCULATION, slots["interview_ready_closing"])
    answer = (
        f"{diagnostic}\n\n"
        f"In practice, {workflow}\n\n"
        f"{compliance} A common mistake is {mistake.lower()}. {example}\n\n"
        f"{closing}"
    )
    return expand_answer_if_short(answer, slots)


def _skill_native_tradeoff_body(slots: dict[str, Any]) -> str:
    """Skill-native peer-teaching body used when the family default is foreign (§5)."""
    parts: list[str] = []
    explanation = str(slots.get("skill_native_explanation") or "").strip()
    if explanation:
        parts.append(explanation if explanation.endswith(".") else explanation + ".")
    mechanisms = [str(m).strip() for m in (slots.get("skill_native_mechanism") or []) if str(m).strip()]
    if mechanisms:
        parts.append("Key mechanisms I would make sure a junior understands: " + "; ".join(mechanisms[:3]) + ".")
    parts.append(
        "Every choice trades off simplicity, performance, and maintainability, so I name the "
        "quality signal I would check after a change rather than guessing."
    )
    return " ".join(parts)


def build_peer_teaching_answer(contract: dict[str, Any], slots: dict[str, Any]) -> str:
    role_family = str(contract.get("role_family") or "default")
    if slots.get("family_workflow_is_foreign") and slots.get("skill_native_explanation"):
        tradeoffs = _skill_native_tradeoff_body(slots)
    else:
        tradeoffs = PEER_TEACHING_TRADEOFFS.get(role_family) or PEER_TEACHING_TRADEOFFS["default"]
    workflow = render_spoken_workflow(slots.get("practical_steps", []))
    compliance = _compliance_body(contract, slots)
    mistake = str(slots.get("common_mistakes", ["Skipping required checks."])[0]).rstrip(".")
    example = _format_example(slots.get("role_specific_example", ""))
    closing = pick_intent_closing(role_family, INTENT_PEER, slots["interview_ready_closing"])
    answer = (
        f"{slots['direct_definition'].rstrip('.')}.\n\n"
        f"{tradeoffs}\n\n"
        f"{workflow}\n\n"
        f"{compliance} A common mistake is {mistake.lower()}. {example}\n\n"
        f"{closing}"
    )
    return expand_answer_if_short(answer, slots)


def build_production_issue_metrics_answer(contract: dict[str, Any], slots: dict[str, Any]) -> str:
    role_family = str(contract.get("role_family") or "default")
    workflow = render_spoken_workflow(slots.get("practical_steps", []))
    compliance = _compliance_body(contract, slots)
    mistake = str(slots.get("common_mistakes", ["Joining tables without understanding cardinality."])[0]).rstrip(".")
    if role_family == "data" and not slots.get("family_workflow_is_foreign"):
        example = (
            "Illustrative example: on a revenue dashboard, a data analyst could identify many-to-many joins "
            "inflating aggregation totals, validate data quality on source freshness, inspect the execution plan "
            "for query performance, and compare runtime before and after the change."
        )
    else:
        example = _format_example(slots.get("role_specific_example", ""))
    issue_block = (
        "A production issue of this kind is a failure with measurable customer or service impact. "
        "A strong answer would diagnose root cause using logs, execution evidence, and controlled comparisons "
        "rather than assumptions, then remove the bottleneck or defect and add monitoring or validation so any "
        "recurrence would be visible early."
    )
    closing = pick_intent_closing(role_family, INTENT_PRODUCTION, slots["interview_ready_closing"])
    answer = (
        f"{slots['direct_definition'].rstrip('.')}.\n\n"
        f"{issue_block}\n\n"
        f"Under pressure, {workflow}\n\n"
        f"{compliance} A common mistake is {mistake.lower()}. {example}\n\n"
        f"{closing}"
    )
    return expand_answer_if_short(answer, slots)


def build_principles_workflow_answer(contract: dict[str, Any], slots: dict[str, Any]) -> str:
    skill = str(contract.get("mapped_skill") or "General")
    role = str(contract.get("role") or "Professional")
    role_family = str(contract.get("role_family") or "default")
    principles = [str(p).strip().rstrip(".") for p in (slots.get("principles") or [])[:5] if p]
    if not principles:
        principles = [f"apply {skill} with documented controls", "verify outputs before sign-off"]
    principle_lines = "\n".join(f"* {p}." for p in principles[:5])
    workflow = render_spoken_workflow(slots.get("practical_steps", []))
    compliance = _compliance_body(contract, slots)
    mistake = str(slots.get("common_mistakes", ["Skipping required checks."])[0]).rstrip(".")
    example = _format_example(slots.get("role_specific_example", ""))
    closing = pick_intent_closing(role_family, INTENT_PRINCIPLES, slots["interview_ready_closing"])
    answer = (
        f"For {role}, the governing principles for {skill} are:\n{principle_lines}\n\n"
        f"The standard workflow is: {workflow}\n\n"
        f"{compliance} A common mistake is {mistake.lower()}. {example}\n\n"
        f"{closing}"
    )
    return expand_answer_if_short(answer, slots)



MAX_COMPLIANCE_WORKFLOW_SIMILARITY = 0.62


def compliance_workflow_overlap_ratio(answer: str) -> float:
    paras = [p.strip() for p in (answer or "").split("\n\n") if p.strip()]
    if len(paras) < 3:
        return 0.0
    return SequenceMatcher(None, paras[1].lower(), paras[2].lower()).ratio()


def build_technical_explain_answer(contract: dict[str, Any], slots: dict[str, Any]) -> str:
    workflow = render_spoken_workflow(slots.get("practical_steps", []))
    role_family = str(contract.get("role_family") or "default")
    compliance = render_compliance_naturally(
        slots.get("standards_or_regulations", []),
        slots.get("quality_checks", []),
        safety_checks=slots.get("safety_checks", []),
        workflow_steps=slots.get("practical_steps", []),
        role_family=role_family,
    )
    safety = render_safety_naturally(slots.get("safety_checks", []))
    mistake = str(slots.get("common_mistakes", ["Skipping required checks."])[0]).rstrip(".")
    example = _format_example(slots.get("role_specific_example", ""))

    body_parts = [compliance]
    if safety and safety.lower() not in (compliance or "").lower():
        body_parts.append(safety)
    body_parts.append(f"A common mistake is {mistake.lower()}.")
    body_parts.append(example)
    body = " ".join(p for p in body_parts if p)

    if role_family == "data":
        workflow = f"{workflow.rstrip('.')}. I monitor join cardinality, data quality, and query performance before publishing results"

    answer = (
        f"{slots['direct_definition'].rstrip('.')}.\n\n"
        f"{workflow}\n\n"
        f"{body}\n\n"
        f"{slots['interview_ready_closing']}"
    )
    return expand_answer_if_short(answer, slots)


def build_scenario_answer(contract: dict[str, Any], slots: dict[str, Any]) -> str:
    workflow = render_spoken_workflow(slots.get("practical_steps", []))
    role_family = str(contract.get("role_family") or "default")
    compliance = render_compliance_naturally(
        slots.get("standards_or_regulations", []),
        slots.get("quality_checks", []),
        safety_checks=slots.get("safety_checks", []),
        workflow_steps=slots.get("practical_steps", []),
        role_family=role_family,
    )
    safety = render_safety_naturally(slots.get("safety_checks", []))
    mistake = str(slots.get("common_mistakes", ["Skipping required checks."])[0]).rstrip(".")
    example = _format_example(slots.get("role_specific_example", ""))

    body_parts = [compliance]
    if safety:
        body_parts.append(safety)
    body_parts.append(f"A common error to avoid is {mistake.lower()}.")
    body_parts.append(example)
    body = " ".join(p for p in body_parts if p)

    answer = (
        f"{slots['direct_definition'].rstrip('.')}.\n\n"
        f"In a high-pressure case, {workflow}\n\n"
        f"{body}\n\n"
        f"{slots['interview_ready_closing']}"
    )
    return expand_answer_if_short(answer, slots)


_INTENT_BUILDERS = {
    INTENT_TERMINOLOGY: build_terminology_definition_answer,
    INTENT_CALCULATION: build_calculation_or_diagnostic_answer,
    INTENT_SCENARIO: build_scenario_answer,
    INTENT_PRODUCTION: build_production_issue_metrics_answer,
    INTENT_PEER: build_peer_teaching_answer,
    INTENT_PRINCIPLES: build_principles_workflow_answer,
    INTENT_GENERAL: build_technical_explain_answer,
}


def compile_answer(contract: dict[str, Any], slots: dict[str, Any]) -> str:
    intent = str(slots.get("question_intent") or INTENT_GENERAL)
    builder = _INTENT_BUILDERS.get(intent, build_technical_explain_answer)
    return builder(contract, slots)


def build_study_module_from_slots(contract: dict[str, Any], slots: dict[str, Any]) -> dict[str, Any]:
    role = str(contract.get("role") or "this role")
    skill = str(contract.get("mapped_skill") or "this skill")
    question = str(contract.get("question") or "")
    method = [s for s in slots.get("practical_steps", []) if s]
    standards = slots.get("standards_or_regulations", []) or []
    tools = slots.get("tools_or_documents", []) or []
    tool_hint = human_join(tools[:3]) if tools else skill
    standard_hint = human_join(standards[:2]) if standards else "the relevant technical reference"
    return {
        "what_this_question_tests": (
            f"Whether you can answer this {skill} interview question for {role}: "
            f"{truncate_at_word(question, 120)}"
        ),
        "beginner_explanation": (
            f"At beginner level, {skill} in {role} work means knowing the task objective, "
            f"the tools or records involved ({tool_hint}), and the minimum checks before handover."
        ),
        "intermediate_explanation": (
            f"At intermediate level, each {skill} step should map to {standard_hint} "
            f"and each check should prevent a named failure mode in live {role} delivery."
        ),
        "advanced_explanation": (
            f"At advanced level, manage edge cases in {skill} without compromising safety or auditability: "
            f"interpret borderline readings, coordinate conflicting constraints, and document corrective action."
        ),
        "key_terms": tools[:8],
        "step_by_step_method": method[:6],
        "formula_or_framework": standards[:4],
        "worked_example": slots.get("role_specific_example", ""),
        "troubleshooting_checklist": slots.get("quality_checks", [])[:5] + slots.get("safety_checks", [])[:3],
        "common_mistakes": slots.get("common_mistakes", [])[:5],
        "interview_traps": [
            f"Answering '{truncate_at_word(question, 60)}' with theory only and no {skill} method.",
            "Claiming compliance without naming the standard or verification check.",
        ],
        "mini_practice_task": (
            f"Draft a {skill} response for {role}: list four execution steps, name {standard_hint}, "
            f"state two checks you would perform, and one realistic failure mode your checks would catch."
        ),
        "follow_up_questions": [
            "Which check would you do first and why?",
            f"What changes in {skill} execution when time pressure increases?",
        ],
    }
