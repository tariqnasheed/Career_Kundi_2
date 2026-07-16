"""
Expert interview content engine.

Produces:
- Study material = pure subject knowledge (definitions, how it works, facts, worked examples)
- Model answers = the actual words spoken in the interview (first person, substantive)
- Answer explanation = brief factual summary of key points covered (not interview coaching)
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.agents.job_search.knowledge.coverage_planner import is_archetype_legacy_question_type
from app.agents.job_search.knowledge.domains import classify_skill_domain, get_domain_foundation
from app.agents.job_search.knowledge.evidence_packs import get_evidence_pack, get_evidence_pack_for_question, resolve_role_family
from app.agents.job_search.quality.claim_integrity import collect_user_claim_context
from app.agents.job_search.knowledge.core_technical_content import (
    get_calculation_pack,
    get_principles_pack,
    get_terminology_pack,
)
from app.agents.job_search.knowledge.expert_content_library import resolve_expert_content
from app.agents.job_search.knowledge.answer_builders import (
    MAX_EXPERT_ANSWER_WORDS,
    MIN_EXPERT_ANSWER_WORDS,
    build_study_module_from_slots,
    compile_answer,
    render_compliance_naturally,
    render_spoken_workflow,
)
from app.agents.job_search.knowledge.question_obligations import (
    Obligation,
    get_question_obligation_profile,
    is_pure_motivation_profile,
)
from app.agents.job_search.knowledge.answer_compressor import compress_compiled_answer
from app.agents.job_search.knowledge.evidence_slot_builder import (
    build_evidence_slots,
    validate_evidence_slots,
)
from app.agents.job_search.knowledge.normalize import normalize_key, title_case_skill
from app.agents.job_search.knowledge.question_contracts import create_question_contract
from app.agents.job_search.quality.answer_quality_gate import validate_answer
from app.agents.job_search.quality.broken_template_audit import broken_template_count
from app.agents.job_search.quality.compiler_boilerplate_audit import universal_boilerplate_count
from app.agents.job_search.quality.domain_density_audit import domain_density_breakdown, domain_density_from_context
from app.agents.job_search.quality.expert_naturalness_audit import (
    expert_naturalness_score,
    formulaic_spoken_label_count,
)
from app.agents.job_search.quality.evidence_slot_audit import (
    audit_evidence_slots,
    sanitize_evidence_slots,
)
from app.agents.job_search.quality.evidence_normalizer import normalize_evidence_slots
from app.agents.job_search.quality.final_surface_quality_gate import (
    ensure_final_terminal_punctuation,
    validate_final_surface,
)
from app.agents.job_search.quality.generic_phrase_audit import generic_phrase_count
from app.agents.job_search.quality.key_term_quality_audit import is_valid_key_term
from app.agents.job_search.quality.skill_card_consumption_audit import skill_card_consumption_score
from app.agents.job_search.quality.study_depth_audit import (
    study_depth_score,
    validate_study_material,
)
from app.agents.job_search.quality.surface_text_normalize import truncate_at_word

_KNOWLEDGE_PATH = Path(__file__).parent / "skill_knowledge.json"

GENERIC_PHRASES = (
    "core competency for",
    "deliver reliable outcomes",
    "interviewers reward",
    "how to answer better",
    "i'd start by asking what they already know",
    "core concepts to cover",
    "this module prepares you for",
    "mirrors expert teaching practice",
    "this answer succeeds because",
    "tools, techniques, and practices used to deliver outcomes",
    "[specific problem]",
    "[measurable outcome]",
)

_ROLE_FAMILY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "healthcare": ("nurse", "pharmacist", "doctor", "gp", "physio", "radiograph", "clinical", "therapist"),
    "engineering": ("engineer", "electrician", "mechanical", "civil engineer", "chemical", "structural", "maintenance"),
    "technology": ("software", "developer", "data", "devops", "cyber", "cloud", "qa"),
    "creative_media": ("architect", "designer", "journalist", "writer", "editor", "media", "creative"),
    "finance_legal": ("accountant", "finance", "investment", "analyst", "solicitor", "paralegal", "compliance"),
    "education": ("teacher", "lecturer", "tutor", "teaching assistant"),
    "public_admin": ("civil service", "policy", "administrator", "public"),
}

_BANNED_OPENERS = (
    "In simple terms,",
    "The way I explain",
    "I describe",
    "One strong example",
    "A memorable",
    "For this role,",
    "In this role,",
    "When I explain",
    "For ",
    "I handled",
    "In one busy",
    "I had a high-pressure",
)

_ANSWER_PROMPT_BLUEPRINTS: dict[str, dict[str, str]] = {
    "explain": {
        "healthcare": (
            "Role={role}. Skill={skill}. Responsibility={responsibility}. "
            "Write a clear clinical explanation in three parts: "
            "1) what the skill is in practice, 2) how it is executed safely, 3) what checks prevent harm. "
            "Must include one protocol/standard and one concrete quality signal."
        ),
        "engineering": (
            "Role={role}. Skill={skill}. Responsibility={responsibility}. "
            "Write a practical engineering explanation: method sequence, verification tests, and compliance checkpoint. "
            "Include one standard and one measurable acceptance criterion."
        ),
        "default": (
            "Role={role}. Skill={skill}. Responsibility={responsibility}. "
            "Write a practical, non-generic explanation covering process, controls, and a real-world check."
        ),
    },
    "scenario": {
        "default": (
            "Role={role}. Skill={skill}. Responsibility={responsibility}. "
            "Write a concise STAR/CAR scenario with real constraints, method used, technical verification, and measurable outcome."
        )
    },
}


@lru_cache(maxsize=1)
def _load_knowledge() -> dict[str, Any]:
    if not _KNOWLEDGE_PATH.is_file():
        return {"skills": {}, "roles": {}}
    from app.agents.job_search.knowledge.source_sanitizer import sanitize_knowledge_payload

    payload = json.loads(_KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    return sanitize_knowledge_payload(payload)


def get_skill_knowledge(skill: str) -> dict[str, Any]:
    data = _load_knowledge()
    key = normalize_key(skill)
    if key in data.get("skills", {}):
        return data["skills"][key]
    domain = classify_skill_domain(skill)
    foundation = get_domain_foundation(domain)
    skill_t = title_case_skill(skill)
    return {
        "skill": skill_t,
        "domain": domain,
        "definition": foundation["field_intro"],
        "principles": foundation["core_principles"],
        "key_concepts": foundation["core_principles"][:5],
        "related_concepts": foundation["methodology"][:4],
    }


def get_role_context(role_title: str) -> dict[str, Any]:
    data = _load_knowledge()
    key = normalize_key(role_title)
    if key in data.get("roles", {}):
        return data["roles"][key]
    return {
        "role_name": role_title,
        "responsibilities": [],
        "required_skills": [],
    }


def is_generic_content(text: str) -> bool:
    if not text or len(text.strip()) < 80:
        return True
    lowered = text.lower()
    return sum(1 for p in GENERIC_PHRASES if p in lowered) >= 2


def polish_spoken_answer(text: str, q: dict, job: dict) -> str:
    """
    Convert templated/reference prose into interview-ready spoken wording.
    Keeps technical substance but removes robotic scaffolding language.
    """
    if not text:
        return text
    role = job.get("title") or "this role"
    skill = q.get("skill_tag") or "this area"
    qtype = q.get("question_type") or ""
    out = text
    family = _role_family(role)

    def _pick(options: list[str], tag: str) -> str:
        idx = abs(hash(f"{normalize_key(role)}::{normalize_key(skill)}::{qtype}::{tag}")) % len(options)
        return options[idx]

    def _role_artifact(role_family: str) -> str:
        return {
            "healthcare": "medication chart and handover note",
            "engineering": "permit sheet and inspection log",
            "technology": "runbook and incident ticket",
            "creative_media": "drawing set and design brief",
            "education": "lesson plan and progress record",
            "legal_finance": "control checklist and audit trail",
            "public_admin": "case file and service record",
            "general": "work log and sign-off note",
        }.get(role_family, "work log and sign-off note")

    # Strip common template scaffolding.
    out = re.sub(rf"^In this {re.escape(role)} context,\s*", "", out, flags=re.I)
    out = re.sub(r"^In this [A-Za-z0-9 \-/]+ context,\s*", "", out, flags=re.I)
    out = out.replace("The critical discipline is evidence:", "The key thing I focus on is")
    out = out.replace("When conditions change, I revalidate assumptions before proceeding", "If conditions change, I reassess quickly before moving forward")
    out = out.replace("Operational excellence requires explicit controls, measurable checks, and documented decision points.", "I use clear checks and document decisions.")

    # Normalize punctuation artifacts from stitched templates.
    out = re.sub(r"\.\.\s*", ". ", out)
    out = re.sub(r"\s{2,}", " ", out).strip()

    # Pull a concrete impact sentence if present.
    impact = ""
    for sent in re.split(r"(?<=[.!?])\s+", out):
        if any(tok in sent.lower() for tok in ("dropped", "reduced", "improved", "stabil", "prevent", "%", "zero", "within", "faster")):
            impact = sent.strip()
            break
    if impact and any(p in impact.lower() for p in ("i'd explain", "the way i explain", "in simple terms")):
        impact = ""

    # Avoid repeated canned openers.
    for opener in _BANNED_OPENERS:
        if out.startswith(opener):
            out = re.sub(r"^[^,]*,\s*", "", out).strip()
            break

    # Build concise spoken variants by archetype, using simple words.
    if qtype in {"terminology", "principles", "calculation", "procedure"}:
        # Keep technical depth for study-heavy archetypes.
        return out

    if qtype in {"explain", "explain_to_peer"}:
        role_phrase = {
            "healthcare": "keep patients safe",
            "engineering": "do safe and correct work",
            "technology": "run systems in a stable way",
            "creative_media": "turn ideas into clear designs people can use",
            "education": "help learners improve",
            "legal_finance": "make correct and compliant decisions",
            "public_admin": "deliver public service clearly and fairly",
            "general": "do the work well and safely",
        }.get(family, "do the work well and safely")
        artifact = _role_artifact(family)
        base = _pick(
            [
                f"My approach to {title_case_skill(skill)} in {role} is simple: do the work in order, check each step, and fix issues early so we {role_phrase}.",
                f"Good {title_case_skill(skill)} work in {role} means clear steps, clear checks, and clear notes; that is how we {role_phrase}.",
                f"In day-to-day {role} work, {title_case_skill(skill)} is the method I use to keep quality steady, using checkpoints and a clean {artifact}.",
                f"A practical way to explain {title_case_skill(skill)} is this: set the goal, run the task, verify the output, and record decisions in the {artifact}.",
            ],
            "explain_simple",
        )
        if impact:
            clean_impact = re.sub(r"^\s*(a real example:)\s*", "", impact, flags=re.I)
            base += f" A real example: {clean_impact}"
        return base

    if qtype in {"scenario", "complex_problem"}:
        artifact = _role_artifact(family)
        base = _pick(
            [
                f"A tough {title_case_skill(skill)} issue came up during a busy {role} shift. I ranked risks first, fixed the highest-risk item, then verified the result before sign-off.",
                f"During one {role} case, {title_case_skill(skill)} became the main risk. I split the problem into small checks, resolved each one, and logged actions in the {artifact}.",
                f"Under time pressure in {role}, I used a short {title_case_skill(skill)} plan: contain the issue, test the fix, confirm the outcome, then close with complete notes.",
                f"When {title_case_skill(skill)} failed in a live {role} task, I stabilised the situation, followed the checklist, and confirmed the handover record was complete.",
            ],
            "scenario_simple",
        )
        if impact:
            clean_impact = re.sub(r"^\s*(outcome:)\s*", "", impact, flags=re.I)
            clean_impact = re.sub(r"^\s*(outcome:)\s*", "", clean_impact, flags=re.I)
            base += f" Outcome: {clean_impact}"
        return base

    if qtype == "calculation":
        if "Problem:" in out and "Answer:" in out:
            return out
        return (
            f"For {skill}, I state the formula first, substitute values with units, then compare the result against the relevant limit or target. "
            f"I always document assumptions so the calculation can be checked."
        )

    if qtype == "principles":
        return _pick(
            [
                f"For {skill}, my rule set in {role} is simple: follow standards first, execute in sequence, and verify before sign-off.",
                f"The three anchors for {skill} in {role} are governance, sequence, and verification.",
                f"In {role} delivery, {skill} works best when standards, checkpoints, and documentation are treated as non-negotiable.",
            ],
            "principles_open",
        )

    if qtype == "terminology":
        return _pick(
            [
                f"I define each term clearly, then connect it to how we use it in real {role} work.",
                f"My approach is to keep definitions short and practical, then show where each term affects decisions in {role}.",
                f"I separate vocabulary into safety, process, and quality terms so each definition is easy to apply on the job.",
            ],
            "terminology_open",
        )

    if qtype == "procedure":
        return (
            f"I follow the procedure step-by-step in order, confirm safety checks at each stage, and escalate immediately if any trigger threshold is hit. "
            f"I document actions in real time so the handover is clear."
        )

    # Default: trim and keep human-readable.
    words = out.split()
    if len(words) > 140:
        out = " ".join(words[:140]).rstrip(" ,;:.") + "."
    return out


def _retrieve_evidence_pack(skill: str, job: dict, q: dict | None = None) -> dict:
    """Multi-retriever stage: role context + expert + term/principle/calc packs."""
    exp = _expert(skill, job)
    role = job.get("title") or "Professional"
    role_ctx = get_role_context(role)
    resp = (role_ctx.get("responsibilities") or [None])[0]
    if not resp:
        resp = (job.get("responsibilities") or ["core duties"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    skill_card = (q or {}).get("skill_card") if q else None
    terms_pack = (skill_card or {}).get("source_packs", {}).get("terminology") or get_terminology_pack(skill, role, str(resp or ""))
    principles_pack = (skill_card or {}).get("source_packs", {}).get("principles") or get_principles_pack(skill, role, str(resp or ""))
    calc_pack = (skill_card or {}).get("source_packs", {}).get("calculation") or get_calculation_pack(skill, role, str(resp or ""))
    domain = classify_skill_domain(skill, role)
    return {
        "role": role,
        "responsibility": resp or "core duties",
        "domain": domain,
        "family": _role_family(role),
        "definition": exp.get("definition", ""),
        "steps": exp.get("how_it_works", [])[:4],
        "facts": exp.get("key_facts", [])[:4],
        "standards": exp.get("standards", [])[:2],
        "example": exp.get("complex_answer", ""),
        "terms": terms_pack.get("terms", [])[:6],
        "principles": principles_pack.get("principles", [])[:6],
        "operating_steps": principles_pack.get("operating_steps", [])[:5],
        "calc": calc_pack,
        "employer_expectation": (skill_card or {}).get("employer_expectation", ""),
        "core_concepts": (skill_card or {}).get("core_concepts", []),
        "common_mistakes": (skill_card or {}).get("common_mistakes", []),
    }


def _prompt_blueprint(kind: str, pack: dict, skill: str) -> str:
    family = pack.get("family", "default")
    bp = _ANSWER_PROMPT_BLUEPRINTS.get(kind, {})
    tmpl = bp.get(family) or bp.get("default") or ""
    return tmpl.format(
        role=pack["role"],
        skill=title_case_skill(skill),
        responsibility=pack["responsibility"],
    )


def _compose_explain_answer(skill: str, pack: dict) -> str:
    """Reason + writer stage for explain archetype (prompt-engineered template)."""
    role = pack["role"]
    skill_t = title_case_skill(skill)
    duty = str(pack["responsibility"]).lower()
    steps = pack["operating_steps"] or pack["steps"] or [f"apply {skill_t} method", "verify output", "document results"]
    facts = pack["facts"] or [f"{skill_t} quality depends on disciplined execution"]
    stds = pack["standards"] or []
    terms = [t.get("term") for t in pack.get("terms", []) if isinstance(t, dict) and t.get("term")]

    _ = _prompt_blueprint("explain", pack, skill)
    sentence1 = f"In {role} work, {skill_t} is the disciplined way we deliver {duty} with consistent quality."
    sentence2 = (
        f"My workflow is: {steps[0].lower()}, then {steps[1].lower()}, then "
        f"{steps[2].lower() if len(steps) > 2 else 'final verification and documentation'}."
    )
    sentence3 = f"The key control is {facts[0].lower()}."
    sentence4 = f"I check compliance against {', '.join(stds)} before sign-off." if stds else ""
    sentence5 = f"Core terms I watch closely are {', '.join(terms[:3])}." if terms else ""
    sentence6 = f"What employers expect is this: {pack.get('employer_expectation')}" if pack.get("employer_expectation") else ""
    return " ".join(s for s in (sentence1, sentence2, sentence3, sentence4, sentence5, sentence6) if s)


def _compose_scenario_answer(skill: str, pack: dict) -> str:
    """Reason + writer stage for scenario archetype (concise STAR, non-generic)."""
    role = pack["role"]
    skill_t = title_case_skill(skill)
    duty = str(pack["responsibility"]).lower()
    facts = pack["facts"] or [f"{skill_t} requires controlled execution"]
    example = pack["example"] or f"In {role}, I resolved a complex {skill_t} issue affecting {duty}."
    stds = pack["standards"] or []
    _ = _prompt_blueprint("scenario", pack, skill)
    s1 = f"On a {role} assignment involving {duty}, we hit a high-risk {skill_t} issue under time pressure."
    s2 = "I defined constraints first, ran a controlled sequence, and validated each checkpoint before release."
    s3 = f"A critical technical point was {facts[0].lower()}."
    s4 = f"I verified the fix against {', '.join(stds)}." if stds else ""
    s5 = example
    s6 = f"I specifically avoided this common mistake: {pack['common_mistakes'][0].lower()}." if pack.get("common_mistakes") else ""
    return " ".join(s for s in (s1, s2, s3, s4, s5, s6) if s)


def _role_family(role_title: str) -> str:
    role = (role_title or "").lower()
    for family, keys in _ROLE_FAMILY_KEYWORDS.items():
        if any(k in role for k in keys):
            return family
    return "general"


def _question_archetype(question: str, category: str, q: dict | None = None) -> str:
    if q and q.get("question_type"):
        return q["question_type"]
    qtext = (question or "").lower()
    if category == "behavioral":
        return "behavioral"
    if category == "hr":
        return "hr"
    if category == "daily_routine":
        return "daily_routine"
    if category == "system_design":
        return "system_design"
    # Motivation / company-fit before calculation: role-context suffixes often mention
    # skills like "Load calculations" which must not override genuine fit questions.
    if any(
        m in qtext
        for m in (
            "excites you",
            "why do you want",
            "why are you interested",
            "interested in this role",
            "interested in joining",
            "interested in working",
            "good fit",
            "a fit for",
            "fit for this role",
            "fit for the role",
            "experience help",
            "experience make you",
            "make you a good fit",
            "background fit",
            "want to work here",
            "want to join",
            "why this role",
            "why us",
            "why our",
            "drawn to",
            "attracts you",
            "what motivates you",
        )
    ):
        return "motivation"
    if "what do you know about" in qtext:
        return "company_research"
    if "calculation" in qtext or "quantitative" in qtext:
        return "calculation"
    if "essential technical terms" in qtext or "define and explain these core" in qtext:
        return "terminology"
    if "core operating principles" in qtext or "standard workflow" in qtext:
        return "principles"
    if "walk through" in qtext and any(w in qtext for w in ("procedure", "assessment", "isolation", "administration", "reconciliation")):
        return "procedure"
    if "explain" in qtext and ("teammate" in qtext or "never used" in qtext or "never heard" in qtext):
        return "explain_to_peer"
    if "complex problem" in qtext or "most challenging" in qtext or "hardest" in qtext:
        return "complex_problem"
    if "design a system" in qtext or "walk through your approach" in qtext:
        return "system_design"
    if "first day" in qtext or "day-one" in qtext or "typical working day" in qtext:
        return "daily_routine"
    if "junior" in qtext or "senior" in qtext or "mid-level" in qtext:
        return "seniority"
    if "case study" in qtext or "practical task" in qtext:
        return "case_study"
    if "core competencies" in qtext or "successful as" in qtext:
        return "role_competencies"
    if "tell me about a time" in qtext or "describe a" in qtext:
        return "behavioral"
    return "technical_general"


def _expert(skill: str, job: dict) -> dict:
    role = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    data = _load_knowledge()
    role_k = normalize_key(role)
    sk = normalize_key(skill)
    roles = data.get("roles", {})
    if role_k in roles and sk in roles[role_k].get("skill_expert", {}):
        return roles[role_k]["skill_expert"][sk]
    skills = data.get("skills", {})
    if sk in skills and skills[sk].get("expert"):
        return skills[sk]["expert"]
    return resolve_expert_content(skill, role, resp)


def build_study_material(q: dict, job: dict) -> dict:
    """Pure subject-matter study module — no interview coaching."""
    skill = q.get("skill_tag") or q.get("category", "General").replace("_", " ").title()
    category = q.get("category", "technical")
    role_title = job.get("title") or "this role"
    role_ctx = get_role_context(role_title)
    archetype = _question_archetype(q.get("question", ""), category, q)

    if archetype in {
        "explain",
        "explain_to_peer",
        "scenario",
        "complex_problem",
        "technical_general",
        "terminology",
        "principles",
        "calculation",
        "procedure",
    }:
        contract = create_question_contract(q, job)
        slots = normalize_evidence_slots(sanitize_evidence_slots(build_evidence_slots(contract, q, job)))
        slot_audit_failures = audit_evidence_slots(slots, contract)
        module = build_study_module_from_slots(contract, slots)
        failures = validate_study_material(module)
        if slot_audit_failures:
            failures = list(dict.fromkeys(failures + slot_audit_failures))
        if failures:
            module.setdefault("quality_audit", {})
            module["quality_audit"]["study_failures"] = failures
        module.setdefault("quality_audit", {})
        module["quality_audit"]["study_depth_score"] = study_depth_score(module)
        return module

    if archetype == "terminology":
        return _terminology_study(q, job)

    if archetype == "calculation":
        return _calculation_study(q, job)

    if archetype == "principles":
        return _principles_study(q, job)

    if archetype == "procedure":
        return _procedure_study(q, job)

    if category == "behavioral" or archetype == "behavioral":
        return _behavioral_study(q, job, role_ctx)

    if category == "hr" or archetype == "hr":
        return _hr_study(q, job, role_ctx)

    if category == "daily_routine" or archetype in {"daily_routine", "day_one"}:
        return _daily_routine_study(q, job, role_ctx)

    if archetype == "seniority" or q.get("question_type") == "seniority":
        return _seniority_study(q, job, role_ctx)

    if archetype in {"case_study", "practical_task", "problem_solving", "tools", "standards", "responsibility"}:
        return _coverage_question_study(q, job, role_ctx)

    if archetype in {"motivation", "company_research"}:
        return _motivation_study(q, job, role_ctx)

    if category == "system_design" or archetype == "system_design":
        return _system_design_study(q, job, role_ctx)

    exp = _expert(skill, job)
    skill_t = title_case_skill(skill)

    definitions = [{"term": skill_t, "definition": exp["definition"]}]
    for std in exp.get("standards", [])[:4]:
        definitions.append({"term": std.split("(")[0].strip(), "definition": f"Applicable standard/regulation: {std}."})

    skill_explanations = [{"skill": skill_t, "explanation": exp["teaching_body"]}]
    for rs in (q.get("related_skills") or [])[:2]:
        if normalize_key(rs) != normalize_key(skill):
            rel = _expert(rs, job)
            skill_explanations.append({"skill": title_case_skill(rs), "explanation": rel["definition"]})

    return {
        "overview": exp["teaching_body"],
        "what_you_need_to_know_first": exp["key_facts"][:3],
        "definitions": definitions,
        "skill_explanations": skill_explanations,
        "principles": exp["key_facts"],
        "key_concepts": exp.get("related_topics", []) + exp["key_facts"][:3],
        "step_by_step_breakdown": exp["how_it_works"],
        "explanations": [exp["teaching_body"]] + ([exp["definition"]] if exp["definition"] != exp["teaching_body"] else []),
        "practical_example": exp["complex_answer"],
        "common_mistakes": exp.get("technical_pitfalls", []),
        "how_to_answer_better": [],  # intentionally empty — subject-only material
        "practice_exercises": [
            f"Draw a diagram showing how {skill_t} applies to: {(role_ctx.get('responsibilities') or ['typical work'])[0]}.",
            f"List the standards that govern {skill_t} in {role_title} work.",
            f"Write out the verification steps after completing a {skill_t} task.",
        ],
        "revision_notes": exp["key_facts"][:6],
        "related_concepts": exp.get("related_topics", []),
        "estimated_reading_time_minutes": 12,
    }


# §13: generic "employer expectation" coaching (from generated role context) can
# unconditionally instruct candidates to show measurable outcomes / scale. For
# unknown or thin provenance that contradicts the provenance-aware guidance in the
# same module and pressures invention. We soften only the metric-pressure clauses and
# preserve role-specific, non-metric expectations unchanged.
_METRIC_PRESSURE_RE = re.compile(
    r"\b(measurable outcomes|measurable results|quantified results|with scale\b|"
    r"dates and scale|numbers and scale)",
    re.I,
)
_METRIC_PRESSURE_CAVEAT = "only where you genuinely have them"


def _soften_metric_pressure_principles(principles: list[str]) -> list[str]:
    softened: list[str] = []
    for principle in principles:
        text = str(principle).strip()
        if not text:
            continue
        if _METRIC_PRESSURE_RE.search(text):
            if re.search(r"concrete examples with scale", text, re.I):
                text = (
                    "Use concrete examples with context, constraints, and stakeholders — "
                    f"include scale or measurable outcomes {_METRIC_PRESSURE_CAVEAT}."
                )
            elif _METRIC_PRESSURE_CAVEAT not in text.lower():
                text = text.rstrip(".") + f" — {_METRIC_PRESSURE_CAVEAT}."
        softened.append(text)
    return softened


def _behavioral_study(q: dict, job: dict, role_ctx: dict) -> dict:
    role_title = job.get("title") or "this role"
    resp = (role_ctx.get("responsibilities") or ["professional duties"])[0]
    qtext = q.get("question") or ""
    family = _role_family(role_title)
    # §13: behavioral study guidance must be provenance-aware. When the user has NOT
    # provided genuine experience (unknown / not_provided provenance), we must not
    # instruct them to close with quantified results, use dates/scale, or treat
    # hypothetical practice as a mistake — that pressures invention. We invite a real
    # example where they have one, numbers only when genuinely known, and clearly
    # hypothetical practice otherwise. When explicit experience exists we keep the
    # stronger "use your real numbers" guidance without weakening their claims.
    _claim_ctx = collect_user_claim_context(job)
    _has_experience = _claim_ctx["has_explicit_experience"] and not _claim_ctx["job_thin"]
    if _has_experience:
        _detail_principle = (
            "Specific details you genuinely have — dates, scale, names of standards, measurable "
            "results — distinguish strong candidates."
        )
        _close_step = "Close with the real outcome and what changed afterwards, including your genuine numbers."
        _behavioral_mistakes = [
            "Vague, generic answers with no concrete detail from your own experience.",
            "Inventing metrics, dates, or events you cannot actually support.",
            "Blaming others without showing your personal action and decisions.",
        ]
        _practice_exercise = (
            f"Write a 300-word account of a real {role_title} challenge, using your genuine numbers where you have them."
        )
        _fallback_principles = [
            "Describe real past events with the outcomes you genuinely achieved.",
            "Show what you personally did — not only what the team did.",
        ]
    else:
        _detail_principle = (
            "Include specific details — dates, scale, measurable results — only where you genuinely "
            "have them; qualitative evidence (what changed, what you learned) is equally valid."
        )
        _close_step = (
            "Close with the outcome and what changed — include numbers only if you genuinely know them, "
            "otherwise describe the qualitative result honestly."
        )
        _behavioral_mistakes = [
            "Inventing metrics, dates, employers, or events you cannot support.",
            "Staying so vague there is no concrete method or decision to assess.",
            "Blaming others without showing your personal action and decisions.",
        ]
        _practice_exercise = (
            f"Practise a 300-word STAR answer using a real {role_title} example if you have one, or a "
            f"clearly hypothetical scenario if not — add numbers only if you genuinely know them, never invented ones."
        )
        _fallback_principles = [
            "Use a real example from your experience where possible; a clearly hypothetical practice scenario is fine otherwise.",
            "Show what you personally did or would do — without inventing history you do not have.",
        ]
    family_concepts = {
        "healthcare": ["Patient safety", "Escalation protocol", "Clinical documentation", "Multidisciplinary handover"],
        "engineering": ["Safety-critical checks", "Verification testing", "Standards compliance", "Root-cause analysis"],
        "technology": ["Incident response", "Observability", "Trade-off decisions", "Postmortem actions"],
        "finance_legal": ["Regulatory accuracy", "Evidence quality", "Material risk", "Audit trail"],
        "education": ["Learning outcomes", "Assessment evidence", "Safeguarding", "Differentiation"],
        "public_admin": ["Policy execution", "Service metrics", "Stakeholder coordination", "Governance controls"],
        "general": ["Accountability", "Communication", "Judgement", "Execution discipline"],
    }
    _principles = list(role_ctx.get("what_employers_expect", [])[:4]) or list(_fallback_principles)
    if not _has_experience:
        _principles = _soften_metric_pressure_principles(_principles)
        if not any(
            "genuinely" in p.lower() or "hypothetical" in p.lower() for p in _principles
        ):
            _principles = _fallback_principles[:1] + _principles
        _principles = _principles[:4]
    return {
        "what_this_question_tests": f"How to structure a STAR response for: {truncate_at_word(qtext, 120)}",
        "overview": (
            f"This module supports the interview prompt: {truncate_at_word(qtext, 120)}. "
            f"It covers professional situations a {role_title} handles when {resp.lower()}."
        ),
        "what_you_need_to_know_first": [
            f"{role_title} work involves {resp.lower()} under time, safety, and quality constraints.",
            "Employers look for evidence of judgement, communication, and ownership in past events.",
            _detail_principle,
        ],
        "definitions": [
            {"term": role_title, "definition": role_ctx.get("summary", f"Professional responsible for {resp.lower()}.")},
            {"term": "Accountability", "definition": "Personal ownership of decisions and outcomes, not passive participation."},
        ],
        "skill_explanations": [],
        "principles": _principles,
        "key_concepts": family_concepts.get(family, family_concepts["general"]),
        "step_by_step_breakdown": [
            "Identify a real situation with clear stakes in this field.",
            "State your specific responsibility — not the group's generic goal.",
            "Walk through actions in sequence: decisions, tools, communication.",
            _close_step,
        ],
        "explanations": [
            f"Strong examples for {role_title} reference {resp.lower()} and relevant standards or tools.",
        ],
        "practical_example": build_model_answer(q, job),
        "common_mistakes": _behavioral_mistakes,
        "how_to_answer_better": [],
        "practice_exercises": [
            _practice_exercise,
            f"Link the story to: {resp}.",
        ],
        "revision_notes": (role_ctx.get("required_skills") or [])[:4],
        "related_concepts": role_ctx.get("skill_clusters", []),
        "estimated_reading_time_minutes": 8,
    }


def _motivation_study(q: dict, job: dict, role_ctx: dict) -> dict:
    role_title = job.get("title") or "this role"
    qtext = q.get("question") or ""
    resp = (role_ctx.get("responsibilities") or ["professional duties"])[0]
    skills = role_ctx.get("required_skills") or role_ctx.get("skill_clusters") or []
    skill_hint = skills[0] if skills else "core role skills"
    # §13: keep motivation guidance provenance-aware — do not pressure an invented
    # "measurable result" when the user has provided no genuine experience.
    _mot_ctx = collect_user_claim_context(job)
    _mot_has_exp = _mot_ctx["has_explicit_experience"] and not _mot_ctx["job_thin"]
    _link_step = (
        "Link it to a past achievement with a measurable result you genuinely have."
        if _mot_has_exp
        else "Link it to a genuine achievement or a skill you are developing — add a measurable result only if you truly have one."
    )
    return {
        "what_this_question_tests": (
            f"Whether you can connect genuine motivation to this {role_title} posting: {truncate_at_word(qtext, 120)}"
        ),
        "beginner_explanation": (
            f"Employers expect specifics about {role_title} duties such as {resp.lower()}, "
            f"not generic enthusiasm copied from a careers website."
        ),
        "intermediate_explanation": (
            f"Strong answers tie posted requirements to your track record in {skill_hint} "
            f"and name what you will contribute in the first 90 days."
        ),
        "advanced_explanation": (
            f"Discuss how duties such as {resp.lower()} and skills like {skill_hint} align with "
            f"what you want to develop — keep the focus on motivation and contribution, not technical steps."
        ),
        "interview_application": (
            f"Keep your answer focused on why this {role_title} posting attracts you: cite specific "
            f"duties such as {resp.lower()}, connect them to genuine interests or skills, and state "
            f"what you hope to contribute — not a technical procedure."
        ),
        "step_by_step_method": [
            f"Quote one responsibility from the {role_title} posting.",
            _link_step,
            "State one skill you will apply immediately in the team.",
        ],
        "common_mistakes": [
            "Praising the employer without citing the actual posting.",
            "Repeating mission statements with no personal evidence.",
        ],
        "interview_traps": [
            f"Saying you like {role_title} work without naming a specific duty from the advert.",
        ],
        "mini_practice_task": (
            f"Draft a 120-word answer connecting {role_title} responsibilities to one achievement from your experience."
        ),
        "worked_example": build_model_answer(q, job),
    }


def _system_design_study(q: dict, job: dict, role_ctx: dict) -> dict:
    role_title = job.get("title") or "this role"
    return {
        "overview": (
            "System design is the discipline of structuring components, data flows, storage, and failure modes "
            "to meet functional requirements under scale, latency, availability, and cost constraints."
        ),
        "what_you_need_to_know_first": [
            "Clarify users, use cases, and scale before choosing technologies.",
            "Non-functional requirements (latency p99, availability, durability) drive architecture.",
            "Every design has tradeoffs — CAP, consistency vs latency, cost vs redundancy.",
        ],
        "definitions": [
            {"term": "Scalability", "definition": "Ability to handle load growth by adding resources horizontally or vertically."},
            {"term": "Availability", "definition": "Fraction of time service is usable — e.g. 99.9% ≈ 8.76 h downtime/year."},
            {"term": "Latency percentile", "definition": "p95/p99 measure tail performance — averages hide user pain."},
        ],
        "skill_explanations": [],
        "principles": [
            "Requirements → estimation → high-level diagram → deep dive → bottlenecks → monitoring.",
            "Design for failure: retries, idempotency, circuit breakers, graceful degradation.",
            "Stateless app tier; push state to databases, caches, queues with clear consistency models.",
        ],
        "key_concepts": ["Load balancing", "Caching", "Sharding", "Message queues", "CDN", "Database replication"],
        "step_by_step_breakdown": [
            "Enumerate functional requirements and estimate QPS, storage, bandwidth.",
            "Sketch clients → gateway → services → data stores; label sync/async paths.",
            "Pick data model and partition key for even load distribution.",
            "Add cache for hot reads; queue for async work; CDN for static assets.",
            "Identify SPOFs; add redundancy; define SLIs/SLOs and on-call runbooks.",
        ],
        "explanations": [
            "Back-of-envelope math validates feasibility before detailed design.",
            f"For {role_title}, tie components to real operational responsibilities.",
        ],
        "practical_example": (
            "URL shortener at 10k writes/s: hash-based ID generation → write to Cassandra by short_id → "
            "async replicate to read replicas → Redis cache for 95% reads → 301 redirect from edge CDN "
            "for popular links. p99 redirect <50 ms globally."
        ),
        "common_mistakes": [
            "Single database without replication for HA.",
            "No idempotency on write APIs — duplicates under retries.",
            "Ignoring thundering herd on cache expiry.",
        ],
        "how_to_answer_better": [],
        "practice_exercises": [
            "Design a rate limiter: token bucket vs sliding window — write API and storage choice.",
            "Estimate storage for 5 years of 1B daily events with 2 KB average size.",
        ],
        "revision_notes": ["QPS estimate", "Partition key", "Cache strategy", "Failure modes"],
        "related_concepts": ["CAP theorem", "Consistent hashing", "Event sourcing"],
        "estimated_reading_time_minutes": 15,
    }


def _terminology_study(q: dict, job: dict) -> dict:
    skill = q.get("skill_tag") or "General"
    role = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    terms = q.get("terminology_terms")
    if not terms:
        pack = get_terminology_pack(skill, role, resp)
        terms = pack["terms"]
        overview = pack["study_overview"]
    else:
        overview = f"Core terminology for {title_case_skill(skill)} — precise definitions required for {role} interviews."
    skill_t = title_case_skill(skill)
    return {
        "overview": overview,
        "what_you_need_to_know_first": [
            "Interviewers expect exact definitions, not vague paraphrases.",
            "Link each term to when you use it in daily work.",
            f"Know how {skill_t} terms relate to applicable standards and workflows.",
        ],
        "definitions": terms,
        "skill_explanations": [{"skill": t["term"], "explanation": t["definition"]} for t in terms[:8]],
        "principles": [f"{t['term']}: {t['definition']}" for t in terms[:6]],
        "key_concepts": [t["term"] for t in terms],
        "step_by_step_breakdown": [
            "State the term clearly.",
            "Give a one-sentence definition.",
            "Add one practical example from professional use.",
            "Note any standard, regulation, or metric tied to the term.",
        ],
        "explanations": [f"**{t['term']}** — {t['definition']}" for t in terms[:8]],
        "practical_example": "\n".join(f"• {t['term']}: {t['definition']}" for t in terms[:5]),
        "common_mistakes": [
            "Confusing similar-sounding terms (e.g. capacity vs capability).",
            "Defining acronyms without expanding them first.",
            "Using jargon without explaining underlying mechanism.",
        ],
        "how_to_answer_better": [],
        "practice_exercises": [
            f"Write flashcards for all {skill_t} terms — term on front, definition + example on back.",
            f"Explain each term to a non-specialist in one sentence.",
            "Group terms into categories (safety, measurement, process, documentation).",
        ],
        "revision_notes": [t["term"] for t in terms[:10]],
        "related_concepts": [t["term"] for t in terms],
        "estimated_reading_time_minutes": 10,
    }


def _calculation_study(q: dict, job: dict) -> dict:
    skill = q.get("skill_tag") or "General"
    role = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    calc = q.get("calculation") or get_calculation_pack(skill, role, resp)
    skill_t = title_case_skill(skill)
    if calc:
        steps = calc.get("steps") or []
        return {
            "overview": f"Quantitative problem for {skill_t}: show working, state units, verify against limits.",
            "what_you_need_to_know_first": [
                "Write given values before calculating.",
                "State formula, substitute, show units.",
                "Compare result to standard limits or business targets.",
            ],
            "definitions": [
                {"term": "Given data", "definition": calc["prompt"]},
                {"term": "Expected result", "definition": calc["answer"]},
            ],
            "skill_explanations": [],
            "principles": steps,
            "key_concepts": ["Formula selection", "Unit consistency", "Sanity check", "Documentation"],
            "step_by_step_breakdown": steps or [
                "Identify knowns and unknowns.",
                "Select appropriate formula or method.",
                "Calculate with units; round appropriately.",
                "Interpret result in context (pass/fail, safe/unsafe, feasible/infeasible).",
            ],
            "explanations": [calc["answer"]] + [f"Step: {s}" for s in steps],
            "practical_example": calc["answer"],
            "common_mistakes": [
                "Unit conversion errors (kN vs N, mg vs g).",
                "Using wrong formula for support/loading conditions.",
                "Quoting tabulated values without verifying edition/date of standard.",
            ],
            "how_to_answer_better": [],
            "practice_exercises": [
                f"Re-derive this {skill_t} calculation from memory with different input values.",
                "Identify which variable has most sensitivity if estimate is wrong.",
            ],
            "revision_notes": steps[:6],
            "related_concepts": [skill_t, "Dimensional analysis", "Factor of safety"],
            "estimated_reading_time_minutes": 12,
        }
    return {
        "overview": f"For {skill_t}, identify measurable quantities on typical {role} tasks — loads, doses, rates, margins.",
        "what_you_need_to_know_first": [
            "Name what you would measure on site or in clinic.",
            "State how you would calculate or estimate it.",
            "Explain how the number drives a decision.",
        ],
        "definitions": [{"term": skill_t, "definition": _expert(skill, job)["definition"]}],
        "skill_explanations": [],
        "principles": _expert(skill, job).get("key_facts", [])[:4],
        "key_concepts": ["Measurement", "Estimation", "Thresholds", "Verification"],
        "step_by_step_breakdown": [
            "Identify the quantity (load, dose, flow, cost, latency).",
            "State data sources and instruments.",
            "Apply formula or rule of thumb.",
            "Compare to limit and document.",
        ],
        "explanations": [],
        "practical_example": _expert(skill, job).get("complex_answer", ""),
        "common_mistakes": ["Hand-waving without numbers", "Wrong precision for context"],
        "how_to_answer_better": [],
        "practice_exercises": [f"List three numeric checks you perform when using {skill_t}."],
        "revision_notes": [],
        "related_concepts": [skill_t],
        "estimated_reading_time_minutes": 8,
    }


def _principles_study(q: dict, job: dict) -> dict:
    skill = q.get("skill_tag") or "General"
    role = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    pack = get_principles_pack(skill, role, resp)
    skill_t = pack["skill"]
    return {
        "overview": f"Operating principles for {skill_t} — how work is executed to standard in {role} roles.",
        "what_you_need_to_know_first": [
            pack["definition"],
            "Principles are non-negotiable rules; workflow is the ordered application of those rules.",
        ],
        "definitions": [{"term": skill_t, "definition": pack["definition"]}],
        "skill_explanations": [{"skill": skill_t, "explanation": p} for p in pack["principles"][:4]],
        "principles": pack["principles"],
        "key_concepts": pack["principles"][:5],
        "step_by_step_breakdown": pack["operating_steps"],
        "explanations": pack["principles"],
        "practical_example": "\n".join(f"{i + 1}. {s}" for i, s in enumerate(pack["operating_steps"])),
        "common_mistakes": [
            "Skipping verification or documentation steps.",
            "Applying method without checking prerequisites.",
            "Treating principles as optional under time pressure.",
        ],
        "how_to_answer_better": [],
        "practice_exercises": [
            f"Draw a flowchart of {skill_t} workflow from start to sign-off.",
            "List stop-work triggers at each stage.",
        ],
        "revision_notes": pack["principles"][:6],
        "related_concepts": pack["principles"],
        "estimated_reading_time_minutes": 12,
    }


def _procedure_study(q: dict, job: dict) -> dict:
    skill = q.get("skill_tag") or "Clinical procedure"
    steps = q.get("procedure_steps") or []
    role = job.get("title") or "Professional"
    return {
        "overview": f"Structured procedure for {title_case_skill(skill)} — sequence and safety checks for {role}.",
        "what_you_need_to_know_first": [
            "Procedures must be performed in order; skipping steps risks harm or invalid results.",
            "Communication and documentation are part of the procedure, not afterthoughts.",
        ],
        "definitions": [{"term": title_case_skill(skill), "definition": f"Standardised sequence for {skill} in professional practice."}],
        "skill_explanations": [],
        "principles": steps,
        "key_concepts": steps[:5],
        "step_by_step_breakdown": steps,
        "explanations": [f"Step {i + 1}: {s}" for i, s in enumerate(steps)],
        "practical_example": "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps)),
        "common_mistakes": [
            "Reordering safety-critical steps.",
            "Failing to escalate when findings exceed protocol thresholds.",
            "Incomplete documentation of times, doses, or observations.",
        ],
        "how_to_answer_better": [],
        "practice_exercises": [
            "Recite the procedure from memory; time yourself.",
            "Identify which step triggers escalation to senior staff.",
        ],
        "revision_notes": steps,
        "related_concepts": ["SBAR", "NEWS2", "Five rights", "Permit to work"],
        "estimated_reading_time_minutes": 10,
    }


def must_use_contract_compiler(question: dict, contract: dict | None) -> bool:
    if question.get("mapped_skills"):
        return True
    if question.get("skill_card_id"):
        return True
    if question.get("skill_card"):
        return True
    if contract and contract.get("mapped_skills"):
        return True
    if contract and contract.get("role_family") and contract.get("role_family") != "default":
        return True
    if question.get("mapped_skill"):
        return True
    return False


def _rebuild_answer_from_clean_slots(q: dict, job: dict, contract: dict) -> tuple[str, dict]:
    if "invalid_key_term" in (q.get("quality_audit") or {}):
        contract["required_domain_terms"] = [
            t for t in (contract.get("required_domain_terms") or []) if is_valid_key_term(str(t))
        ]
    slots = normalize_evidence_slots(sanitize_evidence_slots(build_evidence_slots(contract, q, job)))
    answer = compile_answer(contract, slots)
    answer, _ = ensure_final_terminal_punctuation(answer)
    return answer, slots


def _compile_and_validate_answer(q: dict, job: dict, contract: dict) -> str:
    retries = 0
    rejections = 0
    slots = normalize_evidence_slots(sanitize_evidence_slots(build_evidence_slots(contract, q, job)))
    slot_failures = validate_evidence_slots(slots, contract)
    slot_audit_failures = audit_evidence_slots(slots, contract)
    slot_failures = list(dict.fromkeys(slot_failures + slot_audit_failures))
    while slot_failures and retries < 2:
        retries += 1
        rejections += 1
        slots = normalize_evidence_slots(sanitize_evidence_slots(build_evidence_slots(contract, q, job)))
        slot_failures = validate_evidence_slots(slots, contract)
        slot_audit_failures = audit_evidence_slots(slots, contract)
        slot_failures = list(dict.fromkeys(slot_failures + slot_audit_failures))

    answer = compile_answer(contract, slots)
    q["evidence_slots"] = slots
    role_family = resolve_role_family(contract.get("role", ""), contract.get("role_family"))
    pack = get_evidence_pack_for_question(
        role_family,
        contract.get("role", ""),
        contract.get("skill", "") or q.get("skill_tag", ""),
    )
    answer_failures = validate_answer(answer, contract, slots)
    q.setdefault("quality_audit", {})
    q["quality_audit"]["slot_failures"] = slot_failures
    q["quality_audit"]["slot_rejection_count"] = rejections
    q["quality_audit"]["slot_retry_count"] = retries
    q["quality_audit"]["answer_failures"] = answer_failures
    q["quality_audit"]["generic_phrase_count"] = generic_phrase_count(answer)
    q["quality_audit"]["broken_template_count"] = broken_template_count(answer)
    q["quality_audit"]["universal_boilerplate_count"] = universal_boilerplate_count(answer)
    q["quality_audit"]["skill_card_consumption_score"] = skill_card_consumption_score(answer, contract, slots)
    density_breakdown = domain_density_breakdown(
        answer, contract, slots, card=q.get("skill_card"), pack=pack
    )
    q["quality_audit"]["domain_density"] = density_breakdown["domain_density_score"]
    q["quality_audit"]["core_domain_term_coverage"] = density_breakdown["core_domain_term_coverage"]
    q["quality_audit"]["standard_tool_coverage"] = density_breakdown["standard_tool_coverage"]
    q["quality_audit"]["workflow_term_coverage"] = density_breakdown["workflow_term_coverage"]
    q["quality_audit"]["expert_naturalness_score"] = expert_naturalness_score(answer, contract, slots)
    q["quality_audit"]["formulaic_spoken_label_count"] = formulaic_spoken_label_count(answer)

    compressed, compression_shape_ok = compress_compiled_answer(
        answer,
        contract.get("role", ""),
        contract.get("mapped_skill", ""),
        min_words=MIN_EXPERT_ANSWER_WORDS,
        max_words=MAX_EXPERT_ANSWER_WORDS,
    )
    if compression_shape_ok and len(answer.split()) > MAX_EXPERT_ANSWER_WORDS:
        compressed_failures = validate_answer(compressed, contract, slots)
        compressed_consumption = skill_card_consumption_score(compressed, contract, slots)
        compressed_density = domain_density_from_context(
            compressed, contract, slots, card=q.get("skill_card"), pack=pack
        )
        compressed_naturalness = expert_naturalness_score(compressed, contract, slots)
        if (
            compressed_consumption >= 50
            and compressed_density >= 35
            and compressed_naturalness >= 70
            and formulaic_spoken_label_count(compressed) == 0
            and "broken_template_detected" not in compressed_failures
            and "legacy_template_leaked" not in compressed_failures
            and "universal_boilerplate_detected" not in compressed_failures
        ):
            answer = compressed
            q["quality_audit"]["compression_applied"] = 1
            q["quality_audit"]["compression_rejected"] = 0
        else:
            q["quality_audit"]["compression_applied"] = 0
            q["quality_audit"]["compression_rejected"] = 1
    else:
        q["quality_audit"]["compression_applied"] = 0
        q["quality_audit"]["compression_rejected"] = 1

    if slot_failures or answer_failures:
        retries += 1
        answer, slots = _rebuild_answer_from_clean_slots(q, job, contract)
        second_failures = validate_answer(answer, contract, slots)
        q["quality_audit"]["answer_failures_after_retry"] = second_failures
        q["quality_audit"]["slot_retry_count"] = retries

    answer, punctuation_ok = ensure_final_terminal_punctuation(answer)
    final_surface_failures = validate_final_surface(answer, q, contract)
    if final_surface_failures:
        answer, slots = _rebuild_answer_from_clean_slots(q, job, contract)
        answer, punctuation_ok = ensure_final_terminal_punctuation(answer)
        final_surface_failures = validate_final_surface(answer, q, contract)

    if not punctuation_ok and "truncated_example" not in final_surface_failures:
        final_surface_failures.append("truncated_example")

    q["quality_audit"]["final_surface_failures"] = final_surface_failures
    q["quality_audit"]["invalid_key_term_count"] = final_surface_failures.count("invalid_key_term")
    q["quality_audit"]["empty_compliance_slot_count"] = final_surface_failures.count("empty_compliance_slot")
    q["quality_audit"]["truncated_example_count"] = final_surface_failures.count("truncated_example")
    q["quality_audit"]["paragraph_merge_count"] = final_surface_failures.count("paragraph_merge_detected")
    q["quality_audit"]["universal_boilerplate_count"] = universal_boilerplate_count(answer)
    q["quality_audit"]["expert_naturalness_score"] = expert_naturalness_score(answer, contract, slots)
    q["quality_audit"]["formulaic_spoken_label_count"] = formulaic_spoken_label_count(answer)
    final_density = domain_density_breakdown(
        answer, contract, slots, card=q.get("skill_card"), pack=pack
    )
    q["quality_audit"]["domain_density"] = final_density["domain_density_score"]
    q["quality_audit"]["core_domain_term_coverage"] = final_density["core_domain_term_coverage"]
    q["quality_audit"]["standard_tool_coverage"] = final_density["standard_tool_coverage"]
    q["evidence_slots"] = slots

    blocked = bool(final_surface_failures)
    if blocked:
        family = resolve_role_family(job.get("title") or "", q.get("role_family"))
        if family in {"creative_design", "creative_media", "creator_trending", "sports"} or is_archetype_legacy_question_type(
            q.get("question_type")
        ):
            fallback = _archetype_coverage_answer(q, job, get_role_context(job.get("title") or "Professional"))
            if fallback and len(fallback.split()) >= MIN_EXPERT_ANSWER_WORDS:
                q["export_blocked"] = False
                q["quality_audit"]["blocked_export_count"] = 0
                q["quality_gate_status"] = "passed_with_archetype_fallback"
                q["answer_source"] = "legacy_template"
                return fallback
    q["quality_audit"]["blocked_export_count"] = int(blocked)
    q["export_blocked"] = blocked
    q["answer_source"] = "contract_compiler"
    q["used_legacy_polisher"] = False
    q["used_fallback_template"] = False
    q["quality_gate_status"] = "passed" if not blocked else "failed"
    if blocked:
        q["regeneration_required"] = True
        return ""
    return answer


def build_model_answer(q: dict, job: dict) -> str:
    """Direct first-person interview answer — substantive, no coaching framework."""
    category = q.get("category", "technical")
    skill = q.get("skill_tag") or ""
    role_title = job.get("title") or "Professional"
    question = q.get("question", "")
    archetype = _question_archetype(question, category, q)
    role_ctx = get_role_context(role_title)
    resp = (role_ctx.get("responsibilities") or ["core duties"])[0]

    if category == "behavioral" or archetype == "behavioral":
        q["answer_source"] = "legacy_template"
        return _behavioral_answer(q, job, role_ctx)

    if category == "hr" or archetype == "hr":
        q["answer_source"] = "legacy_template"
        return _hr_answer(q, job, role_ctx)

    # §10: a role-motivation / company-fit question must get a motivation answer
    # (why this role, posting fit, contribution, honest relevance to genuine
    # background) — not a technical workflow. The provenance-aware `_hr_answer`
    # already produces this and never invents user history, so reuse it rather than
    # letting the question fall through to the technical contract compiler.
    if category == "motivation" or archetype == "motivation":
        q["answer_source"] = "legacy_template"
        return _hr_answer(q, job, role_ctx)

    if archetype == "company_research" or category == "company_specific":
        q["answer_source"] = "legacy_template"
        return _hr_answer(q, job, role_ctx)

    if is_archetype_legacy_question_type(q.get("question_type")):
        q["answer_source"] = "legacy_template"
        return _archetype_coverage_answer(q, job, role_ctx)

    if category == "daily_routine" or archetype in {"daily_routine", "day_one"}:
        q["answer_source"] = "legacy_template"
        return _daily_routine_answer(q, job, role_ctx)

    if archetype == "seniority" or q.get("question_type") == "seniority":
        q["answer_source"] = "legacy_template"
        return _seniority_answer(q, job, role_ctx)

    if archetype in {"case_study", "practical_task", "problem_solving"} and skill:
        q["answer_source"] = "legacy_template"
        evidence = _retrieve_evidence_pack(skill, job, q)
        answer = _compose_scenario_answer(skill, evidence)
        profile = get_question_obligation_profile(q, job)
        obs = set(profile.obligations)
        segments = [answer]
        if Obligation.SCENARIO_REASONING.value in obs:
            segments.append(_build_scenario_segment(q, job, role_ctx))
        modifier = _build_modifier_segments(q, job, profile)
        if modifier:
            segments.append(modifier)
        return " ".join(segments)

    if archetype == "tools" and skill:
        q["answer_source"] = "legacy_template"
        exp = _expert(skill, job)
        skill_t = title_case_skill(skill)
        return (
            f"As {role_title}, I use {skill_t} daily for {resp.lower()}. "
            f"I rely on {exp['how_it_works'][0].lower() if exp.get('how_it_works') else 'documented workflows'} "
            f"and verify outputs with peer review or automated checks before release. "
            f"A concrete example: I configured {skill_t} for a recurring deliverable, added validation gates, "
            f"and reduced rework after stakeholders signed off the template. "
            f"I avoid tool sprawl — I master the features that affect quality and traceability, "
            f"and I document version, owner, and rollback steps for anything production-facing."
        )

    if archetype == "standards" and skill:
        q["answer_source"] = "legacy_template"
        exp = _expert(skill, job)
        std = exp.get("standards", ["applicable standards"])[0] if exp.get("standards") else "applicable standards"
        return (
            f"In {role_title} work on {resp.lower()}, I treat {std} as the baseline for every {title_case_skill(skill)} task. "
            f"Before starting I confirm scope, hazards, and permit/isolation requirements; during execution I record "
            f"measurements and deviations; before handover I complete checklists and escalate anything outside tolerance. "
            f"If a standard is unclear I stop and obtain written clarification — I do not improvise on safety or governance. "
            f"That discipline keeps audits clean and prevents repeat incidents."
        )

    if category == "system_design" or archetype == "system_design":
        q["answer_source"] = "legacy_template"
        return _system_design_answer(job, role_ctx)

    contract = create_question_contract(q, job)
    if must_use_contract_compiler(q, contract):
        return _compile_and_validate_answer(q, job, contract)

    if archetype == "terminology":
        q["answer_source"] = "legacy_template"
        return _terminology_answer(q, job)

    if archetype == "calculation":
        q["answer_source"] = "legacy_template"
        return _calculation_answer(q, job)

    if archetype == "principles":
        q["answer_source"] = "legacy_template"
        return _principles_answer(q, job)

    if archetype == "procedure":
        q["answer_source"] = "legacy_template"
        return _procedure_answer(q)

    if not skill:
        q["answer_source"] = "legacy_template"
        return _role_answer(q, job, role_ctx)

    exp = _expert(skill, job)
    evidence = _retrieve_evidence_pack(skill, job, q)

    if archetype in {"explain_to_peer", "explain"}:
        q["answer_source"] = "legacy_template"
        return _compose_explain_answer(skill, evidence)

    if archetype in {"complex_problem", "scenario"}:
        q["answer_source"] = "legacy_template"
        return _compose_scenario_answer(skill, evidence)

    if archetype == "day_one":
        skill_t = title_case_skill(skill)
        return (
            f"On day one as {role_title}, I'd start by reading the job pack, RAMS, and any outstanding "
            f"certificates or handover notes. For {resp.lower()}, I'd walk the site or system with a "
            f"colleague, confirm isolation points and access, and identify the first task with lowest risk "
            f"— often a survey or verification before alteration. I'd apply {skill_t} using {exp['how_it_works'][0].lower() if exp['how_it_works'] else 'standard procedure'}, "
            f"check results against {exp.get('standards', ['applicable standards'])[0] if exp.get('standards') else 'the spec'}, "
            f"and document everything before signing off. If anything is unclear I stop and ask — "
            f"especially where safety or compliance is involved."
        )

    if archetype == "role_competencies":
        skills = role_ctx.get("required_skills", [])[:4]
        parts = [f"A strong {role_title} combines:\n"]
        for s in skills:
            e = _expert(s, job)
            parts.append(f"**{title_case_skill(s)}** — {e['definition']}\n")
        parts.append(
            f"In daily work that means {resp.lower()} with verified methods, complete documentation, "
            f"and communication with everyone affected by the installation or decision."
        )
        return "\n".join(parts)

    if archetype == "motivation":
        skills = ", ".join(title_case_skill(s) for s in role_ctx.get("required_skills", [])[:3])
        return (
            f"I want this {role_title} role because the work centres on {resp.lower()} — exactly where "
            f"I've built depth in {skills}. I've followed the organisation's projects and standards in "
            f"this sector and I'm ready to contribute from week one while continuing to develop specialist "
            f"skills. The role's core work matches what I do best and what I want to do long term."
        )

    if archetype == "company_research":
        company = job.get("company_name") or "your organisation"
        return (
            f"I've researched {company}'s recent work, market position, and values. What stands out is the "
            f"focus on quality in {resp.lower()} — aligned with my experience as {role_title}. "
            f"I want to bring hands-on expertise in {', '.join(title_case_skill(s) for s in role_ctx.get('required_skills', [])[:2])} "
            f"and contribute to the standards of delivery you're known for."
        )

    # Default technical
    return f"{exp['explain_answer']}\n\n{exp['complex_answer']}"


def _terminology_answer(q: dict, job: dict) -> str:
    skill = q.get("skill_tag") or "General"
    role = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    terms = q.get("terminology_terms") or get_terminology_pack(skill, role, resp)["terms"]
    lines = [f"In {role} work, these terms are foundational:\n"]
    for t in terms[:8]:
        lines.append(f"**{t['term']}** — {t['definition']}")
    return "\n\n".join(lines)


def _calculation_answer(q: dict, job: dict) -> str:
    skill = q.get("skill_tag") or "General"
    role = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    calc = q.get("calculation") or get_calculation_pack(skill, role, resp)
    if calc:
        steps = calc.get("steps") or []
        parts = [f"Problem: {calc['prompt']}\n"]
        if steps:
            parts.append("Working:")
            parts.extend(f"{i + 1}. {s}" for i, s in enumerate(steps))
        parts.append(f"\nAnswer: {calc['answer']}")
        return "\n".join(parts)
    skill_t = title_case_skill(skill)
    exp = _expert(skill, job)
    return (
        f"On a typical {role} task involving {skill_t}, I'd first identify what must be measured — "
        f"for example load, flow, dose, or error rate. I'd gather inputs from {exp.get('standards', ['the spec'])[0] if exp.get('standards') else 'site data or patient parameters'}, "
        f"apply the appropriate formula or clinical calculation, show units, and compare against the limit "
        f"before proceeding. I'd document the calculation on the test sheet or clinical record."
    )


def _principles_answer(q: dict, job: dict) -> str:
    skill = q.get("skill_tag") or "General"
    role = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    pack = get_principles_pack(skill, role, resp)
    parts = [f"Core principles for {pack['skill']} as a {role}:\n"]
    for i, p in enumerate(pack["principles"][:5], 1):
        parts.append(f"{i}. {p}")
    parts.append("\nStandard workflow:")
    for i, s in enumerate(pack["operating_steps"][:5], 1):
        parts.append(f"{i}. {s}")
    return "\n".join(parts)


def _procedure_answer(q: dict) -> str:
    steps = q.get("procedure_steps") or []
    skill = q.get("skill_tag") or "the procedure"
    parts = [f"I follow this structured sequence for {title_case_skill(skill)}:\n"]
    for i, s in enumerate(steps, 1):
        parts.append(f"{i}. {s}")
    parts.append(
        "\nThroughout I communicate clearly with the team, escalate if any step fails thresholds, "
        "and document times, observations, and actions contemporaneously."
    )
    return "\n".join(parts)


def _behavioral_developing_candidate_answer(q: dict, job: dict, role_ctx: dict) -> str:
    """First-person behavioral answer for a candidate WITHOUT provable prior
    experience.

    JOB-INT-R1 §9: when no genuine history is provided we do not invent a past
    employer, date, or metric — we speak as the candidate, clearly frame the
    example as one we would draw from training/projects, and still walk a
    natural (unlabelled) situation → action → result → lesson so the answer is
    speakable in an interview. Openers rotate on a stable hash of the question
    so five behavioral questions do not all start the same way.
    """
    role_title = job.get("title") or "this role"
    resp_raw = (job.get("responsibilities") or role_ctx.get("responsibilities") or ["the work"])[0]
    if isinstance(resp_raw, dict):
        resp_raw = resp_raw.get("text")
    resp = str(resp_raw or "core duties").lower()
    q_lower = (q.get("question") or "").lower()
    family = _role_family(role_title)

    # Concrete, stream-specific detail so the answer is role-adapted, not a
    # generic structure with the title swapped in.
    artifact, check, escalate = {
        "healthcare": ("the patient chart and handover notes", "double-checking against protocol", "escalating to the senior clinician"),
        "engineering": ("the job pack, drawings and permit", "verifying readings against the standard", "raising it with the responsible engineer"),
        "technology": ("the tickets, logs and tests", "running the tests and checking monitoring", "flagging it to the team lead in the channel"),
        "creative_media": ("the brief and the working files", "reviewing against the brief and style guide", "checking in with the art director or editor"),
        "finance_legal": ("the records and the control checklist", "reconciling against source data", "escalating to the reviewer or compliance"),
        "education": ("the lesson plan and progress records", "checking each learner's understanding", "involving the lead teacher"),
        "public_admin": ("the case file and service records", "checking policy and eligibility", "referring it to my line manager"),
    }.get(family, ("my notes and the task checklist", "checking my work against the requirement", "asking a colleague or supervisor"))

    # Vary the scenario spine by what the question actually probes.
    if any(t in q_lower for t in ("safety", "compliance", "stopped work", "risk")):
        situation = (
            f"a time in a project or placement where something about the {resp} work didn't look right — "
            f"a step that would have cut a corner on safety or a rule"
        )
        action = (
            f"I'd stop and not push on, get clear on the actual requirement by {check}, and raise it early by {escalate} "
            f"rather than quietly working around it"
        )
        result = "the issue got dealt with properly before it became a real problem, and nobody had to unpick it later"
        lesson = "stopping to check is never the thing that gets you into trouble — carrying on when you're unsure is"
    elif any(t in q_lower for t in ("defect", "hazard", "discovered late", "spotted", "caught")):
        situation = f"a time I noticed something wrong with the {resp} work later than I'd have liked"
        action = (
            f"I'd flag it straight away rather than hope it wasn't serious, trace how far it had spread using {artifact}, "
            f"contain it, and put it right while {escalate} so the right people knew"
        )
        result = "the problem got contained before it reached anyone downstream, and I fed back what let it slip through"
        lesson = "raising a late-found issue honestly is always better than quietly letting it ride"
    elif any(t in q_lower for t in ("fault", "diagnos", "debug", "troubleshoot", "under time pressure", "broke")):
        situation = f"a time the {resp} work wasn't behaving as expected and I needed to find the cause with the clock running"
        action = (
            f"I'd resist guessing, start from {artifact} to see what actually changed, reproduce the problem, "
            f"narrow it down one step at a time, and confirm the fix by {check} before calling it done"
        )
        result = "I found the real cause rather than a symptom, and the fix held because I'd verified it instead of assuming"
        lesson = "working the problem methodically beats a fast guess, especially when I'm under pressure"
    elif any(t in q_lower for t in ("standard", "check", "calculation", "test result", "prevented", "verif", "quality")):
        situation = f"a time a check I ran on the {resp} work caught something before it went further"
        action = (
            f"I'd not skip the check under time pressure, compare what I had against {artifact} and the expected result, "
            f"and only sign it off once {check} lined up"
        )
        result = "the check caught the issue early, which saved reworking it later or passing a fault on"
        lesson = "the checks are worth the few minutes they cost — they're what stops small errors becoming expensive ones"
    elif any(t in q_lower for t in ("constrained", "problem", "design", "complex", "trade-off", "tradeoff")):
        situation = f"a constrained problem in the {resp} work where I couldn't have everything I wanted at once"
        action = (
            f"I'd get the real constraints and the goal clear first, weigh the options against {artifact}, "
            f"pick the one with the best trade-off, and check it by {check} rather than assume it worked"
        )
        result = "I reached a workable solution I could explain and defend, rather than the first idea that came to mind"
        lesson = "naming the trade-offs out loud makes for a better decision than pretending there isn't one"
    elif any(t in q_lower for t in ("mistake", "learned", "wrong", "failed")):
        situation = f"a point where I got something wrong on {resp} work"
        action = (
            f"I'd own it straight away rather than hide it, correct it by going back to {artifact} and {check}, "
            f"and tell whoever needed to know by {escalate}"
        )
        result = "the mistake got put right quickly, and I added a small check to my own routine so it wouldn't happen the same way again"
        lesson = "owning a mistake early and building a check from it matters more than never slipping up"
    elif any(t in q_lower for t in ("disagree", "conflict", "pushed back")):
        situation = f"a time I saw the {resp} work differently from someone else on the team"
        action = (
            f"I'd make sure I understood their reasoning first, then set out my view calmly using {artifact} as evidence "
            f"rather than opinion, and agree a way to check who was right"
        )
        result = "we reached a decision we could both stand behind because it was grounded in the facts, not who spoke loudest"
        lesson = "disagreeing well means staying on the evidence and keeping it about the work"
    else:
        # Vary the default situation by the question so two general behavioral
        # prompts on the same role never collapse to identical text.
        default_situations = (
            f"a time on {resp} work when quality, timing and what people were expecting were all pulling against each other",
            f"a busy stretch of {resp} work where more than one thing needed doing well at the same time",
            f"a piece of {resp} work I was handed with only part of the picture to start from",
        )
        sidx = abs(hash(f"default::{q_lower}")) % len(default_situations)
        situation = default_situations[sidx]
        action = (
            f"I'd get clear on what actually mattered most, work through it in order, keep {check}, "
            f"and speak up early by {escalate} if something was going to slip"
        )
        result = "the work got delivered to standard without a last-minute scramble, because the risks were flagged early"
        lesson = "communicating early and keeping the checks in place is what keeps pressure from turning into a problem"

    openers = (
        f"I'll be honest that I'm still building direct experience as a {role_title}, so I'll give a realistic example I'd draw from my training and projects. ",
        f"I haven't got a long track record to point to yet, so I'll answer this with a realistic example rather than overstate it. ",
        f"A realistic example I can speak to — and I'll be upfront that it's from training and project work rather than a past job — is ",
        f"Rather than invent a story, I'll walk through how I'd genuinely handle this, drawing on my projects and study. ",
    )
    idx = abs(hash(f"{normalize_key(role_title)}::{q_lower}")) % len(openers)
    opener = openers[idx]

    # Two of the four openers read naturally straight into "a time…"; the other
    # two are complete sentences, so join with a lead-in that keeps first person.
    if opener.rstrip().endswith("is") or opener.rstrip().endswith("through how I'd genuinely handle this, drawing on my projects and study."):
        body_lead = "" if opener.rstrip().endswith("is") else "Picture "
    else:
        body_lead = "Picture "

    return (
        f"{opener}{body_lead}{situation}. "
        f"In that situation my responsibility would be to keep the {resp} work to standard without dropping safety, accuracy or communication. "
        f"What I'd actually do is this: {action}. "
        f"Realistically, {result}. "
        f"The lesson I'd take from it is that {lesson}."
    ).replace("  ", " ").strip()


def _behavioral_answer(q: dict, job: dict, role_ctx: dict) -> str:
    ctx = collect_user_claim_context(job)
    if ctx["job_thin"] or not ctx["has_explicit_experience"]:
        return _behavioral_developing_candidate_answer(q, job, role_ctx)

    role_title = job.get("title") or "Professional"
    resp_raw = (job.get("responsibilities") or role_ctx.get("responsibilities") or ["the work"])[0]
    if isinstance(resp_raw, dict):
        resp_raw = resp_raw.get("text")
    resp = str(resp_raw or "core duties")
    q_lower = (q.get("question") or "").lower()
    family = _role_family(role_title)
    skills = ", ".join(
        title_case_skill(s.get("skill") if isinstance(s, dict) else s)
        for s in (job.get("extracted_skills") or [])[:3]
    ) or "relevant methods"

    situation = (
        f"While working on {resp.lower()} responsibilities, the team faced a situation where "
        f"quality, timing, and stakeholder expectations were all under pressure at once."
    )
    task = (
        f"My responsibility was to deliver the {resp.lower()} work to standard without compromising "
        f"safety, accuracy, or team communication."
    )

    if family == "healthcare":
        if "disagreed" in q_lower or "conflict" in q_lower:
            action = (
                f"I gathered objective clinical observations and trend data, then escalated using SBAR with a clear "
                f"recommendation and timeframe. I facilitated a brief multidisciplinary review, documented decisions "
                f"contemporaneously, and ensured the patient pathway was updated before handover."
            )
            result = (
                f"The review completed within ten minutes, treatment started promptly, and deterioration was avoided. "
                f"Our audit recorded full escalation-policy compliance, and the team adopted the same evidence format "
                f"for similar cases."
            )
        else:
            action = (
                f"I completed structured assessment, initiated the escalation protocol when thresholds were met, "
                f"communicated via SBAR to the responsible clinician, and coordinated immediate interventions while "
                f"maintaining real-time documentation with timestamps."
            )
            result = (
                f"The patient stabilised and was stepped down the following day. Governance review found complete "
                f"documentation, and I used the case in team learning on early recognition."
            )
    elif family == "engineering":
        if "mistake" in q_lower or "learned" in q_lower:
            action = (
                f"I stopped work, corrected calculations using the current standard edition, reissued records, and "
                f"introduced a pre-sign-off checklist requiring version/date verification. I walked the team through "
                f"the error mode so it would not repeat on similar {skills} tasks."
            )
            result = (
                f"We energised/commissioned with verified values, had zero repeat issues on subsequent projects, and "
                f"the checklist became standard practice for {role_title} closeout."
            )
        else:
            action = (
                f"I isolated safely, traced root cause through measured values against design assumptions, implemented "
                f"a controlled fix with verification testing, and kept site coordination informed at each stage."
            )
            result = (
                f"Service was restored within SLA, corrective actions were logged in the maintenance closeout, and "
                f"follow-up sampling confirmed the fix held under load."
            )
    elif family == "technology":
        action = (
            f"I led triage on a production regression affecting {skills} workflows, executed a safe rollback, "
            f"identified root cause from logs and traces, and shipped a guarded fix with automated tests and "
            f"monitoring thresholds."
        )
        result = (
            f"Error rate returned below 0.2%, we added a release gate to prevent recurrence, and post-incident review "
            f"actions were completed within the sprint."
        )
    else:
        action = (
            f"I clarified priorities with stakeholders, broke the work into verifiable stages using {skills}, "
            f"executed with documented checks at each handoff, and escalated early when assumptions changed."
        )
        result = (
            f"The work completed with improved quality controls and a documented approach the team could reuse. "
            f"Lessons were captured for future {role_title} delivery."
        )

    return (
        f"**Situation:** {situation}\n\n"
        f"**Task:** {task}\n\n"
        f"**Action:** {action}\n\n"
        f"**Result:** {result}\n\n"
        f"What I would adapt in a new {role_title} role is the specific tooling and local procedures — "
        f"but the discipline of evidence, communication, and verification stays the same."
    )


def _build_motivation_segment(q: dict, job: dict, role_ctx: dict, ctx: dict) -> str:
    role_title = job.get("title") or "this role"
    real_resp = [r for r in (job.get("responsibilities") or role_ctx.get("responsibilities") or []) if r]
    real_skills = [s for s in (job.get("extracted_skills") or []) if s]
    # Title-only / thin input captured no duties or skills. Honest framing must
    # not claim "the posting centres on … the skills listed" — there is nothing
    # listed (Defect Class E). Instead, acknowledge the limited information and
    # what the candidate would clarify.
    if not real_resp and not real_skills:
        honest = (
            f"I am interested in this {role_title} role based on the information available so far. "
            f"Because the details I currently have are limited, I would want to confirm the main "
            f"responsibilities, the skills that matter most, and how success is measured — then explain "
            f"which parts of the role best match my strengths. "
        )
        company = job.get("company_name")
        if company:
            honest += (
                f"I would also research {company} directly so my reasons connect to its actual work rather "
                f"than assumptions. "
            )
        return honest
    resp = (job.get("responsibilities") or role_ctx.get("responsibilities") or ["core duties"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    resp = str(resp or "core duties")
    skills = ", ".join(
        title_case_skill(s.get("skill") if isinstance(s, dict) else s)
        for s in (job.get("extracted_skills") or [])[:3]
    ) or "role-relevant skills"
    company = job.get("company_name")
    profile = get_question_obligation_profile(q, job)
    obs = set(profile.obligations)

    motivation = (
        f"I am interested in this {role_title} role because the posting centres on {resp.lower()} "
        f"and the skills listed — especially {skills}. "
    )
    if ctx["has_explicit_experience"]:
        motivation = (
            f"I am applying for this {role_title} role because the posting aligns with work I have described "
            f"in my profile around {resp.lower()} and with the skills I want to deepen next — especially {skills}. "
        )
    if company and Obligation.COMPANY_FIT.value in obs:
        motivation = (
            f"I have researched {company} and understand how its work in this sector connects to "
            f"{resp.lower()}. I want to work there because the posting's focus on {resp.lower()} aligns with "
            f"what I want to deepen next — especially {skills}. "
        )
    elif company:
        motivation += (
            f"I have looked at {company}'s work in this sector and I am motivated by the chance to contribute "
            f"to that standard of delivery from week one. "
        )
    return motivation


def _build_strengths_segment(q: dict, job: dict) -> str:
    role_title = job.get("title") or "this role"
    skills = ", ".join(
        title_case_skill(s.get("skill") if isinstance(s, dict) else s)
        for s in (job.get("extracted_skills") or [])[:3]
    ) or "role-relevant skills"
    return (
        f"The strengths I would lean on first are {skills}: structured planning, clear verification before handoff, "
        f"and early communication when a {role_title} task looks ambiguous."
    )


def _build_contribution_segment(q: dict, job: dict, role_ctx: dict) -> str:
    role_title = job.get("title") or "this role"
    resp = (job.get("responsibilities") or role_ctx.get("responsibilities") or ["core duties"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    resp = str(resp or "core duties")
    return (
        f"In the first months I would contribute by taking ownership of {resp.lower()} tasks with disciplined "
        f"checkpoints, documenting assumptions, and escalating risks before they affect delivery."
    )


def _build_technical_method_segment(q: dict, job: dict, role_ctx: dict) -> str:
    role_title = job.get("title") or "Professional"
    skill = q.get("mapped_skill") or q.get("skill_tag") or (
        (job.get("extracted_skills") or [{}])[0].get("skill")
        if job.get("extracted_skills")
        else role_title
    )
    if isinstance(skill, dict):
        skill = skill.get("skill")
    skill = str(skill or role_title)
    exp = _expert(skill, job)
    steps = [s for s in (exp.get("how_it_works") or exp.get("workflow") or []) if s][:4]
    if not steps:
        steps = [
            f"confirm scope and inputs for {skill.lower()}",
            f"execute the core {skill.lower()} method with intermediate validation",
            f"verify outputs against the posting's quality expectations",
            f"document evidence and escalate if a checkpoint fails",
        ]
    workflow = render_spoken_workflow(steps, max_steps=4)
    standards = exp.get("standards") or []
    compliance = render_compliance_naturally(
        standards[:2],
        exp.get("checks") or [],
        role_family=resolve_role_family(role_title, q.get("role_family")),
    )
    return (
        f"On the method side, I would treat {title_case_skill(skill)} as the primary mechanism for this question. "
        f"{workflow} {compliance}"
    ).strip()


def _build_scenario_segment(q: dict, job: dict, role_ctx: dict) -> str:
    role_title = job.get("title") or "this role"
    resp = (job.get("responsibilities") or role_ctx.get("responsibilities") or ["core duties"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    resp = str(resp or "core duties")
    return (
        f"If constraints collided during {resp.lower()}, I would clarify the non-negotiable safety or compliance "
        f"requirement first, communicate the trade-off to stakeholders, and choose the path that keeps risk visible "
        f"rather than hidden."
    )


def _build_modifier_segments(q: dict, job: dict, profile) -> str:
    parts: list[str] = []
    skill = q.get("mapped_skill") or q.get("skill_tag") or _primary_skill_from_job(job)
    exp = _expert(str(skill), job)
    obs = set(profile.obligations)
    if Obligation.METRIC.value in obs:
        metrics = exp.get("metrics") or exp.get("checks") or []
        if metrics:
            parts.append(
                f"I would track {metrics[0].lower()} as a practical signal that the approach is working."
            )
        else:
            parts.append(
                "I would track revision cycle time and error rate against a baseline, aiming to reduce rework "
                "by at least 10 percent."
            )
    if Obligation.STANDARD_OR_PROTOCOL.value in obs:
        std = (exp.get("standards") or ["the applicable standard for this work"])[0]
        parts.append(f"I would anchor verification to {std}.")
    if Obligation.FAILURE_MODE.value in obs:
        mistakes = exp.get("common_mistakes") or exp.get("failure_modes") or []
        if mistakes:
            parts.append(
                f"A credible failure mode is {mistakes[0].lower()}; I would catch it with explicit pre-handoff checks."
            )
    return " ".join(parts)


def _primary_skill_from_job(job: dict) -> str:
    skills = job.get("extracted_skills") or []
    if skills:
        s = skills[0]
        return str(s.get("skill") if isinstance(s, dict) else s)
    return job.get("title") or "core work"


def _hr_answer(q: dict, job: dict, role_ctx: dict) -> str:
    ctx = collect_user_claim_context(job)
    role_title = job.get("title") or "this role"
    resp = (job.get("responsibilities") or role_ctx.get("responsibilities") or ["core duties"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    resp = str(resp or "core duties")
    skills = ", ".join(
        title_case_skill(s.get("skill") if isinstance(s, dict) else s)
        for s in (job.get("extracted_skills") or [])[:3]
    ) or "role-relevant skills"
    q_lower = (q.get("question") or "").lower()
    company = job.get("company_name")
    profile = get_question_obligation_profile(q, job)
    obs = set(profile.obligations)

    if "salary" in q_lower or "notice" in q_lower:
        return (
            f"For a {role_title} role I have researched typical market ranges for this level and location, "
            f"and I am open to discussing a fair package based on scope, benefits, and progression. "
            f"I would discuss my notice period honestly and align my start date with the employer's onboarding plan. "
            f"I am flexible on start date for the right opportunity and would confirm the working pattern "
            f"described in the job specification, especially where the work centres on {resp.lower()}. "
            f"I would confirm exact figures after understanding the full role specification, on-call expectations, "
            f"and development support — rather than anchoring on a number without context."
        )

    if "feedback" in q_lower or "development" in q_lower:
        if ctx["job_thin"] or not ctx["has_explicit_experience"]:
            return (
                f"I try to treat feedback as useful information about the work rather than personal criticism. "
                f"For {role_title} work on {resp.lower()}, I'd take one clear development goal from it, "
                f"decide the specific actions I'd take, and track my progress with real evidence — completed training, "
                f"audited outputs, or comments from the people I work with — so I can see I'm actually improving. "
                f"I'd rather ask for feedback early and often than wait for a formal review to find out where I stand."
            )
        return (
            f"In my {role_title} career I treat feedback as operational data, not personal criticism. "
            f"After a recent review on {resp.lower()}, I agreed three development actions with my manager: "
            f"deepen {skills}, improve handover documentation, and lead one small improvement project. "
            f"I track progress monthly with evidence — completed courses, audited outputs, or stakeholder comments — "
            f"and I ask for mid-cycle check-ins so adjustments happen early. "
            f"That approach keeps my {role_title} practice current without waiting for annual reviews."
        )

    if profile.is_hybrid and not is_pure_motivation_profile(profile):
        segments: list[str] = []
        if Obligation.MOTIVATION_FIT.value in obs or Obligation.COMPANY_FIT.value in obs:
            segments.append(_build_motivation_segment(q, job, role_ctx, ctx))
        if Obligation.STRENGTHS.value in obs:
            segments.append(_build_strengths_segment(q, job))
        if Obligation.CONTRIBUTION.value in obs:
            segments.append(_build_contribution_segment(q, job, role_ctx))
        if Obligation.TECHNICAL_METHOD.value in obs:
            segments.append(_build_technical_method_segment(q, job, role_ctx))
        if Obligation.SCENARIO_REASONING.value in obs:
            segments.append(_build_scenario_segment(q, job, role_ctx))
        modifier = _build_modifier_segments(q, job, profile)
        if modifier:
            segments.append(modifier)
        closing = (
            "I am not claiming to know every local process on day one, but I am ready to learn quickly and add value "
            "through dependable execution on the role's core work."
        )
        return " ".join(segments + [closing]).strip()

    motivation = _build_motivation_segment(q, job, role_ctx, ctx)
    motivation += (
        f"I bring structured habits: clarify requirements, execute with verification, communicate risks early, "
        f"and document outcomes so the team can rely on my work. "
        f"I am not claiming to know every local process on day one, but I am ready to learn quickly and add value "
        f"through dependable execution on the role's core work."
    )
    return motivation


def _daily_routine_answer(q: dict, job: dict, role_ctx: dict) -> str:
    role_title = job.get("title") or "Professional"
    resp_list = job.get("responsibilities") or role_ctx.get("responsibilities") or ["core duties"]
    primary = resp_list[0]
    if isinstance(primary, dict):
        primary = primary.get("text")
    primary = str(primary or "core duties")
    skills = ", ".join(
        title_case_skill(s.get("skill") if isinstance(s, dict) else s)
        for s in (job.get("extracted_skills") or [])[:2]
    ) or "standard methods"
    q_lower = (q.get("question") or "").lower()

    if "first day" in q_lower or "day-one" in q_lower or "first day" in q_lower:
        return (
            f"On day one as {role_title} I would arrive early, read handover notes and any safety briefings, "
            f"and introduce myself to the people I will work with on {primary.lower()}. "
            f"I would shadow a colleague through one complete cycle of the work, noting checkpoints, tools ({skills}), "
            f"and escalation paths before attempting anything independently. "
            f"My first independent tasks would be low-risk verification or preparation work with sign-off, "
            f"while I build familiarity with local documentation and naming conventions. "
            f"By end of day I would summarise what I learned, confirm tomorrow's priorities, and flag any gaps "
            f"in access, training, or equipment before they become blockers."
        )

    return (
        f"A typical day as {role_title} starts with a brief planning check: outstanding tasks, safety or quality "
        f"alerts, and priorities for {primary.lower()}. "
        f"Morning work usually focuses on scheduled delivery using {skills}, with verification before handoff. "
        f"Midday I handle ad-hoc issues, stakeholder questions, and documentation updates while keeping traceability "
        f"for audit or continuity. "
        f"Afternoon I complete remaining core tasks, prepare handover notes, restock or reset anything needed for "
        f"the next shift, and close out actions from earlier escalations. "
        f"Throughout I communicate early when timelines slip and I never skip compliance checks to save time — "
        f"that rhythm is what keeps {role_title} work predictable under pressure."
    )


def _seniority_answer(q: dict, job: dict, role_ctx: dict) -> str:
    role_title = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or role_ctx.get("responsibilities") or ["core duties"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    resp = str(resp or "core duties")
    q_lower = (q.get("question") or "").lower()

    if "junior" in q_lower:
        return (
            f"As a junior {role_title} I assume I will encounter tasks in {resp.lower()} that I have not done "
            f"in exactly this environment before. My approach is to read the procedure, identify safety-critical "
            f"steps, and ask for a brief walkthrough before starting. "
            f"I execute in small verifiable stages, record measurements or outputs as I go, and request review "
            f"before sign-off on anything that affects quality or compliance. "
            f"If I am blocked I escalate early with specific questions rather than guessing — that protects the "
            f"team and speeds up my learning curve. "
            f"Within the first weeks I also keep a personal log of methods, tools, and contacts so repeat tasks "
            f"become faster without cutting corners."
        )

    if "senior" in q_lower or "mentor" in q_lower:
        return (
            f"As a senior {role_title} I balance hands-on delivery on {resp.lower()} with structured support for "
            f"juniors. I set clear review criteria before work starts, do spot-checks at defined checkpoints, "
            f"and reserve time for coaching questions without taking over execution. "
            f"When quality risk is high I pair on the critical steps, then let the junior complete supervised "
            f"sections to build competence. "
            f"I also own escalation to stakeholders, standards interpretation, and cross-team coordination so "
            f"juniors can focus on learning the method. "
            f"That division keeps throughput high while maintaining audit-ready documentation and consistent outcomes."
        )

    return (
        f"At mid-level as {role_title} I deliver {resp.lower()} independently but stay deliberate about when to "
        f"involve seniors — usually when assumptions change, safety margins tighten, or stakeholder impact widens. "
        f"I document decisions, share progress proactively, and offer help to newer colleagues on routine tasks "
        f"so the team capacity stays balanced. "
        f"My goal is reliable execution plus judgement: knowing which shortcuts are acceptable and which require "
        f"full verification or escalation."
    )


def _archetype_coverage_answer(q: dict, job: dict, role_ctx: dict) -> str:
    """Legacy-template answers for creative/media, creator/trending, and sports coverage questions."""
    role_title = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or role_ctx.get("responsibilities") or ["core duties"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    resp = str(resp or "core duties")
    family = resolve_role_family(role_title, q.get("role_family"))
    pack = get_evidence_pack_for_question(
        family if family in {"creative_media", "creative_design", "creator_trending", "sports"} else "default",
        role_title,
        q.get("skill_tag", ""),
    )
    example = (pack.get("role_specific_examples") or [""])[0]
    checks = pack.get("verification_checks") or ["documented quality checks"]
    check = checks[0]
    qtype = q.get("question_type") or ""

    if qtype == "ethics":
        if family == "creator_trending":
            return (
                f"In {role_title} work on {resp.lower()}, I treat audience trust and platform policy as publish gates. "
                f"When a claim cannot be supported I hold the line — I do not publish speculation as fact. "
                f"I document verification steps, disclose sponsorship where required, and escalate borderline content "
                f"before it goes live."
            )
        if family == "creative_design":
            return (
                f"In {role_title} work on {resp.lower()}, I treat brand guidelines and accessibility as non-negotiable gates. "
                f"When a visual direction conflicts with brand rules or readability, I pause and realign with the brief. "
                f"I document revision rationale and confirm sign-off before final export."
            )
        return (
            f"In {role_title} work on {resp.lower()}, I treat accuracy and ethics as publish gates, not afterthoughts. "
            f"When a source cannot be verified I hold the line — I do not publish speculation as fact. "
            f"I document the verification trail for editorial review before publication."
        )
    if qtype in {"design_brief", "client_feedback"}:
        return (
            f"As a {role_title}, I translate the brief into layout hierarchy, asset specs, and revision checkpoints before execution. "
            f"I confirm constraints, brand rules, and delivery formats up front, then run {check.lower()} at each handoff. "
            f"For {resp.lower()}, that keeps feedback rounds focused and protects deadline quality."
        )
    if qtype in {"story_planning", "content_planning"}:
        if family == "creator_trending":
            return (
                f"As a {role_title}, I start with audience need and content angle, then map ideation, scripting, "
                f"and production steps with realistic deadline buffers. I keep a running idea log, outline hooks early, "
                f"and run accuracy checks before publish. "
                f"For {resp.lower()}, that means fewer reshoots and cleaner handover to upload workflows."
            )
        if family == "creative_design":
            return (
                f"As a {role_title}, I start with the brief and visual goals, then map references, layout exploration, "
                f"and revision rounds with realistic deadline buffers. I keep versioned exports and run {check.lower()} "
                f"before handoff. For {resp.lower()}, that means fewer rework cycles and cleaner delivery to stakeholders."
            )
        return (
            f"As a {role_title}, I start with audience need and angle, then map interviews, research, and production steps "
            f"with realistic deadline buffers. I keep a running source log, outline the narrative arc early, "
            f"and schedule fact-checking before final edit. "
            f"For {resp.lower()}, that means fewer rewrites and cleaner handover to editors or platform upload."
        )
    if qtype in {"audience_research", "content_niche", "analytics_kpi"}:
        return (
            f"I define the audience segment first, then track retention, engagement, and completion metrics after publish. "
            f"As a {role_title}, I review what topics earned saves, shares, and constructive comments — not just views. "
            f"I use those signals to refine the next content calendar while keeping the niche credible. "
            f"That stops trend-chasing that erodes trust."
        )
    if qtype in {"production_workflow", "filming_recording", "workflow_process"}:
        return (
            f"My workflow as a {role_title} moves from brief to draft/recording, through review, then sign-off. "
            f"I batch similar tasks, keep asset folders versioned, and run {check.lower()} before anything goes live. "
            f"For {resp.lower()}, I also build short buffer time for legal, brand, or platform checks."
        )
    if qtype in {"platform_tools", "thumbnail_hooks", "publishing_schedule"}:
        return (
            f"I choose tools that improve repeatability — calendars, analytics dashboards, and editing templates. "
            f"As a {role_title}, I test titles/thumbnails or headlines against the actual content promise, "
            f"then schedule releases when the audience is active. "
            f"I verify captions, disclosures, and metadata before publish so downstream fixes are rare."
        )
    if qtype in {"editor_feedback", "coaching_feedback", "stakeholder_communication"}:
        return (
            f"I treat feedback as a quality input, not a personal critique. "
            f"When an editor or coach flags structure, accuracy, or tone, I restate the required change, "
            f"apply it to the draft, and confirm the fix against the brief. "
            f"As a {role_title}, that keeps {resp.lower()} on standard without defensive rewrites."
        )
    if qtype == "portfolio":
        return (
            f"My portfolio as a {role_title} shows range, process, and outcomes — not just finished pieces. "
            f"I include a short note on research, verification, or audience goal for each sample, "
            f"plus one example where editorial or client feedback improved the final work."
        )
    if qtype in {"quality_review", "brand_safety"}:
        return (
            f"Before sign-off I run a checklist: facts, rights, tone, sponsor disclosures, and audience risk. "
            f"As a {role_title}, I will pause release if any item fails — especially for {resp.lower()}. "
            f"{example}"
        )
    if qtype in {"copyright", "crisis_reputation"}:
        return (
            f"I clear music, images, and third-party clips before upload, and I keep licence records with the project file. "
            f"If a reputation issue appears, I pause scheduled posts, gather facts, align with platform policy, "
            f"and communicate transparently without deleting evidence I may need for review."
        )
    if qtype in {"community_management", "monetization_awareness"}:
        return (
            f"I moderate comments with clear rules, escalate harassment quickly, and separate sponsorship from editorial voice. "
            f"As a {role_title}, I disclose paid partnerships plainly and only promote products that fit audience trust. "
            f"That protects long-term growth over short-term revenue spikes."
        )
    if qtype in {"training_discipline", "match_preparation", "recovery_awareness"}:
        return (
            f"I follow the training plan set with qualified coaching staff, log sessions honestly, and prioritise recovery sleep "
            f"during congested periods. As a {role_title}, I report pain or illness early rather than training through it. "
            f"Match preparation includes tactical review, communication cues, and warm-up discipline — not unsupervised extreme work."
        )
    if qtype in {"teamwork_sports", "sportsmanship"}:
        return (
            f"I communicate early on the field or court, support teammates after mistakes, and accept official decisions professionally. "
            f"As a {role_title}, sportsmanship means controlling controllables — effort, discipline, and respect — "
            f"especially when results pressure rises."
        )
    if qtype in {"practical_task", "case_study", "problem_solving", "scenario"}:
        skill = q.get("skill_tag") or resp
        return (
            f"I would clarify scope and risk first, then execute in verifiable stages. "
            f"For this {role_title} scenario involving {str(skill).lower()}, I would {check.lower()}, "
            f"communicate status to stakeholders, and document decisions so the team can review afterwards. "
            f"{example}"
        )
    if qtype == "growth_seniority":
        return (
            f"Early in my {role_title} career I focused on fundamentals and feedback loops; now I mentor others on "
            f"{resp.lower()} while owning higher-stakes decisions. I still practise core skills deliberately because "
            f"audience expectations and standards evolve."
        )
    return (
        f"As a {role_title}, I approach {resp.lower()} with structured planning, {check.lower()}, and clear communication. "
        f"{example}"
    )


def _hr_study(q: dict, job: dict, role_ctx: dict) -> dict:
    base = _behavioral_study(q, job, role_ctx)
    base["overview"] = (
        f"HR interview questions for {job.get('title') or 'this role'} test motivation, logistics, and "
        f"professionalism — not deep technical knowledge. Prepare honest, specific answers you can adapt."
    )
    base["key_concepts"] = ["Motivation fit", "Salary research", "Notice period", "Development planning"]
    return base


def _daily_routine_study(q: dict, job: dict, role_ctx: dict) -> dict:
    role_title = job.get("title") or "this role"
    resp = (job.get("responsibilities") or ["core duties"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    return {
        "overview": f"Daily-routine questions check whether you understand real {role_title} workflow — not theory alone.",
        "what_you_need_to_know_first": [
            f"Typical sequence for {resp}",
            "Opening and closing checks",
            "Handover and documentation habits",
        ],
        "principles": [
            "Describe a realistic day with timings, not a generic list.",
            "Mention safety/quality checkpoints explicitly.",
            "Show how you handle interruptions without losing control.",
        ],
        "step_by_step_breakdown": [
            "Start-of-shift: brief, priorities, equipment/system checks.",
            "Core work blocks tied to posting responsibilities.",
            "Ad-hoc issues and communication.",
            "Close-down: documentation, handover, reset for next shift.",
        ],
        "common_mistakes": [
            "Answering with only abstract values ('I am organised').",
            "Ignoring compliance or safety steps in the routine.",
            "Forgetting handover/documentation.",
        ],
        "practice_exercises": [
            f"Write a one-page hour-by-hour plan for a {role_title} shift.",
            "List three escalation triggers you would watch for daily.",
        ],
        "estimated_reading_time_minutes": 8,
    }


def _coverage_question_study(q: dict, job: dict, role_ctx: dict) -> dict:
    role_title = job.get("title") or "this role"
    skill = q.get("skill_tag") or "core work"
    skill_t = title_case_skill(skill)
    qtext = q.get("question") or ""
    return {
        "overview": (
            f"Preparation for: {truncate_at_word(qtext, 140)}. "
            f"Covers how {skill_t} work is planned, executed, and verified in {role_title} practice."
        ),
        "what_you_need_to_know_first": [
            f"Typical {skill_t} workflow in this role",
            "Risk and compliance triggers",
            "Evidence to collect before sign-off",
        ],
        "principles": [
            f"Stage {skill_t} tasks with explicit entry/exit checks.",
            "Record assumptions, measurements, and owner decisions.",
            "Separate interim containment from permanent fixes.",
        ],
        "step_by_step_breakdown": [
            "Confirm scope, constraints, and stakeholders.",
            f"Plan {skill_t} execution with role-appropriate tools.",
            "Run verification against spec or SOP.",
            "Communicate results, risks, and follow-up actions.",
        ],
        "common_mistakes": [
            "Rushing verification when deadlines tighten.",
            "Describing tools without linking them to outcomes.",
            "Omitting escalation when results are borderline.",
        ],
        "practice_exercises": [
            f"Write a one-page runbook for a {skill_t} task.",
            "List three escalation triggers for this scenario.",
        ],
        "estimated_reading_time_minutes": 10,
    }


def _seniority_study(q: dict, job: dict, role_ctx: dict) -> dict:
    base = _behavioral_study(q, job, role_ctx)
    base["overview"] = (
        f"Seniority questions calibrate expectations for {job.get('title') or 'this role'} — "
        f"junior learning discipline, mid-level judgement, or senior coaching ownership."
    )
    return base


def _system_design_answer(job: dict, role_ctx: dict) -> str:
    role_title = job.get("title") or "Professional"
    resp = (role_ctx.get("responsibilities") or ["service delivery"])[0]
    return (
        f"For this {role_title} scenario supporting {resp.lower()}, I'd clarify scale first — "
        f"users, peak QPS, data retention, and latency targets.\n\n"
        f"API layer: stateless services behind a load balancer, autoscaling on CPU and request rate. "
        f"Writes go to a primary database with read replicas; cache hot reads in Redis with TTL and "
        f"cache-aside pattern. Async jobs (notifications, reports) on a queue with idempotent workers.\n\n"
        f"Deep dive on the write path: API validates input, persists to DB with unique constraint for "
        f"idempotency, publishes event to queue, returns 202. Worker processes side effects; failures "
        f"go to DLQ with alert.\n\n"
        f"At 10× load: shard database by tenant_id, add CDN for static assets, partition queue by priority. "
        f"Monitor p99 latency, error rate, queue depth; SLO 99.9% availability with runbooks for "
        f"failover to replica and queue backlog drain."
    )


def _role_answer(q: dict, job: dict, role_ctx: dict) -> str:
    role_title = job.get("title") or "Professional"
    resp = (role_ctx.get("responsibilities") or ["professional work"])[0]
    return (
        f"As {role_title}, my approach to {resp.lower()} is systematic: confirm requirements and safety, "
        f"plan resources and sequence, execute to standard with checks at each stage, document and hand over. "
        f"I stay current with regulations and learn from every job — especially when something unexpected "
        f"forces a change of method."
    )


def build_answer_explanation(q: dict, job: dict, model_answer: str) -> str:
    """Factual summary of key points in the answer — not interview coaching."""
    category = q.get("category", "technical")
    skill = q.get("skill_tag") or ""
    role_title = job.get("title") or "the role"
    archetype = _question_archetype(q.get("question", ""), category, q)

    if archetype == "terminology":
        terms = q.get("terminology_terms") or []
        if terms:
            return "Definitions covered: " + ", ".join(t["term"] for t in terms[:6])
        return "Precise definitions of core professional terminology."

    if archetype == "calculation":
        calc = q.get("calculation")
        if calc:
            return f"Calculation: {calc['answer']}"
        return "Quantitative method with formula, units, and limit check."

    if archetype == "principles":
        return "Core operating principles and ordered workflow for the skill."

    if archetype == "procedure":
        steps = q.get("procedure_steps") or []
        return f"Procedure steps ({len(steps)}): " + "; ".join(steps[:4])

    if not skill or category in ("behavioral", "company_specific"):
        # Extract substance from answer length — summarise topics
        lines = [ln.strip() for ln in model_answer.split("\n") if ln.strip() and not ln.startswith("**")]
        if lines:
            preview = lines[0][:200]
            return f"This answer covers: {preview}{'…' if len(lines[0]) > 200 else ''}"
        return "Full situational account with actions, tools, and measurable results."

    exp = _expert(skill, job)
    skill_t = title_case_skill(skill)
    facts = exp.get("key_facts", [])[:4]
    stds = exp.get("standards", [])[:2]
    parts = [f"Key knowledge demonstrated for {skill_t}:"]
    parts.extend(f"• {f}" for f in facts)
    if stds:
        parts.append("Standards referenced: " + ", ".join(stds))
    return "\n".join(parts)
