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


from app.agents.job_search.knowledge.coverage_planner import apply_coverage_plan
from app.agents.job_search.quality.surface_text_normalize import (
    normalize_study_material_dict,
    normalize_surface_text,
)
from app.agents.job_search.knowledge.study_sources import attach_study_source_metadata
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


def _role_specific_context(job: dict) -> str:
    role = job.get("title") or "this role"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
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
    qtype = enriched.get("question_type") or enriched.get("category", "other")
    qtext = enriched.get("question", "")
    key = _global_fingerprint(qtext, qtype)
    bucket = _GLOBAL_QUESTION_FINGERPRINTS.setdefault(qtype, set())
    if key in bucket:
        context = _role_specific_context(job)
        if "In this role-specific case" not in qtext:
            enriched["question"] = f"{qtext} In this role-specific case, address: {context}."
            qtext = enriched["question"]
            key = _global_fingerprint(qtext, qtype)
            if key in bucket:
                skill = enriched.get("skill_tag") or "core competency"
                enriched["question"] = (
                    f"{qtext} Include one concrete {skill} metric, one governing standard/protocol, "
                    f"and one failure mode relevant to {context}."
                )
                key = _global_fingerprint(enriched["question"], qtype)
    bucket.add(key)


def _boost_specificity(enriched: dict, job: dict) -> None:
    """Ensure answer/study mention role-specific technical anchors."""
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
    skills: list[str] = []
    if q.get("skill_tag"):
        skills.append(q["skill_tag"])
    for s in job.get("extracted_skills", [])[:3]:
        name = s.get("skill") if isinstance(s, dict) else s
        if name and name not in skills:
            skills.append(name)
    cat = q.get("category", "")
    if cat and cat not in skills:
        skills.append(cat.replace("_", " ").title())
    return skills


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
    _enforce_cross_role_uniqueness(enriched, job)
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
    if is_generic_content(enriched.get("model_answer", "")):
        enriched["model_answer"] = build_model_answer(enriched, job)
    if not compiler_only:
        enriched["model_answer"] = polish_spoken_answer(enriched.get("model_answer", ""), enriched, job)
    # Force at least one role anchor in technical answers.
    role_anchor = (job.get("title") or "").lower()
    if role_anchor and enriched.get("category") in ("technical", "role_specific"):
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
    enriched["question"] = normalize_surface_text(enriched.get("question", ""))
    if enriched.get("model_answer"):
        enriched["model_answer"] = normalize_surface_text(enriched["model_answer"])
        enriched["expert_reference_answer"] = enriched["model_answer"]
    if enriched.get("answer_explanation"):
        enriched["answer_explanation"] = normalize_surface_text(enriched["answer_explanation"])
    if enriched.get("study_material"):
        enriched["study_material"] = normalize_study_material_dict(enriched["study_material"])
    attach_study_source_metadata(enriched, job)
    return enriched


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
        questions.extend(build_technical_questions_for_skill(skill, role, resp))

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

    questions.append(
        {
            "category": "role_specific",
            "question": f"What excites you specifically about this {job.get('title', 'role')} position, based on what you've read?",
            "why_asked": "Tests genuine engagement with the actual posting rather than a rehearsed generic answer.",
            "ideal_answer_points": ["References specific responsibilities or requirements from the real posting"],
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

    if not questions:
        questions.extend(_role_baseline_questions(job))

    questions = apply_coverage_plan(job, questions, difficulty=difficulty)

    unique_questions: list[dict] = []
    seen: set[str] = set()
    for q in questions:
        q.setdefault("generation_stage_meta", {})
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
        if card:
            q["skill_card"] = card
            q["mapped_skill"] = card.get("skill")
            q["employer_expectation"] = card.get("employer_expectation")
        key = _question_dedupe_key(q)
        if key not in seen:
            seen.add(key)
            unique_questions.append(q)

    return [_finalize_question(q, job, difficulty, i) for i, q in enumerate(unique_questions) if not q.get("export_blocked")]


def finalize_questions_list(questions: list[dict], job: dict, difficulty: str) -> list[dict]:
    """Ensure every question has model answers, study material, and coverage (live + mock paths)."""
    expanded = apply_coverage_plan(job, list(questions), difficulty=difficulty)
    unique: list[dict] = []
    seen: set[str] = set()
    for q in expanded:
        key = _question_dedupe_key(q)
        if key in seen:
            continue
        seen.add(key)
        unique.append(q)
    finalized = [_finalize_question(q, job, difficulty, i) for i, q in enumerate(unique)]
    return [q for q in finalized if not q.get("export_blocked")]


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
