"""
studio_template.py
==================
Helpers for persisting the CVB-F2 15-template gallery selection on a
GeneratedCV without a schema migration.

Storage: a reserved entry in `section_config` JSON:

    {"section_id": "_studio", "enabled": true, "studio_template_id": "bold-sidebar"}

Allowed IDs match `FRONTEND_TEMPLATE_TO_PDF_STYLE` in document_export.
"""

from __future__ import annotations

from typing import Any

from app.tools.document_export import FRONTEND_TEMPLATE_TO_PDF_STYLE

STUDIO_META_SECTION_ID = "_studio"
DEFAULT_STUDIO_TEMPLATE_ID = "minimal-corporate"
ALLOWED_STUDIO_TEMPLATE_IDS: frozenset[str] = frozenset(FRONTEND_TEMPLATE_TO_PDF_STYLE.keys())


def validate_studio_template_id(value: str | None) -> str | None:
    """Return a validated studio template id, or None. Raises ValueError if unknown."""
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    if cleaned not in ALLOWED_STUDIO_TEMPLATE_IDS:
        allowed = ", ".join(sorted(ALLOWED_STUDIO_TEMPLATE_IDS))
        raise ValueError(f"Unknown studio_template_id '{cleaned}'. Allowed: {allowed}")
    return cleaned


def extract_studio_template_id(section_config: list[Any] | None) -> str | None:
    """Pull studio_template_id from section_config meta entry, if present and valid."""
    for item in section_config or []:
        if not isinstance(item, dict):
            continue
        if item.get("section_id") != STUDIO_META_SECTION_ID:
            continue
        raw = item.get("studio_template_id")
        if not raw:
            return None
        cleaned = str(raw).strip()
        if cleaned in ALLOWED_STUDIO_TEMPLATE_IDS:
            return cleaned
        return None
    return None


def inject_studio_template_id(
    section_config: list[Any] | None,
    studio_template_id: str | None,
) -> list[dict[str, Any]]:
    """
    Return a copy of section_config with the `_studio` meta entry replaced
    (or removed when studio_template_id is None).
    """
    cleaned: list[dict[str, Any]] = []
    for item in section_config or []:
        if isinstance(item, dict) and item.get("section_id") == STUDIO_META_SECTION_ID:
            continue
        if isinstance(item, dict):
            cleaned.append(dict(item))
    validated = validate_studio_template_id(studio_template_id)
    if validated:
        cleaned.append(
            {
                "section_id": STUDIO_META_SECTION_ID,
                "enabled": True,
                "studio_template_id": validated,
            }
        )
    return cleaned


def resolve_studio_template_id(
    section_config: list[Any] | None,
    *,
    fallback: str = DEFAULT_STUDIO_TEMPLATE_ID,
) -> str:
    """Extract persisted id or return fallback (default minimal-corporate)."""
    extracted = extract_studio_template_id(section_config)
    if extracted:
        return extracted
    if fallback in ALLOWED_STUDIO_TEMPLATE_IDS:
        return fallback
    return DEFAULT_STUDIO_TEMPLATE_ID


def visible_section_config(section_config: list[Any] | None) -> list[dict[str, Any]]:
    """section_config without the reserved `_studio` meta row (for UI toggles)."""
    out: list[dict[str, Any]] = []
    for item in section_config or []:
        if isinstance(item, dict) and item.get("section_id") == STUDIO_META_SECTION_ID:
            continue
        if isinstance(item, dict):
            out.append(dict(item))
    return out
