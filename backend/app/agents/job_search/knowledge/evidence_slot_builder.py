from __future__ import annotations

from typing import Any

from app.agents.job_search.knowledge.answer_builders import pick_intent_closing
from app.agents.job_search.knowledge.core_technical_content import (
    get_calculation_pack,
    get_principles_pack,
    get_terminology_pack,
)
from app.agents.job_search.knowledge.question_intent import detect_question_intent
from app.agents.job_search.knowledge.evidence_packs import (
    get_evidence_pack,
    get_evidence_pack_for_question,
    resolve_role_family,
    select_role_family_opening,
)
from app.agents.job_search.knowledge.expert_content_library import (
    has_curated_expert_content,
    resolve_expert_content,
)
from app.agents.job_search.knowledge.normalize import title_case_skill
from app.agents.job_search.quality.broken_template_audit import contains_broken_pattern
from app.agents.job_search.quality.compiler_boilerplate_audit import contains_universal_boilerplate
from app.agents.job_search.quality.example_quality_audit import has_weak_example
from app.agents.job_search.quality.generic_phrase_audit import contains_generic_pattern
from app.agents.job_search.quality.key_term_quality_audit import is_valid_key_term


def _sanitize_steps(steps: list[str]) -> list[str]:
    cleaned: list[str] = []
    for step in steps:
        text = str(step).strip()
        if not text or contains_universal_boilerplate(text):
            continue
        cleaned.append(text)
    return cleaned


def _workflow_steps(family_pack: dict[str, Any], skill: str, role: str) -> list[str]:
    checks = family_pack.get("verification_checks") or []
    if checks:
        return [str(c).rstrip(".") for c in checks[:6]]
    return [
        f"Confirm scope and requirements for {title_case_skill(skill)} in {role}",
        f"Execute the {title_case_skill(skill)} workflow with intermediate checks",
        f"Verify outputs against applicable standards and records",
        f"Document decisions, risks, and handover notes",
        f"Review results and update the process for the next cycle",
    ]


# Marker phrases that identify the GENERIC expert-content fallback (i.e. no genuine
# skill-native material exists for this skill). Used so we only prefer expert content
# over role-family content when the expert content is actually skill-specific.
_GENERIC_EXPERT_MARKERS = (
    "the body of knowledge, tools, standards, and verified procedures",
    "role-specific checks appropriate to",
    "professional work in any field requires",
)


def _expert_is_skill_specific(exp: dict[str, Any]) -> bool:
    """True when the expert-content entry is genuinely skill-native, not the generic template."""
    blob = " ".join(
        str(exp.get(k) or "") for k in ("definition", "teaching_body", "how_it_works")
    ).lower()
    if not blob.strip():
        return False
    return not any(marker in blob for marker in _GENERIC_EXPERT_MARKERS)


def _skill_native_mechanisms(exp: dict[str, Any], skill: str) -> list[str]:
    """Skill-native mechanism statements from expert content (empty if only generic)."""
    if not _expert_is_skill_specific(exp):
        return []
    items: list[str] = []
    for key in ("how_it_works", "key_facts"):
        for entry in exp.get(key) or []:
            text = str(entry).strip()
            if text and not contains_universal_boilerplate(text):
                items.append(text.rstrip("."))
    # Dedupe while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        low = item.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(item)
    return out[:6]


# Generic/cross-domain words that do not, on their own, indicate that a workflow
# belongs to a specific skill. Filtered from both the skill vocabulary and the
# family workflow tokens so overlap only counts genuinely distinctive terms.
_GENERIC_SKILL_TOKENS = frozenset(
    {
        "data", "source", "work", "working", "business", "quality", "check", "checks",
        "review", "confirm", "performance", "result", "results", "value", "values",
        "system", "systems", "task", "tasks", "team", "standard", "standards", "process",
        "processes", "output", "outputs", "input", "inputs", "record", "records",
        "professional", "professionals", "role", "roles", "practice", "method", "methods",
        "workflow", "step", "steps", "with", "that", "this", "when", "which", "will",
        "would", "from", "into", "before", "after", "against", "using", "used", "apply",
        "applied", "required", "assumptions", "completeness", "freshness", "definitions",
        "requirement", "requirements", "constraints", "high", "level", "language",
    }
)


def _skill_vocabulary(skill: str, card: dict[str, Any], exp: dict[str, Any]) -> set[str]:
    """Distinctive content words that identify the primary skill's own subject matter."""
    import re as _re

    text = " ".join(
        [
            str(skill),
            " ".join(str(c) for c in (card.get("core_concepts") or [])),
            str(exp.get("definition") or ""),
            " ".join(str(x) for x in (exp.get("key_facts") or [])),
        ]
    ).lower()
    return {
        tok
        for tok in _re.findall(r"[a-z][a-z+]{3,}", text)
        if tok not in _GENERIC_SKILL_TOKENS
    }


def _family_workflow_is_foreign(
    family_steps: list[str], skill: str, card: dict[str, Any], exp: dict[str, Any]
) -> bool:
    """True when the role-family default workflow does not belong to the primary skill.

    We only override the family workflow when (a) the skill genuinely has its own
    skill-native content and (b) none of the family workflow steps' distinctive
    vocabulary overlaps the skill's own distinctive vocabulary. This keeps the
    family's rich workflow for its native skill (e.g. SQL in the data family) while
    preventing it from being applied verbatim to an adjacent skill (e.g. Python),
    per §5. Generic cross-domain words (data, work, quality, ...) are ignored so a
    coincidental shared word does not mask genuine skill mismatch.
    """
    if not _expert_is_skill_specific(exp):
        return False
    import re as _re

    vocab = _skill_vocabulary(skill, card, exp)
    if not vocab:
        return False
    family_tokens = {
        tok
        for tok in _re.findall(r"[a-z][a-z+]{3,}", " ".join(family_steps).lower())
        if tok not in _GENERIC_SKILL_TOKENS
    }
    if not family_tokens:
        return False
    return not (vocab & family_tokens)


def _skill_anchored_workflow(skill: str, role: str) -> list[str]:
    """Generalized skill-native workflow used when the family default is foreign to the skill."""
    s = title_case_skill(skill)
    return [
        f"Clarify the {s} requirement, inputs, and constraints for the task",
        f"Design the {s} approach and implement it in small, verifiable steps",
        f"Validate {s} behaviour with appropriate tests, checks, or measurements",
        f"Review edge cases, performance, and correctness before sign-off",
    ]


# Base-form verbs that mark an expert `how_it_works` entry as an actionable workflow
# step (as opposed to a declarative mechanism statement like "Objects are ...").
_IMPERATIVE_STEP_VERBS = frozenset(
    {
        "establish", "apply", "account", "calculate", "check", "confirm", "validate",
        "verify", "select", "size", "determine", "measure", "inspect", "record",
        "review", "plan", "design", "identify", "assess", "estimate", "compare",
        "balance", "allow", "total", "convert", "clarify", "prepare", "execute",
        "document", "evaluate", "monitor", "install", "route", "terminate",
        "commission", "issue", "isolate", "gather", "define", "build", "run",
    }
)


def _skill_first_opening(role: str, skill: str, exp: dict[str, Any]) -> str:
    """Build a skill-native definition opening from expert content (empty if unavailable).

    Reframes the skill's own definition as "For a {role}, {skill} means {predicate}."
    so that a skill whose family default is foreign (e.g. Load Calculations in the
    electrical family) is not defined by the family's installation/testing opening (§5).
    """
    import re as _re

    definition = str(exp.get("definition") or "").strip()
    if not definition:
        return ""
    first_sentence = _re.split(r"(?<=\.)\s+", definition)[0].strip()
    match = _re.match(r"^.*?\b(?:is|are)\s+(.*)$", first_sentence)
    if not match:
        return ""
    predicate = match.group(1).strip().rstrip(".")
    if len(predicate.split()) < 4:
        return ""
    predicate = predicate[0].lower() + predicate[1:]
    article = "an" if (role[:1].lower() in "aeiou") else "a"
    return f"For {article} {role}, {title_case_skill(skill)} means {predicate}."


def _opening_is_skill_distinct(skill_opening: str, family_opening: str) -> bool:
    """True when the skill-native opening carries meaning the family opening does not.

    Prevents a redundant swap when the skill IS the family core (e.g. Electrical
    Installation, whose expert definition largely restates the family opening),
    while still replacing a genuinely foreign family opening (e.g. the electrical
    installation opening standing in for Load Calculations) (§5).
    """
    if not skill_opening:
        return False
    import re as _re

    def _content_tokens(text: str) -> set[str]:
        return {
            tok
            for tok in _re.findall(r"[a-z][a-z+]{3,}", text.lower())
            if tok not in _GENERIC_SKILL_TOKENS
        }

    skill_tokens = _content_tokens(skill_opening)
    family_tokens = _content_tokens(family_opening)
    if not skill_tokens:
        return False
    novel = skill_tokens - family_tokens
    # The skill opening is distinct when a clear majority of its distinctive
    # content words do not already appear in the family opening.
    return len(novel) >= max(3, (len(skill_tokens) + 1) // 2)


def _skill_native_workflow(exp: dict[str, Any], skill: str) -> list[str]:
    """Skill-native, actionable workflow taken from skill-specific expert `how_it_works`.

    Only used when the expert content is genuinely skill-specific and its steps are
    actionable (imperative). This is the highest-precedence workflow source (§5):
    the primary skill's own method, ahead of any role-family default.
    """
    if not _expert_is_skill_specific(exp):
        return []
    import re as _re

    steps: list[str] = []
    for entry in exp.get("how_it_works") or []:
        text = str(entry).strip()
        if not text or contains_universal_boilerplate(text):
            continue
        words = _re.findall(r"[A-Za-z]+", text)
        if words and words[0].lower() in _IMPERATIVE_STEP_VERBS:
            steps.append(text.rstrip("."))
    return steps[:6] if len(steps) >= 3 else []


def _pick_example(
    role: str,
    skill: str,
    family_pack: dict[str, Any],
    exp: dict[str, Any],
    *,
    prefer_expert: bool = False,
) -> str:
    # Skill-first: when the family default is foreign to the primary skill, a
    # genuinely skill-native worked example must win over the role-family default
    # so e.g. a Python question is not illustrated with a SQL revenue-dashboard
    # example (§5).
    complex_answer = str(exp.get("complex_answer") or "")
    expert_ok = bool(complex_answer) and not has_weak_example(complex_answer) and len(complex_answer.split()) >= 25
    if prefer_expert and expert_ok:
        return complex_answer
    examples = family_pack.get("role_specific_examples") or []
    if examples:
        return str(examples[0])
    if expert_ok:
        return complex_answer
    domain = ", ".join((family_pack.get("domain_terms") or [])[:4])
    if domain:
        return (
            f"Illustrative example: a {role} applying {title_case_skill(skill)} would work with "
            f"{domain}, complete the required verification checks, and record the outcome before sign-off."
        )
    return (
        f"Illustrative example: a {role} would apply {title_case_skill(skill)} methodically, "
        f"complete the required verification checks, and record the outcome before sign-off."
    )


def _sanitize_text_items(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if contains_broken_pattern(text) or contains_universal_boilerplate(text) or contains_generic_pattern(text):
            continue
        cleaned.append(text)
    return cleaned


def _principles_for_question(
    principles_pack: dict[str, Any],
    family_pack: dict[str, Any],
    skill: str,
) -> list[str]:
    principles = _sanitize_text_items(list(principles_pack.get("principles") or []))
    if len(principles) >= 3:
        return principles[:6]
    domain = family_pack.get("domain_terms") or []
    fallback = [
        f"Keep {title_case_skill(skill)} deliverables accurate, coordinated, and revision-controlled",
        f"Verify {title_case_skill(skill)} outputs against applicable standards before issue",
        "Record design decisions, constraints, and compliance evidence for audit and handover",
    ]
    if domain:
        fallback.insert(0, f"Apply {domain[0]} controls consistently in every {title_case_skill(skill)} deliverable")
    return fallback[:6]


def _sanitize_terminology_terms(terms: list[dict[str, Any]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for term in terms:
        if not isinstance(term, dict):
            continue
        name = str(term.get("term") or "").strip()
        definition = str(term.get("definition") or "").strip().rstrip(".")
        if not name or not definition:
            continue
        if not is_valid_key_term(name):
            continue
        if contains_broken_pattern(name) or contains_broken_pattern(definition):
            continue
        if contains_universal_boilerplate(name) or contains_universal_boilerplate(definition):
            continue
        cleaned.append({"term": name, "definition": definition})
    return cleaned


def _terminology_terms_for_question(
    q: dict[str, Any],
    terms_pack: dict[str, Any],
    card: dict[str, Any],
    family_pack: dict[str, Any],
    skill: str,
    role: str = "Professional",
) -> list[dict[str, str]]:
    raw = list(q.get("terminology_terms") or terms_pack.get("terms") or [])
    sanitized = _sanitize_terminology_terms(raw)
    if len(sanitized) >= 4:
        return sanitized[:8]
    fallback_terms: list[dict[str, str]] = []
    skill_t = title_case_skill(skill)
    for concept in (card.get("core_concepts") or [])[:6]:
        text = str(concept).strip()
        if text and is_valid_key_term(text):
            fallback_terms.append(
                {
                    "term": text,
                    "definition": (
                        f"{text} is a concept a {role} applies within {skill_t}; "
                        f"know what it means, when it applies, and how to check it is correct."
                    ),
                }
            )
    for term in (family_pack.get("domain_terms") or [])[:6]:
        text = str(term).strip()
        if text and is_valid_key_term(text):
            fallback_terms.append(
                {
                    "term": text,
                    "definition": (
                        f"{text} is used in {skill_t} work for {role}s; be able to explain its "
                        f"purpose and how it affects the outcome."
                    ),
                }
            )
    merged = _sanitize_terminology_terms(sanitized + fallback_terms)
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in merged:
        key = item["term"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:8]


# Skill-specific interview closings for closely-adjacent data skills. The data
# evidence pack historically handed the SQL closing to EVERY data skill, so a
# Python / Excel / Dashboarding answer closed by claiming "reliable SQL
# analysis" (Defect Class D). The closing must stay aligned to the question's
# primary skill, so these take precedence over the family-level closing.
_SKILL_SPECIFIC_CLOSINGS: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        ("sql", "structured query"),
        "In an interview, I would show that I can build reliable SQL analysis with sound joins, data quality controls, and performance awareness.",
    ),
    (
        ("python", "pandas"),
        "In an interview, I would show that I can build reliable, tested Python data workflows with clear structure and data-quality checks.",
    ),
    (
        ("excel", "spreadsheet"),
        "In an interview, I would show that I can build reliable, auditable Excel analysis with controlled formulas and reconciliation checks.",
    ),
    (
        ("dashboard", "visualisation", "visualization", "tableau", "power bi", "looker"),
        "In an interview, I would show that I can build clear, trustworthy dashboards with validated metrics and accessible design.",
    ),
)


def _skill_specific_closing(skill: str) -> str:
    s = (skill or "").lower()
    for keys, closing in _SKILL_SPECIFIC_CLOSINGS:
        if any(k in s for k in keys):
            return closing
    return ""


def _pick_closing(role_family: str, family_pack: dict[str, Any], role: str, skill: str) -> str:
    skill_specific = _skill_specific_closing(skill)
    if skill_specific:
        return skill_specific
    closings = family_pack.get("interview_closings") or []
    if closings:
        return str(closings[0])
    legacy = {
        "healthcare": "In an interview, I would show that I can connect pharmacology knowledge to safe prescribing, patient monitoring, escalation, and documentation.",
        "hospitality": "In an interview, I would show that I can prepare drinks consistently while controlling hygiene, allergens, speed, and customer experience.",
        "electrical": "In an interview, I would show that I understand installation as both a practical wiring task and a regulated inspection-and-testing responsibility.",
        "public_administration": "In an interview, I would show that I can run compliant public-service workflows with audit-ready records and clear escalation decisions.",
        "architecture": "In an interview, I would show that I can translate design intent into accurate, compliant, and revision-controlled deliverables.",
    }
    return legacy.get(role_family, f"In an interview, I would show applied technical judgement for {title_case_skill(skill)} in {role}.")


def build_evidence_slots(contract: dict[str, Any], q: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    skill = contract.get("mapped_skill") or q.get("skill_tag") or "General"
    role = contract.get("role") or (job.get("title") or "Professional")
    role_family = resolve_role_family(role, contract.get("role_family") or q.get("role_family"))
    card = q.get("skill_card") or {}
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    exp = resolve_expert_content(str(skill), role, str(resp or ""))
    family_pack = get_evidence_pack_for_question(role_family, role, str(skill))
    terms_pack = get_terminology_pack(str(skill), role, str(resp or ""))
    principles_pack = get_principles_pack(str(skill), role, str(resp or ""))
    calc_pack = q.get("calculation") or get_calculation_pack(str(skill), role, str(resp or ""))
    question_intent = detect_question_intent(
        q.get("question") or "",
        q.get("question_type"),
        category=q.get("category"),
    )
    terminology_terms = _terminology_terms_for_question(q, terms_pack, card, family_pack, str(skill), role)
    terms = [str(t.get("term")) for t in terminology_terms if isinstance(t, dict) and t.get("term")]
    standards = list(dict.fromkeys((card.get("standards") or []) + (exp.get("standards") or [])))
    domain_terms = list(
        dict.fromkeys(
            [str(t) for t in family_pack.get("domain_terms", [])]
            + terms
            + [str(s) for s in standards[:4]]
        )
    )
    domain_terms = [t for t in domain_terms if is_valid_key_term(str(t))]
    # §5 precedence: primary-skill native workflow first, then role-family default.
    # The skill-native override machinery is trusted only for *curated* per-skill
    # expert content. A generic per-profile fallback (e.g. Pharmacology borrowing the
    # healthcare-profile steps) must not masquerade as skill-native and displace the
    # family verification workflow, which is the appropriate method for the family-core
    # skill and carries required domain terms. `family_is_foreign` is determined
    # independently of which workflow wins, so a skill that IS the family core keeps its
    # single family opening/example and no redundant skill-native layer.
    expert_is_curated = has_curated_expert_content(str(skill), role)
    native_workflow = _skill_native_workflow(exp, str(skill)) if expert_is_curated else []
    family_workflow = _sanitize_steps(_workflow_steps(family_pack, str(skill), role))
    family_is_foreign = expert_is_curated and _family_workflow_is_foreign(
        family_workflow, str(skill), card, exp
    )
    if native_workflow:
        # The skill's own documented method dominates; the family workflow is not
        # applied as the core method. Family safety/verification still flow via
        # quality_checks/safety_checks below as an overlay.
        steps = native_workflow
    elif family_is_foreign:
        steps = _skill_anchored_workflow(str(skill), role)
    else:
        steps = family_workflow
    # When the primary skill is foreign to the family, prefer the skill's own
    # pitfalls over the family's default mistakes.
    if family_is_foreign:
        common_mistakes = (exp.get("technical_pitfalls") or card.get("common_mistakes") or family_pack.get("common_mistakes") or [])[:4]
    else:
        common_mistakes = (family_pack.get("common_mistakes") or exp.get("technical_pitfalls") or card.get("common_mistakes") or [])[:4]

    quality_checks = list(family_pack.get("verification_checks") or [])
    safety_checks = list(family_pack.get("safety_checks") or [])
    if not quality_checks:
        quality_checks = [
            "inspect output against required technical standard",
            "confirm readings are within permitted limits",
            "record measured test values correctly",
        ]
    if not safety_checks:
        safety_checks = [f"apply {s}" for s in standards[:2]] if standards else ["confirm safety prerequisites before execution"]

    # Use a skill-native opening when the skill has its own documented method
    # (native workflow) or the family default is foreign to it, so a specific
    # sub-skill (e.g. Load Calculations) is not defined by the family's generic
    # installation/testing opening (§5). The skill-first opening only *replaces*
    # the family opening — it is not layered on top — so length is unaffected.
    family_definition = select_role_family_opening(role_family, role, title_case_skill(str(skill)))
    if native_workflow or family_is_foreign:
        skill_opening = _skill_first_opening(role, str(skill), exp)
        definition = skill_opening if _opening_is_skill_distinct(skill_opening, family_definition) else family_definition
    else:
        definition = family_definition
    example = _pick_example(role, str(skill), family_pack, exp, prefer_expert=family_is_foreign)
    closing = pick_intent_closing(role_family, question_intent, _pick_closing(role_family, family_pack, role, str(skill)))

    skill_specific = expert_is_curated and _expert_is_skill_specific(exp)
    skill_native_mechanism = _skill_native_mechanisms(exp, str(skill)) if expert_is_curated else []
    skill_native_explanation = ""
    if skill_specific:
        for key in ("explain_answer", "teaching_body"):
            candidate = str(exp.get(key) or "").strip()
            if len(candidate.split()) >= 25:
                skill_native_explanation = candidate
                break

    return {
        "direct_definition": definition,
        "practical_steps": [str(s) for s in steps],
        "skill_native_mechanism": skill_native_mechanism,
        "skill_native_explanation": skill_native_explanation,
        "skill_is_specific": skill_specific,
        "family_workflow_is_foreign": family_is_foreign,
        "standards_or_regulations": [str(s) for s in standards] or [f"{role_family.replace('_', ' ').title()} standards"],
        "tools_or_documents": domain_terms[:10],
        "safety_checks": safety_checks,
        "quality_checks": quality_checks[:4],
        "common_mistakes": [str(m) for m in common_mistakes],
        "role_specific_example": example,
        "interview_ready_closing": closing,
        "question_intent": question_intent,
        "role_family": role_family,
        "terminology_terms": terminology_terms[:8],
        "calculation_pack": calc_pack or {},
        "principles": _principles_for_question(principles_pack, family_pack, str(skill)),
    }


def validate_evidence_slots(slots: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    qtype = contract.get("question_type")
    if qtype in {"technical_explain", "scenario", "technical_general", "standards"}:
        if not slots.get("direct_definition"):
            failures.append("missing_direct_definition")
        if len(slots.get("practical_steps") or []) < 4:
            failures.append("missing_practical_steps")
        if not (slots.get("standards_or_regulations") or []):
            failures.append("missing_standards")
        if not (slots.get("safety_checks") or []):
            failures.append("missing_safety_checks")
        if not (slots.get("common_mistakes") or []):
            failures.append("missing_common_mistake")
        if len((slots.get("role_specific_example") or "").split()) < 25:
            failures.append("weak_example")
    return failures
