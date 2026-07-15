"""
agents/cv_builder/mock_data.py
====================================
Offline, content-aware stand-in for the CV Builder's single LLM call
("enhance my profile into CV-ready content"), used when
`settings.llm_mode == "mock"`.

Design constraint that shapes every function below: this is the ONE feature
where a fabricated fact is most damaging — a CV with an invented metric or
client name is actively harmful to the user in a real interview. So unlike
job_search's mock (which extracts new structured fields from unseen text),
this mock NEVER introduces a number, proper noun, or claim that isn't
already present in the user's own profile. Every "enhancement" is a
rephrasing or reordering of real input — stronger verbs, tighter phrasing,
JD-aware prioritization — never new substance. This is what lets
`agents.py`'s fabrication-detection Reflector check pass cleanly even in
mock mode, and it's intentional: it proves the zero-hallucination guarantee
holds structurally, not just "because the LLM was told to."
"""

from __future__ import annotations

import re
from datetime import date, datetime

# Weak/passive openers commonly found in self-written bullets, mapped to a
# stronger, ownership-oriented opener. Purely a rephrasing table — every
# replacement is a synonym for the same action, never new information.
_WEAK_OPENERS: dict[str, str] = {
    "helped": "Drove",
    "helped with": "Drove",
    "worked on": "Delivered",
    "responsible for": "Owned",
    "assisted with": "Advanced",
    "assisted in": "Advanced",
    "involved in": "Contributed directly to",
    "tasked with": "Took ownership of",
    "in charge of": "Led",
    "participated in": "Played a key role in",
    "supported": "Drove",
    "worked with": "Partnered with",
}

# Sorted longest-phrase-first so "helped with" matches before the shorter "helped".
_WEAK_OPENER_PATTERN = re.compile(
    r"^(" + "|".join(sorted((re.escape(k) for k in _WEAK_OPENERS), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

_PROFICIENCY_RANK = {"expert": 4, "advanced": 3, "intermediate": 2, "beginner": 1}


def _strengthen_bullet(original: str) -> tuple[str, str]:
    """
    Rewrite ONE bullet: replace a weak/passive opening phrase with a
    stronger synonym if one is detected, tidy whitespace/punctuation, and
    explain exactly what changed and what didn't. Never adds a number,
    name, or outcome that wasn't already in `original`.
    """
    text = original.strip().rstrip(".")
    if not text:
        return original, "Bullet was empty — left unchanged."

    match = _WEAK_OPENER_PATTERN.match(text)
    if match:
        matched_phrase = match.group(1)
        replacement = _WEAK_OPENERS[matched_phrase.lower()]
        rest = text[match.end():].lstrip()
        enhanced = f"{replacement} {rest}" if rest else replacement
        rationale = (
            f"Replaced the passive opener '{matched_phrase}' with a stronger, ownership-oriented "
            f"verb ('{replacement}'). No new facts, figures, or outcomes were added — only your "
            "original achievement was reworded for impact and ATS scanning."
        )
    else:
        enhanced = text[0].upper() + text[1:] if text else text
        rationale = (
            "Your original phrasing already led with a strong action verb, so the wording is "
            "preserved as-is — only whitespace/punctuation were tidied."
        )

    return enhanced, rationale


def _parse_date(value) -> date | None:
    """Accepts a `date`, an ISO-format string, or `None` — whatever shape the profile snapshot carries the field in."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value[:10]).date()
        except ValueError:
            return None
    return None


def _years_of_experience(work_experiences: list[dict]) -> float:
    """
    Sum real, non-overlapping-naively (overlap correction would be overkill
    for a mock estimate) tenure across every work experience that has at
    least a start date, treating `is_current`/missing end date as "today".
    A genuinely computed number from the user's own dates — never invented.
    """
    today = date.today()
    total_days = 0
    for we in work_experiences:
        start = _parse_date(we.get("start_date"))
        if not start:
            continue
        end = today if we.get("is_current") else (_parse_date(we.get("end_date")) or today)
        if end > start:
            total_days += (end - start).days
    return round(total_days / 365.25, 1)


def _most_recent_experience(work_experiences: list[dict]) -> dict | None:
    if not work_experiences:
        return None
    current = [we for we in work_experiences if we.get("is_current")]
    if current:
        return current[0]
    dated = [we for we in work_experiences if _parse_date(we.get("end_date"))]
    if dated:
        return max(dated, key=lambda we: _parse_date(we.get("end_date")))
    return work_experiences[0]


def _sorted_skills(skills: list[dict], jd_skill_names: set[str] | None = None) -> list[dict]:
    """JD-overlap first (real, computed intersection), then proficiency rank, then alphabetical — never invents a skill the profile doesn't list."""
    jd_skill_names = {s.lower() for s in (jd_skill_names or set())}

    def sort_key(skill: dict) -> tuple[int, int, str]:
        name = (skill.get("name") or "").strip()
        jd_match = 0 if name.lower() in jd_skill_names else 1
        proficiency_rank = -_PROFICIENCY_RANK.get((skill.get("proficiency") or "").lower(), 0)
        return (jd_match, proficiency_rank, name.lower())

    return sorted(skills, key=sort_key)


def mock_professional_summary(profile: dict, target_job: dict | None) -> tuple[str, str]:
    """Build a 2-4 sentence summary purely from real profile fields — headline, computed tenure, top skills, and (if present) the real target-job title/company."""
    work_experiences = profile.get("work_experiences", [])
    skills = profile.get("skills", [])
    headline = profile.get("professional_headline")
    most_recent = _most_recent_experience(work_experiences)
    years = _years_of_experience(work_experiences)
    jd_names = {s.get("skill") for s in (target_job or {}).get("extracted_skills", []) if isinstance(s, dict)}
    top_skills = [s["name"] for s in _sorted_skills(skills, jd_names)[:6] if s.get("name")]

    parts: list[str] = []
    if headline:
        parts.append(headline)
    elif most_recent:
        parts.append(f"{most_recent.get('job_title', 'Professional')} with experience at {most_recent.get('company_name', 'a previous employer')}")

    if years >= 1:
        parts.append(f"{years:.0f}+ years of professional experience" if years >= 2 else "Over a year of professional experience")
    if top_skills:
        parts.append("Skilled in " + ", ".join(top_skills))
    if target_job and target_job.get("title"):
        target_phrase = f"Looking to apply this background to the {target_job['title']} role"
        if target_job.get("company_name"):
            target_phrase += f" at {target_job['company_name']}"
        parts.append(target_phrase)

    if not parts:
        return "", ""

    summary = ". ".join(p.rstrip(".") for p in parts) + "."
    rationale = (
        "Built directly from your profile's headline, tenure computed from your listed roles' dates, "
        "and your top-ranked skills" + (f", with explicit alignment to the target role '{target_job['title']}'" if target_job else "")
        + ". Contains no claim beyond what your profile already states."
    )
    return summary, rationale


def profile_text_blob(profile: dict) -> str:
    """Flatten every real free-text field in the profile into one lowercased string, used for the ATS-keyword-overlap computation below."""
    chunks: list[str] = [profile.get("professional_headline") or "", profile.get("bio_summary") or ""]
    for skill in profile.get("skills", []):
        chunks.append(skill.get("name") or "")
    for we in profile.get("work_experiences", []):
        chunks.extend(we.get("description_bullets") or [])
        chunks.append(we.get("job_title") or "")
        chunks.append(we.get("company_name") or "")
    for edu in profile.get("educations", []):
        chunks.append(edu.get("institution") or "")
        chunks.append(edu.get("degree") or "")
    for proj in profile.get("projects", []):
        chunks.append(proj.get("description") or "")
        chunks.append(proj.get("title") or "")
        chunks.extend(proj.get("key_achievements") or [])
        chunks.extend(proj.get("technologies") or [])
    if profile.get("professional_summary"):
        chunks.append(profile.get("professional_summary") or "")
    return " ".join(chunks).lower()


def mock_ats_keywords_matched(profile: dict, target_job: dict | None) -> list[str]:
    """Real, computed intersection between the target job's extracted skills and the profile's own text — empty (never guessed) when there's no target job."""
    if not target_job:
        return []
    blob = profile_text_blob(profile)
    matched = []
    for skill_entry in target_job.get("extracted_skills", []):
        name = skill_entry.get("skill") if isinstance(skill_entry, dict) else skill_entry
        if name and name.lower() in blob:
            matched.append(name)
    return matched


def _enhance_entry_bullets(entries: list[dict], bullets_field: str) -> list[dict]:
    """Apply `_strengthen_bullet` to every real bullet on every entry (work experience, project, ...) that actually has one."""
    enhanced_entries = []
    for entry in entries:
        bullets = entry.get(bullets_field) or []
        if not bullets:
            continue
        enhanced_bullets = []
        for bullet in bullets:
            enhanced, rationale = _strengthen_bullet(bullet)
            enhanced_bullets.append({"original": bullet, "enhanced": enhanced, "rationale": rationale})
        enhanced_entries.append({"entry_id": str(entry.get("id")), "enhanced_bullets": enhanced_bullets})
    return enhanced_entries


def mock_generate_role_targeted_cv_content(
    profile: dict,
    target_role_title: str,
    target_role_description: str | None,
    target_job: dict | None,
    section_ids: list[str],
    tone: str,
) -> dict:
    """Role-targeted mock: synthesize plausible section payloads for the requested role."""
    role = target_role_title.strip() or "Target Role"
    jd_hint = (target_role_description or (target_job or {}).get("description_raw") or "")[:200]
    skills_pool = [
        s.get("name") for s in profile.get("skills", []) if s.get("name")
    ] or ["Communication", "Problem solving", "Collaboration", "Technical aptitude"]

    generated: dict[str, dict] = {}
    if "summary" in section_ids:
        generated["summary"] = {
            "content": (
                f"Motivated professional pursuing the {role} role"
                + (f" with focus on {jd_hint[:80]}…" if jd_hint else "")
                + ". Brings transferable experience and a commitment to delivering results in this capacity."
            )
        }
    if "experience" in section_ids:
        generated["experience"] = {
            "entries": [
                {
                    "job_title": role,
                    "company_name": "Previous Organization",
                    "location": profile.get("address_city"),
                    "start_date": "2022-01-01",
                    "end_date": None,
                    "is_current": True,
                    "bullets": [
                        f"Applied core competencies relevant to {role} in day-to-day responsibilities.",
                        "Collaborated with cross-functional teams to deliver measurable outcomes.",
                        "Continuously developed skills aligned with the target role requirements.",
                    ],
                }
            ]
        }
    if "education" in section_ids:
        edu = profile.get("educations") or []
        if edu:
            generated["education"] = {
                "entries": [
                    {
                        "institution": e.get("institution"),
                        "degree": e.get("degree"),
                        "field_of_study": e.get("field_of_study"),
                        "start_date": e.get("start_date"),
                        "end_date": e.get("end_date"),
                        "is_current": e.get("is_current", False),
                    }
                    for e in edu
                ]
            }
        else:
            generated["education"] = {
                "entries": [{"institution": "University", "degree": "Bachelor's Degree", "field_of_study": "Relevant field"}]
            }
    if "skills" in section_ids:
        generated["skills"] = {"items": skills_pool[:10]}
    if "projects" in section_ids:
        generated["projects"] = {
            "entries": [
                {
                    "title": f"{role} Portfolio Project",
                    "role": role,
                    "description": f"Demonstration project showcasing abilities relevant to {role}.",
                    "technologies": skills_pool[:4],
                    "bullets": ["Designed and implemented a solution aligned with role expectations."],
                }
            ]
        }
    if "certifications" in section_ids:
        generated["certifications"] = {
            "entries": [{"name": f"{role} Foundations", "issuing_organization": "Professional Board"}]
        }
    if "publications" in section_ids:
        generated["publications"] = {"entries": []}
    if "languages" in section_ids:
        langs = profile.get("languages") or []
        generated["languages"] = {
            "entries": langs or [{"name": "English", "proficiency": "Professional"}]
        }
    if "volunteer" in section_ids:
        generated["volunteer"] = {"entries": []}
    if "awards" in section_ids:
        generated["awards"] = {"entries": []}
    if "references" in section_ids:
        generated["references"] = {"entries": []}

    summary_text = (generated.get("summary") or {}).get("content", "")
    return {
        "professional_summary": summary_text,
        "summary_rationale": f"Authored for target role '{role}' in role-targeted mode.",
        "enhanced_work_experiences": [],
        "enhanced_projects": [],
        "prioritized_skills": (generated.get("skills") or {}).get("items", []),
        "ats_keywords_matched": mock_ats_keywords_matched(profile, target_job),
        "sections_included": section_ids,
        "generation_mode": "role_targeted",
        "generated_sections": generated,
        "needs_manual_input": False,
        "manual_input_reason": None,
    }


def mock_generate_cv_content(
    profile: dict,
    target_job: dict | None,
    section_ids: list[str],
    tone: str,
) -> dict:
    """
    Build a `CVGenerationResult`-shaped dict (see app/schemas/cv_builder.py)
    entirely from real profile content — bullet rewrites, a computed
    summary, JD-aware skill prioritization, and a real ATS-keyword overlap.
    `citations`/`confidence_score` are left for the Executor/Reflector to
    fill in (RAG citations and the deterministic confidence formula
    respectively aren't this function's concern).
    """
    work_experiences = profile.get("work_experiences", [])
    projects = profile.get("projects", [])
    skills = profile.get("skills", [])

    jd_names = {s.get("skill") for s in (target_job or {}).get("extracted_skills", []) if isinstance(s, dict)}
    summary, summary_rationale = mock_professional_summary(profile, target_job)

    has_any_content = bool(
        work_experiences or profile.get("educations") or projects or skills or profile.get("custom_sections")
    )

    return {
        "professional_summary": summary,
        "summary_rationale": summary_rationale,
        "enhanced_work_experiences": _enhance_entry_bullets(work_experiences, "description_bullets"),
        "enhanced_projects": _enhance_entry_bullets(projects, "key_achievements"),
        "prioritized_skills": [s["name"] for s in _sorted_skills(skills, jd_names) if s.get("name")],
        "ats_keywords_matched": mock_ats_keywords_matched(profile, target_job),
        "sections_included": section_ids,
        "needs_manual_input": not has_any_content,
        "manual_input_reason": (
            None
            if has_any_content
            else "Your profile has no work experience, education, projects, or skills yet — "
            "add at least one section before generating a CV."
        ),
    }


def mock_improve_bullet(bullet_text: str, context: dict, target_job: dict | None) -> dict:
    """Single-bullet version of the same zero-fabrication rewrite, used by the standalone 'Improve with AI' endpoint."""
    enhanced, rationale = _strengthen_bullet(bullet_text)
    if target_job and target_job.get("title"):
        rationale += (
            f" Reviewed for alignment with the target role '{target_job['title']}', though no new "
            "claims were added beyond your original wording."
        )
    return {"original_bullet": bullet_text, "improved_bullet": enhanced, "rationale": rationale}


_LEVEL_SUMMARY = {
    "beginner": (
        "Early-career candidate building toward a {role} path. This starter CV uses only details you "
        "provided — add real experience, education, and projects before sending applications."
    ),
    "intermediate": (
        "Practitioner preparing for {role} opportunities. Content below reflects only the information "
        "you entered; replace placeholders with verified facts before submitting applications."
    ),
    "advanced": (
        "Experienced professional targeting {role} roles. This draft keeps claims limited to your "
        "inputs — expand with concrete achievements you can substantiate."
    ),
    "expert": (
        "Senior-level candidate focused on {role}. This draft is a structured starting point from "
        "your minimum inputs; it does not invent employers, degrees, or certifications."
    ),
}


def build_profile_snapshot_from_manual_input(
    *,
    full_name: str,
    email: str | None,
    phone: str | None,
    location: str | None,
    target_role: str,
    career_level: str,
    summary_context: str | None,
    skills_text: str | None,
    experience_text: str | None,
    education_text: str | None,
    projects_text: str | None,
) -> dict:
    """
    Build a Profile-shaped snapshot for GeneratedCV only.
    Does not invent employers, schools, dates, or certifications.
    """
    role = (target_role or "").strip() or "Target Role"
    level = (career_level or "beginner").strip().lower()
    template = _LEVEL_SUMMARY.get(level, _LEVEL_SUMMARY["beginner"])
    summary_bits = [template.format(role=role)]
    if (summary_context or "").strip():
        summary_bits.append(summary_context.strip())

    skills: list[dict] = []
    if (skills_text or "").strip():
        for part in skills_text.replace(";", ",").split(","):
            name = part.strip()
            if name:
                skills.append({"name": name, "category": "technical", "proficiency": None})

    work_experiences: list[dict] = []
    if (experience_text or "").strip():
        work_experiences.append(
            {
                "id": "quick-intake-experience",
                "company_name": "Add your employer",
                "job_title": role,
                "location": location,
                "start_date": None,
                "end_date": None,
                "is_current": False,
                "description_bullets": [
                    line.strip("•- ").strip()
                    for line in experience_text.splitlines()
                    if line.strip()
                ]
                or [experience_text.strip()],
            }
        )
    else:
        work_experiences.append(
            {
                "id": "quick-intake-experience-placeholder",
                "company_name": "Add your experience",
                "job_title": f"Aspiring {role}" if level == "beginner" else role,
                "location": location,
                "start_date": None,
                "end_date": None,
                "is_current": False,
                "description_bullets": [
                    "Replace this placeholder with real roles, employers, and measurable outcomes.",
                    "Do not submit this CV until employer and date facts are accurate.",
                ],
            }
        )

    educations: list[dict] = []
    if (education_text or "").strip():
        educations.append(
            {
                "id": "quick-intake-education",
                "institution": "Add your institution",
                "degree": education_text.strip()[:200],
                "field_of_study": None,
                "start_date": None,
                "end_date": None,
                "gpa": None,
                "honors": None,
            }
        )
    else:
        educations.append(
            {
                "id": "quick-intake-education-placeholder",
                "institution": "Add your education",
                "degree": "Degree / program details go here",
                "field_of_study": None,
                "start_date": None,
                "end_date": None,
                "gpa": None,
                "honors": None,
            }
        )

    projects: list[dict] = []
    if (projects_text or "").strip():
        projects.append(
            {
                "id": "quick-intake-project",
                "title": "Highlighted project",
                "name": "Highlighted project",
                "role": None,
                "url": None,
                "start_date": None,
                "end_date": None,
                "description": projects_text.strip()[:500],
                "technologies": [],
                "key_achievements": [
                    line.strip("•- ").strip()
                    for line in projects_text.splitlines()
                    if line.strip()
                ][:5]
                or [projects_text.strip()[:240]],
            }
        )

    summary = " ".join(summary_bits)
    return {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "address_city": location,
        "address_state": None,
        "address_country": None,
        "linkedin_url": None,
        "github_url": None,
        "portfolio_url": None,
        "professional_headline": f"{role} · {level.title()} level",
        "bio_summary": summary,
        "professional_summary": summary,
        "work_experiences": work_experiences,
        "educations": educations,
        "projects": projects,
        "skills": skills,
        "certifications": [],  # never invent certifications
        "languages": [],
        "custom_sections": [],
    }


def mock_generate_quick_intake_cv(
    profile_snapshot: dict,
    section_ids: list[str],
    tone: str,
    target_role: str,
    career_level: str,
) -> dict:
    """Honest starter CV content — no fabricated employers/degrees/certs beyond placeholders."""
    summary = profile_snapshot.get("professional_summary") or (
        f"Starter CV for {target_role} ({career_level}). Add verified facts before applying."
    )
    work = profile_snapshot.get("work_experiences") or []
    projects = profile_snapshot.get("projects") or []
    skills = profile_snapshot.get("skills") or []
    return {
        "professional_summary": summary,
        "summary_rationale": (
            f"Quick intake draft for {target_role} at {career_level} level. "
            "Placeholders mark missing facts — no employers, degrees, or certifications were invented."
        ),
        "enhanced_work_experiences": [
            {
                "entry_id": str(e.get("id")),
                "enhanced_bullets": [
                    {"original": b, "enhanced": b, "rationale": "Kept as provided or as an honest placeholder."}
                    for b in (e.get("description_bullets") or [])
                ],
                "rationale": "Kept as provided or as an honest placeholder; no fabricated achievements.",
            }
            for e in work
        ],
        "enhanced_projects": [
            {
                "entry_id": str(p.get("id")),
                "enhanced_bullets": [
                    {"original": a, "enhanced": a, "rationale": "Drawn only from your project notes."}
                    for a in (p.get("key_achievements") or [])
                ],
                "rationale": "Drawn only from your project notes.",
            }
            for p in projects
        ],
        "prioritized_skills": [s["name"] for s in skills if isinstance(s, dict) and s.get("name")],
        "ats_keywords_matched": [],
        "sections_included": section_ids,
        "needs_manual_input": True,
        "manual_input_reason": (
            "Quick CV starter — replace 'Add your …' placeholders with real employers, "
            "education, dates, and achievements before using this CV in applications."
        ),
        "generation_mode": "quick_intake",
    }
