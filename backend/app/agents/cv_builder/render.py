"""
agents/cv_builder/render.py
================================
Deterministic, NON-generative CV rendering: turns an APPROVED
`CVGenerationResult` (the dict the Reflector has already passed) plus the
original profile snapshot into the exact `GeneratedCV.rendered_content`
JSON structure that the frontend's live preview and
`tools/document_export.py`'s PDF/DOCX/Markdown exporters both consume.

Per the platform-wide design principle ("scraping happens before the
graph" in job_search/graph.py — the analogous rule applies here), this
module runs AFTER the LangGraph pipeline returns, never as a graph node:
every value placed into the output here either came verbatim from the
profile (pass-through sections) or was already verified by
`CVReflectorAgent.domain_checks()` (the enhanced summary/bullets/skills),
so there is nothing left to quality-gate — only template assembly.

Field names below are deliberately kept in lockstep with
`app/db/models/profile.py` / `app/schemas/profile.py` (e.g. `Project.title`
+ `Project.project_url`, NOT `name`/`url`; `Volunteer.organization`, NOT
`organization_name`; `Award.name` + `Award.issuing_organization`, NOT
`title`/`issuer`) — a mismatch here would silently render blank fields on
every generated CV.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_SECTION_TITLES: dict[str, str] = {
    "summary": "Professional Summary",
    "experience": "Work Experience",
    "education": "Education",
    "skills": "Skills",
    "projects": "Projects",
    "certifications": "Certifications",
    "publications": "Publications",
    "languages": "Languages",
    "volunteer": "Volunteer Experience",
    "awards": "Awards",
    "references": "References",
}


def _render_generated_section(section_id: str, payload: dict) -> dict | None:
    """Turn one role-targeted generated_sections entry into rendered_content section shape."""
    title = _SECTION_TITLES.get(section_id, section_id.replace("_", " ").title())
    if section_id == "summary":
        content = payload.get("content")
        if not content:
            return None
        return {"section_id": "summary", "title": title, "content": content}
    if section_id == "skills":
        items = payload.get("items") or []
        if not items:
            return None
        return {"section_id": "skills", "title": title, "items": items}
    entries = payload.get("entries")
    if entries is None:
        return None
    return {"section_id": section_id, "title": title, "entries": entries}


def _render_role_targeted_sections(draft: dict, section_ids: list[str]) -> list[dict]:
    generated = draft.get("generated_sections") or {}
    sections: list[dict] = []
    for section_id in section_ids:
        if section_id == "summary":
            content = (generated.get("summary") or {}).get("content") or draft.get("professional_summary")
            if content:
                sections.append({"section_id": "summary", "title": _SECTION_TITLES["summary"], "content": content})
            continue
        if section_id == "custom":
            for custom in generated.get("custom", {}).get("sections", []):
                sections.append(
                    {
                        "section_id": f"custom-{custom.get('id', 'generated')}",
                        "title": custom.get("title", "Custom Section"),
                        "section_type": custom.get("section_type", "list"),
                        "free_text_content": custom.get("free_text_content"),
                        "tags": custom.get("tags", []),
                        "entries": custom.get("entries", []),
                    }
                )
            continue
        payload = generated.get(section_id)
        if not payload:
            continue
        rendered = _render_generated_section(section_id, payload)
        if rendered:
            sections.append(rendered)
    return sections


def _bullets_for_entry(entry: dict, enhanced_groups: list[dict], original_field: str) -> list[str]:
    """Prefer the Reflector-approved enhanced bullets for this entry (matched by its real ORM id); fall back to the original, unenhanced bullets if none were produced (e.g. the entry had no bullets to begin with)."""
    entry_id = str(entry.get("id"))
    for group in enhanced_groups:
        if group.get("entry_id") == entry_id:
            enhanced = [b.get("enhanced") for b in group.get("enhanced_bullets", []) if b.get("enhanced")]
            if enhanced:
                return enhanced
    return list(entry.get(original_field) or [])


def _render_experience_section(profile: dict, draft: dict) -> dict:
    enhanced_groups = draft.get("enhanced_work_experiences") or []
    entries = [
        {
            "id": str(we.get("id")),
            "job_title": we.get("job_title"),
            "company_name": we.get("company_name"),
            "company_url": we.get("company_url"),
            "location": we.get("location"),
            "employment_type": we.get("employment_type"),
            "start_date": we.get("start_date"),
            "end_date": we.get("end_date"),
            "is_current": we.get("is_current", False),
            "bullets": _bullets_for_entry(we, enhanced_groups, "description_bullets"),
        }
        for we in profile.get("work_experiences", [])
    ]
    return {"section_id": "experience", "title": "Work Experience", "entries": entries}


def _render_projects_section(profile: dict, draft: dict) -> dict:
    enhanced_groups = draft.get("enhanced_projects") or []
    entries = [
        {
            "id": str(proj.get("id")),
            "title": proj.get("title"),
            "description": proj.get("description"),
            "project_url": proj.get("project_url"),
            "role": proj.get("role"),
            "start_date": proj.get("start_date"),
            "end_date": proj.get("end_date"),
            "technologies": proj.get("technologies", []),
            "bullets": _bullets_for_entry(proj, enhanced_groups, "key_achievements"),
        }
        for proj in profile.get("projects", [])
    ]
    return {"section_id": "projects", "title": "Projects", "entries": entries}


def _render_education_section(profile: dict) -> dict:
    entries = [
        {
            "id": str(edu.get("id")),
            "institution": edu.get("institution"),
            "degree": edu.get("degree"),
            "field_of_study": edu.get("field_of_study"),
            "location": edu.get("location"),
            "start_date": edu.get("start_date"),
            "end_date": edu.get("end_date"),
            "is_current": edu.get("is_current", False),
            "grade": edu.get("grade"),
            "description_bullets": edu.get("description_bullets", []),
            "relevant_coursework": edu.get("relevant_coursework", []),
        }
        for edu in profile.get("educations", [])
    ]
    return {"section_id": "education", "title": "Education", "entries": entries}


def _render_skills_section(draft: dict) -> dict:
    return {"section_id": "skills", "title": "Skills", "items": draft.get("prioritized_skills", [])}


def _render_simple_list_section(
    profile: dict, profile_field: str, section_id: str, title: str, field_names: list[str]
) -> dict:
    """Generic pass-through renderer for sections the agent pipeline never touches (certifications, publications, languages, volunteer, awards, references) — every value here came straight from the profile, unmodified."""
    entries = [{name: item.get(name) for name in ("id", *field_names)} for item in profile.get(profile_field, [])]
    return {"section_id": section_id, "title": title, "entries": entries}


def _render_custom_sections(profile: dict) -> list[dict]:
    rendered = []
    for section in profile.get("custom_sections", []):
        rendered.append(
            {
                "section_id": f"custom-{section.get('id')}",
                "title": section.get("title", "Custom Section"),
                "section_type": section.get("section_type", "list"),
                "free_text_content": section.get("free_text_content"),
                "tags": section.get("tags", []),
                "entries": section.get("entries", []),
            }
        )
    return rendered


# Field names match `app/schemas/profile.py` exactly — see module docstring.
_SIMPLE_SECTION_SPECS: dict[str, dict] = {
    "certifications": {
        "profile_field": "certifications",
        "title": "Certifications",
        "field_names": ["name", "issuing_organization", "issue_date", "expiry_date", "credential_id", "credential_url"],
    },
    "publications": {
        "profile_field": "publications",
        "title": "Publications",
        "field_names": ["title", "publisher", "publication_date", "url", "co_authors", "abstract"],
    },
    "languages": {
        "profile_field": "languages",
        "title": "Languages",
        "field_names": ["name", "proficiency"],
    },
    "volunteer": {
        "profile_field": "volunteer_entries",
        "title": "Volunteer Experience",
        "field_names": ["role", "organization", "cause_area", "start_date", "end_date", "description_bullets"],
    },
    "awards": {
        "profile_field": "awards",
        "title": "Awards",
        "field_names": ["name", "issuing_organization", "date_received", "description"],
    },
    "references": {
        "profile_field": "references",
        "title": "References",
        "field_names": ["name", "title", "organization", "email", "phone", "relationship_to_user"],
    },
}


def _format_location(profile: dict) -> str | None:
    """Deterministic ', '-joined city/state/country string — pure formatting, never an LLM call."""
    parts = [profile.get(f) for f in ("address_city", "address_state", "address_country")]
    parts = [p for p in parts if p]
    return ", ".join(parts) if parts else None


def _build_links(profile: dict) -> list[dict]:
    """Deterministic list of {"label", "url"} built from the profile's own URL fields plus any user-added `other_social_links` entries."""
    links = []
    for label, field in (("LinkedIn", "linkedin_url"), ("GitHub", "github_url"), ("Portfolio", "portfolio_url"), ("Twitter", "twitter_url")):
        url = profile.get(field)
        if url:
            links.append({"label": label, "url": url})
    links.extend(profile.get("other_social_links") or [])
    return links


def render_cv(
    *,
    profile: dict[str, Any],
    target_job: dict[str, Any] | None,
    draft: dict[str, Any],
    section_ids: list[str],
    template: str,
    tone: str,
    citations: list[dict],
    confidence_score: float,
) -> dict[str, Any]:
    """
    Build the full `GeneratedCV.rendered_content` JSON, limited to
    `section_ids` (the toggled-on sections). Every section's content is
    either (a) the Reflector-approved enhanced text from `draft`, for the
    handful of sections the agent pipeline actually rewrites (summary,
    experience bullets, project bullets, prioritized skills), or (b) a
    verbatim pass-through of the profile's own fields for every other
    section — never anything generated outside the agent pipeline.
    """
    sections: list[dict] = []
    generation_mode = draft.get("generation_mode", "profile")

    if generation_mode == "role_targeted":
        sections = _render_role_targeted_sections(draft, section_ids)
    else:
        if "summary" in section_ids and draft.get("professional_summary"):
            sections.append(
                {"section_id": "summary", "title": "Professional Summary", "content": draft["professional_summary"]}
            )
        if "experience" in section_ids:
            sections.append(_render_experience_section(profile, draft))
        if "education" in section_ids:
            sections.append(_render_education_section(profile))
        if "skills" in section_ids:
            sections.append(_render_skills_section(draft))
        if "projects" in section_ids:
            sections.append(_render_projects_section(profile, draft))

        for section_id, spec in _SIMPLE_SECTION_SPECS.items():
            if section_id in section_ids:
                sections.append(
                    _render_simple_list_section(profile, spec["profile_field"], section_id, spec["title"], spec["field_names"])
                )

        if "custom" in section_ids:
            sections.extend(_render_custom_sections(profile))

    personal_info = {
        # `full_name`/`email` come from the User row, not Profile — the route
        # layer injects them into `profile_snapshot` before this is called
        # (see api/routes/cv_builder.py), since CV Builder's pipeline only
        # ever reads `profile_snapshot`, never touches the User row directly.
        "full_name": profile.get("full_name"),
        "email": profile.get("email"),
        "phone": profile.get("phone"),
        "headline": profile.get("professional_headline"),
        "location": _format_location(profile),
        "links": _build_links(profile),
        "photo_url": profile.get("photo_url"),
    }

    return {
        "personal_info": personal_info,
        "sections": sections,
        "meta": {
            "template": template,
            "tone": tone,
            "generation_mode": generation_mode,
            "target_role_title": draft.get("target_role_title") or (target_job or {}).get("title"),
            "target_job_title": (target_job or {}).get("title"),
            "ats_keywords_matched": draft.get("ats_keywords_matched", []),
            "citations": citations,
            "confidence_score": confidence_score,
            "needs_manual_input": draft.get("needs_manual_input", False),
            "manual_input_reason": draft.get("manual_input_reason"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
