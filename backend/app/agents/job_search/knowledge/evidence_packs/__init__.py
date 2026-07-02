from __future__ import annotations

from app.agents.job_search.knowledge.evidence_packs.architecture import ARCHITECTURE_PACK
from app.agents.job_search.knowledge.evidence_packs.data import DATA_PACK
from app.agents.job_search.knowledge.evidence_packs.default import DEFAULT_PACK
from app.agents.job_search.knowledge.evidence_packs.education import EDUCATION_PACK
from app.agents.job_search.knowledge.evidence_packs.electrical import ELECTRICAL_PACK
from app.agents.job_search.knowledge.evidence_packs.finance import FINANCE_PACK
from app.agents.job_search.knowledge.evidence_packs.healthcare import HEALTHCARE_PACK
from app.agents.job_search.knowledge.evidence_packs.hospitality import HOSPITALITY_PACK
from app.agents.job_search.knowledge.evidence_packs.human_resources import HUMAN_RESOURCES_PACK
from app.agents.job_search.knowledge.evidence_packs.legal import LEGAL_PACK
from app.agents.job_search.knowledge.evidence_packs.mechanical_engineering import MECHANICAL_ENGINEERING_PACK
from app.agents.job_search.knowledge.evidence_packs.operations import OPERATIONS_PACK
from app.agents.job_search.knowledge.evidence_packs.project_management import PROJECT_MANAGEMENT_PACK
from app.agents.job_search.knowledge.evidence_packs.public_administration import PUBLIC_ADMIN_PACK
from app.agents.job_search.knowledge.evidence_packs.science_laboratory import SCIENCE_LABORATORY_PACK
from app.agents.job_search.knowledge.evidence_packs.technology import TECHNOLOGY_PACK

_PACKS = {
    "electrical": ELECTRICAL_PACK,
    "healthcare": HEALTHCARE_PACK,
    "hospitality": HOSPITALITY_PACK,
    "public_administration": PUBLIC_ADMIN_PACK,
    "architecture": ARCHITECTURE_PACK,
    "legal": LEGAL_PACK,
    "technology": TECHNOLOGY_PACK,
    "science_laboratory": SCIENCE_LABORATORY_PACK,
    "education": EDUCATION_PACK,
    "operations": OPERATIONS_PACK,
    "data": DATA_PACK,
    "human_resources": HUMAN_RESOURCES_PACK,
    "mechanical_engineering": MECHANICAL_ENGINEERING_PACK,
    "finance": FINANCE_PACK,
    "project_management": PROJECT_MANAGEMENT_PACK,
    "default": DEFAULT_PACK,
}


def resolve_role_family(role: str, explicit: str | None = None) -> str:
    if explicit and explicit in _PACKS:
        return explicit
    r = (role or "").lower()
    if any(k in r for k in ("electrician", "electrical", "wiring")):
        return "electrical"
    if any(k in r for k in ("pharmacist", "nurse", "doctor", "clinical", "therap", "gp")):
        return "healthcare"
    if any(k in r for k in ("barista", "restaurant", "hospitality", "cafe", "chef", "waiter")):
        return "hospitality"
    if any(k in r for k in ("civil service", "administrator", "policy officer", "public")):
        return "public_administration"
    if "architect" in r and "software" not in r:
        return "architecture"
    if any(k in r for k in ("solicitor", "paralegal", "lawyer", "legal")):
        return "legal"
    if any(k in r for k in ("devops", "software", "developer", "cloud", "aws", "cyber")):
        return "technology"
    if any(k in r for k in ("laboratory", "lab scientist", "research biologist", "environmental scientist")):
        return "science_laboratory"
    if any(k in r for k in ("lecturer", "teacher", "tutor", "teaching")):
        return "education"
    if any(k in r for k in ("operations manager", "operations", "site manager")):
        return "operations"
    if any(k in r for k in ("data analyst", "data entry", "data scientist", "sql")):
        return "data"
    if any(k in r for k in ("hr ", "human resources", "hr advisor", "hr business")):
        return "human_resources"
    if any(k in r for k in ("mechanical", "hvac", "heating")):
        return "mechanical_engineering"
    if any(k in r for k in ("financial analyst", "investment", "accountant", "finance")):
        return "finance"
    if any(k in r for k in ("project manager", "programme manager", "pmo")):
        return "project_management"
    return "default"


def get_evidence_pack(role_family: str) -> dict:
    return _PACKS.get(role_family, DEFAULT_PACK)


ROLE_FAMILY_OPENINGS = {
    "legal": [
        "{skill} in {role} work means finding the controlling law, checking how it applies to the client's facts, and turning that analysis into defensible advice.",
        "For a {role}, {skill} is not just searching for information; it is checking statutes, case law, procedure, and risk before advising the client.",
    ],
    "technology": [
        "For a {role}, {skill} means building and operating cloud services in a way that is secure, observable, repeatable, and recoverable.",
        "{skill} in a DevOps context is about making deployments predictable: permissions, pipelines, monitoring, rollback, and incident response all need to be designed together.",
    ],
    "science_laboratory": [
        "{skill} means carrying out laboratory work in a controlled way so sample integrity, calibration, contamination control, and traceability are protected.",
        "For a {role}, {skill} is not just following a procedure; it is protecting sample validity, safety, calibration accuracy, and repeatable results.",
    ],
    "education": [
        "In university teaching, {skill} means connecting learning outcomes, research methods, academic integrity, and assessment so students learn the subject at the right level.",
        "For a {role}, {skill} is both academic and practical: it shapes how modules are taught, how evidence is evaluated, and how students are assessed.",
    ],
    "operations": [
        "{skill} in operations means finding where work slows down, measuring the bottleneck, fixing the root cause, and standardising the improved process.",
        "For an {role}, {skill} is about turning operational data into better flow, clearer ownership, and more reliable daily performance.",
    ],
    "healthcare": [
        "For a {role}, {skill} means applying clinical knowledge with patient safety, evidence-based practice, and clear documentation at every step.",
        "{skill} in healthcare is about protecting the patient while meeting regulatory, ethical, and prescribing standards.",
    ],
    "electrical": [
        "For a {role}, {skill} means installing and testing electrical work so it is safe, compliant, and ready for inspection.",
        "{skill} in electrical work is both practical and regulated: wiring, protection, testing, and certification must align.",
    ],
    "architecture": [
        "For a {role}, {skill} means translating design intent into compliant drawings, specifications, and coordinated deliverables.",
        "{skill} in architectural practice connects design decisions, building regulations, and revision-controlled documentation.",
    ],
    "public_administration": [
        "For a {role}, {skill} means running public-service processes with transparency, policy alignment, and audit-ready records.",
        "{skill} in public administration is about accountable decisions, clear escalation, and defensible documentation.",
    ],
    "hospitality": [
        "For a {role}, {skill} means delivering consistent service while controlling hygiene, allergens, speed, and customer experience.",
        "{skill} in hospitality combines preparation standards, safety controls, and reliable customer-facing execution.",
    ],
    "data": [
        "For a {role}, {skill} means turning raw data into reliable insight through validation, modelling, and clear communication.",
        "{skill} in data work is about trustworthy inputs, reproducible analysis, and decisions stakeholders can act on.",
    ],
    "human_resources": [
        "For a {role}, {skill} means applying employment policy fairly while protecting employee rights and organisational compliance.",
        "{skill} in HR work combines policy knowledge, case handling, confidentiality, and documented decisions.",
    ],
    "mechanical_engineering": [
        "For a {role}, {skill} means designing or maintaining mechanical systems with safety margins, standards, and traceable verification.",
        "{skill} in mechanical engineering links calculations, installation practice, and inspection evidence.",
    ],
    "finance": [
        "For a {role}, {skill} means analysing financial information with rigour, controls, and defensible assumptions.",
        "{skill} in finance work requires reconciling numbers, regulatory requirements, and clear reporting.",
    ],
    "project_management": [
        "For a {role}, {skill} means coordinating scope, risk, stakeholders, and delivery evidence so projects finish on time and budget.",
        "{skill} in project management is about planned execution, controlled change, and visible progress.",
    ],
    "default": [
        "For a {role}, {skill} means applying professional methods, relevant standards, and verification so the work is safe and auditable.",
    ],
}


def select_role_family_opening(role_family: str, role: str, skill: str) -> str:
    templates = ROLE_FAMILY_OPENINGS.get(role_family) or ROLE_FAMILY_OPENINGS["default"]
    template = templates[0]
    return template.format(role=role, skill=skill)
