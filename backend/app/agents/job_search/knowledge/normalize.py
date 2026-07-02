"""Normalize skill and role names for knowledge lookup."""

from __future__ import annotations

import re

# Canonical display names for tools, acronyms, and proper nouns
CANONICAL_NAMES: dict[str, str] = {
    "autocad": "AutoCAD",
    "revit": "Revit",
    "cad": "CAD",
    "sql": "SQL",
    "aws": "AWS",
    "api": "API",
    "apis": "APIs",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "nodejs": "Node.js",
    "node_js": "Node.js",
    "cicd": "CI/CD",
    "ci_cd": "CI/CD",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "python": "Python",
    "react": "React",
    "graphql": "GraphQL",
    "terraform": "Terraform",
    "git": "Git",
    "fea": "FEA",
    "plc": "PLC",
    "emr": "EMR",
    "gis": "GIS",
    "gds": "GDS",
    "ifrs": "IFRS",
    "kpi": "KPI",
    "kpis": "KPIs",
    "pos": "POS",
    "pcr": "PCR",
    "siem": "SIEM",
    "adl": "ADL",
    "esl": "ESL",
    "cbt": "CBT",
    "cpr": "CPR",
    "crm": "CRM",
    "seo": "SEO",
    "b2b": "B2B",
    "haccp": "HACCP",
    "lv": "LV",
    "hv": "HV",
    "bim": "BIM",
    "excel": "Excel",
    "power_bi": "Power BI",
    "premiere_pro": "Premiere Pro",
    "after_effects": "After Effects",
    "lightroom": "Lightroom",
    "photoshop": "Photoshop",
    "illustrator": "Illustrator",
}


def normalize_key(text: str) -> str:
    """Lowercase alphanumeric key for dictionary lookup."""
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")


def title_case_skill(text: str) -> str:
    """Return canonical display name for a skill when known."""
    if not text:
        return text
    key = normalize_key(text)
    if key in CANONICAL_NAMES:
        return CANONICAL_NAMES[key]
    if text.isupper() and len(text) <= 6:
        return text
    return text.strip().title()
