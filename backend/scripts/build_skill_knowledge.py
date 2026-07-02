#!/usr/bin/env python3
"""
Build skill_knowledge.json — PhD-level definitions, principles, and examples
for every skill in the popular roles catalog.

Run: cd backend && uv run python scripts/build_skill_knowledge.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agents.job_search.knowledge.domains import classify_skill_domain, get_domain_foundation
from app.agents.job_search.knowledge.expert_content_library import resolve_expert_content
from app.agents.job_search.knowledge.normalize import normalize_key, title_case_skill

CATALOG = json.loads((ROOT / "app/data/popular_roles_catalog.json").read_text())
OUT = ROOT / "app/agents/job_search/knowledge/skill_knowledge.json"


def _all_catalog_skills() -> list[str]:
    seen: set[str] = set()
    skills: list[str] = []
    for role in CATALOG:
        for s in role.get("skills", []):
            k = normalize_key(s)
            if k not in seen:
                seen.add(k)
                skills.append(s)
    return sorted(skills, key=str.lower)


# Curated expert definitions — real concepts, not placeholders.
EXPERT_DEFINITIONS: dict[str, str] = {
    "autocad": (
        "AutoCAD is Autodesk's industry-standard computer-aided design (CAD) application for precision "
        "2D drafting and 3D modeling. Drawings are stored in the DWG format and organized using layers, "
        "blocks, and annotative scaling so that plans, sections, and details remain consistent across "
        "sheet sets. Architects and engineers use model space for geometry and paper space (layouts) for "
        "plotted deliverables at defined scales."
    ),
    "revit": (
        "Autodesk Revit is a building information modeling (BIM) platform where building elements are "
        "parametric objects with embedded metadata (materials, fire ratings, costs). Changes propagate "
        "across views and schedules automatically — unlike dumb CAD linework. Revit supports clash detection, "
        "quantity take-offs, and collaborative workflows via cloud worksharing."
    ),
    "building_regulations": (
        "Building regulations (e.g. Approved Documents in England, or local equivalents) are statutory "
        "performance standards covering structure, fire safety, accessibility, energy, and drainage. "
        "Compliance is demonstrated through design calculations, specifications, and on-site inspection — "
        "approval may be via building control bodies or approved inspectors."
    ),
    "structural_analysis": (
        "Structural analysis applies mechanics (statics, dynamics, material science) to predict how structures "
        "respond to loads — dead, live, wind, seismic, and thermal. Engineers use hand calculations, "
        "finite element models, and code-based design (Eurocode, ACI, AISC) to verify that members and "
        "connections meet strength, serviceability, and ductility requirements."
    ),
    "python": (
        "Python is a high-level, dynamically typed programming language emphasizing readability. Its "
        "interpreter executes bytecode; CPython is the reference implementation. Python supports multiple "
        "paradigms (procedural, OOP, functional) and ships with extensive standard libraries. In industry, "
        "it dominates data science (NumPy, pandas), ML (PyTorch, scikit-learn), automation, and backend "
        "services (FastAPI, Django)."
    ),
    "sql": (
        "SQL (Structured Query Language) is the declarative language for relational databases. It defines "
        "schemas (DDL), manipulates rows (DML), and queries with joins, aggregations, and window functions. "
        "ACID transactions guarantee atomicity and isolation; query planners optimize execution via indexes "
        "and statistics. Dialects (PostgreSQL, MySQL, T-SQL) extend the ANSI standard."
    ),
    "machine_learning": (
        "Machine learning is a subset of AI where algorithms learn patterns from data rather than explicit "
        "rules. Supervised learning maps inputs to labels (regression, classification); unsupervised finds "
        "structure (clustering, dimensionality reduction). Training minimizes a loss function via gradient "
        "descent; generalization is measured on held-out validation data to detect overfitting."
    ),
    "statistics": (
        "Statistics is the science of collecting, analyzing, and interpreting data under uncertainty. "
        "Descriptive statistics summarize samples (mean, variance, distributions); inferential statistics "
        "test hypotheses with p-values, confidence intervals, and effect sizes. Regression models quantify "
        "relationships; experimental design controls confounders for causal claims."
    ),
    "client_presentations": (
        "Client presentations in architecture are structured communications that translate design intent "
        "into decisions clients can approve. They combine visual storytelling (plans, renders, material "
        "boards), regulatory context (planning constraints, budget), and options analysis so clients "
        "understand tradeoffs between cost, programme, aesthetics, and performance."
    ),
    "project_management": (
        "Project management is the disciplined application of initiation, planning, execution, monitoring, "
        "and closing to achieve defined objectives within scope, time, cost, and quality constraints. "
        "Frameworks such as PMBOK and PRINCE2 emphasise stakeholder management, risk registers, "
        "work breakdown structures, and earned-value tracking."
    ),
    "cad": (
        "Computer-Aided Design (CAD) is the use of software to create precise geometric models and "
        "drawings for manufacturing or construction. Unlike manual drafting, CAD supports parametric "
        "constraints, layers, blocks, and automated dimensioning — enabling design iteration, "
        "clash detection, and CNC/CAM integration."
    ),
    "fea": (
        "Finite Element Analysis (FEA) is a numerical method that discretises structures into elements "
        "to solve partial differential equations for stress, strain, deformation, and heat transfer. "
        "Engineers use FEA (e.g. ANSYS, Abaqus) to validate designs against failure modes before "
        "physical prototyping — with mesh convergence studies and factor-of-safety checks."
    ),
    "thermodynamics": (
        "Thermodynamics is the branch of physics governing energy transfer, entropy, and equilibrium "
        "in systems. The four laws constrain heat engines, refrigeration cycles, and chemical processes; "
        "mechanical engineers apply them to HVAC, power generation, and combustion analysis using "
        "property tables, psychrometrics, and exergy methods."
    ),
    "data_analysis": (
        "Data analysis is the systematic process of inspecting, cleaning, transforming, and modelling "
        "data to discover patterns and support decisions. It combines descriptive statistics, "
        "hypothesis testing, visualization, and domain knowledge — with explicit attention to bias, "
        "missing data, and reproducibility."
    ),
    "network_security": (
        "Network security protects confidentiality, integrity, and availability of data in transit "
        "and at rest across enterprise infrastructure. Controls include segmentation, firewalls, IDS/IPS, "
        "zero-trust architecture, encryption (TLS, IPsec), and security monitoring aligned to frameworks "
        "such as NIST CSF and ISO 27001."
    ),
    "docker": (
        "Docker is a platform for packaging applications with their dependencies into immutable "
        "container images defined by Dockerfiles. Containers share the host kernel but isolate "
        "processes, filesystems, and networks — enabling reproducible builds, faster CI/CD, "
        "and consistent dev/prod parity via orchestrators like Kubernetes."
    ),
    "kubernetes": (
        "Kubernetes is an open-source container orchestration system that automates deployment, "
        "scaling, and self-healing of containerised workloads. Core objects include Pods, Deployments, "
        "Services, Ingress, ConfigMaps, and PersistentVolumes — managed declaratively via YAML and "
        "controllers that reconcile desired state."
    ),
    "javascript": (
        "JavaScript is a multi-paradigm programming language that powers interactive web applications "
        "in browsers (via the DOM and event loop) and server-side services (Node.js). ES6+ features "
        "include closures, promises/async-await, modules, and prototypal inheritance — with ecosystem "
        "tools for bundling, transpilation, and type checking (TypeScript)."
    ),
    "financial_modelling": (
        "Financial modelling builds quantitative representations of a company's performance for "
        "forecasting, valuation, and decision support. Core constructs include three-statement models, "
        "DCF analysis, sensitivity tables, and scenario planning — with audit trails and error checks "
        "to meet investment banking and corporate finance standards."
    ),
    "legal_research": (
        "Legal research is the systematic identification and analysis of primary sources (statutes, "
        "case law, regulations) and secondary sources (textbooks, journals) to answer legal questions. "
        "Practitioners use structured methods (IRAC), citators, and database tools (Westlaw, Lexis) "
        "while maintaining professional conduct and currency of law."
    ),
    "pharmacology": (
        "Pharmacology is the science of drug action — how medicines interact with biological systems "
        "at molecular, cellular, and organ levels. Clinical pharmacists apply pharmacokinetics "
        "(absorption, distribution, metabolism, excretion) and pharmacodynamics to optimise dosing, "
        "prevent interactions, and counsel patients under evidence-based guidelines."
    ),
    "medical_imaging": (
        "Medical imaging uses physical modalities (X-ray, CT, MRI, ultrasound) to visualise internal "
        "anatomy and pathology non-invasively. Radiographers optimise image quality while minimising "
        "radiation dose (ALARP principle), position patients safely, and apply contrast protocols "
        "under IR(ME)R regulations and local trust policies."
    ),
    "brand_management": (
        "Brand management is the strategic discipline of creating, positioning, and maintaining a "
        "brand's identity, equity, and consistency across touchpoints. It integrates market research, "
        "positioning (Keller's CBBE model), architecture decisions, and campaign measurement (awareness, "
        "consideration, loyalty) to drive commercial and reputational value."
    ),
    "seo": (
        "Search Engine Optimisation (SEO) improves organic visibility by aligning content, technical "
        "infrastructure, and authority signals with search engine ranking algorithms. Practitioners "
        "work across on-page factors (keywords, schema, Core Web Vitals), off-page links, and "
        "content strategy — measuring via impressions, CTR, and conversion attribution."
    ),
    "excel": (
        "Microsoft Excel is a spreadsheet environment for data organisation, calculation, and analysis. "
        "Advanced use includes structured references, pivot tables, Power Query, array formulas, "
        "scenario modelling, and VBA automation — with audit practices to prevent formula errors "
        "in financial and operational reporting."
    ),
    "aws": (
        "Amazon Web Services (AWS) is a cloud computing platform offering on-demand infrastructure "
        "(EC2, S3, RDS, Lambda) and managed services across regions and availability zones. Architects "
        "design for the shared responsibility model, IAM least privilege, VPC networking, and "
        "well-architected pillars: operational excellence, security, reliability, performance, cost."
    ),
    "agile": (
        "Agile is an iterative product-delivery philosophy emphasising customer collaboration, "
        "working software, and response to change (Agile Manifesto). Scrum and Kanban are common "
        "implementations with roles (Product Owner, Scrum Master), ceremonies (sprint planning, "
        "retrospectives), and WIP limits to improve flow and feedback cycles."
    ),
    "copywriting": (
        "Copywriting is the craft of writing persuasive text that drives specific audience actions "
        "(purchase, sign-up, click). Effective copy applies AIDA or PAS frameworks, audience research, "
        "tone-of-voice guidelines, and A/B testing — balancing clarity, benefit-led messaging, and "
        "brand compliance across channels."
    ),
    "food_hygiene": (
        "Food hygiene encompasses HACCP-based controls that prevent contamination and foodborne illness "
        "in preparation and service environments. Critical control points include temperature monitoring, "
        "cross-contamination prevention, personal hygiene, allergen management, and cleaning schedules "
        "aligned to local environmental health regulations."
    ),
    "cbt": (
        "Cognitive Behavioural Therapy (CBT) is an evidence-based psychotherapy linking thoughts, "
        "feelings, and behaviours through structured interventions. Techniques include cognitive "
        "restructuring, behavioural activation, exposure hierarchies, and homework assignments — "
        "validated for depression, anxiety, and other disorders in NICE guidelines."
    ),
    "risk_assessment": (
        "Risk assessment is the systematic identification, analysis, and evaluation of hazards and "
        "their likelihood and severity. The five steps (identify, decide who may be harmed, evaluate, "
        "record, review) underpin health-and-safety law; financial and project contexts extend the "
        "method with risk registers, heat maps, and mitigation owners."
    ),
    "stakeholder_management": (
        "Stakeholder management identifies individuals and groups affected by a project, analyses "
        "their influence and interest (power/interest grid), and plans engagement to align expectations. "
        "Effective practitioners maintain communication plans, manage conflict, and document decisions "
        "to prevent scope creep and reputational damage."
    ),
    "git": (
        "Git is a distributed version control system tracking changes to source code via commits, "
        "branches, and merges. Workflows (GitFlow, trunk-based) coordinate teams; concepts include "
        "SHA hashes, rebasing vs merging, pull requests, and semantic versioning — enabling "
        "collaborative development with auditable history."
    ),
    "terraform": (
        "Terraform is an Infrastructure-as-Code tool by HashiCorp that provisions cloud resources "
        "declaratively using HCL. State files track real infrastructure; modules encapsulate reuse; "
        "plan/apply workflows enable review before changes — supporting multi-environment pipelines "
        "with remote backends and policy-as-code (Sentinel/OPA)."
    ),
    "photoshop": (
        "Adobe Photoshop is a raster graphics editor for photo manipulation, compositing, and digital "
        "art. Professionals work non-destructively with layers, masks, adjustment layers, and smart "
        "objects; colour management (ICC profiles, CMYK vs RGB) ensures print-ready output."
    ),
    "premiere_pro": (
        "Adobe Premiere Pro is a non-linear video editor for professional post-production. Editors "
        "organise sequences, apply colour correction (Lumetri), audio mixing, and export via codecs "
        "(H.264, ProRes) with broadcast-safe levels and caption accessibility compliance."
    ),
    "safeguarding": (
        "Safeguarding is the legal and moral duty to protect children and vulnerable adults from abuse, "
        "neglect, and exploitation. Practitioners must recognise signs, record concerns factually, and "
        "refer to designated safeguarding leads or statutory agencies (local authority, police) without "
        "conducting investigations themselves. Policies align with Keeping Children Safe in Education (KCSIE) "
        "or equivalent national frameworks."
    ),
    "clinical_diagnosis": (
        "Clinical diagnosis is the systematic process of identifying a patient's condition through history "
        "taking, physical examination, and targeted investigations. Clinicians construct a differential "
        "diagnosis ranked by probability and severity, apply Bayesian reasoning as new data arrives, and "
        "document reasoning to meet professional and medico-legal standards."
    ),
    "lesson_planning": (
        "Lesson planning translates curriculum objectives into a sequenced instructional episode. Effective "
        "plans state learning intentions, success criteria, prior knowledge activation, instructional "
        "methods (I do / We do / You do), differentiation strategies, and formative assessment checkpoints "
        "aligned to Bloom's taxonomy."
    ),
    "communication": (
        "Professional communication is the deliberate exchange of information to achieve shared understanding "
        "and action. It spans verbal, written, and non-verbal channels; effective communicators adapt register "
        "to audience, use active listening, confirm comprehension, and document decisions for accountability."
    ),
    "customer_service": (
        "Customer service is the end-to-end management of customer interactions to meet needs, resolve "
        "issues, and build loyalty. Frameworks like HEART (Hear, Empathise, Apologise, Resolve, Thank) "
        "structure recovery; metrics include CSAT, NPS, first-contact resolution, and average handle time."
    ),
}


def _expert_principles(skill: str, domain: str) -> list[str]:
    base = get_domain_foundation(domain)["core_principles"]
    skill_t = title_case_skill(skill)
    return base[:3] + [
        f"Apply {skill_t} with explicit reference to standards, tools, and measurable outcomes in this domain.",
        f"Document assumptions and limitations whenever {skill_t} informs a decision others will rely on.",
    ]


def _key_concepts(skill: str, domain: str) -> list[str]:
    skill_t = title_case_skill(skill)
    domain_concepts = {
        "engineering": ["Standards compliance", "Safety factors", "Design documentation", "QA/QC", "As-built records"],
        "technology": ["Abstraction", "Testing", "Observability", "Security", "Scalability"],
        "healthcare": ["Evidence base", "Consent", "Risk assessment", "Documentation", "Escalation"],
        "legal_finance": ["Materiality", "Due diligence", "Professional ethics", "Audit trail", "Jurisdiction"],
        "education": ["Scaffolding", "Assessment for learning", "Inclusion", "Safeguarding", "Metacognition"],
        "creative_media": ["Visual hierarchy", "Brand consistency", "Color theory", "Accessibility", "Version control"],
        "hospitality_operations": ["SOPs", "HACCP", "Yield", "Service recovery", "Labour efficiency"],
        "social_care": ["Strengths-based practice", "Boundaries", "Multi-agency", "Trauma-informed care", "CPD"],
        "general_professional": ["Clarity", "Accountability", "Continuous improvement", "Stakeholder alignment"],
    }
    extras = domain_concepts.get(domain, domain_concepts["general_professional"])
    return [skill_t, *extras[:6]]


def _deep_explanation(skill: str, domain: str) -> str:
    skill_t = title_case_skill(skill)
    intro = get_domain_foundation(domain)["field_intro"]
    return (
        f"{skill_t} sits within this professional context: {intro} "
        f"In practice, {skill_t} is not a checkbox on a CV — it is a bundle of theory, tool fluency, "
        f"judgment under constraints, and the ability to explain tradeoffs to non-specialists. "
        f"Interviewers probe whether you understand *why* a technique applies, not merely *that* you have used it."
    )


def _practical_example(skill: str, domain: str, role_hint: str | None = None) -> str:
    skill_t = title_case_skill(skill)
    role = role_hint or "a professional in this field"
    examples = {
        "engineering": (
            f"On a bridge refurbishment contract, {role} used {skill_t} to verify that temporary works "
            f"would not overload pier caps during deck replacement. Calculations were peer-reviewed, "
            f"assumptions about traffic loading were documented, and the method statement was approved "
            f"before night possessions began — avoiding a 48-hour delay."
        ),
        "technology": (
            f"During a production incident, {role} applied {skill_t} to isolate a memory leak causing "
            f"p99 latency to spike from 120ms to 4s. By correlating heap dumps with deployment timestamps, "
            f"the team identified an unclosed connection pool, shipped a hotfix behind a feature flag, "
            f"and added an alert on pool saturation — restoring SLO within 35 minutes."
        ),
        "healthcare": (
            f"In a ward with rising NEWS2 scores, {role} used {skill_t} to prioritise a patient with "
            f"silent hypoxia. Early escalation to the medical team triggered supplemental oxygen and "
            f"chest imaging within 20 minutes, preventing ICU admission — demonstrating how systematic "
            f"assessment saves lives under pressure."
        ),
        "legal_finance": (
            f"Before a £12m acquisition, {role} applied {skill_t} to flag a contingent liability buried "
            f"in subsidiary notes. Further due diligence renegotiated the price by 8% and inserted "
            f"indemnity clauses — protecting the client from post-completion surprises."
        ),
        "education": (
            f"With a mixed-ability Year 9 class struggling with algebra, {role} used {skill_t} to design "
            f"a lesson where manipulatives and tiered problems let lower-attaining students grasp linear "
            f"equations while others tackled simultaneous forms. Exit tickets showed 78% met the success "
            f"criteria versus 41% the week before."
        ),
        "creative_media": (
            f"For a rebrand launch, {role} applied {skill_t} to develop a visual system where typography, "
            f"colour tokens, and grid rules scaled from social assets to billboard. Stakeholder testing "
            f"showed 23% higher message recall versus the legacy identity."
        ),
        "hospitality_operations": (
            f"On a Saturday peak with two staff absent, {role} used {skill_t} to rebalance stations, "
            f"pre-batch high-volume items, and communicate wait times honestly to guests. Cover count "
            f"held at 92% of forecast with complaint rate below baseline."
        ),
        "social_care": (
            f"Working with a family at risk of breakdown, {role} used {skill_t} to coordinate education, "
            f"health, and housing services around SMART goals. After 12 weeks, school attendance rose "
            f"from 61% to 89% and the child remained safely at home."
        ),
        "general_professional": (
            f"Facing a tight deadline, {role} applied {skill_t} to clarify scope with stakeholders, "
            f"deliver incrementally with quality checks, and communicate a one-day slip early with "
            f"a recovery plan — preserving trust and avoiding rework."
        ),
    }
    return examples.get(domain, examples["general_professional"])


def _common_mistakes(skill: str, domain: str) -> list[str]:
    skill_t = title_case_skill(skill)
    return [
        f"Treating {skill_t} as a buzzword without explaining underlying theory or standards.",
        f"Citing tools or jargon without describing the problem being solved and success metrics.",
        f"Presenting only success stories — omitting limitations, failures, or alternative approaches.",
    ]


def _related_concepts(skill: str, domain: str) -> list[str]:
    foundation = get_domain_foundation(domain)
    return foundation["methodology"][:3] + _key_concepts(skill, domain)[1:4]


def _compose_definition(skill: str, domain: str) -> str:
    key = normalize_key(skill)
    if key in EXPERT_DEFINITIONS:
        return EXPERT_DEFINITIONS[key]
    skill_t = title_case_skill(skill)
    domain_intros = {
        "engineering": (
            f"{skill_t} is an engineering competency encompassing applied science, codes of practice, "
            f"and field verification. It requires translating design intent into safe, buildable outcomes "
            f"with documented calculations and quality assurance."
        ),
        "technology": (
            f"{skill_t} is a technical capability in software/data systems involving formal models, "
            f"implementation patterns, and operational concerns (reliability, security, performance). "
            f"Mastery means designing solutions that fail gracefully and are observable in production."
        ),
        "healthcare": (
            f"{skill_t} is a clinical or care competency grounded in evidence-based guidelines, "
            f"professional regulation, and patient safety frameworks. Practitioners must balance efficacy, "
            f"consent, and dignity while maintaining accurate records."
        ),
        "legal_finance": (
            f"{skill_t} is a professional capability within legal/financial practice requiring analytical "
            f"rigour, regulatory awareness, and fiduciary responsibility. Outcomes must be defensible to "
            f"clients, auditors, and regulators."
        ),
        "education": (
            f"{skill_t} is a pedagogical competency linking curriculum standards to observable learning "
            f"gains. It integrates instructional design, assessment literacy, and safeguarding duties."
        ),
        "creative_media": (
            f"{skill_t} is a creative-technical competency combining aesthetic judgment, production "
            f"craft, and delivery standards. Work must communicate clearly to target audiences within "
            f"brand and accessibility constraints."
        ),
        "hospitality_operations": (
            f"{skill_t} is an operational competency managing real-time service delivery, hygiene, "
            f"and commercial targets. Excellence requires SOPs, teamwork, and calm problem-solving under pressure."
        ),
        "social_care": (
            f"{skill_t} is a practice competency in human services requiring ethical judgment, "
            f"safeguarding awareness, and multi-agency coordination to improve outcomes for vulnerable people."
        ),
        "general_professional": (
            f"{skill_t} is a transferable professional capability demonstrated through reliable execution, "
            f"clear communication, and measurable contribution to organisational goals."
        ),
    }
    return domain_intros.get(domain, domain_intros["general_professional"])


def build_skill_entry(skill: str, role_hint: str | None = None) -> dict:
    domain = classify_skill_domain(skill, role_hint)
    skill_t = title_case_skill(skill)
    definition = _compose_definition(skill, domain)
    principles = _expert_principles(skill, domain)
    expert = resolve_expert_content(skill, role_hint)
    return {
        "skill": skill_t,
        "domain": domain,
        "definition": expert.get("definition") or definition,
        "principles": principles,
        "key_concepts": _key_concepts(skill, domain),
        "deep_explanation": expert.get("teaching_body") or _deep_explanation(skill, domain),
        "practical_example": expert.get("complex_answer") or _practical_example(skill, domain, role_hint),
        "common_mistakes": expert.get("technical_pitfalls") or _common_mistakes(skill, domain),
        "related_concepts": expert.get("related_topics") or _related_concepts(skill, domain),
        "methodology_steps": expert.get("how_it_works") or get_domain_foundation(domain)["methodology"],
        "expert": expert,
    }


def build_role_context(role: dict) -> dict:
    title = role["title"]
    skills = role.get("skills", [])
    responsibilities = role.get("responsibilities", [])
    requirements = role.get("requirements", [])
    stream = role.get("stream_id", "")
    exp = role.get("experience_level", "")

    skill_clusters: list[str] = []
    domains_seen: set[str] = set()
    for s in skills:
        d = classify_skill_domain(s)
        if d not in domains_seen:
            domains_seen.add(d)
            skill_clusters.append(d.replace("_", " ").title())

    summary = (
        f"The {title} role integrates {', '.join(skills[:4])}{'...' if len(skills) > 4 else ''} "
        f"to deliver on responsibilities such as {responsibilities[0].lower() if responsibilities else 'core duties'}. "
        f"Employers at the {exp or 'target'} level expect candidates to demonstrate both conceptual depth "
        f"and applied experience — not surface familiarity with keywords."
    )

    expectations = [
        f"Explain how {skills[0]} supports daily responsibilities when asked technical or scenario questions." if skills else "Demonstrate structured thinking under role-relevant scenarios.",
        "Use concrete examples with scale, constraints, stakeholders, and measurable outcomes.",
        "Reference professional standards, regulations, or best-practice frameworks appropriate to this field.",
        "Acknowledge tradeoffs, errors, and lessons learned — intellectual honesty signals seniority.",
    ]
    if requirements:
        expectations.append(f"Connect answers to stated requirements such as: {requirements[0]}.")

    return {
        "role_name": title,
        "stream_id": stream,
        "summary": summary,
        "responsibilities": responsibilities,
        "required_skills": skills,
        "requirements": requirements,
        "what_employers_expect": expectations,
        "skill_clusters": skill_clusters,
        "experience_level": exp,
    }


def main() -> None:
    skills = _all_catalog_skills()
    # Map skill -> example role for contextualised examples
    skill_role_hint: dict[str, str] = {}
    for role in CATALOG:
        for s in role.get("skills", []):
            skill_role_hint.setdefault(normalize_key(s), role["title"])

    skill_data = {
        normalize_key(s): build_skill_entry(s, skill_role_hint.get(normalize_key(s)))
        for s in skills
    }
    role_data: dict = {}
    for role in CATALOG:
        title = role["title"]
        resp = (role.get("responsibilities") or [None])[0]
        skill_experts = {
            normalize_key(s): resolve_expert_content(s, title, resp)
            for s in role.get("skills", [])
        }
        role_data[normalize_key(title)] = {
            **build_role_context(role),
            "skill_expert": skill_experts,
        }

    payload = {"skills": skill_data, "roles": role_data, "version": "2.0"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(skill_data)} skills and {len(role_data)} roles to {OUT}")


if __name__ == "__main__":
    main()
