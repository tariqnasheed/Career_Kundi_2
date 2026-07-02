"""Domain classification and shared academic foundations per professional field."""

from __future__ import annotations

from app.agents.job_search.knowledge.normalize import normalize_key

# Each domain carries foundational theory reused when composing skill-specific modules.
DOMAIN_FOUNDATIONS: dict[str, dict] = {
    "engineering": {
        "field_intro": (
            "Engineering applies scientific and mathematical principles to design, build, and maintain "
            "systems that meet safety, performance, and regulatory constraints. Professional engineers "
            "translate ambiguous requirements into verifiable specifications, document assumptions, "
            "and validate outcomes through calculation, simulation, and inspection."
        ),
        "core_principles": [
            "First principles: identify loads, constraints, materials, and failure modes before selecting tools.",
            "Standards compliance: national and international codes (ISO, BS, IEC, ASME) govern acceptable practice.",
            "Design for safety: apply factors of safety and redundancy where human life or critical infrastructure is at stake.",
            "Traceability: every design decision should be auditable through calculations, drawings, and change records.",
            "Iterative validation: prototype, test, measure, and refine — never assume a design works without evidence.",
        ],
        "methodology": [
            "Define the problem scope, stakeholders, and acceptance criteria.",
            "Gather inputs: site conditions, regulations, budget, and operational requirements.",
            "Develop conceptual options and evaluate tradeoffs (cost, risk, maintainability).",
            "Produce detailed design with drawings, BOMs, and calculation packages.",
            "Review via peer check, QA, and regulatory submission where required.",
            "Support construction/manufacturing with clarifications and as-built records.",
        ],
    },
    "technology": {
        "field_intro": (
            "Software and data engineering rest on formal models of computation, information, and distributed "
            "systems. Practitioners combine computer science theory (algorithms, complexity, concurrency) with "
            "engineering discipline (testing, observability, security) to build reliable software at scale."
        ),
        "core_principles": [
            "Separation of concerns: modular boundaries reduce coupling and simplify change.",
            "Correctness before optimization: prove the solution works, then profile and improve bottlenecks.",
            "Fail-safe defaults: systems should degrade gracefully; errors must be observable and actionable.",
            "Security by design: least privilege, input validation, and threat modeling from day one.",
            "Continuous verification: automated tests, code review, and monitoring close the feedback loop.",
        ],
        "methodology": [
            "Clarify functional and non-functional requirements (latency, availability, compliance).",
            "Model data flows, APIs, and state; choose appropriate storage and communication patterns.",
            "Implement incrementally with tests at unit, integration, and end-to-end levels.",
            "Deploy with CI/CD, feature flags, and rollback strategy.",
            "Operate with metrics, logs, traces, and incident post-mortems.",
        ],
    },
    "healthcare": {
        "field_intro": (
            "Healthcare practice integrates biomedical science, clinical guidelines, and professional ethics. "
            "Every intervention must balance evidence-based efficacy, patient autonomy, confidentiality, "
            "and regulatory frameworks (GMC, NMC, HCPC, CQC) that protect vulnerable populations."
        ),
        "core_principles": [
            "Patient-centred care: respect dignity, consent, and individual preferences.",
            "Evidence-based practice: integrate best research, clinical expertise, and patient values.",
            "Do no harm: risk assessment, infection control, and medication safety are non-negotiable.",
            "Multidisciplinary collaboration: handoffs require structured communication (SBAR, ISBAR).",
            "Documentation integrity: records must be contemporaneous, accurate, and legally defensible.",
        ],
        "methodology": [
            "Assess — history, examination, and baseline observations.",
            "Diagnose/plan — differential diagnosis, investigations, and shared decision-making.",
            "Implement — treatment, monitoring, and escalation pathways.",
            "Evaluate — outcome measures, adverse events, and care plan review.",
            "Discharge/transfer — safe continuity with clear instructions and follow-up.",
        ],
    },
    "legal_finance": {
        "field_intro": (
            "Legal and financial professions operate under statutory frameworks, professional body rules, "
            "and fiduciary duties. Accuracy, confidentiality, and analytical rigour are essential because "
            "errors can cause material harm to clients, markets, or the rule of law."
        ),
        "core_principles": [
            "Duty of care and confidentiality to clients and stakeholders.",
            "Materiality: focus analysis on items that could change decisions or compliance outcomes.",
            "Substance over form: understand economic reality, not only legal labels.",
            "Professional scepticism: challenge assumptions and verify source documents.",
            "Regulatory awareness: legislation and standards evolve — continuous learning is mandatory.",
        ],
        "methodology": [
            "Intake and scope — identify parties, jurisdiction, and engagement limits.",
            "Research and discovery — statutes, case law, contracts, or financial records.",
            "Analysis — apply frameworks (IRAC for law; DCF, ratios for finance).",
            "Advice/delivery — clear recommendations with risk disclosure.",
            "Review and file — quality control, audit trail, and retention policies.",
        ],
    },
    "education": {
        "field_intro": (
            "Education science draws on pedagogy, developmental psychology, and curriculum theory. "
            "Effective teaching aligns learning objectives, instructional methods, and assessment "
            "to move learners from novice to competent performance through deliberate practice and feedback."
        ),
        "core_principles": [
            "Constructivism: learners build understanding by connecting new ideas to prior knowledge.",
            "Differentiation: adapt pace, scaffolding, and resources to diverse needs.",
            "Formative assessment: frequent checks for understanding guide instruction in real time.",
            "Bloom's taxonomy: move from recall through application to analysis and creation.",
            "Safeguarding: child and vulnerable-adult protection overrides all other priorities.",
        ],
        "methodology": [
            "Establish clear learning intentions and success criteria.",
            "Activate prior knowledge and surface misconceptions.",
            "Model, guide practice, and gradually release responsibility.",
            "Assess formatively and provide actionable feedback.",
            "Review and adapt the next lesson based on evidence of learning.",
        ],
    },
    "creative_media": {
        "field_intro": (
            "Creative and media production combines aesthetic judgment with technical craft. "
            "Professionals balance audience intent, brand constraints, narrative structure, and "
            "toolchain mastery (Adobe suite, cameras, NLEs) to deliver communicative artifacts."
        ),
        "core_principles": [
            "Purpose-driven design: every visual or editorial choice should serve the message.",
            "Hierarchy and contrast: guide attention through scale, colour, and composition.",
            "Consistency: grids, style guides, and brand systems maintain coherence.",
            "Iterative critique: peer review and user testing refine weak executions.",
            "Technical standards: colour spaces, codecs, resolution, and accessibility matter in delivery.",
        ],
        "methodology": [
            "Brief analysis — audience, constraints, deliverables, and success metrics.",
            "Concept development — mood boards, storyboards, or wireframes.",
            "Production — capture, design, or edit with version control.",
            "Review cycles — stakeholder feedback with documented revisions.",
            "Export and archive — correct formats, metadata, and asset libraries.",
        ],
    },
    "hospitality_operations": {
        "field_intro": (
            "Hospitality and operations management optimises guest experience, throughput, and margin "
            "under real-time pressure. Success depends on standard operating procedures, inventory "
            "control, staff coordination, and service recovery when things go wrong."
        ),
        "core_principles": [
            "Guest-first mindset: anticipate needs and recover gracefully from errors.",
            "Consistency through SOPs: recipes, scripts, and checklists reduce variance.",
            "Hygiene and safety: HACCP, allergen control, and licensing are legal requirements.",
            "Revenue and cost control: yield management, wastage tracking, and labour scheduling.",
            "Team communication: briefings, handovers, and escalation paths during service peaks.",
        ],
        "methodology": [
            "Pre-service preparation — mise en place, briefing, and equipment checks.",
            "Service delivery — pace, quality checks, and upselling where appropriate.",
            "Issue resolution — acknowledge, fix, compensate, and log for review.",
            "Close-down — reconciliation, cleaning, and stock counts.",
            "Continuous improvement — review complaints, KPIs, and training gaps.",
        ],
    },
    "social_care": {
        "field_intro": (
            "Social care and psychology apply ethical frameworks, statutory duties, and therapeutic "
            "models to support individuals and communities. Practitioners navigate complexity, trauma, "
            "and multi-agency systems while maintaining professional boundaries and safeguarding duties."
        ),
        "core_principles": [
            "Person-centred and strengths-based practice.",
            "Safeguarding: recognise, record, and escalate abuse or neglect promptly.",
            "Professional boundaries: clarity prevents dependency and ethical drift.",
            "Anti-oppressive practice: challenge discrimination and promote equity.",
            "Reflective practice: supervision and CPD manage vicarious trauma and competence.",
        ],
        "methodology": [
            "Assessment — holistic biopsychosocial formulation.",
            "Care plan — SMART goals with multi-agency coordination.",
            "Intervention — evidence-based methods matched to need.",
            "Review — outcome monitoring and plan adjustment.",
            "Closure/transition — sustainable handover to other services.",
        ],
    },
    "general_professional": {
        "field_intro": (
            "Professional work in any field requires structured communication, reliability, and "
            "continuous improvement. Interviewers assess whether you can translate abstract "
            "competencies into observable behaviours that deliver outcomes for employers and customers."
        ),
        "core_principles": [
            "Clarity: define terms before arguing conclusions.",
            "Evidence: support claims with data, examples, or documented outcomes.",
            "Accountability: own mistakes and describe corrective action.",
            "Adaptability: learn new tools and contexts without losing quality standards.",
            "Ethics: honesty and confidentiality build long-term trust.",
        ],
        "methodology": [
            "Understand the request and confirm expectations.",
            "Plan resources, timeline, and quality checks.",
            "Execute with attention to detail and stakeholder updates.",
            "Verify output against acceptance criteria.",
            "Reflect and improve the process for next time.",
        ],
    },
}

# Map normalized skill keys to domains
SKILL_DOMAIN_MAP: dict[str, str] = {}

_DOMAIN_SKILL_LISTS: dict[str, list[str]] = {
    "engineering": [
        "AutoCAD", "Structural analysis", "Project management", "Site supervision", "CAD", "Thermodynamics",
        "Manufacturing processes", "FEA", "Circuit design", "PLC programming", "Power systems", "Safety standards",
        "Process design", "Hazmat safety", "Quality control", "Blueprints", "Building regulations", "Revit",
        "Electrical installation", "Fault finding", "Assembly", "Machinery operation", "Site safety",
        "Subcontractor coordination", "Wiring regulations", "Basic repairs", "Physical work", "Heavy lifting",
    ],
    "technology": [
        "Python", "JavaScript", "SQL", "AWS", "Docker", "Kubernetes", "CI/CD", "Machine learning", "Statistics",
        "Analytics", "Data analysis", "System design", "APIs", "Git", "Terraform", "Testing", "Network security",
        "SIEM", "Agile", "Power BI", "Excel", "Data handling", "Visualization", "User research", "UI basics",
        "Conversion optimization", "Shopify", "Digital marketing", "SEO", "CRM", "Pipeline management",
    ],
    "healthcare": [
        "Clinical diagnosis", "Pharmacology", "Patient care", "Patient assessment", "Medication administration",
        "Medication prompts", "Medical imaging", "Radiation safety", "Manual therapy", "Exercise prescription",
        "Rehabilitation", "Patient counseling", "Patient positioning", "EMR systems", "First aid", "CPR",
        "Personal care", "Care planning", "Care with belongings", "Mental health support", "Therapeutic interventions",
        "Assistive technology", "ADL training", "Lab techniques", "Lab analysis", "PCR", "Molecular biology",
    ],
    "legal_finance": [
        "Legal research", "Legal documentation", "Contract drafting", "Litigation support", "E-discovery",
        "Compliance", "Regulatory compliance", "Regulations", "IFRS", "Financial modelling", "Financial reporting",
        "Forecasting", "Budgeting", "Tax", "Valuation", "Equity research", "Market analysis", "Bloomberg",
        "Audit", "Risk assessment", "Policy analysis", "Policy writing", "Policy guidance",
    ],
    "education": [
        "Lesson planning", "Classroom management", "Differentiated instruction", "Assessment", "Exam preparation",
        "Behaviour management", "Safeguarding", "Childcare", "Classroom support", "Mathematics curriculum",
        "Mathematics", "English", "ESL", "Academic writing", "Scientific writing", "Lecture delivery",
        "Research", "Multi-agency working",
    ],
    "creative_media": [
        "Adobe Creative Suite", "Photoshop", "Illustrator", "InDesign" if False else "Illustrator",
        "Premiere Pro", "After Effects", "Lightroom", "Photography", "Video editing" if False else "Photography",
        "Typography", "Brand identity", "Branding", "Brand management", "Copywriting", "Storytelling",
        "Color grading", "Editing", "Fact-checking", "Digital publishing", "Presentation",
    ],
    "hospitality_operations": [
        "Customer service", "Sales", "B2B sales", "Merchandising", "Retail operations", "Inventory management",
        "Cash handling", "POS systems", "Kitchen management", "Menu development", "Food hygiene", "Food safety",
        "Coffee preparation", "Table service", "Order taking", "Upselling", "Guest services", "Hospitality software",
        "Revenue management", "Route planning", "Navigation", "Safe driving", "Package handling", "Order picking",
        "Warehouse" if False else "Order picking", "Cleaning", "Time management", "Scheduling", "Team leadership",
        "Staff training", "Retail Store Manager" if False else "Merchandising",
    ],
    "social_care": [
        "Case management", "Counselling", "CBT", "Crisis management", "Safeguarding", "Empathy", "Ethics",
        "Confidentiality", "Interviewing", "Stakeholder engagement", "Stakeholder management",
    ],
}

# Fix creative_media list - remove invalid entries
_DOMAIN_SKILL_LISTS["creative_media"] = [
    "Adobe Creative Suite", "Photoshop", "Illustrator", "Premiere Pro", "After Effects", "Lightroom",
    "Photography", "Typography", "Brand identity", "Branding", "Brand management", "Copywriting",
    "Storytelling", "Color grading", "Editing", "Fact-checking", "Digital publishing", "Presentation",
]

_DOMAIN_SKILL_LISTS["hospitality_operations"] = [
    "Customer service", "Sales", "B2B sales", "Merchandising", "Retail operations", "Inventory management",
    "Cash handling", "POS systems", "Kitchen management", "Menu development", "Food hygiene", "Food safety",
    "Coffee preparation", "Table service", "Order taking", "Upselling", "Guest services", "Hospitality software",
    "Revenue management", "Route planning", "Navigation", "Safe driving", "Package handling", "Order picking",
    "Cleaning", "Time management", "Scheduling", "Team leadership", "Staff training", "Kitchen support",
    "Itinerary planning", "Tool use", "Typing", "Accuracy", "Reliability", "Punctuality", "Teamwork",
    "Phone manner", "Product knowledge", "Sales targets",
]

for domain, skills in _DOMAIN_SKILL_LISTS.items():
    for skill in skills:
        SKILL_DOMAIN_MAP[normalize_key(skill)] = domain


def classify_skill_domain(skill: str, role_title: str | None = None) -> str:
    key = normalize_key(skill)
    role_k = normalize_key(role_title or "")
    # Disambiguate skills that mean different things in different roles
    trade_roles = {
        "electrician", "electrical_engineer", "construction_site_manager",
        "mechanical_engineer", "civil_engineer", "chemical_engineer", "architect",
    }
    if key == "testing" and role_k in trade_roles:
        return "engineering"
    if key == "testing" and role_k in {"software_engineer", "devops_engineer", "data_scientist", "cybersecurity_analyst"}:
        return "technology"
    return SKILL_DOMAIN_MAP.get(key, "general_professional")


def get_domain_foundation(domain: str) -> dict:
    return DOMAIN_FOUNDATIONS.get(domain, DOMAIN_FOUNDATIONS["general_professional"])
