"""
Core technical interview content: terminology, calculations, operating principles,
and clinical/field procedures — generated per skill and role.
"""

from __future__ import annotations

from app.agents.job_search.knowledge.domains import classify_skill_domain, get_domain_foundation
from app.agents.job_search.knowledge.expert_content_library import resolve_expert_content
from app.agents.job_search.knowledge.normalize import normalize_key, title_case_skill
from app.agents.job_search.quality.key_term_quality_audit import is_valid_key_term

_ROLE_FAMILY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "healthcare": ("nurse", "pharmacist", "doctor", "gp", "physio", "radiograph", "clinical", "therapist"),
    "engineering": ("engineer", "electrician", "mechanical", "civil engineer", "chemical", "structural", "maintenance"),
    "technology": ("software", "developer", "data scientist", "devops", "cyber", "cloud", "architect", "qa"),
    "education": ("teacher", "lecturer", "tutor", "teaching assistant"),
    "legal_finance": ("accountant", "finance", "investment", "solicitor", "paralegal", "compliance"),
    "public_admin": ("civil service", "policy", "administrator", "public service"),
}


def _pick_variant(options: list[str], role: str, skill: str, label: str) -> str:
    key = f"{normalize_key(role)}::{normalize_key(skill)}::{label}"
    idx = abs(hash(key)) % len(options)
    return options[idx]


# Curated calculation banks keyed by normalized skill or domain profile
_CALC_BY_SKILL: dict[str, dict] = {
    "electrical_installation": {
        "prompt": "A final circuit is protected by a 32 A Type B MCB. Cable is 2.5 mm² T&E, 30 m run. Given R1+R2 ≈ 0.75 Ω and Ze = 0.35 Ω, calculate Zs and state if it meets BS 7671 max Zs for a B32 (≈1.44 Ω).",
        "answer": "Zs = Ze + (R1+R2) = 0.35 + 0.75 = 1.10 Ω. Since 1.10 Ω < 1.44 Ω tabulated maximum for B32, the circuit meets disconnection requirements (verify at furthest point on site).",
        "steps": ["Zs = Ze + (R1+R2)", "Compare Zs to tabulated max for device", "Record on schedule of test results"],
    },
    "structural_analysis": {
        "prompt": "A simply supported beam span 6 m carries a uniformly distributed load of 12 kN/m. Calculate maximum bending moment.",
        "answer": "M_max = wL²/8 = 12 × 6² / 8 = 54 kNm.",
        "steps": ["Identify support conditions", "Apply UDL formula M = wL²/8", "State units and sign convention"],
    },
    "thermodynamics": {
        "prompt": "An ideal gas at 300 K and 1 bar is compressed isothermally to 4 bar. By what factor does volume change?",
        "answer": "P1V1 = P2V2 → V2/V1 = P1/P2 = 1/4. Volume reduces to 25% of initial.",
        "steps": ["Apply isothermal relation PV = constant", "Rearrange for volume ratio", "Interpret physically"],
    },
    "python": {
        "prompt": "What is the time complexity of searching an unsorted list of n items vs a sorted list with binary search?",
        "answer": "Unsorted linear search: O(n). Binary search on sorted data: O(log n). For n=1,000,000, that's up to 1M comparisons vs ~20.",
        "steps": ["Define n", "State complexity classes", "Compare practical impact at scale"],
    },
    "sql": {
        "prompt": "A table has 10 million rows. An index on user_id reduces lookup from full scan to index seek. Why does SELECT * still perform poorly?",
        "answer": "Index helps find rows quickly but SELECT * fetches all columns — key lookup + heap/clustered fetch (bookmark lookup) adds I/O. Covering index on needed columns avoids extra lookups.",
        "steps": ["Explain index seek vs scan", "Describe bookmark/covering index", "Recommend SELECT only required columns"],
    },
    "excel": {
        "prompt": "A sales sheet has 12,000 rows. A VLOOKUP against a 5,000-row product table returns #N/A for 400 rows. What does that indicate and how do you verify it?",
        "answer": "#N/A means those lookup keys are absent from the product table (or have trailing spaces / type mismatches). Verify with TRIM/CLEAN, confirm exact-match (FALSE) not approximate, and reconcile the 400 unmatched keys against the source before trusting any aggregation built on the join.",
        "steps": ["Isolate the #N/A keys", "Check for whitespace/type mismatches and exact-match flag", "Reconcile unmatched keys before aggregating"],
    },
    "dashboarding": {
        "prompt": "A dashboard shows total revenue of £1.2m but the underlying pivot sums to £1.35m. Where do you look first?",
        "answer": "A mismatch usually means the dashboard measure is filtered or de-duplicated differently from the pivot — check slicer/filter context, excluded categories, and whether one view removes duplicate transaction IDs. Reconcile both against a control total from the raw source before publishing.",
        "steps": ["Compare filter/slicer context between views", "Check de-duplication and excluded categories", "Reconcile to a raw-source control total"],
    },
    "data_visualization": {
        "prompt": "A dashboard shows total revenue of £1.2m but the underlying pivot sums to £1.35m. Where do you look first?",
        "answer": "A mismatch usually means the dashboard measure is filtered or de-duplicated differently from the pivot — check slicer/filter context, excluded categories, and whether one view removes duplicate transaction IDs. Reconcile both against a control total from the raw source before publishing.",
        "steps": ["Compare filter/slicer context between views", "Check de-duplication and excluded categories", "Reconcile to a raw-source control total"],
    },
    "financial_modelling": {
        "prompt": "FCF year 1 = £120k, growth 5%, discount rate 10%, terminal growth 2%. Outline DCF logic for enterprise value.",
        "answer": "Discount explicit forecast cash flows, then terminal value TV = FCF_n × (1+g) / (WACC − g_terminal), discount TV to present. Sum PV flows + PV terminal = EV. Sensitivity on WACC and g is mandatory.",
        "steps": ["Project FCF", "Discount each year", "Calculate terminal value", "Sum present values"],
    },
    "pharmacology": {
        "prompt": "Patient weighs 70 kg. Dose is 5 mg/kg. Stock is 10 mg/mL. Calculate volume to draw up.",
        "answer": "Total dose = 5 × 70 = 350 mg. Volume = 350 / 10 = 35 mL. Verify renal function, max single dose, and route per protocol before administration.",
        "steps": ["Dose × weight", "Divide by concentration", "Clinical verification checks"],
    },
    "medication_administration": {
        "prompt": "Prescribed 500 mg amoxicillin QDS. Available 250 mg capsules. How many capsules per dose?",
        "answer": "500 / 250 = 2 capsules per dose, four times daily. Apply five rights, check allergies, and document batch/expiry.",
        "steps": ["Dose required / strength per unit", "Confirm frequency", "Rights of administration"],
    },
    "hazmat_safety": {
        "prompt": "A drum contains 80% ethanol by volume in a poorly ventilated room (100 m³). Why is LEL monitoring critical before hot work?",
        "answer": "Ethanol vapor can reach LEL (~3.3% vol) with sufficient evaporation. Hot work provides ignition source. LEL meter ensures atmosphere < safe threshold (typically <10% LEL) before work.",
        "steps": ["Identify flammable component", "State LEL concept", "Link ventilation + monitoring to permit-to-work"],
    },
    "process_design": {
        "prompt": "A reactor feed is 1000 kg/h with 40 wt% reactant. If conversion is 85%, calculate product flow assuming byproducts negligible.",
        "answer": "Reactant in = 400 kg/h. Converted = 340 kg/h product (same mass basis if 1:1 stoichiometry). Unconverted reactant 60 kg/h remains in outlet — always state assumptions.",
        "steps": ["Mass flow of reactant", "Apply conversion", "Mass balance outlet streams"],
    },
    "statistics": {
        "prompt": "Mean exam score 68, SD 12, n=200. Approximately what percentage scored above 80 assuming normal distribution?",
        "answer": "z = (80−68)/12 = 1.0. P(Z>1) ≈ 15.9%. Roughly 32 students above 80.",
        "steps": ["Compute z-score", "Use normal table", "Interpret in context"],
    },
    "machine_learning": {
        "prompt": "Training accuracy 99%, validation accuracy 72%. Diagnose likely issue and one remedy.",
        "answer": "Severe overfitting. Remedies: more data, regularisation (L2/dropout), simpler model, cross-validation, early stopping.",
        "steps": ["Compare train vs val gap", "Name phenomenon", "Propose evidence-based fixes"],
    },
}

_CALC_BY_DOMAIN: dict[str, dict] = {
    "engineering": {
        "prompt": "A component must carry 50 kN load with factor of safety 2.5. What is the required design strength?",
        "answer": "Required ultimate capacity = 50 × 2.5 = 125 kN. Design must ensure failure load ≥ 125 kN with documented material properties.",
        "steps": ["Load × FoS", "Compare to material capacity", "Document assumption"],
    },
    "healthcare": {
        "prompt": "Patient heart rate 110, BP 100/60, RR 24, SpO2 91% on room air. Why might NEWS2 trigger escalation?",
        "answer": "Tachycardia, tachypnoea, hypoxia each add points in NEWS2. Combined score likely ≥5 → urgent medical review per local escalation protocol.",
        "steps": ["Score each parameter", "Sum NEWS2", "Apply escalation pathway"],
    },
    "technology": {
        "prompt": "Service must handle 2,000 requests/s with 50 ms p99 latency. If each request needs 2 DB queries at 5 ms each, is a single DB likely sufficient?",
        "answer": "2,000 × 2 = 4,000 QPS to DB. At 5 ms/query, one connection handles ~200 QPS. Need pool of ~20+ connections plus caching to avoid saturation — architecture must scale reads.",
        "steps": ["Estimate QPS", "Per-connection throughput", "Identify bottleneck"],
    },
    "legal_finance": {
        "prompt": "Company EBITDA £2m, multiple 8×, net debt £3m. Estimate equity value.",
        "answer": "EV = 2 × 8 = £16m. Equity = EV − net debt = £13m (before adjustments for cash, pensions, working capital).",
        "steps": ["EV = EBITDA × multiple", "Subtract net debt", "Note adjustment items"],
    },
    "education": {
        "prompt": "Class 30 pupils, 18 met learning objective. What is attainment percentage and one intervention if below 70% target?",
        "answer": "18/30 = 60%. Below 70% target — run re-teach with hinge questions, small-group support, and reassessment next lesson.",
        "steps": ["Calculate percentage", "Compare to target", "Plan intervention"],
    },
    "hospitality_operations": {
        "prompt": "Food cost £4.50, selling price £14. What is gross food margin %?",
        "answer": "Margin = (14 − 4.50) / 14 × 100 = 67.9%. Monitor against target; if labour is high, contribution still may be insufficient.",
        "steps": ["(Price − cost) / price", "Express as %", "Link to total GP"],
    },
}

# Role-level procedure questions (healthcare / clinical)
_ROLE_PROCEDURES: dict[str, list[dict]] = {
    "registered_nurse": [
        {
            "skill": "Patient assessment",
            "question": "Walk through a structured ABCDE primary assessment on a deteriorating ward patient.",
            "steps": [
                "Airway: patency, voice, obstruction signs",
                "Breathing: rate, SpO2, chest expansion, auscultation",
                "Circulation: pulse, BP, cap refill, bleeding",
                "Disability: AVPU/GCS, glucose, pupils",
                "Exposure: temperature, rash, wounds — maintain dignity",
            ],
        },
        {
            "skill": "Medication administration",
            "question": "Describe the full safe medication administration procedure from prescription to documentation.",
            "steps": [
                "Five rights: patient, drug, dose, route, time",
                "Check allergies, interactions, renal/hepatic considerations",
                "Prepare, verify with second nurse if high-risk",
                "Administer, observe, document immediately in record",
            ],
        },
    ],
    "general_practitioner": [
        {
            "skill": "Clinical diagnosis",
            "question": "Outline your systematic approach to a patient presenting with undifferentiated chest pain.",
            "steps": [
                "Red flags: ACS, PE, dissection, pneumothorax",
                "History: OPQRST, risk factors, drugs",
                "Exam + ECG + troponin pathway per guidelines",
                "Working diagnosis, safety-net advice, follow-up",
            ],
        },
    ],
    "clinical_pharmacist": [
        {
            "skill": "Pharmacology",
            "question": "How do you conduct a structured medicines reconciliation on hospital admission?",
            "steps": [
                "Best possible medication history from patient + records",
                "Compare to admission prescription",
                "Resolve discrepancies with prescriber",
                "Document changes and counsel patient",
            ],
        },
    ],
    "radiographer": [
        {
            "skill": "Medical imaging",
            "question": "Describe the standard procedure before exposing a patient to ionising radiation.",
            "steps": [
                "Confirm identity, consent, and correct study request",
                "Pregnancy/last menstrual period check where relevant",
                "ALARP: collimation, technique factors, shielding",
                "Verify image quality and repeat only if clinically required",
            ],
        },
    ],
    "physiotherapist": [
        {
            "skill": "Manual therapy",
            "question": "Describe subjective and objective assessment structure for a new musculoskeletal patient.",
            "steps": [
                "Subjective: history, aggravating/easing, red flags",
                "Objective: ROM, strength, special tests, functional tasks",
                "Clinical impression and SMART goals",
                "Treatment plan and outcome measures",
            ],
        },
    ],
    "electrician": [
        {
            "skill": "Electrical installation",
            "question": "Describe the safe isolation procedure before working on a live electrical circuit.",
            "steps": [
                "Identify point of isolation",
                "Switch off, lock off, tag",
                "Prove dead on ALL conductors with GS38 tester",
                "Prove tester on proving unit before and after",
            ],
        },
    ],
}


def _terminology_from_expert(skill: str, role: str, exp: dict) -> list[dict[str, str]]:
    """Build glossary entries for a skill."""
    skill_t = title_case_skill(skill)
    terms: list[dict[str, str]] = [{"term": skill_t, "definition": exp.get("definition", "")}]

    for std in (exp.get("standards") or [])[:3]:
        terms.append({"term": std.split("(")[0].strip(), "definition": f"Standard/framework governing {skill_t}: {std}."})

    for fact in (exp.get("key_facts") or [])[:4]:
        # Only "Named concept: gloss" facts yield a glossary term. Prose facts
        # without a leading named concept are NOT clipped into a term — that is
        # exactly what produced malformed entries like "Clear scope and
        # verification steps keep" (Defect Class B). The prose fact still lives
        # on in principles/study material; it just never masquerades as a term.
        if ":" not in fact:
            continue
        candidate = fact.split(":", 1)[0].strip()
        if is_valid_key_term(candidate):
            terms.append({"term": candidate, "definition": fact.split(":", 1)[1].strip()})

    for topic in (exp.get("related_topics") or [])[:3]:
        if topic != skill_t:
            terms.append({"term": topic, "definition": f"Related concept used with {skill_t} in professional practice."})

    # Deduplicate by term and enforce the terminology type boundary: a term must
    # be a noun-like domain concept / named tool / standard — never a clipped
    # prose principle or sentence fragment.
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for t in terms:
        key = t["term"].lower()
        if key in seen or not t.get("definition"):
            continue
        if not is_valid_key_term(t["term"]):
            continue
        seen.add(key)
        unique.append(t)
    return unique[:8]


def get_terminology_pack(skill: str, role: str, responsibility: str | None = None) -> dict:
    exp = resolve_expert_content(skill, role, responsibility)
    terms = _terminology_from_expert(skill, role, exp)
    skill_t = title_case_skill(skill)
    return {
        "skill": skill_t,
        "terms": terms,
        "study_overview": (
            f"Core terminology for {skill_t} — definitions you must know cold for {role} work."
        ),
    }


def get_calculation_pack(skill: str, role: str, responsibility: str | None = None) -> dict | None:
    sk = normalize_key(skill)
    domain = classify_skill_domain(skill, role)
    calc = _CALC_BY_SKILL.get(sk) or _CALC_BY_DOMAIN.get(domain)
    if not calc:
        return None
    return {
        "skill": title_case_skill(skill),
        "prompt": calc["prompt"],
        "answer": calc["answer"],
        "steps": calc["steps"],
    }


def get_principles_pack(skill: str, role: str, responsibility: str | None = None) -> dict:
    exp = resolve_expert_content(skill, role, responsibility)
    domain = classify_skill_domain(skill, role)
    foundation = get_domain_foundation(domain)
    principles = exp.get("key_facts") or foundation["core_principles"]
    how = exp.get("how_it_works") or foundation["methodology"]
    return {
        "skill": title_case_skill(skill),
        "principles": principles[:6],
        "operating_steps": how[:5],
        "definition": exp.get("definition", ""),
    }


def get_role_terminology_question(job: dict) -> dict | None:
    """One consolidated terminology question covering all role skills."""
    role = job.get("title") or "Professional"
    skills = [s.get("skill") if isinstance(s, dict) else s for s in job.get("extracted_skills", [])]
    if not skills:
        return None
    terms: list[dict[str, str]] = []
    seen_terms: set[str] = set()
    for s in skills[:4]:
        pack = get_terminology_pack(s, role, (job.get("responsibilities") or [None])[0])
        for t in pack["terms"][:3]:
            key = (t.get("term") or "").strip().lower()
            # Structural type boundary + cross-skill dedupe so a malformed or
            # repeated fragment cannot survive aggregation into the consolidated
            # terminology question (Defect Class B).
            if not key or key in seen_terms or not is_valid_key_term(t.get("term") or ""):
                continue
            seen_terms.add(key)
            terms.append(t)
    if not terms:
        return None
    term_list = ", ".join(t["term"] for t in terms[:6])
    return {
        "category": "technical",
        "question_type": "terminology",
        "question": f"As a {role}, define and explain these core professional terms: {term_list}.",
        "why_asked": "Tests foundational vocabulary — interviewers expect precise definitions, not vague familiarity.",
        "skill_tag": "Core terminology",
        "terminology_terms": terms[:6],
    }


def get_procedure_questions_for_role(job: dict) -> list[dict]:
    role_k = normalize_key(job.get("title") or "")
    procs = _ROLE_PROCEDURES.get(role_k, [])
    out: list[dict] = []
    for p in procs:
        out.append({
            "category": "technical",
            "question_type": "procedure",
            "question": p["question"],
            "why_asked": f"Tests ability to execute standard {p['skill']} procedure safely and in correct order.",
            "skill_tag": p["skill"],
            "procedure_steps": p["steps"],
        })
    # Healthcare fallback if role not in map but domain is healthcare
    if not out and classify_skill_domain(job.get("title") or "", job.get("title")) == "healthcare":
        out.append({
            "category": "technical",
            "question_type": "procedure",
            "question": "Describe a standard clinical escalation procedure when a patient's observations deteriorate.",
            "why_asked": "Tests knowledge of structured response pathways (SBAR/NEWS2) used in clinical settings.",
            "skill_tag": "Patient assessment",
            "procedure_steps": [
                "Re-assess ABCDE/NEWS2",
                "Communicate using SBAR to responsible clinician",
                "Initiate prescribed escalation protocol",
                "Document time, actions, and response",
            ],
        })
    return out


def build_technical_questions_for_skill(skill: str, role: str, responsibility: str | None) -> list[dict]:
    """Full technical set per skill: explain, scenario, terminology, calculation, principles."""
    skill_t = title_case_skill(skill)
    domain = classify_skill_domain(skill, role)
    role_l = (role or "").lower()
    role_family = "general"
    for family, keys in _ROLE_FAMILY_KEYWORDS.items():
        if any(k in role_l for k in keys):
            role_family = family
            break
    if role_family == "public_admin" and domain in ("technology", "general_professional"):
        domain = "general_professional"
    resp_clause = f" while handling '{responsibility}'" if responsibility else ""
    exp = resolve_expert_content(skill, role, responsibility)
    standards = exp.get("standards") or []
    anchor_std = standards[0] if standards else "the applicable standard"
    term_pack = get_terminology_pack(skill, role, responsibility)
    term_names = [t["term"] for t in term_pack.get("terms", [])[:4]]
    term_hint = ", ".join(term_names[:3]) if term_names else title_case_skill(skill)
    explain_q = _pick_variant([
        f"Walk me through how you would explain {skill} to a teammate who has never used it in a {role} context{resp_clause}.",
        f"How would you teach {skill} to a new colleague in a {role} team{resp_clause}, including where beginners fail first?",
        f"If a new hire joined your {role} function{resp_clause}, how would you break down {skill} into practical steps with reference to {anchor_std}?",
    ], role, skill, "explain")
    scenario_q = _pick_variant([
        f"Describe the most complex problem you've solved using {skill} as a {role}{resp_clause}.",
        f"In your {role} experience{resp_clause}, what high-stakes incident required deep use of {skill}, and how did you resolve it?",
        f"Give a detailed example where {skill} was critical to recovering a difficult {role} outcome{resp_clause}.",
    ], role, skill, "scenario")
    principles_q = _pick_variant([
        f"What are the core operating principles and standard workflow for applying {skill} in a {role} role{resp_clause}?",
        f"Which non-negotiable rules and execution sequence govern {skill} for {role} work{resp_clause}?",
        f"When performing {skill} as a {role}{resp_clause}, what are the governing principles, checkpoints, and sign-off criteria under {anchor_std}?",
    ], role, skill, "principles")
    calc_fallback_q = _pick_variant([
        f"Give a quantitative example related to {skill}: what would you measure, calculate, or estimate on a typical {role} task{resp_clause}?",
        f"For {skill} in {role} delivery{resp_clause}, which numeric thresholds or KPIs determine whether work is acceptable?",
        f"What calculation or numeric validation do you rely on most when applying {skill} as a {role}{resp_clause}?",
    ], role, skill, "calc")

    if domain == "healthcare":
        role_l = (role or "").lower()
        if "pharmac" in role_l:
            clinical_anchor = "BNF, NICE, and local formulary governance"
        else:
            clinical_anchor = "clinical guidelines and medicines safety policy"
        explain_q = (
            f"As a {role}, explain {skill} to a newly qualified clinician and include clinical safety checks "
            f"tied to {clinical_anchor}."
        )
        scenario_q = f"Describe a high-risk clinical case where {skill} changed patient management."
        principles_q = f"Which clinical operating principles and protocol sequence govern {skill} in {role} practice?"
        calc_fallback_q = f"For {skill}, which clinical observations or dose metrics do you calculate before acting?"
    elif domain == "engineering":
        explain_q = f"Explain {skill} to an apprentice and include how you verify compliance to standards (e.g. {anchor_std})."
        scenario_q = f"Describe a technically difficult {skill} fault/design problem you resolved under constraints."
        principles_q = f"What are the engineering principles and site workflow used to execute {skill} safely?"
        calc_fallback_q = f"For {skill}, which design/test values do you calculate and what limits do you check?"
    elif domain == "technology":
        explain_q = f"Explain {skill} to a junior engineer and include trade-offs in production systems and one measurable quality signal."
        scenario_q = f"Describe the most complex production issue you solved using {skill}, including impact metrics."
        principles_q = f"What are the core operating principles and delivery workflow for {skill} in {role} execution?"
        calc_fallback_q = f"For {skill}, what performance or capacity calculations do you use before implementation?"
    elif domain == "education":
        explain_q = f"Explain {skill} to a new teacher and include how you evidence learner progress with concrete metrics."
        scenario_q = f"Describe a difficult classroom/learning challenge where {skill} improved outcomes."
        principles_q = f"What instructional principles and lesson workflow guide {skill} in {role} practice?"
        calc_fallback_q = f"For {skill}, what attainment/progress data do you calculate to decide interventions?"
    elif domain == "legal_finance":
        explain_q = f"Explain {skill} to a new colleague and include compliance/evidence expectations tied to {anchor_std}."
        scenario_q = f"Describe a complex case/analysis where {skill} changed risk or financial outcome."
        principles_q = f"What are the governing principles and review workflow for {skill} in a {role} role?"
        calc_fallback_q = f"For {skill}, which financial/risk metrics do you compute before recommendations?"
    elif role_family == "public_admin":
        explain_q = f"Explain {skill} to a new civil-service colleague and include governance controls and audit checkpoints."
        scenario_q = f"Describe a complex public-service delivery challenge where {skill} improved outcomes."
        principles_q = f"What policy/governance principles and workflow govern {skill} in {role} delivery?"
        calc_fallback_q = f"For {skill}, what service KPIs or compliance metrics would you calculate and monitor?"

    questions: list[dict] = [
        {
            "category": "technical",
            "question_type": "explain",
            "question": explain_q,
            "why_asked": f"Tests genuine conceptual understanding of {skill}, not just résumé familiarity.",
            "skill_tag": skill,
        },
        {
            "category": "technical",
            "question_type": "scenario",
            "question": scenario_q,
            "why_asked": f"Probes depth of hands-on experience with {skill} under real constraints.",
            "skill_tag": skill,
        },
        {
            "category": "technical",
            "question_type": "terminology",
            "question": _pick_variant([
                f"What are the essential technical terms every {role} must know when working with {skill}{resp_clause}? Define each precisely.",
                f"List the critical terminology for {skill} in {role} practice{resp_clause} (for example: {term_hint}), and define each term with precision.",
                f"Which professional vocabulary separates a competent vs weak {role} practitioner in {skill}{resp_clause}? Define each term.",
            ], role, skill, "terminology"),
            "why_asked": f"Core terminology separates practitioners who understand {skill} from those who only name-drop it.",
            "skill_tag": skill,
        },
        {
            "category": "technical",
            "question_type": "principles",
            "question": principles_q,
            "why_asked": f"Tests whether you know how {skill} is actually executed to standard, not only what it is called.",
            "skill_tag": skill,
        },
    ]

    calc = get_calculation_pack(skill, role, responsibility)
    questions[2]["terminology_terms"] = term_pack["terms"]
    if calc:
        questions.append({
            "category": "technical",
            "question_type": "calculation",
            "question": _pick_variant([
                f"Calculation / quantitative question for {role} ({skill}){resp_clause}: {calc['prompt']}",
                f"Quantitative validation scenario ({role}, {skill}){resp_clause}: {calc['prompt']}",
                f"Numbers-driven check for {role} work using {skill}{resp_clause}: {calc['prompt']}",
            ], role, skill, "calc_bank"),
            "why_asked": f"Tests numerical and analytical competence in {skill} — essential for {role} roles.",
            "skill_tag": skill,
            "calculation": calc,
        })
    else:
        questions.append({
            "category": "technical",
            "question_type": "calculation",
            "question": calc_fallback_q,
            "why_asked": f"Tests ability to work with numbers, metrics, or measurable outcomes in {skill}.",
            "skill_tag": skill,
        })

    return questions
