"""Job Intelligence Profile — deterministic extraction from user job input (Iteration 004E-A)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.config import settings

_TOOL_KEYWORDS = (
    "sql", "excel", "power bi", "tableau", "python", "r ", "spark", "snowflake",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "jenkins", "terraform",
    "autocad", "revit", "matlab", "jira", "confluence", "sap", "salesforce",
    "premiere", "final cut", "canva", "figma", "adobe", "photoshop",
)

_SOFT_SKILL_HINTS = (
    "communication", "stakeholder", "teamwork", "collaboration", "leadership",
    "presentation", "negotiation", "time management", "problem solving",
)

_COMPLIANCE_HINTS = (
    "safety", "compliance", "regulation", "standard", "ethics", "gdpr", "hipaa",
    "bs 7671", "iec", "copyright", "brand safety", "governance", "risk",
    "haccp", "allergen", "commissioning", "inspection",
)

_SENIORITY_HINTS: tuple[tuple[str, str], ...] = (
    (r"\b(entry|junior|graduate|trainee)\b", "entry"),
    (r"\b(mid|intermediate)\b", "mid"),
    (r"\b(senior|lead|principal|staff)\b", "senior"),
    (r"\b(manager|head of|director)\b", "leadership"),
)

_PREFERRED_MARKERS = (
    "preferred", "nice to have", "nice-to-have", "bonus", "desirable", "plus",
)

_DAILY_MARKERS = (
    "daily", "day-to-day", "day to day", "each day", "routine", "ongoing",
)

_WARN_TITLE_ONLY = (
    "You entered only a role title. The generated pack may be more general. "
    "For a stronger interview pack, add the complete job description, responsibilities, "
    "company profile, tools, skills, and extra notes."
)

_WARN_LINK_NO_EXTRACTION = (
    "A job posting link was provided, but full link extraction is not enabled in this "
    "iteration. Paste the job description manually for a more accurate pack."
)


@dataclass
class JobIntelligenceItem:
    item_type: str
    text: str
    source: str
    importance: str
    covered: bool = False
    related_question_ids: list[str] = field(default_factory=list)
    missing_reason: str | None = None


@dataclass
class JobIntelligenceProfile:
    job_title: str
    company_name: str | None = None
    company_profile: str | None = None
    company_scope: str | None = None
    company_products_services: str | None = None
    industry_domain: str | None = None
    job_description: str | None = None
    responsibilities: list[str] = field(default_factory=list)
    daily_responsibilities: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    tools_software: list[str] = field(default_factory=list)
    qualifications: list[str] = field(default_factory=list)
    experience_requirements: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    technical_skills: list[str] = field(default_factory=list)
    compliance_safety_ethics: list[str] = field(default_factory=list)
    seniority_level: str | None = None
    location_context: str | None = None
    department_team_context: str | None = None
    extra_notes: str | None = None
    job_posting_url: str | None = None
    extracted_link_content: str | None = None
    extracted_items: list[JobIntelligenceItem] = field(default_factory=list)
    completeness_score: int = 0
    warnings: list[str] = field(default_factory=list)
    source_status: dict[str, str] = field(default_factory=dict)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _line_items(values: list[Any] | None) -> list[str]:
    out: list[str] = []
    for v in values or []:
        text = v.get("text") if isinstance(v, dict) else v
        text = _norm(str(text or ""))
        if text and text not in out:
            out.append(text)
    return out


def _split_required_preferred(requirements: list[str]) -> tuple[list[str], list[str]]:
    required: list[str] = []
    preferred: list[str] = []
    for req in requirements:
        lowered = req.lower()
        if any(marker in lowered for marker in _PREFERRED_MARKERS):
            preferred.append(req)
        else:
            required.append(req)
    return required, preferred


def _extract_tools_from_text(*chunks: str) -> list[str]:
    blob = " ".join(_norm(c).lower() for c in chunks if c)
    found: list[str] = []
    for tool in _TOOL_KEYWORDS:
        if re.search(rf"\b{re.escape(tool.strip())}\b", blob):
            label = tool.strip().title() if tool.strip() != "r " else "R"
            if label not in found:
                found.append(label)
    return found


def _extract_compliance_clues(*chunks: str) -> list[str]:
    out: list[str] = []
    for chunk in chunks:
        for line in re.split(r"[\n;•]", chunk or ""):
            text = _norm(line)
            if not text:
                continue
            lowered = text.lower()
            if any(h in lowered for h in _COMPLIANCE_HINTS) and text not in out:
                out.append(text)
    return out[:12]


def _detect_seniority(job: dict[str, Any], blob: str) -> str | None:
    exp = job.get("experience_level")
    if isinstance(exp, str) and exp.strip():
        lowered = exp.lower()
        if "entry" in lowered:
            return "entry"
        if "mid" in lowered:
            return "mid"
        if "senior" in lowered or "lead" in lowered or "principal" in lowered:
            return "senior"
    for pattern, label in _SENIORITY_HINTS:
        if re.search(pattern, blob, re.I):
            return label
    return None


def _company_fields(company_profile: dict[str, Any] | None) -> tuple[str | None, str | None, str | None, str | None]:
    if not company_profile:
        return None, None, None, None
    profile = _norm(str(company_profile.get("summary") or company_profile.get("description") or ""))
    scope = _norm(str(company_profile.get("scope") or company_profile.get("market") or ""))
    products = _norm(
        str(
            company_profile.get("products_services")
            or company_profile.get("products")
            or company_profile.get("services")
            or ""
        )
    )
    industry = _norm(str(company_profile.get("industry") or company_profile.get("domain") or ""))
    return profile or None, scope or None, products or None, industry or None


def _build_extracted_items(profile: JobIntelligenceProfile) -> list[JobIntelligenceItem]:
    items: list[JobIntelligenceItem] = []

    def add_many(item_type: str, values: list[str], source: str, importance: str) -> None:
        for text in values:
            items.append(JobIntelligenceItem(item_type=item_type, text=text, source=source, importance=importance))

    add_many("responsibility", profile.responsibilities, "user_field", "critical")
    add_many("daily_responsibility", profile.daily_responsibilities, "parsed_description", "high")
    add_many("required_skill", profile.required_skills, "user_field", "critical")
    add_many("preferred_skill", profile.preferred_skills, "user_field", "medium")
    add_many("tool", profile.tools_software, "parsed_description", "high")
    add_many("technical_skill", profile.technical_skills, "extracted_skill", "high")
    add_many("soft_skill", profile.soft_skills, "parsed_description", "medium")
    add_many("compliance", profile.compliance_safety_ethics, "parsed_description", "high")
    add_many("qualification", profile.qualifications, "user_field", "medium")
    add_many("experience", profile.experience_requirements, "user_field", "medium")

    if profile.company_profile:
        items.append(
            JobIntelligenceItem(
                item_type="company_profile",
                text=profile.company_profile,
                source="user_field",
                importance="high",
            )
        )
    if profile.company_products_services:
        items.append(
            JobIntelligenceItem(
                item_type="company_products",
                text=profile.company_products_services,
                source="user_field",
                importance="high",
            )
        )
    if profile.industry_domain:
        items.append(
            JobIntelligenceItem(
                item_type="industry_domain",
                text=profile.industry_domain,
                source="user_field",
                importance="medium",
            )
        )
    return items


def _compute_completeness_score(profile: JobIntelligenceProfile) -> int:
    score = 0
    if profile.job_title:
        score += 10
    if profile.company_name:
        score += 8
    if profile.company_profile:
        score += 12
    if profile.company_products_services or profile.industry_domain:
        score += 8
    if profile.job_description and len(profile.job_description) > 80:
        score += 15
    elif profile.job_description:
        score += 8
    score += min(len(profile.responsibilities) * 6, 18)
    score += min(len(profile.daily_responsibilities) * 4, 8)
    score += min(len(profile.required_skills) * 4, 16)
    score += min(len(profile.preferred_skills) * 2, 6)
    score += min(len(profile.tools_software) * 3, 12)
    score += min(len(profile.technical_skills) * 2, 8)
    score += min(len(profile.compliance_safety_ethics) * 3, 9)
    if profile.seniority_level:
        score += 4
    if profile.location_context:
        score += 3
    if profile.extra_notes:
        score += 5
    if profile.extracted_link_content:
        score += 10
    return max(0, min(100, score))


def _build_warnings(profile: JobIntelligenceProfile, job: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    thin = (
        not profile.job_description
        and not profile.responsibilities
        and not profile.required_skills
        and not profile.tools_software
        and not profile.company_profile
    )
    if thin:
        warnings.append(_WARN_TITLE_ONLY)
    url = profile.job_posting_url
    if url and not profile.extracted_link_content and not profile.job_description:
        warnings.append(_WARN_LINK_NO_EXTRACTION)
    elif url and not profile.extracted_link_content and thin:
        warnings.append(_WARN_LINK_NO_EXTRACTION)
    if profile.completeness_score <= 30 and _WARN_TITLE_ONLY not in warnings:
        warnings.append(_WARN_TITLE_ONLY)
    return warnings


def _build_source_status(profile: JobIntelligenceProfile, job: dict[str, Any]) -> dict[str, str]:
    user_signal = bool(
        profile.job_description
        or profile.responsibilities
        or profile.required_skills
        or profile.company_profile
        or profile.extra_notes
    )
    user_status = "used" if user_signal else "thin"
    link_status = "used" if profile.extracted_link_content else (
        "not_present" if not profile.job_posting_url else "not_configured"
    )
    model_status = "disabled"
    if settings.job_search_enable_model_knowledge:
        model_status = "available_not_used"
    return {
        "user_fields": user_status,
        "link_extraction": link_status,
        "web_research": "not_configured",
        "model_knowledge": model_status,
        "document_library": "available",
        "local_fallback": "used",
    }


def build_job_intelligence_profile(job: dict[str, Any]) -> JobIntelligenceProfile:
    """Deterministically build a JobIntelligenceProfile from a job snapshot dict."""
    from app.agents.job_search.mock_data import _extract_sections, _extract_skills

    title = _norm(job.get("title") or "Untitled Role")
    company_name = _norm(job.get("company_name") or "") or None
    description = job.get("description_raw") or ""
    responsibilities = _line_items(job.get("responsibilities"))
    requirements = _line_items(job.get("requirements"))
    parsed_sections = _extract_sections(description) if description else {"responsibilities": [], "requirements": []}
    if not responsibilities and parsed_sections.get("responsibilities"):
        responsibilities = parsed_sections["responsibilities"]
    if not requirements and parsed_sections.get("requirements"):
        requirements = parsed_sections["requirements"]

    required_skills, preferred_skills = _split_required_preferred(requirements)
    for skill_row in job.get("extracted_skills") or []:
        name = skill_row.get("skill") if isinstance(skill_row, dict) else str(skill_row)
        name = _norm(str(name or ""))
        if not name:
            continue
        importance = skill_row.get("importance") if isinstance(skill_row, dict) else "medium"
        if importance in ("critical", "high") and name not in required_skills:
            required_skills.append(name)
        elif name not in preferred_skills and name not in required_skills:
            required_skills.append(name)

    daily_responsibilities = [
        r for r in responsibilities if any(m in r.lower() for m in _DAILY_MARKERS)
    ]
    if not daily_responsibilities and description:
        for line in description.splitlines():
            text = _norm(line.lstrip("-•* "))
            if text and any(m in text.lower() for m in _DAILY_MARKERS):
                daily_responsibilities.append(text)

    blob = " ".join(
        filter(
            None,
            [description, " ".join(responsibilities), " ".join(requirements), title],
        )
    )
    tools = _extract_tools_from_text(description, " ".join(requirements), " ".join(responsibilities))
    parsed_skills = _extract_skills(description) if description else []
    technical_skills = [s["skill"] for s in parsed_skills if s.get("skill")]
    for skill in technical_skills:
        if skill not in required_skills and skill not in preferred_skills:
            required_skills.append(skill)

    soft_skills = []
    for chunk in requirements + responsibilities + ([description] if description else []):
        lowered = chunk.lower()
        for hint in _SOFT_SKILL_HINTS:
            if hint in lowered and hint.title() not in soft_skills:
                soft_skills.append(hint.title())

    compliance = _extract_compliance_clues(description, " ".join(responsibilities), " ".join(requirements))
    qualifications = [r for r in requirements if any(w in r.lower() for w in ("degree", "certification", "qualified", "license", "chartered"))]
    experience_requirements = [r for r in requirements if any(w in r.lower() for w in ("years", "experience", "proven track"))]

    company_profile_dict = job.get("company_profile") if isinstance(job.get("company_profile"), dict) else {}
    cp, scope, products, industry = _company_fields(company_profile_dict)
    extra_notes = _norm(str(job.get("extra_notes") or company_profile_dict.get("notes") or "")) or None

    profile = JobIntelligenceProfile(
        job_title=title,
        company_name=company_name,
        company_profile=cp,
        company_scope=scope,
        company_products_services=products,
        industry_domain=industry,
        job_description=_norm(description) or None,
        responsibilities=responsibilities,
        daily_responsibilities=daily_responsibilities,
        required_skills=list(dict.fromkeys(required_skills)),
        preferred_skills=list(dict.fromkeys(preferred_skills)),
        tools_software=tools,
        qualifications=qualifications,
        experience_requirements=experience_requirements,
        soft_skills=soft_skills,
        technical_skills=list(dict.fromkeys(technical_skills)),
        compliance_safety_ethics=compliance,
        seniority_level=_detect_seniority(job, blob),
        location_context=_norm(job.get("location") or "") or None,
        department_team_context=_norm(str(company_profile_dict.get("department") or company_profile_dict.get("team") or "")) or None,
        extra_notes=extra_notes,
        job_posting_url=_norm(job.get("source_url") or "") or None,
        extracted_link_content=_norm(job.get("extracted_link_content") or "") or None,
    )
    profile.completeness_score = _compute_completeness_score(profile)
    profile.warnings = _build_warnings(profile, job)
    profile.source_status = _build_source_status(profile, job)
    profile.extracted_items = _build_extracted_items(profile)
    return profile


def profile_to_dict(profile: JobIntelligenceProfile) -> dict[str, Any]:
    data = asdict(profile)
    return data


def profile_summary_text(profile: JobIntelligenceProfile) -> str:
    parts = [
        f"Role: {profile.job_title}",
        f"Completeness: {profile.completeness_score}/100",
    ]
    if profile.company_name:
        parts.append(f"Company: {profile.company_name}")
    if profile.responsibilities:
        parts.append(f"Responsibilities tracked: {len(profile.responsibilities)}")
    if profile.required_skills:
        parts.append(f"Required skills: {', '.join(profile.required_skills[:6])}")
    if profile.tools_software:
        parts.append(f"Tools: {', '.join(profile.tools_software[:6])}")
    if profile.compliance_safety_ethics:
        parts.append(f"Compliance/safety clues: {len(profile.compliance_safety_ethics)}")
    return " | ".join(parts)
