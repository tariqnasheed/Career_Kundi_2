"""
data/popular_roles_catalog.py
==============================
Canonical list of popular job roles for pre-seeding the interview-pack
document library. Synced from ``frontend/src/lib/popularJobRoles.ts`` via
``popular_roles_catalog.json`` (regenerate with ``make sync-role-catalog``).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CATALOG_PATH = Path(__file__).with_name("popular_roles_catalog.json")


@lru_cache
def get_all_catalog_roles() -> list[dict[str, Any]]:
    if not _CATALOG_PATH.exists():
        return []
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def catalog_role_to_job_snapshot(role: dict[str, Any]) -> dict[str, Any]:
    """Convert a catalog role entry into a job snapshot for pack generation."""
    skills = role.get("skills") or []
    return {
        "title": role["title"],
        "company_name": "Various employers",
        "description_raw": (
            f"{role['title']} — {role.get('employment_type', 'Full-time')} role. "
            f"Typical duties: {'; '.join(role.get('responsibilities', [])[:3])}."
        ),
        "responsibilities": role.get("responsibilities") or [],
        "requirements": role.get("requirements") or [],
        "extracted_skills": [{"skill": s, "category": "technical", "importance": "medium"} for s in skills],
    }
