"""Cross-domain contamination guard (Iteration 004E-E2.2)."""

from __future__ import annotations

import re
from typing import Any, Literal

from app.agents.job_search.knowledge.evidence_packs import resolve_role_family

ContaminationStatus = Literal[
    "clean",
    "cross_domain_suspected",
    "cross_domain_confirmed",
    "source_justified",
]

_DOMAIN_SIGNALS: dict[str, tuple[str, ...]] = {
    "journalism": (
        "breaking story",
        "sub-editor",
        "defamation",
        "newsroom",
        "editorial policy",
        "fact-checking",
        "headline sign-off",
        "independent sources",
    ),
    "marketing": (
        "qualified lead rate",
        "campaign funnel",
        "demand generation",
        "crm hygiene",
        "conversion pipeline",
        "audience segmentation",
        "marketing qualified",
    ),
    "devops": (
        "ci/cd pipeline",
        "rollback criteria",
        "kubernetes",
        "infrastructure automation",
        "deployment gate",
    ),
    "clinical": (
        "medication review",
        "prescribing safety",
        "patient counselling",
        "bnf",
        "clinical governance",
    ),
    "electrical": (
        "cable sizing",
        "earth fault",
        "bs 7671",
        "rcd",
        "consumer unit",
    ),
    "creative_design": (
        "visual hierarchy",
        "brand guidelines",
        "layout grid",
        "adobe creative",
        "typography",
        "colour palette",
    ),
    "hr_er": (
        "grievance case",
        "disciplinary action",
        "investigation notes",
        "fair investigation",
    ),
    # Food & beverage / hospitality service. These anchors are what leaked into
    # Delivery Driver / Warehouse Picker case studies (Defect Class A). They are
    # deliberately specific to food-and-drink service so they never fire on
    # generic "customer" or "quality" language in other sectors.
    "hospitality": (
        "drink quality",
        "espresso",
        "latte art",
        "barista",
        "table service",
        "coffee preparation",
    ),
}

_ROLE_PRIMARY_DOMAIN: dict[str, str] = {
    "graphic designer": "creative_design",
    "journalist": "journalism",
    "reporter": "journalism",
    "editor": "journalism",
    "marketing specialist": "marketing",
    "marketing manager": "marketing",
    "hr assistant": "hr_er",
    "clinical pharmacist": "clinical",
    "devops engineer": "devops",
    "systems engineer": "devops",
    "senior systems engineer": "devops",
    "site reliability engineer": "devops",
    "software engineer": "devops",
    "platform engineer": "devops",
    "electrical engineer": "electrical",
    "barista": "hospitality",
    "waiter": "hospitality",
    "waitress": "hospitality",
    "bartender": "hospitality",
    "café": "hospitality",
    "cafe": "hospitality",
}

# Known profession names from clearly DIFFERENT sectors. If generated content
# for one role names one of these professions (with contaminating framing) and
# it is not present in the job's own source text, that is a strong cross-role
# contamination signal (e.g. "Chartered Accountant" inside a Data Analyst Excel
# module). Tech-adjacent, highly-overlapping engineering titles are deliberately
# excluded to avoid false positives between closely related roles.
_KNOWN_PROFESSIONS: tuple[str, ...] = (
    "chartered accountant",
    "accountant",
    "journalist",
    "reporter",
    "sub-editor",
    "graphic designer",
    "clinical pharmacist",
    "pharmacist",
    "electrician",
    "teaching assistant",
    "registered nurse",
    "solicitor",
    "barrister",
    "chef",
)

# Minimal cross-SKILL leak map: technical terms that belong to a *different*
# skill and should not appear as if they define the keyed skill. Kept small and
# targeted rather than a universal ontology.
_SKILL_FOREIGN_TERMS: dict[str, tuple[str, ...]] = {
    "excel": (
        "qps",
        "connection pool",
        "connection-pool",
        "kubernetes",
        "ci/cd",
        "index seek",
        "bookmark lookup",
        "execution plan",
        "query execution plan",
        "join cardinality",
        "schema design",
        "least privilege",
        "rollback plan",
    ),
    "dashboarding": (
        "qps",
        "connection pool",
        "kubernetes",
        "ci/cd",
        "join cardinality",
        "execution plan",
    ),
}


def _role_domain(role: str, skill: str = "") -> str:
    text = f"{role} {skill}".lower()
    for key, domain in _ROLE_PRIMARY_DOMAIN.items():
        if key in text:
            return domain
    family = resolve_role_family(role)
    if family == "creative_media":
        if any(k in text for k in ("journal", "reporter", "editor", "broadcast", "news")):
            return "journalism"
        return "creative_design"
    if family == "human_resources":
        return "hr_er"
    if family == "healthcare":
        return "clinical"
    if family == "technology":
        return "devops"
    if family == "electrical":
        return "electrical"
    return family or "general"


def _detect_domains(text: str) -> set[str]:
    lowered = (text or "").lower()
    found: set[str] = set()
    for domain, signals in _DOMAIN_SIGNALS.items():
        if any(sig in lowered for sig in signals):
            found.add(domain)
    return found


def _job_source_blob(job: dict[str, Any], skill: str = "") -> str:
    return " ".join(
        [
            str(job.get("title") or ""),
            str(job.get("description_raw") or ""),
            " ".join(str(r) for r in (job.get("responsibilities") or [])),
            " ".join(str(r) for r in (job.get("requirements") or [])),
            " ".join(
                str(s.get("skill") if isinstance(s, dict) else s)
                for s in (job.get("extracted_skills") or [])
            ),
            skill or "",
        ]
    ).lower()


def _source_justifies_domain(job: dict[str, Any], skill: str, domain: str) -> bool:
    blob = _job_source_blob(job, skill)
    signals = _DOMAIN_SIGNALS.get(domain, ())
    return any(sig in blob for sig in signals)


def _detect_foreign_role_hits(text: str, role: str, job: dict[str, Any]) -> list[str]:
    lowered = (text or "").lower()
    role_l = (role or "").lower()
    source_blob = _job_source_blob(job)
    hits: list[str] = []
    for prof in _KNOWN_PROFESSIONS:
        if prof in role_l or prof in role_l.replace("-", " "):
            continue
        if prof in source_blob:
            continue  # named in the job's own sources -> justified
        # Only flag contaminating framing (the profession presented as the
        # practitioner/context), not an incidental collaborator mention.
        contaminating = (
            f"{prof} professional" in lowered
            or f"{prof} practice" in lowered
            or f"{prof} settings" in lowered
            or f"{prof} context" in lowered
            or f"in {prof}," in lowered
            or f"as {prof}," in lowered
            or f"as a {prof}" in lowered
            or f"in {prof} practice" in lowered
        )
        if contaminating:
            hits.append(prof)
    return hits


def _detect_skill_foreign_terms(text: str, skill: str, job: dict[str, Any]) -> list[str]:
    sk = re.sub(r"[^a-z]+", "_", (skill or "").lower()).strip("_")
    key = "excel" if "excel" in sk else ("dashboarding" if ("dashboard" in sk or "visual" in sk) else sk)
    foreign = _SKILL_FOREIGN_TERMS.get(key)
    if not foreign:
        return []
    source_blob = _job_source_blob(job, skill)
    lowered = (text or "").lower()
    hits: list[str] = []
    for term in foreign:
        if term in lowered and term not in source_blob:
            hits.append(term)
    return hits


def audit_cross_domain_contamination(
    text: str,
    *,
    role: str,
    skill: str = "",
    job: dict[str, Any] | None = None,
) -> dict[str, Any]:
    job = job or {}
    primary = _role_domain(role, skill)
    found = _detect_domains(text)
    foreign = found - {primary}
    # Allow closely related creative domains when design role mentions brand/marketing collaboration.
    if primary == "creative_design" and foreign == {"marketing"}:
        if _source_justifies_domain(job, skill, "marketing"):
            foreign = set()
        elif "collaborate with marketing" in " ".join(str(r) for r in job.get("responsibilities") or []).lower():
            foreign = set()

    hits: list[str] = []
    status: ContaminationStatus = "clean"
    for domain in sorted(foreign):
        for sig in _DOMAIN_SIGNALS.get(domain, ()):
            if sig in (text or "").lower():
                if _source_justifies_domain(job, skill, domain):
                    status = "source_justified"
                else:
                    hits.append(sig)
                    status = "cross_domain_confirmed"

    foreign_roles = _detect_foreign_role_hits(text, role, job)
    skill_foreign = _detect_skill_foreign_terms(text, skill, job)
    for term in foreign_roles + skill_foreign:
        hits.append(term)
        status = "cross_domain_confirmed"

    return {
        "contamination_status": status,
        "cross_domain_contamination_hits": len(hits),
        "cross_domain_signals": hits[:8],
        "foreign_role_hits": foreign_roles[:8],
        "skill_foreign_term_hits": skill_foreign[:8],
        "primary_domain": primary,
        "detected_domains": sorted(found),
    }


def cross_domain_contamination_count(
    text: str,
    *,
    role: str,
    skill: str = "",
    job: dict[str, Any] | None = None,
) -> int:
    return audit_cross_domain_contamination(text, role=role, skill=skill, job=job)[
        "cross_domain_contamination_hits"
    ]
