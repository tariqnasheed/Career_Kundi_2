"""Internal multi-obligation contract for interview questions (004E-E2.3 A–D)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# --- Vocabulary ----------------------------------------------------------------

class Obligation(str, Enum):
    MOTIVATION_FIT = "motivation_fit"
    COMPANY_FIT = "company_fit"
    STRENGTHS = "strengths"
    CONTRIBUTION = "contribution"
    TECHNICAL_METHOD = "technical_method"
    SCENARIO_REASONING = "scenario_reasoning"
    METRIC = "metric"
    STANDARD_OR_PROTOCOL = "standard_or_protocol"
    FAILURE_MODE = "failure_mode"


MAJOR_OBLIGATIONS = frozenset(
    {
        Obligation.MOTIVATION_FIT.value,
        Obligation.COMPANY_FIT.value,
        Obligation.STRENGTHS.value,
        Obligation.CONTRIBUTION.value,
        Obligation.TECHNICAL_METHOD.value,
        Obligation.SCENARIO_REASONING.value,
    }
)
MODIFIER_OBLIGATIONS = frozenset(
    {
        Obligation.METRIC.value,
        Obligation.STANDARD_OR_PROTOCOL.value,
        Obligation.FAILURE_MODE.value,
    }
)


class QuestionOrigin(str, Enum):
    SYNTHETIC = "synthetic"
    EMPLOYER_PROVIDED = "employer_provided"
    UNKNOWN = "unknown"


_ORIGIN_SYNTHETIC_MARKERS = frozenset(
    {
        "mock_generate",
        "coverage_planner",
        "core_technical_content",
        "source_ladder",
        "profile_driven",
        "role_baseline",
    }
)


@dataclass(frozen=True)
class QuestionObligationProfile:
    obligations: tuple[str, ...]
    primary_obligation: str
    origin: str
    is_hybrid: bool
    synthetic_overload: bool
    overload_reasons: tuple[str, ...] = ()
    evidence_by_obligation: dict[str, str] = field(default_factory=dict)


# --- Origin --------------------------------------------------------------------

def resolve_question_origin(question: dict[str, Any]) -> str:
    explicit = (question.get("question_origin") or "").strip().lower()
    if explicit in {o.value for o in QuestionOrigin}:
        return explicit
    if question.get("employer_provided") or question.get("source") == "employer":
        return QuestionOrigin.EMPLOYER_PROVIDED.value
    gen = question.get("generation_stage_meta") or {}
    if isinstance(gen, dict) and any(
        gen.get(k)
        for k in (
            "stage_1_role_intelligence",
            "stage_2_skill_map",
            "stage_3_question_generation",
            "obligation_origin_source",
            "split_from",
        )
    ):
        return QuestionOrigin.SYNTHETIC.value
    return QuestionOrigin.UNKNOWN.value


def mark_synthetic_question(question: dict[str, Any], *, source: str = "coverage_planner") -> dict[str, Any]:
    out = dict(question)
    out["question_origin"] = QuestionOrigin.SYNTHETIC.value
    meta = dict(out.get("generation_stage_meta") or {})
    meta.setdefault("obligation_origin_source", source)
    out["generation_stage_meta"] = meta
    return out


# --- Clause segmentation -------------------------------------------------------

_ROLE_SUFFIX_RE = re.compile(
    r"\s+in this role-specific case.*$",
    re.I | re.S,
)
_MODIFIER_SUFFIX_RE = re.compile(
    r"\s+include one concrete .*?(?:metric|standard|protocol|failure mode).*$",
    re.I | re.S,
)
_COMPOUND_AND_RE = re.compile(
    r"(?:,\s*|\?\s*)and\s+(how would you|which strengths|what would you|how do you|how would)\s+",
    re.I,
)


def _strip_question_suffixes(text: str) -> str:
    out = _ROLE_SUFFIX_RE.sub("", text or "").strip()
    out = _MODIFIER_SUFFIX_RE.sub("", out).strip()
    return out


def segment_question_clauses(question: str) -> list[str]:
    """Bounded clause segmentation — avoids naive split on every 'and'."""
    base = _strip_question_suffixes(question)
    parts: list[str] = []
    for chunk in re.split(r"[?;]\s*", base):
        chunk = chunk.strip()
        if not chunk:
            continue
        split = _COMPOUND_AND_RE.split(chunk, maxsplit=1)
        if len(split) == 3:
            left, connector, right = (p.strip() for p in split)
            if left:
                parts.append(left if left.endswith("?") else f"{left}?")
            if right:
                joined = f"{connector} {right}".strip()
                parts.append(joined if joined.endswith("?") else f"{joined}?")
        elif len(split) == 2:
            left, right = split[0].strip(), split[1].strip()
            if left:
                parts.append(left if left.endswith("?") else f"{left}?")
            if right:
                parts.append(right if right.endswith("?") else f"{right}?")
        else:
            parts.append(chunk if chunk.endswith("?") else f"{chunk}?")
    return parts or [base]


# --- Obligation markers (support layer, not sole architecture) -----------------

_MOTIVATION_MARKERS = (
    "why do you want",
    "why are you interested",
    "why are you pursuing",
    "what excites you",
    "interested in this",
    "drawn to",
    "attracts you",
    "why this role",
    "why us",
    "why our",
    "want to work here",
    "want to join",
)
_COMPANY_MARKERS = (
    "what do you know about",
    "why do you want to work there",
    "why this company",
    "why this organisation",
    "why this organization",
    "alignment with",
)
_STRENGTHS_MARKERS = (
    "which strengths",
    "what strengths",
    "your strengths",
    "capabilities would",
    "what are you good at",
    "qualities would",
)
_CONTRIBUTION_MARKERS = (
    "how would you contribute",
    "what would you bring",
    "what would you contribute",
    "how would you help",
    "add value",
    "help you deliver",
    "help deliver",
)
_TECH_METHOD_MARKERS = (
    "how would you turn",
    "how would you improve",
    "how you would improve",
    "how would you deliver",
    "how would you perform",
    "how would you keep",
    "how do you apply",
    "walk me through how",
    "how would you approach",
    "break down",
    "workflow",
    "method",
)
_SCENARIO_MARKERS = (
    "handle conflicting",
    "what would you do if",
    "under constraints",
    "competing priorities",
    "when deadlines",
    "during busy rush",
    "during busy",
    "under pressure",
    "conflicting safety",
)
_METRIC_MARKERS = (
    "impact metric",
    "measurable quality signal",
    "measurable signal",
    "including impact metrics",
    "one concrete",
    " core competency metric",
    " kpi ",
    "measurable success",
    "which metric",
    "what metric",
    "which kpi",
    "what kpi",
)
_STANDARD_MARKERS = (
    "governing standard",
    "standard/protocol",
    "named standard",
    "regulation",
    "protocol",
    "compliance basis",
    " bs ",
    " iec ",
    " haccp",
    "nice ",
    "mhra",
)
_FAILURE_MARKERS = (
    "failure mode",
    "what can go wrong",
    "risk of failure",
    "mistake you actively avoid",
    "one failure",
)

_EXPLICIT_METRIC_ASK_MARKERS = (
    "which metric",
    "what metric",
    "which kpi",
    "what kpi",
    "which measurable",
    "what measurable",
)
_EXPLICIT_FAILURE_ASK_MARKERS = (
    "what failure mode",
    "which failure mode",
    "failure mode would you",
)
_EXPLICIT_STANDARD_ASK_MARKERS = (
    "which standard",
    "what standard",
    "which protocol",
    "what protocol",
    "governing standard",
)
_EXPLICIT_STANDARD_ASK_RE = re.compile(
    r"\bwhich\s+(?:[a-z]+\s+){0,3}standard\b"
    r"|\bwhat\s+(?:[a-z]+\s+){0,3}standard\b"
    r"|\bwhich\s+(?:[a-z]+\s+){0,2}protocol\b"
    r"|\bwhat\s+(?:[a-z]+\s+){0,2}protocol\b"
    r"|\bgoverning standard\b",
    re.I,
)

_METRIC_CANDIDATE_DIRECTED_RE = re.compile(
    r"\b(the\s+)?(impact\s+)?metric(s)?\s+you\s+(would|will|should)\s+"
    r"(monitor|track|measure|verify|use|watch)\b",
    re.I,
)
_METRIC_INCLUDING_DIRECTED_RE = re.compile(
    r"\bincluding\s+(the\s+)?(impact\s+)?metric(s)?\s+you\s+(would|will|should)\b",
    re.I,
)
_FAILURE_CANDIDATE_DIRECTED_RE = re.compile(
    r"\b(the\s+)?(main\s+)?failure mode(s)?\s+you\s+(would|will|should)\s+"
    r"(prepare|plan|guard|mitigat|avoid|handle|expect)\b",
    re.I,
)
_STANDARD_CANDIDATE_DIRECTED_RE = re.compile(
    r"\b(the\s+)?(governing\s+)?(standard|protocol|regulation)(s)?\s+you\s+(would|will|should)\s+"
    r"(follow|apply|use|cite|reference|retain|track|monitor|verify)\b",
    re.I,
)
_STANDARD_INCLUDING_DIRECTED_RE = re.compile(
    r"\bincluding\s+(the\s+)?(escalation\s+)?(standard|protocol|regulation)(s)?\s+you\s+(would|will|should)\b",
    re.I,
)
_PROTOCOL_CANDIDATE_DIRECTED_RE = re.compile(
    r"\b(the\s+)?(escalation\s+)?protocol(s)?\s+you\s+(would|will|should)\s+"
    r"(follow|apply|use|invoke|trigger|execute|run)\b",
    re.I,
)
_IMPERATIVE_MODIFIER_INCLUDE_RE = re.compile(
    # Allow a short noun phrase between "concrete" and the modifier keyword so
    # "Include one concrete Cable Sizing metric" / "one concrete core competency
    # metric" are recognised as imperative modifier demands, not just the bare
    # "include one concrete metric".
    r"\binclude\s+(one\s+)?(concrete\s+)?(?:[\w][\w /-]{0,40}?\s+)?(kpi|metric|failure mode|standard|protocol)\b",
    re.I,
)
_INCIDENTAL_METRIC_CONTEXT_RE = re.compile(
    r"\b(that|which|where)\s+included\s+(impact\s+)?metrics?\b"
    r"|\bworking with\s+.+\s+that included\s+(impact\s+)?metrics?\b"
    r"|\bincluded\s+(impact\s+)?metrics?\s+for\s+(operational|reporting|dashboard)\b",
    re.I,
)
_INCIDENTAL_STANDARD_CONTEXT_RE = re.compile(
    r"\b(governed by|under|working on .+ under|projects under)\s+[a-z0-9 /-]*\s*"
    r"(standards?|regulations?|protocols?)\b",
    re.I,
)


def _is_incidental_modifier_mention(clause: str, obligation: str) -> bool:
    lower = (clause or "").lower()
    if obligation == Obligation.METRIC.value:
        return bool(_INCIDENTAL_METRIC_CONTEXT_RE.search(lower))
    if obligation == Obligation.STANDARD_OR_PROTOCOL.value:
        if not _INCIDENTAL_STANDARD_CONTEXT_RE.search(lower):
            return False
        if any(m in lower for m in _EXPLICIT_STANDARD_ASK_MARKERS):
            return False
        if _EXPLICIT_STANDARD_ASK_RE.search(lower):
            return False
        if (
            _STANDARD_CANDIDATE_DIRECTED_RE.search(lower)
            or _STANDARD_INCLUDING_DIRECTED_RE.search(lower)
            or _PROTOCOL_CANDIDATE_DIRECTED_RE.search(lower)
        ):
            return False
        if _IMPERATIVE_MODIFIER_INCLUDE_RE.search(lower) and any(
            t in lower for t in ("standard", "protocol")
        ):
            return False
        return True
    return False


def _modifier_candidate_directed(clause: str, obligation: str) -> bool:
    lower = (clause or "").lower()
    if obligation == Obligation.METRIC.value:
        return bool(
            _METRIC_CANDIDATE_DIRECTED_RE.search(lower)
            or _METRIC_INCLUDING_DIRECTED_RE.search(lower)
        )
    if obligation == Obligation.FAILURE_MODE.value:
        return bool(_FAILURE_CANDIDATE_DIRECTED_RE.search(lower)) or (
            "failure mode" in lower and "you would" in lower
        )
    if obligation == Obligation.STANDARD_OR_PROTOCOL.value:
        return bool(
            _STANDARD_CANDIDATE_DIRECTED_RE.search(lower)
            or _STANDARD_INCLUDING_DIRECTED_RE.search(lower)
            or _PROTOCOL_CANDIDATE_DIRECTED_RE.search(lower)
        ) or (
            "you would" in lower and any(t in lower for t in ("standard", "protocol", "regulation"))
        )
    return False


def _modifier_explicitly_interrogated(clause: str, obligation: str) -> bool:
    lower = (clause or "").lower()
    if obligation == Obligation.METRIC.value:
        return any(m in lower for m in _EXPLICIT_METRIC_ASK_MARKERS)
    if obligation == Obligation.FAILURE_MODE.value:
        return any(m in lower for m in _EXPLICIT_FAILURE_ASK_MARKERS)
    if obligation == Obligation.STANDARD_OR_PROTOCOL.value:
        return any(m in lower for m in _EXPLICIT_STANDARD_ASK_MARKERS) or bool(
            _EXPLICIT_STANDARD_ASK_RE.search(lower)
        )
    return False


def _modifier_imperatively_required(clause: str, obligation: str) -> bool:
    lower = (clause or "").lower()
    if not _IMPERATIVE_MODIFIER_INCLUDE_RE.search(lower):
        return False
    if obligation == Obligation.METRIC.value:
        return "metric" in lower or "kpi" in lower
    if obligation == Obligation.FAILURE_MODE.value:
        return "failure mode" in lower
    if obligation == Obligation.STANDARD_OR_PROTOCOL.value:
        return any(t in lower for t in ("standard", "protocol"))
    return False


def _modifier_is_demanded(clause: str, obligation: str) -> bool:
    if _is_incidental_modifier_mention(clause, obligation):
        return False
    return (
        _modifier_explicitly_interrogated(clause, obligation)
        or _modifier_candidate_directed(clause, obligation)
        or _modifier_imperatively_required(clause, obligation)
    )


def _clause_has_modifier_surface(clause: str, obligation: str) -> bool:
    lower = (clause or "").lower()
    if obligation == Obligation.METRIC.value:
        return any(m in lower for m in _METRIC_MARKERS) or bool(
            re.search(r"\b(the\s+)?metric(s)?\s+you\s+(would|will|should)\b", lower)
        )
    if obligation == Obligation.FAILURE_MODE.value:
        return any(m in lower for m in _FAILURE_MARKERS) or bool(
            re.search(r"\bfailure mode(s)?\s+you\s+(would|will|should)\b", lower)
        )
    if obligation == Obligation.STANDARD_OR_PROTOCOL.value:
        return (
            any(m in lower for m in _STANDARD_MARKERS)
            or any(m in lower for m in _EXPLICIT_STANDARD_ASK_MARKERS)
            or bool(_EXPLICIT_STANDARD_ASK_RE.search(lower))
            or bool(_STANDARD_CANDIDATE_DIRECTED_RE.search(lower))
            or bool(_STANDARD_INCLUDING_DIRECTED_RE.search(lower))
            or bool(_PROTOCOL_CANDIDATE_DIRECTED_RE.search(lower))
        )
    return False


def _clause_obligations(clause: str) -> dict[str, str]:
    lower = clause.lower()
    found: dict[str, str] = {}
    if any(m in lower for m in _MOTIVATION_MARKERS):
        found[Obligation.MOTIVATION_FIT.value] = clause.strip()
    if any(m in lower for m in _COMPANY_MARKERS):
        found[Obligation.COMPANY_FIT.value] = clause.strip()
    if any(m in lower for m in _STRENGTHS_MARKERS):
        found[Obligation.STRENGTHS.value] = clause.strip()
    if any(m in lower for m in _CONTRIBUTION_MARKERS):
        found[Obligation.CONTRIBUTION.value] = clause.strip()
    if any(m in lower for m in _TECH_METHOD_MARKERS):
        found[Obligation.TECHNICAL_METHOD.value] = clause.strip()
    if any(m in lower for m in _SCENARIO_MARKERS):
        found[Obligation.SCENARIO_REASONING.value] = clause.strip()
    if _clause_has_modifier_surface(clause, Obligation.METRIC.value) and _modifier_is_demanded(
        clause, Obligation.METRIC.value
    ):
        found[Obligation.METRIC.value] = clause.strip()
    if _clause_has_modifier_surface(clause, Obligation.STANDARD_OR_PROTOCOL.value) and _modifier_is_demanded(
        clause, Obligation.STANDARD_OR_PROTOCOL.value
    ):
        found[Obligation.STANDARD_OR_PROTOCOL.value] = clause.strip()
    if _clause_has_modifier_surface(clause, Obligation.FAILURE_MODE.value) and _modifier_is_demanded(
        clause, Obligation.FAILURE_MODE.value
    ):
        found[Obligation.FAILURE_MODE.value] = clause.strip()
    return found


def _metadata_obligations(question: dict[str, Any]) -> dict[str, str]:
    meta = question.get("obligation_metadata") or {}
    if isinstance(meta, dict) and meta.get("obligations"):
        out: dict[str, str] = {}
        for item in meta.get("obligations") or []:
            if isinstance(item, str):
                out[item] = str(meta.get("evidence") or question.get("question") or "")
            elif isinstance(item, dict) and item.get("obligation"):
                out[str(item["obligation"])] = str(item.get("evidence") or "")
        return out
    qtype = (question.get("question_type") or "").lower()
    if qtype == "hr_motivation":
        return {Obligation.MOTIVATION_FIT.value: question.get("question") or ""}
    if qtype == "hr_logistics":
        return {}
    return {}


def extract_question_obligations(
    question: dict[str, Any],
    job: dict[str, Any] | None = None,
) -> QuestionObligationProfile:
    """Deterministic multi-label obligation extraction."""
    _ = job
    origin = resolve_question_origin(question)
    meta_found = _metadata_obligations(question)
    evidence: dict[str, str] = dict(meta_found)

    if not evidence:
        for clause in segment_question_clauses(question.get("question") or ""):
            for ob, ev in _clause_obligations(clause).items():
                evidence.setdefault(ob, ev)

    # Category hints when text is sparse.
    category = (question.get("category") or "").lower()
    qtype = (question.get("question_type") or "").lower()
    if not evidence and category in {"hr", "motivation", "role_specific", "company_specific"}:
        qtext = (question.get("question") or "").lower()
        if any(m in qtext for m in _MOTIVATION_MARKERS):
            evidence[Obligation.MOTIVATION_FIT.value] = question.get("question") or ""
        if category == "company_specific" or "what do you know about" in qtext:
            evidence.setdefault(Obligation.COMPANY_FIT.value, question.get("question") or "")
    if qtype in {"scenario", "case_study", "problem_solving", "complex_problem"}:
        evidence.setdefault(Obligation.SCENARIO_REASONING.value, question.get("question") or "")
    if qtype in {"calculation", "principles", "procedure", "explain", "tools", "standards", "technical_method"}:
        evidence.setdefault(Obligation.TECHNICAL_METHOD.value, question.get("question") or "")

    # Explicit modifier demands (metric / standard / failure mode) carried by a
    # genuinely technical or employer-provided question are REAL obligations and
    # must survive clause-suffix stripping. They are treated as unwanted only
    # when a non-technical question acquires them late (see
    # detect_synthetic_overload), so we detect them here from the full text but
    # only when the question is technical-anchored or employer-authored.
    raw_question = question.get("question") or ""
    if (
        Obligation.TECHNICAL_METHOD.value in evidence
        or origin == QuestionOrigin.EMPLOYER_PROVIDED.value
    ):
        for ob in (
            Obligation.METRIC.value,
            Obligation.STANDARD_OR_PROTOCOL.value,
            Obligation.FAILURE_MODE.value,
        ):
            if (
                ob not in evidence
                and _clause_has_modifier_surface(raw_question, ob)
                and _modifier_is_demanded(raw_question, ob)
            ):
                evidence[ob] = raw_question

    obligations = tuple(sorted(evidence.keys()))
    if not obligations:
        qtext = question.get("question") or ""
        if category == "behavioral" or qtype == "behavioral":
            obligations = (Obligation.SCENARIO_REASONING.value,)
        elif category == "company_specific":
            obligations = (Obligation.COMPANY_FIT.value,)
        else:
            obligations = (Obligation.TECHNICAL_METHOD.value,)
        evidence = {obligations[0]: qtext}

    major = [o for o in obligations if o in MAJOR_OBLIGATIONS]
    primary = major[0] if major else obligations[0]
    is_hybrid = len(major) > 1 or (
        len(major) == 1 and any(o in MODIFIER_OBLIGATIONS for o in obligations)
    )
    overload, reasons = detect_synthetic_overload(
        obligations,
        origin=origin,
        question=question,
    )
    return QuestionObligationProfile(
        obligations=obligations,
        primary_obligation=primary,
        origin=origin,
        is_hybrid=is_hybrid,
        synthetic_overload=overload,
        overload_reasons=reasons,
        evidence_by_obligation=evidence,
    )


def detect_synthetic_overload(
    obligations: tuple[str, ...] | list[str],
    *,
    origin: str,
    question: dict[str, Any] | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """True when a CareerKundi-controlled question combines unnecessary independent demands."""
    if origin != QuestionOrigin.SYNTHETIC.value:
        return False, ()
    obs = set(obligations)
    reasons: list[str] = []
    major = obs & MAJOR_OBLIGATIONS
    modifiers = obs & MODIFIER_OBLIGATIONS

    has_motivation = Obligation.MOTIVATION_FIT.value in obs or Obligation.COMPANY_FIT.value in obs
    has_technical = Obligation.TECHNICAL_METHOD.value in obs
    has_scenario = Obligation.SCENARIO_REASONING.value in obs

    if has_motivation and has_technical:
        reasons.append("motivation_plus_technical_method")
    if has_motivation and has_scenario and Obligation.MOTIVATION_FIT.value in obs:
        reasons.append("motivation_plus_scenario")
    if has_motivation and len(modifiers) >= 2:
        reasons.append("motivation_plus_multiple_modifiers")
    if has_motivation and has_technical and modifiers:
        reasons.append("motivation_technical_plus_modifiers")

    qtext = (question or {}).get("question") or ""
    if "include one concrete" in qtext.lower() and has_motivation:
        reasons.append("motivation_plus_forced_modifiers")

    # Late-stage triple-modifier reintroduction on a NON-technical question is
    # overload regardless of motivation content: a behavioral / daily-routine /
    # HR question that acquired "Include one concrete ... metric, one governing
    # standard/protocol, and one failure mode" from a uniqueness/dedupe pass was
    # never meant to demand technical modifiers (Defect Class C). This audits the
    # FINAL exported text, so it catches reintroduction even after overload
    # repair ran earlier in the pipeline.
    q_category = ((question or {}).get("category") or "").lower()
    q_type = ((question or {}).get("question_type") or "").lower()
    non_technical_intent = q_category in {
        "behavioral",
        "daily_routine",
        "hr",
        "motivation",
        "company_specific",
    } or q_type in {
        "behavioral",
        "daily_routine",
        "hr_motivation",
        "hr_logistics",
        "hr_development",
        "seniority",
        "day_one",
    }
    if non_technical_intent and "include one concrete" in qtext.lower():
        reasons.append("forced_modifiers_on_non_technical")

    # Strengths + motivation alone is a coherent hybrid — not overload.
    if reasons == [] and len(major) > 2:
        reasons.append("too_many_major_obligations")

    return bool(reasons), tuple(dict.fromkeys(reasons))


def profile_to_dict(profile: QuestionObligationProfile) -> dict[str, Any]:
    return {
        "obligations": list(profile.obligations),
        "primary_obligation": profile.primary_obligation,
        "origin": profile.origin,
        "is_hybrid": profile.is_hybrid,
        "synthetic_overload": profile.synthetic_overload,
        "overload_reasons": list(profile.overload_reasons),
        "evidence_by_obligation": dict(profile.evidence_by_obligation),
    }


def attach_obligation_profile(question: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    profile = extract_question_obligations(question, job)
    out = dict(question)
    out["obligation_profile"] = profile_to_dict(profile)
    return out


def get_question_obligation_profile(question: dict[str, Any], job: dict[str, Any] | None = None) -> QuestionObligationProfile:
    cached = question.get("obligation_profile")
    if isinstance(cached, dict) and cached.get("obligations"):
        return QuestionObligationProfile(
            obligations=tuple(cached.get("obligations") or ()),
            primary_obligation=str(cached.get("primary_obligation") or ""),
            origin=str(cached.get("origin") or QuestionOrigin.UNKNOWN.value),
            is_hybrid=bool(cached.get("is_hybrid")),
            synthetic_overload=bool(cached.get("synthetic_overload")),
            overload_reasons=tuple(cached.get("overload_reasons") or ()),
            evidence_by_obligation=dict(cached.get("evidence_by_obligation") or {}),
        )
    return extract_question_obligations(question, job or {})


def has_intentionally_retained_modifier_obligations(profile: QuestionObligationProfile) -> bool:
    """True when a modifier obligation is genuinely demanded by the question, not incidental."""
    for obligation in profile.obligations:
        if obligation not in MODIFIER_OBLIGATIONS:
            continue
        evidence = profile.evidence_by_obligation.get(obligation, "")
        if _modifier_is_demanded(evidence, obligation):
            return True
        if (
            profile.origin == QuestionOrigin.EMPLOYER_PROVIDED.value
            and _modifier_candidate_directed(evidence, obligation)
        ):
            return True
    return False


def question_in_obligation_audit_scope(question: dict[str, Any], profile: QuestionObligationProfile) -> bool:
    """Narrow canonical audit to HR/hybrid collapse defects (A–D), not all technical prompts."""
    if has_intentionally_retained_modifier_obligations(profile):
        return True
    category = (question.get("category") or "").lower()
    if category not in {"hr", "role_specific", "company_specific", "motivation"}:
        return False
    obs = set(profile.obligations)
    if profile.synthetic_overload:
        return True
    if obs & {Obligation.MOTIVATION_FIT.value, Obligation.COMPANY_FIT.value}:
        return True
    if profile.is_hybrid and len(obs & MAJOR_OBLIGATIONS) > 1:
        return True
    if is_pure_motivation_profile(profile):
        return True
    return False


def is_pure_motivation_profile(profile: QuestionObligationProfile) -> bool:
    obs = set(profile.obligations)
    allowed = {Obligation.MOTIVATION_FIT.value, Obligation.COMPANY_FIT.value}
    return obs.issubset(allowed) and Obligation.MOTIVATION_FIT.value in obs


def is_role_fit_study_profile(profile: QuestionObligationProfile) -> bool:
    """Study should teach fit (not workflow) when only motivation/company obligations are present."""
    obs = set(profile.obligations)
    disallowed = MAJOR_OBLIGATIONS - {
        Obligation.MOTIVATION_FIT.value,
        Obligation.COMPANY_FIT.value,
    }
    if obs & disallowed:
        return False
    return bool(obs & {Obligation.MOTIVATION_FIT.value, Obligation.COMPANY_FIT.value})


def _primary_responsibility(job: dict[str, Any]) -> str:
    # Neutral fallback ("the core work of the role") never claims a posting
    # captured specific listed duties when it did not (Defect Class E).
    resp = (job.get("responsibilities") or ["the core work of the role"])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    return str(resp or "the core work of the role")


def _primary_skill(job: dict[str, Any]) -> str:
    skills = job.get("extracted_skills") or []
    if skills:
        s = skills[0]
        return str(s.get("skill") if isinstance(s, dict) else s)
    return "core work"


def split_synthetic_overloaded_question(
    question: dict[str, Any],
    job: dict[str, Any],
    profile: QuestionObligationProfile | None = None,
) -> list[dict[str, Any]]:
    """Split an overloaded synthetic question into atomic learning units."""
    profile = profile or extract_question_obligations(question, job)
    if not profile.synthetic_overload:
        return [attach_obligation_profile(question, job)]

    role = job.get("title") or "this role"
    resp = _primary_responsibility(job)
    skill = question.get("mapped_skill") or question.get("skill_tag") or _primary_skill(job)
    base_meta = dict(question.get("generation_stage_meta") or {})
    base_meta["split_from"] = question.get("question_id") or question.get("question", "")[:80]

    motivation_q = mark_synthetic_question(
        {
            **{k: v for k, v in question.items() if k not in {"question_id", "model_answer", "study_material"}},
            "category": "hr",
            "question_type": "hr_motivation",
            "question": f"Why are you interested in this {role} role, particularly its focus on {resp.lower()}?",
            "skill_tag": None,
            "why_asked": "HR screen — genuine motivation and posting fit without unrelated technical workflow.",
            "ideal_answer_points": [
                "References specific responsibilities from the posting",
                "Connects motivation to genuine interests or development goals",
                "Avoids generic flattery or invented history",
            ],
        },
        source="obligation_split",
    )

    technical_text = profile.evidence_by_obligation.get(Obligation.TECHNICAL_METHOD.value, "")
    if Obligation.TECHNICAL_METHOD.value in profile.obligations:
        if technical_text and len(technical_text.split()) > 8:
            tech_question = _strip_question_suffixes(technical_text).rstrip("?") + "?"
        else:
            tech_question = (
                f"How would you approach {resp.lower()} in this {role} role using {skill}, "
                f"including the checks you would run before handoff?"
            )
        technical_q = mark_synthetic_question(
            {
                **{k: v for k, v in question.items() if k not in {"question_id", "model_answer", "study_material"}},
                "category": "technical",
                "question_type": "technical_method",
                "question": tech_question,
                "skill_tag": skill,
                "mapped_skill": skill,
                "why_asked": "Technical screen — method and verification for the primary responsibility.",
                "ideal_answer_points": [
                    "Clear method tied to the primary skill",
                    "Named checks or validation steps",
                    "Realistic failure awareness without inventing metrics",
                ],
            },
            source="obligation_split",
        )
        return [motivation_q, technical_q]

    if Obligation.STRENGTHS.value in profile.obligations or Obligation.CONTRIBUTION.value in profile.obligations:
        strengths_q = mark_synthetic_question(
            {
                **{k: v for k, v in question.items() if k not in {"question_id", "model_answer", "study_material"}},
                "category": "hr",
                "question_type": "hr_motivation",
                "question": (
                    f"Why are you interested in this {role} role, and which strengths would help you "
                    f"deliver on {resp.lower()} from the first month?"
                ),
                "skill_tag": None,
                "why_asked": "Hybrid HR — motivation plus relevant strengths, without unrelated modifiers.",
            },
            source="obligation_split_strengths",
        )
        return [strengths_q]

    cleaned = mark_synthetic_question(
        {
            **question,
            "question": f"Why are you interested in this {role} role, particularly its focus on {resp.lower()}?",
            "category": "hr",
            "question_type": "hr_motivation",
        },
        source="obligation_rewrite",
    )
    return [cleaned]


def repair_synthetic_question_overload(questions: list[dict[str, Any]], job: dict[str, Any]) -> list[dict[str, Any]]:
    """Layer-2 safety net: split/rewrite overloaded synthetic questions before finalize."""
    out: list[dict[str, Any]] = []
    for q in questions:
        q = dict(q)
        if resolve_question_origin(q) == QuestionOrigin.EMPLOYER_PROVIDED.value:
            out.append(attach_obligation_profile(q, job))
            continue
        profile = extract_question_obligations(q, job)
        if profile.synthetic_overload and profile.origin == QuestionOrigin.SYNTHETIC.value:
            out.extend(split_synthetic_overloaded_question(q, job, profile))
        else:
            out.append(attach_obligation_profile(q, job))
    return out
