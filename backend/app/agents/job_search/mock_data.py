"""
agents/job_search/mock_data.py
==================================
Offline, content-aware stand-ins for the two LLM calls in this feature
(job-field extraction, interview-question generation), used when
`settings.llm_mode == "mock"`.

Per the architectural principle stated in `app/tools/llm.py`, generic
mock plumbing (latency simulation, token accounting) lives in
`MockGeminiProvider`; the DOMAIN-SPECIFIC synthesis that actually inspects
the real input and produces a structurally and substantively realistic
result lives here. Both functions below genuinely parse/scan the real job
text handed to them — they do not return canned, input-independent
placeholders — which is what lets the rest of the pipeline (RAG retrieval,
GraphRAG enrichment, Reflector checks, persistence) exercise real logic
end-to-end even with zero API keys configured.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

# A broader, job-posting-flavored skill keyword list than the small
# GraphRAG seed graph (which is tuned for roadmap traversal) — this is
# specifically for scanning raw job description text for mentioned skills.
JOB_SKILL_KEYWORDS: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript": [r"\btypescript\b"],
    "React": [r"\breact(\.js)?\b"],
    "Node.js": [r"\bnode(\.js)?\b"],
    "SQL": [r"\bsql\b", r"\bpostgres(ql)?\b", r"\bmysql\b"],
    "Distributed Systems": [r"\bdistributed systems?\b"],
    "System Design": [r"\bsystem design\b", r"\barchitecture\b"],
    "Docker": [r"\bdocker\b", r"\bcontaineri[sz]ation\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "CI/CD": [r"\bci\/cd\b", r"\bcontinuous (integration|deployment)\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Azure": [r"\bazure\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Statistics": [r"\bstatistics\b", r"\bstatistical\b"],
    "Data Visualization": [r"\bdata visuali[sz]ation\b", r"\btableau\b", r"\bpower ?bi\b"],
    "ETL Pipelines": [r"\betl\b", r"\bdata pipelines?\b"],
    "REST API Design": [r"\brest(ful)? apis?\b", r"\bapi design\b"],
    "GraphQL": [r"\bgraphql\b"],
    "Technical Leadership": [r"\btechnical leadership\b", r"\btech lead\b"],
    "Mentoring": [r"\bmentor(ing|ship)?\b"],
    "Agile": [r"\bagile\b", r"\bscrum\b"],
    "Testing": [r"\bunit test(ing|s)?\b", r"\btest-driven\b", r"\btdd\b"],
    "Security": [r"\bsecurity\b", r"\bowasp\b"],
}

_SECTION_HEADERS: dict[str, list[str]] = {
    "responsibilities": [r"responsibilit(y|ies)", r"what you.?ll do", r"the role", r"duties"],
    "requirements": [r"requirements", r"qualifications", r"what you.?ll need", r"skills?(?! we)"],
    "benefits": [r"benefits", r"perks", r"what we offer", r"compensation"],
}


def _detect_title(text: str) -> str | None:
    """First non-empty, reasonably short line is usually the job title in a pasted posting."""
    for line in text.splitlines():
        stripped = line.strip(" \t-•*#")
        if 3 < len(stripped) <= 100 and not stripped.endswith("."):
            return stripped
    return None


def _detect_company(text: str) -> str | None:
    match = re.search(r"\bat\s+([A-Z][A-Za-z0-9&.,' ]{1,60}?)(?:[.,\n]|\s+is\s|\s+in\s)", text)
    if match:
        return match.group(1).strip()
    match = re.search(r"^company:\s*(.+)$", text, re.I | re.M)
    return match.group(1).strip() if match else None


def _detect_employment_type(text: str) -> str | None:
    lowered = text.lower()
    for kind in ("full-time", "part-time", "contract", "internship", "temporary"):
        if kind in lowered or kind.replace("-", " ") in lowered:
            return kind
    return None


def _detect_remote(text: str) -> bool | None:
    lowered = text.lower()
    if "fully remote" in lowered or re.search(r"\bremote\b", lowered):
        return True
    if "on-site" in lowered or "onsite" in lowered or "in office" in lowered or "in-office" in lowered:
        return False
    return None


def _extract_sections(text: str) -> dict[str, list[str]]:
    """
    Walk the text line by line; when a line matches a known section header,
    start collecting subsequent bullet-ish lines into that bucket until the
    next recognized header. Lines outside any recognized section are
    discarded (they're prose/boilerplate, not list items).
    """
    buckets: dict[str, list[str]] = {key: [] for key in _SECTION_HEADERS}
    current: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched_header = None
        for section, patterns in _SECTION_HEADERS.items():
            if any(re.search(p, line, re.I) for p in patterns) and len(line) < 60:
                matched_header = section
                break
        if matched_header:
            current = matched_header
            continue

        if current and len(line) > 8:
            cleaned = line.lstrip("-•*● \t")
            if cleaned and cleaned not in buckets[current]:
                buckets[current].append(cleaned)

    return buckets


def _extract_skills(text: str) -> list[dict]:
    """
    Scan for known skill keywords; a skill mentioned inside the detected
    "requirements" section is tagged `importance="critical"`, one mentioned
    elsewhere in the posting is tagged `"medium"` — a simple but genuinely
    input-dependent importance signal.
    """
    sections = _extract_sections(text)
    requirements_text = " ".join(sections.get("requirements", [])).lower()
    found = []
    for skill, patterns in JOB_SKILL_KEYWORDS.items():
        if any(re.search(p, text, re.I) for p in patterns):
            importance = "critical" if any(re.search(p, requirements_text, re.I) for p in patterns) else "medium"
            found.append({"skill": skill, "category": "technical", "importance": importance})
    return found


def mock_parse_job(text: str) -> dict:
    """Build a `JobEnrichmentResult`-shaped dict (minus citations/confidence, added by the Executor) purely from real text scanning — no fabricated fields."""
    sections = _extract_sections(text)
    return {
        "title": _detect_title(text) or "Untitled Role (title not detected in pasted text)",
        "company_name": _detect_company(text),
        "company_url": None,
        "location": "Remote" if _detect_remote(text) else None,
        "employment_type": _detect_employment_type(text),
        "is_remote": _detect_remote(text),
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "responsibilities": sections.get("responsibilities", []),
        "requirements": sections.get("requirements", []),
        "benefits": sections.get("benefits", []),
        "extracted_skills": _extract_skills(text),
    }


from app.agents.job_search.knowledge.coverage_planner import (
    MIN_EXPORTABLE_PACK_QUESTIONS,
    apply_coverage_plan,
    build_coverage_floor_questions,
    detect_coverage_archetype,
)
from app.agents.job_search.quality.surface_text_normalize import (
    normalize_study_material_dict,
    normalize_surface_text,
)
from app.agents.job_search.knowledge.study_sources import attach_study_source_metadata
from app.agents.job_search.knowledge.study_synthesis import (
    build_user_facing_related_skills,
    synthesize_study_module,
)
from app.agents.job_search.knowledge.content_engine import (
    build_answer_explanation,
    build_model_answer,
    build_study_material,
    is_generic_content,
    must_use_contract_compiler,
    polish_spoken_answer,
)
from app.agents.job_search.knowledge.core_technical_content import (
    build_technical_questions_for_skill,
    get_procedure_questions_for_role,
    get_role_terminology_question,
)
from app.agents.job_search.knowledge.evidence_packs import resolve_role_family
from app.agents.job_search.knowledge.question_contracts import create_question_contract
from app.agents.job_search.knowledge.skill_cards import (
    build_role_intelligence,
    build_skill_card_bank,
    map_question_to_skill_card,
)
from app.agents.job_search.job_intelligence import build_job_intelligence_profile, profile_to_dict
from app.agents.job_search.job_coverage_audit import (
    audit_pack_coverage,
    audit_to_dict,
    build_audit_items_for_profile,
    build_missing_coverage_questions,
    build_profile_driven_questions,
)
from app.agents.job_search.knowledge.source_ladder import (
    annotate_question_source_metadata,
    apply_source_ladder_to_job,
    build_source_ladder_questions,
    refresh_source_ladder_usage_from_questions,
)
from app.agents.job_search.knowledge.question_study_material import apply_finalized_study_module
from app.agents.job_search.knowledge.question_obligations import (
    attach_obligation_profile,
    mark_synthetic_question,
    repair_synthetic_question_overload,
)
from app.agents.job_search.quality.silly_question_guard import is_silly_or_vague_question
from app.agents.job_search.quality.broken_template_audit import broken_template_count
from app.agents.job_search.quality.compiler_boilerplate_audit import (
    compiler_boilerplate_count,
    universal_boilerplate_count,
)
from app.agents.job_search.quality.domain_contamination_audit import domain_contamination_count
from app.agents.job_search.quality.domain_density_audit import domain_density_breakdown, domain_density_from_context
from app.agents.job_search.quality.expert_naturalness_audit import (
    expert_naturalness_score,
    formulaic_spoken_label_count,
)
from app.agents.job_search.quality.generic_phrase_audit import generic_phrase_count
from app.agents.job_search.quality.legacy_template_audit import legacy_template_count
from app.agents.job_search.knowledge.study_material_budget import enforce_study_hard_max_after_export_touchup
from app.agents.job_search.quality.claim_integrity import rewrite_or_flag_unsupported_claims
from app.agents.job_search.quality.surface_quality_guard import fix_surface_quality_defects
from app.agents.job_search.quality.study_depth_audit import study_depth_score

_GENERIC_BEHAVIORAL_TEMPLATES = [
    "Tell me about a time you disagreed with a teammate's technical decision. How did you handle it?",
    "Describe a project where the requirements changed significantly midway through. What did you do?",
    "Walk me through a time you had to learn an unfamiliar technology quickly to deliver a project.",
    "Tell me about a mistake you made in a past role and what you learned from it.",
]

_DIFFICULTY_MAP = {"entry": "Easy", "mid": "Medium", "senior": "Hard", "auto": "Medium"}
_QUESTION_TYPE_SUFFIX = {
    "terminology": "TERM",
    "calculation": "CALC",
    "principles": "PRIN",
    "procedure": "PROC",
    "explain": "EXPL",
    "scenario": "SCEN",
}
_GLOBAL_QUESTION_FINGERPRINTS: dict[str, set[str]] = {}
COMPILER_ONLY_TYPES = {
    "technical",
    "technical_explain",
    "conceptual",
    "scenario",
    "complex_problem",
    "problem_solving",
    "case_study",
    "practical_task",
    "tools",
    "software",
    "standards",
    "regulation",
    "explain",
    "explain_to_peer",
}

_ROLE_FAMILY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "healthcare": ("nurse", "pharmacist", "doctor", "gp", "physio", "radiograph", "clinical", "therapist"),
    "engineering": ("engineer", "electrician", "mechanical", "civil engineer", "chemical", "structural", "maintenance"),
    "technology": ("software", "developer", "data", "devops", "cyber", "cloud", "architect", "qa"),
    "finance_legal": ("accountant", "finance", "investment", "analyst", "solicitor", "paralegal", "compliance"),
    "education": ("teacher", "lecturer", "tutor", "teaching assistant"),
    "public_admin": ("civil service", "policy", "administrator", "public"),
    "creative_design": (
        "graphic designer", "visual designer", "brand designer", "ui designer", "illustrator", "art director",
    ),
    "creative_media": (
        "journalist", "video editor", "content writer", "copywriter", "photographer", "reporter", "sub-editor",
    ),
    "creator_trending": (
        "youtuber", "influencer", "podcaster", "social media creator", "content creator", "streamer", "esports",
    ),
    "sports": ("footballer", "cricketer", "athlete", "coach", "fitness trainer", "personal trainer"),
}


# --- Interview pack synthesis --------------------------------------------------------


def _role_family(role_title: str) -> str:
    role = (role_title or "").lower()
    for family, keys in _ROLE_FAMILY_KEYWORDS.items():
        if any(k in role for k in keys):
            return family
    return "general"


def _role_family_for_pack(role_title: str) -> str:
    return resolve_role_family(role_title)


def _family_behavioral_templates(job: dict) -> list[str]:
    role = job.get("title") or "this role"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    ctx = f" while handling '{resp}'" if resp else ""
    role_key = re.sub(r"[^a-z0-9]+", "-", role.lower()).strip("-")
    selector = abs(hash(role_key)) % 3
    family = _role_family(role)
    if family == "healthcare":
        variants = [
            [
                f"Describe a time you identified a patient safety risk in {role} work{ctx} and how you escalated it.",
                f"Tell me about a situation in {role} practice{ctx} where you had to prioritise multiple deteriorating patients.",
                f"Give a case from {role} duties{ctx} where SBAR communication changed a clinical outcome.",
            ],
            [
                f"In {role} work{ctx}, describe a near-miss you intercepted through early risk recognition.",
                f"Explain a shift in {role} practice{ctx} where triage prioritisation directly affected outcomes.",
                f"Share an example from {role} care{ctx} where escalation timing was the deciding factor.",
            ],
            [
                f"Describe a safety-critical judgement call you made as a {role}{ctx}.",
                f"Tell me about a patient deterioration scenario you managed in {role} practice{ctx}.",
                f"Provide an example where your documentation/hand-off in {role} work{ctx} prevented harm.",
            ],
        ]
        return variants[selector]
    if family == "engineering":
        variants = [
            [
                f"Describe a time you stopped work due to a safety/compliance risk in a {role} task{ctx}.",
                f"Tell me about a technical fault you diagnosed under time pressure in {role} work{ctx} and how you verified the fix.",
                f"Give an example where your calculations or test results in {role} delivery{ctx} prevented rework or failure.",
            ],
            [
                f"In {role} execution{ctx}, describe a decision where compliance overruled schedule pressure.",
                f"Share a root-cause investigation from {role} work{ctx} where measured values contradicted assumptions.",
                f"Describe a verification plan you designed in {role} practice{ctx} to prove technical integrity.",
            ],
            [
                f"Tell me about a defect or hazard you discovered late in a {role} workflow{ctx} and how you contained it.",
                f"Describe a constrained engineering problem in {role} work{ctx} where your method choice mattered most.",
                f"Give one example of a standards-based check in {role} delivery{ctx} that changed the outcome.",
            ],
        ]
        return variants[selector]
    if family == "technology":
        variants = [
            [
                f"Describe a production incident you handled in a {role} context{ctx} and your root-cause process.",
                f"Tell me about a time in {role} delivery{ctx} you traded speed against reliability or security.",
                f"Describe a system or query optimization you shipped as a {role}{ctx} and the measurable impact.",
            ],
            [
                f"In {role} operations{ctx}, describe an outage response where you owned mitigation and follow-up.",
                f"Give an example where a technical debt decision in {role} work{ctx} improved long-term stability.",
                f"Describe a performance bottleneck you resolved in {role} systems{ctx} with before/after metrics.",
            ],
            [
                f"Tell me about a rollback or hotfix decision you made in {role} production work{ctx}.",
                f"Describe a security-reliability tradeoff you handled in {role} delivery{ctx}.",
                f"Share one optimization you implemented in {role} practice{ctx} and how you measured success.",
            ],
        ]
        return variants[selector]
    if family == "finance_legal":
        return [
            f"Tell me about a time you caught a material risk/compliance issue in {role} work.",
            "Describe a difficult stakeholder challenge where evidence and regulation guided your decision.",
            "Give an example where your analysis changed a business or case outcome.",
        ]
    if family == "education":
        return [
            f"Describe a lesson/intervention that moved outcomes for underperforming learners in {role} work.",
            "Tell me about a safeguarding or pastoral issue and how you handled it.",
            "Give an example of adapting instruction based on assessment evidence.",
        ]
    if family == "public_admin":
        return [
            f"Describe a policy or service-delivery decision you supported with evidence in {role} work.",
            "Tell me about a time you coordinated multiple stakeholders with conflicting priorities.",
            "Give an example of improving process compliance without delaying delivery.",
        ]
    if family == "creative_design":
        return [
            f"Describe a deadline crisis in {role} work{ctx} and how you protected quality while still delivering assets.",
            f"Tell me about a design brief{ctx} where stakeholder feedback changed your final layout or visual direction.",
            f"Give an example of handling brand-guideline constraints in {role} practice{ctx}.",
        ]
    if family == "creative_media":
        return [
            f"Describe a deadline crisis in {role} work{ctx} and how you protected accuracy while still publishing.",
            f"Tell me about a story or piece{ctx} where source verification changed your final angle.",
            f"Give an example of handling sensitive editorial feedback in {role} practice{ctx}.",
        ]
    if family == "creator_trending":
        return [
            f"Describe a content launch as a {role}{ctx} that underperformed and how you diagnosed the issue.",
            f"Tell me about a sponsorship or brand decision{ctx} where you prioritised audience trust.",
            f"Give an example of community moderation or reputation pressure{ctx} you managed calmly.",
        ]
    if family == "sports":
        return [
            f"Describe how you prepared for an important match or competition as a {role}{ctx}.",
            f"Tell me about a teamwork moment{ctx} where communication changed the outcome.",
            f"Give an example of applying coaching feedback{ctx} to improve performance safely.",
        ]
    variants = [
        [
            f"Describe a difficult delivery challenge specific to {role} responsibilities{ctx} and how you resolved it.",
            f"Tell me about a time you improved quality or outcomes in your {role} work{ctx} using measurable evidence.",
            f"Describe a stakeholder conflict in {role} work{ctx} and the decision framework you used.",
        ],
        [
            f"In {role} duties{ctx}, describe a deadline risk and the controls you used to keep delivery on track.",
            f"Share an example from {role} work{ctx} where you improved process reliability or quality.",
            f"Tell me about a cross-team disagreement in {role} practice{ctx} and how you reached alignment.",
        ],
        [
            f"Describe one complex assignment in {role} work{ctx} where your planning prevented failure.",
            f"Give an example where your evidence or metrics in {role} delivery{ctx} changed a decision.",
            f"Explain a stakeholder-management challenge from {role} work{ctx} and the outcome.",
        ],
    ]
    return variants[selector]


def _question_dedupe_key(q: dict) -> str:
    text = (q.get("question") or "").lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\b(this|that|the|a|an|role|position|job)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return " ".join(text.split()[:16])


def _skill_aligned_context_responsibility(job: dict, skill: str | None) -> str:
    """Pick a responsibility to use as question context without borrowing a
    DIFFERENT skill's responsibility.

    A Python / Excel / Dashboarding question anchored to a "SQL dashboard
    creation" responsibility framed the question around a foreign skill (Defect
    Class D framing). We prefer a responsibility that does not name any of the
    role's OTHER extracted skills; only if none qualifies do we fall back to the
    first responsibility.
    """
    resps = [
        (r.get("text") if isinstance(r, dict) else r)
        for r in (job.get("responsibilities") or [])
    ]
    resps = [str(r).strip() for r in resps if r]
    if not resps:
        return ""
    skill_l = (skill or "").lower()
    other_skills = [
        str(s.get("skill") if isinstance(s, dict) else s).lower()
        for s in (job.get("extracted_skills") or [])
    ]
    other_skills = [s for s in other_skills if s and s != skill_l]
    for resp in resps:
        rl = resp.lower()
        if not any(os and os in rl for os in other_skills):
            return resp
    return resps[0]


def _role_specific_context(job: dict, skill: str | None = None) -> str:
    role = job.get("title") or "this role"
    resp = _skill_aligned_context_responsibility(job, skill)
    if resp:
        return f"{role} context: {resp}"
    return role


def _global_fingerprint(question: str, qtype: str) -> str:
    text = (question or "").lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\b(registered nurse|civil service administrator|electrical engineer|chemical engineer|software engineer|data scientist|general practitioner|clinical pharmacist|radiographer|physiotherapist)\b", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = " ".join(text.split()[:22])
    return f"{qtype}:{text}"


def _enforce_cross_role_uniqueness(enriched: dict, job: dict) -> None:
    from app.agents.job_search.knowledge.study_material_budget import is_job_thin

    qtype = enriched.get("question_type") or enriched.get("category", "other")
    qtext = enriched.get("question", "")
    category = (enriched.get("category") or "").lower()
    q_lower = qtext.lower()
    thin = is_job_thin(job)
    qtype_l = (enriched.get("question_type") or "").lower()
    # A metric/standard/failure-mode demand is only appropriate on a genuinely
    # technical question. Appending it to behavioral, daily-routine, HR, or
    # motivation questions as a uniqueness/dedupe device is exactly the
    # synthetic overload that Defect Class C reproduced. Skip those categories
    # (and thin inputs) so a late uniqueness pass can never overload them.
    skip_modifier_suffix = (
        category in {"hr", "motivation", "company_specific", "behavioral", "daily_routine"}
        or qtype_l in {
            "behavioral",
            "daily_routine",
            "hr_motivation",
            "hr_logistics",
            "hr_development",
            "seniority",
            "day_one",
            "responsibility",
        }
        or any(
            m in q_lower
            for m in (
                "why are you interested",
                "why do you want",
                "what excites you",
                "what do you know about",
            )
        )
        or thin
    )
    # `skip_modifier_suffix` retained for callers/telemetry; the uniqueness pass
    # itself no longer appends metric/standard/failure-mode demands (Defect
    # Class C invariant), so it can never overload a question as a dedupe device.
    _ = skip_modifier_suffix
    key = _global_fingerprint(qtext, qtype)
    bucket = _GLOBAL_QUESTION_FINGERPRINTS.setdefault(qtype, set())
    if key in bucket:
        context = _role_specific_context(job, enriched.get("skill_tag"))
        if "In this role-specific case" not in qtext:
            # Role-specific context is a semantically-neutral differentiator. We
            # deliberately do NOT escalate to appending technical modifier
            # demands (metric / standard / failure mode) when a residual
            # collision remains — that reintroduction is exactly Defect Class C.
            enriched["question"] = f"{qtext} In this role-specific case, address: {context}."
            qtext = enriched["question"]
            key = _global_fingerprint(qtext, qtype)
    bucket.add(key)


def _boost_specificity(enriched: dict, job: dict) -> None:
    """Ensure answer/study mention role-specific technical anchors."""
    if enriched.get("export_blocked"):
        return
    if enriched.get("category") in ("hr", "daily_routine", "behavioral"):
        return
    if enriched.get("question_type") in {
        "case_study",
        "practical_task",
        "hr_motivation",
        "hr_logistics",
        "hr_development",
        "seniority",
        "daily_routine",
        "day_one",
        "responsibility",
    }:
        return
    role = job.get("title") or "this role"
    model = enriched.get("model_answer", "")
    study = enriched.get("study_material") or {}
    principles = study.get("principles") or []
    definitions = study.get("definitions") or []
    anchors: list[str] = []
    for p in principles[:2]:
        if isinstance(p, str):
            anchors.append(p)
    for d in definitions[:2]:
        if isinstance(d, dict):
            term = d.get("term")
            if term:
                anchors.append(str(term))
    if not anchors:
        anchors = enriched.get("related_skills", [])[:2]

    must_mention = role.lower() in model.lower()
    has_anchor = any(a and a.lower() in model.lower() for a in anchors if isinstance(a, str))
    if not must_mention or not has_anchor:
        addendum = f"\n\nIn {role} practice, I anchor this using: {', '.join(str(a) for a in anchors[:3])}."
        enriched["model_answer"] = (model + addendum).strip()


def _study_material_for_question(q: dict, job: dict) -> dict:
    """Delegate to PhD-level content engine."""
    return build_study_material(q, job)


def _answer_explanation(q: dict, job: dict) -> str:
    """Delegate to content engine with model answer context."""
    model = q.get("model_answer") or _model_answer_from_points(q, job)
    return build_answer_explanation(q, job, model)


def _related_skills_for(q: dict, job: dict) -> list[str]:
    return build_user_facing_related_skills(q, job)


def _role_baseline_questions(job: dict) -> list[dict]:
    """When no skills were extracted, still generate role-specific questions from title/description."""
    role = job.get("title") or "this role"
    desc = (job.get("description_raw") or "")[:500]
    reqs = job.get("requirements") or []
    return [
        {
            "category": "role_specific",
            "question": f"What core competencies make someone successful as a {role}?",
            "why_asked": "Tests whether the candidate understands the role beyond the job title.",
            "ideal_answer_points": [
                f"Names 3–5 competencies specific to {role}, not generic soft skills only",
                "Connects each competency to real workplace outcomes",
                "References responsibilities from the posting" if desc or reqs else "Uses concrete examples",
            ],
            "skill_tag": role,
        },
        {
            "category": "behavioral",
            "question": f"Describe a challenging situation you handled that is relevant to working as a {role}.",
            "why_asked": "Assesses past behavior using STAR under role-relevant pressure.",
            "ideal_answer_points": ["Situation", "Task", "Action", "Result (quantified)"],
            "skill_tag": None,
        },
        {
            "category": "technical" if any(w in role.lower() for w in ("engineer", "developer", "analyst", "scientist")) else "role_specific",
            "question": f"How would you approach a typical day-one task in a {role} position?",
            "why_asked": "Reveals practical readiness and structured thinking for the role.",
            "ideal_answer_points": [
                "Clarifies assumptions before acting",
                "Outlines a step-by-step approach",
                "Mentions tools, methods, or standards appropriate to the role",
            ],
            "skill_tag": role,
        },
    ]


def _model_answer_from_points(q: dict, job: dict) -> str:
    """Synthesize a comprehensive PhD-level model answer via the content engine."""
    return build_model_answer(q, job)


def _common_mistakes_for(q: dict) -> list[str]:
    category = q.get("category", "technical")
    if category == "behavioral":
        return [
            "Answering hypothetically instead of citing a specific past example.",
            "Spending too long on Situation and skipping measurable Result.",
            "Blaming others without showing personal accountability.",
        ]
    return [
        "Reciting jargon without explaining underlying concepts.",
        "Claiming expertise without a concrete example.",
        "Ignoring tradeoffs or failure modes.",
    ]


# Study-material keys whose values are metadata/numeric bookkeeping, not prose.
_STUDY_SANITIZE_SKIP_KEYS = frozenset(
    {
        "study_depth",
        "study_depth_label",
        "study_complexity_level",
        "complexity_signals",
        "budget_status",
        "budget_reason",
        "concise_complete_reason",
        "target_min_words",
        "target_max_words",
        "hard_max_words",
        "actual_word_count",
        "hard_max_ratio",
        "estimated_reading_time_minutes",
        "depth_contract_required_elements",
        "depth_contract_present_elements",
        "depth_contract_substantive_elements",
        "depth_contract_weak_elements",
        "depth_contract_missing_elements",
        "depth_contract_coverage",
        "substantive_contract_coverage",
        "source_types_used",
        "source_priority_used",
        "source_status",
    }
)


# Question-level keys to leave untouched by the final prose-sanitiser pass:
# the question stem (kept verbatim / surface-fixed separately), study_material
# (already sanitised + hard-max enforced), and non-prose metadata/ids.
_QUESTION_PROSE_SKIP_KEYS = frozenset(
    {
        "question",
        "question_id",
        "study_material",
        "category",
        "question_type",
        "skill_tag",
        "mapped_skill",
        "role_family",
        "answer_source",
        "difficulty",
        "export_blocked",
        "used_fallback_template",
        "used_legacy_polisher",
        "estimated_answer_time_minutes",
        "coverage_item_ids",
        "question_source_items",
        "question_source_types",
        "source_priority_used",
        "source_status",
        "study_sources",
        "quality_audit",
        "quality_gate_status",
        "generation_stage_meta",
        "model_knowledge_support",
        "related_skills",
    }
)


# Minimal cross-SKILL scrub: SQL/DevOps jargon that must not appear as if it
# defines a spreadsheet/visualisation skill. Replacements keep sentences coherent
# and skill-appropriate rather than leaving dangling fragments. Applied ONLY when
# the question's own skill is Excel/Dashboarding, so genuine SQL/DevOps questions
# are untouched. Ordered longest-first so specific phrases win over generic ones.
_EXCEL_FOREIGN_SCRUB: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"query execution plans?", re.I), "formula and calculation efficiency"),
    (re.compile(r"execution plans?", re.I), "calculation efficiency"),
    (re.compile(r"join cardinality", re.I), "lookup key matching"),
    (re.compile(r"schema design", re.I), "workbook and table structure"),
    (re.compile(r"connection[- ]pool(?:\s+sizing)?s?", re.I), "workbook data connections"),
    (re.compile(r"\bqps\b", re.I), "recalculation load"),
    (re.compile(r"index seeks?", re.I), "lookups"),
    (re.compile(r"bookmark lookups?", re.I), "cell lookups"),
    (re.compile(r"\bkubernetes\b", re.I), "the spreadsheet toolset"),
    (re.compile(r"\bci/cd\b", re.I), "the update workflow"),
    (re.compile(r"least privilege", re.I), "restricted access"),
    (re.compile(r"rollback plan", re.I), "change backup"),
    (re.compile(r"rollback criteria", re.I), "change-backout criteria"),
)

_DASHBOARDING_FOREIGN_SCRUB: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"query execution plans?", re.I), "dashboard refresh efficiency"),
    (re.compile(r"execution plans?", re.I), "refresh efficiency"),
    (re.compile(r"join cardinality", re.I), "data relationship matching"),
    (re.compile(r"schema design", re.I), "data model structure"),
    (re.compile(r"connection[- ]pool(?:\s+sizing)?s?", re.I), "data source connections"),
    (re.compile(r"\bqps\b", re.I), "refresh load"),
    (re.compile(r"\bkubernetes\b", re.I), "the reporting toolset"),
    (re.compile(r"\bci/cd\b", re.I), "the publish workflow"),
    (re.compile(r"rollback criteria", re.I), "change-backout criteria"),
)


def _skill_scrub_rules(skill: str) -> tuple[tuple[re.Pattern[str], str], ...]:
    s = (skill or "").lower()
    if "excel" in s or "spreadsheet" in s:
        return _EXCEL_FOREIGN_SCRUB
    if "dashboard" in s or "visual" in s:
        return _DASHBOARDING_FOREIGN_SCRUB
    return ()


def _scrub_skill_foreign_terms(text: str, rules: tuple[tuple[re.Pattern[str], str], ...]) -> str:
    if not rules or not text:
        return text
    out = text
    for pattern, repl in rules:
        out = pattern.sub(repl, out)
    return re.sub(r"[ \t]{2,}", " ", out)


def _sanitize_prose_value(
    value: str,
    job: dict,
    role_title: str,
    scrub_rules: tuple[tuple[re.Pattern[str], str], ...] = (),
) -> str:
    cleaned = fix_surface_quality_defects(value, role=role_title)
    cleaned, _ = rewrite_or_flag_unsupported_claims(cleaned, job)
    cleaned = _scrub_skill_foreign_terms(cleaned, scrub_rules)
    return cleaned


def _sanitize_study_material_recursive(
    node, job: dict, role_title: str, scrub_rules: tuple[tuple[re.Pattern[str], str], ...] = ()
):
    """Recursively fix surface defects, unsupported claims, and cross-skill
    foreign jargon across all user-facing prose — including nested lists/dicts
    (e.g. advanced_extension) — while skipping metadata keys."""
    if isinstance(node, str):
        return _sanitize_prose_value(node, job, role_title, scrub_rules)
    if isinstance(node, dict):
        out = {}
        for key, val in node.items():
            if isinstance(key, str) and key in _STUDY_SANITIZE_SKIP_KEYS:
                out[key] = val
            else:
                out[key] = _sanitize_study_material_recursive(val, job, role_title, scrub_rules)
        return out
    if isinstance(node, list):
        return [_sanitize_study_material_recursive(item, job, role_title, scrub_rules) for item in node]
    return node


def _finalize_question(q: dict, job: dict, difficulty: str, index: int = 0) -> dict:
    """Enrich a draft question with model answer, study material, and evaluation metadata."""
    enriched = dict(q)
    slug = re.sub(r"[^A-Z0-9]+", "-", (job.get("title") or "ROLE").upper())[:20]
    skill_part = re.sub(r"[^A-Z0-9]+", "-", (enriched.get("skill_tag") or enriched.get("category", "GEN")).upper())[:12]
    type_suffix = _QUESTION_TYPE_SUFFIX.get(enriched.get("question_type", ""), "")
    id_core = f"{slug}-{skill_part}"
    if type_suffix:
        id_core = f"{id_core}-{type_suffix}"
    enriched.setdefault("question_id", f"{id_core}-{index + 1:03d}")
    enriched.setdefault("difficulty", _DIFFICULTY_MAP.get(difficulty, "Medium"))
    enriched.setdefault("related_skills", _related_skills_for(enriched, job))
    enriched.setdefault("evaluation_criteria", list(enriched.get("ideal_answer_points") or []))
    enriched.setdefault("common_mistakes", _common_mistakes_for(enriched))
    follow_ups = enriched.get("follow_ups") or []
    enriched.setdefault("follow_up_questions", list(follow_ups))
    enriched.setdefault("estimated_answer_time_minutes", 5 if enriched.get("category") == "behavioral" else 8)
    enriched = attach_obligation_profile(enriched, job)
    _enforce_cross_role_uniqueness(enriched, job)
    enriched = attach_obligation_profile(enriched, job)
    enriched.setdefault("model_answer", _model_answer_from_points(enriched, job))
    enriched.setdefault("expert_reference_answer", enriched.get("model_answer", ""))
    contract = create_question_contract(enriched, job)
    compiler_only = must_use_contract_compiler(enriched, contract)
    if not compiler_only:
        enriched["model_answer"] = polish_spoken_answer(enriched.get("model_answer", ""), enriched, job)
        enriched["used_legacy_polisher"] = True
    else:
        enriched["used_legacy_polisher"] = False
    enriched.setdefault("answer_explanation", _answer_explanation(enriched, job))
    enriched.setdefault("study_material", _study_material_for_question(enriched, job))
    # Upgrade thin or generic LLM content from live path
    if is_generic_content(enriched.get("model_answer", "")) and not enriched.get("export_blocked"):
        enriched["model_answer"] = build_model_answer(enriched, job)
    if not compiler_only:
        enriched["model_answer"] = polish_spoken_answer(enriched.get("model_answer", ""), enriched, job)
    # Force at least one role anchor in technical answers.
    role_anchor = (job.get("title") or "").lower()
    if role_anchor and enriched.get("category") in ("technical", "role_specific") and not enriched.get("export_blocked"):
        if role_anchor not in enriched.get("model_answer", "").lower():
            enriched["model_answer"] = build_model_answer(enriched, job)
    study = enriched.get("study_material") or {}
    if is_generic_content(study.get("overview", "")):
        enriched["study_material"] = build_study_material(enriched, job)
    if is_generic_content(enriched.get("answer_explanation", "")):
        enriched["answer_explanation"] = build_answer_explanation(enriched, job, enriched["model_answer"])
    quality = enriched.setdefault("quality_audit", {})
    quality["generic_phrase_count"] = generic_phrase_count(enriched.get("model_answer", ""))
    quality["broken_template_count"] = broken_template_count(enriched.get("model_answer", ""))
    quality["legacy_template_count"] = legacy_template_count(enriched.get("model_answer", ""))
    quality["compiler_boilerplate_count"] = compiler_boilerplate_count(enriched.get("model_answer", ""))
    quality["universal_boilerplate_count"] = universal_boilerplate_count(enriched.get("model_answer", ""))
    quality["domain_contamination_count"] = domain_contamination_count(
        enriched.get("model_answer", ""), enriched.get("role_family", "default")
    )
    quality["domain_density"] = (enriched.get("quality_audit") or {}).get(
        "domain_density",
        domain_density_from_context(
            enriched.get("model_answer", ""),
            contract,
            enriched.get("evidence_slots"),
            card=enriched.get("skill_card"),
        ),
    )
    quality["core_domain_term_coverage"] = (enriched.get("quality_audit") or {}).get("core_domain_term_coverage", 0.0)
    quality["standard_tool_coverage"] = (enriched.get("quality_audit") or {}).get("standard_tool_coverage", 0.0)
    quality["overlap_excluded_count"] = (enriched.get("quality_audit") or {}).get("overlap_excluded_count", 0.0)
    quality["final_recalibrated_density"] = (enriched.get("quality_audit") or {}).get(
        "final_recalibrated_density",
        quality.get("domain_density", 0.0),
    )
    quality["expert_naturalness_score"] = (enriched.get("quality_audit") or {}).get(
        "expert_naturalness_score",
        expert_naturalness_score(enriched.get("model_answer", ""), contract, enriched.get("evidence_slots")),
    )
    quality["formulaic_spoken_label_count"] = (enriched.get("quality_audit") or {}).get(
        "formulaic_spoken_label_count",
        formulaic_spoken_label_count(enriched.get("model_answer", "")),
    )
    quality["study_depth_score"] = study_depth_score(enriched.get("study_material") or {})
    quality["skill_card_consumption_score"] = (enriched.get("quality_audit") or {}).get(
        "skill_card_consumption_score", 0.0
    )
    final_surface_failures = (enriched.get("quality_audit") or {}).get("final_surface_failures", [])
    quality["final_surface_failure_count"] = len(final_surface_failures)
    quality["empty_compliance_slot_count"] = final_surface_failures.count("empty_compliance_slot")
    quality["invalid_key_term_count"] = final_surface_failures.count("invalid_key_term")
    quality["truncated_example_count"] = final_surface_failures.count("truncated_example")
    quality["paragraph_merge_count"] = final_surface_failures.count("paragraph_merge_detected")
    quality["blocked_export_count"] = int(enriched.get("export_blocked", False))
    answer_source = enriched.get("answer_source", "legacy_template")
    enriched["answer_source"] = answer_source
    if compiler_only and answer_source != "contract_compiler":
        # Enforce compiler-only: regenerate through compiler and keep non-fallback source.
        enriched["model_answer"] = build_model_answer(enriched, job)
        enriched["answer_source"] = enriched.get("answer_source", "contract_compiler")
        answer_source = enriched["answer_source"]
    enriched["used_fallback_template"] = bool(compiler_only and answer_source != "contract_compiler")
    quality["legacy_leakage"] = int(compiler_only and answer_source != "contract_compiler")
    quality["slot_rejection_count"] = quality.get("slot_rejection_count", 0)
    quality["slot_retry_count"] = quality.get("slot_retry_count", 0)
    quality["quality_gate_status"] = enriched.get("quality_gate_status", "unknown")
    if quality["domain_density"] < 15 and enriched.get("skill_card") and not enriched.get("export_blocked"):
        enriched["model_answer"] = build_model_answer(enriched, job)
        if not compiler_only:
            enriched["model_answer"] = polish_spoken_answer(enriched.get("model_answer", ""), enriched, job)
        quality["domain_density"] = (enriched.get("quality_audit") or {}).get(
            "domain_density",
            domain_density_from_context(
                enriched.get("model_answer", ""),
                contract,
                None,
                card=enriched.get("skill_card"),
            ),
        )
        quality["generic_phrase_count"] = generic_phrase_count(enriched.get("model_answer", ""))
    if enriched.get("export_blocked") or not enriched.get("model_answer"):
        enriched["export_blocked"] = True
        quality["blocked_export_count"] = 1
        enriched.pop("model_answer", None)
        enriched.pop("expert_reference_answer", None)
    study = enriched.get("study_material") or {}
    _boost_specificity(enriched, job)
    enriched["evaluation_criteria"] = study.get("principles") or study.get("key_concepts") or enriched.get("evaluation_criteria", [])
    enriched["common_mistakes"] = study.get("common_mistakes") or enriched.get("common_mistakes", [])
    enriched["practice_tasks"] = study.get("practice_exercises") or [
        f"Review the key facts for this topic and write a 200-word summary from memory.",
    ]
    enriched.setdefault("revision_notes", study.get("revision_notes") or [])
    enriched["question"] = fix_surface_quality_defects(
        normalize_surface_text(enriched.get("question", "")),
        role=job.get("title") or "",
    )
    if is_silly_or_vague_question(enriched.get("question", ""), job, job.get("job_intelligence_profile")):
        enriched["export_blocked"] = True
        quality["blocked_export_count"] = 1
        quality["silly_or_vague_question"] = True
    if enriched.get("model_answer"):
        enriched["model_answer"] = normalize_surface_text(enriched["model_answer"])
        enriched["model_answer"] = fix_surface_quality_defects(
            enriched["model_answer"], role=job.get("title") or ""
        )
        enriched["model_answer"], claim_meta = rewrite_or_flag_unsupported_claims(
            enriched["model_answer"], job
        )
        enriched.setdefault("quality_audit", {}).update(claim_meta)
        enriched["expert_reference_answer"] = enriched["model_answer"]
    role_title = job.get("title") or ""
    scrub_rules = _skill_scrub_rules(enriched.get("skill_tag") or enriched.get("mapped_skill") or "")
    if enriched.get("answer_explanation"):
        enriched["answer_explanation"] = normalize_surface_text(enriched["answer_explanation"])
        enriched["answer_explanation"] = _sanitize_prose_value(
            enriched["answer_explanation"], job, role_title, scrub_rules
        )
    if enriched.get("study_material"):
        enriched["study_material"] = normalize_study_material_dict(enriched["study_material"])
    attach_study_source_metadata(enriched, job)
    synthesize_study_module(enriched, job)
    annotate_question_source_metadata(enriched, job)
    apply_finalized_study_module(enriched, job)
    study = enriched.get("study_material") or {}
    study = _sanitize_study_material_recursive(study, job, role_title, scrub_rules)
    enriched["study_material"] = enforce_study_hard_max_after_export_touchup(study, enriched, job)
    # Final safety net: sanitise ALL remaining user-facing prose on the question
    # (evidence slots, expert reference, common mistakes, follow-ups, etc.) so the
    # audited content matches what a user could ever see. study_material and the
    # question stem are handled above / kept verbatim.
    for key, value in list(enriched.items()):
        if key in _QUESTION_PROSE_SKIP_KEYS:
            continue
        enriched[key] = _sanitize_study_material_recursive(value, job, role_title, scrub_rules)
    return attach_obligation_profile(enriched, job)


def mock_generate_questions(
    job: dict,
    *,
    focus_areas: list[str],
    difficulty: str,
) -> list[dict]:
    """
    Generate an interview pack sized by how much real signal the job
    actually contains — every extracted skill yields its own pair of
    technical questions, every responsibility/requirement informs a
    tailored behavioral prompt, and a system-design question is added only
    when the role's own skills genuinely warrant one. No fixed question
    count is hardcoded anywhere in this function.
    """
    questions: list[dict] = []
    ladder_ctx = apply_source_ladder_to_job(job)
    intelligence_profile = build_job_intelligence_profile(job)
    job["job_intelligence_profile"] = profile_to_dict(intelligence_profile)
    role_intelligence = build_role_intelligence(job)
    role = job.get("title") or "Professional"
    role_family_pack = _role_family_for_pack(role)
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")

    skills = [s["skill"] for s in job.get("extracted_skills", [])]
    if focus_areas:
        # Focus areas the user explicitly asked about get priority placement and are
        # included even if the scraper/parser didn't independently detect them.
        skills = list(dict.fromkeys(focus_areas + skills))
    skill_card_bank = build_skill_card_bank(job, skills)

    for skill in skills:
        # Anchor each skill's questions to a responsibility that does not name a
        # DIFFERENT skill, so e.g. a Python question is not framed "while handling
        # 'SQL dashboard creation'" (Defect Class D framing contamination).
        skill_resp = _skill_aligned_context_responsibility(job, skill) or resp
        questions.extend(build_technical_questions_for_skill(skill, role, skill_resp))

    role_term = get_role_terminology_question(job)
    if role_term:
        questions.append(role_term)

    questions.extend(get_procedure_questions_for_role(job))

    if any(s in ("System Design", "Distributed Systems", "Architecture") for s in skills):
        questions.append(
            {
                "category": "system_design",
                "question": (
                    f"Design a system that fulfills the core responsibilities of this "
                    f"{job.get('title', 'role')} posting at scale. Walk through your approach."
                ),
                "why_asked": "Tests structured design thinking and tradeoff articulation under ambiguity.",
                "ideal_answer_points": [
                    "Clarifies requirements and scale targets before designing",
                    "Presents a high-level architecture before diving into one component",
                    "Explicitly discusses at least one tradeoff (consistency vs. availability, latency vs. cost)",
                ],
                "follow_ups": ["How would this design change at 10x the load?"],
                "skill_tag": "System Design",
            }
        )

    for responsibility in job.get("responsibilities", [])[:6]:
        questions.append(
            {
                "category": "behavioral",
                "question": f"This role involves '{responsibility}'. Tell me about a time you did something similar.",
                "why_asked": "Behavioral question tailored to a specific responsibility actually listed in this posting, using the STAR structure.",
                "ideal_answer_points": ["Situation", "Task", "Action (most detail here)", "Result (quantified)"],
                "follow_ups": ["What would you do differently with more time or resources?"],
                "skill_tag": None,
            }
        )

    for template in _family_behavioral_templates(job):
        questions.append(
            {
                "category": "behavioral",
                "question": template,
                "why_asked": "Standard behavioral probe using the STAR method, included regardless of job specifics.",
                "ideal_answer_points": ["Situation", "Task", "Action (most detail here)", "Result (quantified)"],
                "follow_ups": [],
                "skill_tag": None,
            }
        )

    _real_resp = [r for r in (job.get("responsibilities") or []) if r]
    _real_skills = [s for s in (job.get("extracted_skills") or []) if s]
    if not _real_resp and not _real_skills and not (job.get("description_raw") or "").strip():
        # Title-only input: do not imply a posting was read (Defect Class E).
        excites_q = (
            f"What interests you about this {job.get('title', 'role')} role based on the "
            f"information available so far, and what would you want to clarify about it?"
        )
        excites_points = [
            "Honest interest given limited information",
            "Sensible questions to clarify responsibilities, skills, and success measures",
        ]
    else:
        excites_q = (
            f"What excites you specifically about this {job.get('title', 'role')} position, "
            f"based on what you've read?"
        )
        excites_points = ["References specific responsibilities or requirements from the real posting"]
    questions.append(
        {
            "category": "role_specific",
            "question": excites_q,
            "why_asked": "Tests genuine engagement with the actual posting rather than a rehearsed generic answer.",
            "ideal_answer_points": excites_points,
            "follow_ups": [],
            "skill_tag": None,
        }
    )

    if job.get("company_name"):
        questions.append(
            {
                "category": "company_specific",
                "question": f"What do you know about {job['company_name']}, and why do you want to work there specifically?",
                "why_asked": "Tests genuine research into the company rather than a generic answer that could apply anywhere.",
                "ideal_answer_points": ["Specific, verifiable facts about the company, not guesses"],
                "follow_ups": [],
                "skill_tag": None,
            }
        )
        cr = job.get("company_research") if isinstance(job.get("company_research"), dict) else None
        if cr:
            for product in (cr.get("products_services") or [])[:1]:
                questions.append(
                    {
                        "category": "company_specific",
                        "question": (
                            f"How would your experience help {job['company_name']} deliver "
                            f"{product} effectively?"
                        ),
                        "why_asked": "Tests alignment with researched company products or services.",
                        "ideal_answer_points": [
                            f"References {product}",
                            "Links experience to company offering",
                        ],
                        "follow_ups": [],
                        "skill_tag": None,
                    }
                )
            for industry in (cr.get("industries") or [])[:1]:
                questions.append(
                    {
                        "category": "company_specific",
                        "question": (
                            f"What industry-specific challenges in {industry} would you expect in this role "
                            f"at {job['company_name']}?"
                        ),
                        "why_asked": "Tests domain awareness from researched company industry context.",
                        "ideal_answer_points": [
                            f"Names a realistic {industry} challenge",
                            "Connects challenge to role responsibilities",
                        ],
                        "follow_ups": [],
                        "skill_tag": None,
                    }
                )

    questions.extend(build_source_ladder_questions(job, ladder_ctx))

    if not questions:
        questions.extend(_role_baseline_questions(job))

    questions.extend(build_profile_driven_questions(intelligence_profile))

    questions = apply_coverage_plan(job, questions, difficulty=difficulty)
    questions = repair_synthetic_question_overload(questions, job)

    unique_questions: list[dict] = []
    seen: set[str] = set()
    for q in questions:
        q.setdefault("generation_stage_meta", {})
        if not q.get("question_origin"):
            q = mark_synthetic_question(q, source="mock_generate")
        q["generation_stage_meta"]["stage_1_role_intelligence"] = {
            "role": role_intelligence["role"],
            "domain": role_intelligence["domain"],
            "seniority": role_intelligence["seniority"],
        }
        q["role_family"] = role_family_pack
        q["generation_stage_meta"]["stage_2_skill_map"] = {
            "skill_count": len(skill_card_bank),
        }
        q["generation_stage_meta"]["stage_3_question_generation"] = {
            "question_type": q.get("question_type") or q.get("category"),
            "skill_tag": q.get("skill_tag"),
        }
        card = map_question_to_skill_card(q, skill_card_bank)
        if card and not q.get("skip_skill_card"):
            q["skill_card"] = card
            q["mapped_skill"] = card.get("skill")
            q["employer_expectation"] = card.get("employer_expectation")
        key = _question_dedupe_key(q)
        if key not in seen:
            seen.add(key)
            unique_questions.append(q)

    archetype = detect_coverage_archetype(job)
    exportable: list[dict] = []
    for floor_round in range(5):
        finalized = [
            _finalize_question(q, job, difficulty, i) for i, q in enumerate(unique_questions)
        ]
        exportable = [q for q in finalized if not q.get("export_blocked")]
        if len(exportable) >= MIN_EXPORTABLE_PACK_QUESTIONS:
            break
        if archetype is None:
            break
        extra = build_coverage_floor_questions(
            job,
            archetype=archetype,
            round_index=floor_round,
            existing=unique_questions,
        )
        if not extra:
            break
        for q in extra:
            key = _question_dedupe_key(q)
            if key in seen:
                continue
            seen.add(key)
            unique_questions.append(q)

    exportable = [
        q for q in (_finalize_question(q, job, difficulty, i) for i, q in enumerate(unique_questions))
        if not q.get("export_blocked")
    ]
    if exportable:
        missing_raw = build_missing_coverage_questions(intelligence_profile, exportable)
        added = 0
        for q in missing_raw:
            finalized = _finalize_question(q, job, difficulty, len(exportable) + added)
            if finalized.get("export_blocked"):
                continue
            key = _question_dedupe_key(finalized)
            if key in seen:
                continue
            seen.add(key)
            exportable.append(finalized)
            added += 1
        coverage_audit = audit_pack_coverage(intelligence_profile, exportable)
        coverage_audit.added_question_count = added
    else:
        coverage_audit = audit_pack_coverage(intelligence_profile, exportable)

    audit_payload = audit_to_dict(coverage_audit)
    audit_payload["audit_items"] = build_audit_items_for_profile(intelligence_profile)
    job["coverage_audit"] = audit_payload

    if exportable:
        refresh_source_ladder_usage_from_questions(job, exportable)

    return exportable if exportable else [
        q for q in (_finalize_question(q, job, difficulty, i) for i, q in enumerate(unique_questions))
        if not q.get("export_blocked")
    ]


def finalize_questions_list(questions: list[dict], job: dict, difficulty: str) -> list[dict]:
    """Ensure every question has model answers, study material, and coverage (live + mock paths)."""
    apply_source_ladder_to_job(job)
    intelligence_profile = build_job_intelligence_profile(job)
    job["job_intelligence_profile"] = profile_to_dict(intelligence_profile)
    expanded = apply_coverage_plan(job, list(questions), difficulty=difficulty)
    expanded.extend(build_profile_driven_questions(intelligence_profile))
    unique: list[dict] = []
    seen: set[str] = set()
    for q in expanded:
        key = _question_dedupe_key(q)
        if key in seen:
            continue
        seen.add(key)
        unique.append(q)
    finalized = [_finalize_question(q, job, difficulty, i) for i, q in enumerate(unique)]
    exportable = [q for q in finalized if not q.get("export_blocked")]
    missing_raw = build_missing_coverage_questions(intelligence_profile, exportable)
    added = 0
    for q in missing_raw:
        item = _finalize_question(q, job, difficulty, len(exportable) + added)
        if item.get("export_blocked"):
            continue
        key = _question_dedupe_key(item)
        if key in seen:
            continue
        seen.add(key)
        exportable.append(item)
        added += 1
    audit = audit_pack_coverage(intelligence_profile, exportable)
    audit.added_question_count = added
    audit_payload = audit_to_dict(audit)
    audit_payload["audit_items"] = build_audit_items_for_profile(intelligence_profile)
    job["coverage_audit"] = audit_payload
    refresh_source_ladder_usage_from_questions(job, exportable)
    return exportable


def mock_company_profile(company_name: str | None) -> dict:
    """
    Deliberately returns an EMPTY profile rather than fabricating company
    facts (industry, size, funding) the platform has no real source for in
    mock mode — per the zero-hallucination mandate, "I don't know" beats a
    plausible-sounding guess. Live mode populates this via Google Search
    grounding instead (see app/agents/job_search/agents.py).
    """
    return {} if company_name else {}


def mock_timestamp() -> datetime:
    return datetime.now(timezone.utc)
