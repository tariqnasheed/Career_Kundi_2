"""
agents/cv_builder/agents.py
===============================
The two Guardrail -> Planner -> Executor -> Reflector agent quartets for
this feature (§4.3):

1. CV generation — CVBuilderGuardrailAgent, CVPlannerAgent,
   CVBulletWriterExecutorAgent, CVReflectorAgent.
2. Single-bullet improvement ("Improve with AI" on one Profile entry) —
   BulletImprovementGuardrailAgent, BulletImprovementPlannerAgent,
   BulletImprovementExecutorAgent, BulletImprovementReflectorAgent.

Both share `_check_bullet_fabrication()`, the deterministic safety net that
makes the platform's "never invent a fact" rule concrete for this feature:
it diffs every NEW number and capitalized term in an "enhanced" bullet
against an "allowed corpus" built from the user's own real input, and flags
anything that doesn't trace back to something the user actually wrote.

Both Reflectors also override `render_for_review()` to strip digits out of
the text handed to the BASE class's generic `check_unsupported_claims()`
heuristic. That heuristic assumes RAG-grounded prose, where every number
should trace to a `[n]` citation — exactly backwards for a CV, where the
numbers ARE the user's own verified facts (a "20% revenue increase" bullet
needs no citation, it needs to be true to the user's profile, which is what
`_check_bullet_fabrication` verifies instead, far more precisely). Citation
integrity and generic-boilerplate-language checks are still run normally —
they're a good fit for any feature's output, CV included.
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.common.base import BaseAgent
from app.agents.common.cost_monitor import CostMonitor
from app.agents.common.guardrail import BaseGuardrailAgent
from app.agents.common.prompts import build_system_prompt
from app.agents.common.reflector import BaseReflectorAgent
from app.core.config import settings
from app.schemas.cv_builder import CVGenerationResult
from app.tools.llm import PromptSpec, get_llm
from app.tools.rag import citations_from_documents, format_context_for_prompt, retrieve

from . import mock_data

_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?%?")


def _check_bullet_fabrication(original: str, enhanced: str, allowed_corpus: str) -> list[str]:
    """
    Deterministic fabrication check, shared by both Reflectors below.

    - Any number/percent in `enhanced` that doesn't appear in `original` OR
      `allowed_corpus` is flagged — a rewrite can never introduce a metric
      the user never stated, even one that "sounds plausible."
    - Any capitalized word in `enhanced` (skipping the sentence's first
      word, which is ALWAYS capitalized by English sentence casing
      regardless of meaning — including the verb-strengthening table's own
      replacements like "Drove"/"Owned"/"Led") that isn't found anywhere in
      `original` or `allowed_corpus` is flagged as a possible invented
      proper noun (a fabricated client, tool, or company name).
    """
    issues: list[str] = []
    enhanced_numbers = set(_NUMBER_PATTERN.findall(enhanced))
    known_numbers = set(_NUMBER_PATTERN.findall(original)) | set(_NUMBER_PATTERN.findall(allowed_corpus))
    novel_numbers = enhanced_numbers - known_numbers
    if novel_numbers:
        issues.append(
            f"Enhanced bullet introduces number(s) {sorted(novel_numbers)} that don't appear "
            "anywhere in your original profile content."
        )

    lower_corpus = allowed_corpus.lower()
    lower_original = original.lower()
    words = enhanced.split()
    invented_terms = set()
    for idx, word in enumerate(words):
        if idx == 0:
            continue
        cleaned = word.strip(".,;:()[]\"'")
        if len(cleaned) > 2 and cleaned[0].isupper() and cleaned.lower() not in lower_corpus and cleaned.lower() not in lower_original:
            invented_terms.add(cleaned)
    if invented_terms:
        issues.append(
            f"Enhanced bullet introduces capitalized term(s) {sorted(invented_terms)} not found "
            "in your original profile content — possible fabrication."
        )
    return issues


def _strip_digits(text: str) -> str:
    return _NUMBER_PATTERN.sub("", text)


# === 1. CV generation quartet ===========================================================

_CV_WRITER_ROLE = """
You are the CV Builder agent for Careerkundi. You transform a candidate's
full profile data into polished CV content: a professional summary,
stronger-worded bullet points, and a prioritized skill list. You write
ONLY in the voice of a resume-writing expert improving phrasing, never as
someone adding new accomplishments.
""".strip()

_FABRICATION_DIRECTIVE = """
This is a CV — every bullet, number, and claim must come directly from the
candidate's own profile data provided to you. NEVER invent a metric,
percentage, client name, company name, or outcome that is not explicitly
present in the input profile JSON. If a bullet has no quantifiable result
in the original, improve its phrasing and impact WITHOUT adding a
fabricated number — strong action verbs and concision are enough.
Reordering and prioritizing real skills based on the target job's
requirements is encouraged; inventing a skill the candidate doesn't list is
not.
""".strip()

_ROLE_TARGETED_WRITER_ROLE = """
You are the CV Builder agent for Careerkundi. The candidate wants a CV
written for a DIFFERENT target role than their saved profile emphasizes.
Using their profile only as background context, you fully author every
ENABLED section's content so it reads as a credible CV for the requested
target role. Section toggles control inclusion only — you decide the wording,
structure, and emphasis inside each enabled section.
""".strip()

_ROLE_TARGETED_DIRECTIVE = """
Generate complete, professional CV content for the target role described.
Use the candidate's profile as grounding context where helpful (real names,
contact info, education dates) but rewrite experience bullets, skills, and
summary to align with the target role. Plausible, role-appropriate
achievements and skills are expected — this is aspirational CV drafting,
not a verbatim copy of the saved profile. Return content only for the
sections listed in sections_included; omit disabled sections entirely.
""".strip()

_CV_RESULT_SCHEMA = CVGenerationResult.model_json_schema()

_SECTION_PRESENCE_CHECKS: dict[str, str] = {
    "summary": "professional_headline",
    "experience": "work_experiences",
    "education": "educations",
    "skills": "skills",
    "projects": "projects",
    "certifications": "certifications",
    "publications": "publications",
    "languages": "languages",
    "volunteer": "volunteer_entries",
    "awards": "awards",
    "references": "references",
    "custom": "custom_sections",
}

_ALL_SECTION_IDS = list(_SECTION_PRESENCE_CHECKS.keys())


def _available_sections(profile: dict) -> list[str]:
    """Which CV sections actually have real data behind them — drives both the Planner's default selection and the §4.3 'Dynamic Section Toggles' UI."""
    available: list[str] = []
    has_summary_material = bool(
        profile.get("professional_headline") or profile.get("bio_summary") or profile.get("work_experiences")
    )
    if has_summary_material:
        available.append("summary")
    for section_id, profile_field in _SECTION_PRESENCE_CHECKS.items():
        if section_id == "summary":
            continue
        if profile.get(profile_field):
            available.append(section_id)
    return available


class CVBuilderGuardrailAgent(BaseGuardrailAgent):
    name = "CVBuilderGuardrailAgent"
    input_field = "raw_input"

    async def extra_checks(self, state: dict, sanitized_input: str) -> list[str]:
        if not state.get("profile_snapshot"):
            return ["No profile data was provided — cannot generate a CV from nothing."]
        if state.get("generation_mode") == "role_targeted" and not (state.get("target_role_title") or "").strip():
            return ["A target role title is required for role-targeted CV generation."]
        if state.get("generation_mode") == "quick_intake" and not (state.get("target_role_title") or "").strip():
            return ["A target role is required for quick CV intake."]
        return []


class CVPlannerAgent(BaseAgent):
    name = "CVPlannerAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict) -> dict:
        profile = state["profile_snapshot"]
        target_job = state.get("target_job_snapshot")
        requested = state.get("requested_section_ids")
        generation_mode = state.get("generation_mode", "profile")

        if generation_mode == "role_targeted":
            default_sections = [s for s in _ALL_SECTION_IDS if s != "custom"]
            section_ids = [s for s in (requested or default_sections) if s in _ALL_SECTION_IDS]
        elif generation_mode == "quick_intake":
            default_sections = ["summary", "experience", "education"]
            available = set(_available_sections(profile))
            if "skills" in available:
                default_sections.append("skills")
            if "projects" in available:
                default_sections.append("projects")
            section_ids = [s for s in (requested or default_sections) if s in _ALL_SECTION_IDS]
        else:
            available = _available_sections(profile)
            section_ids = [s for s in requested if s in available] if requested else available

        profile_chars = len(mock_data.profile_text_blob(profile))
        job_chars = len((target_job or {}).get("description_raw") or "")
        role_chars = len(state.get("target_role_description") or "")
        tier = self.cost_monitor.recommend_tier(
            input_length_chars=profile_chars + job_chars + role_chars,
            force_pro=bool(target_job) or generation_mode == "role_targeted",
        )

        jd_keywords = [
            entry.get("skill")
            for entry in (target_job or {}).get("extracted_skills", [])
            if isinstance(entry, dict) and entry.get("skill")
        ]

        plan = {
            "tier": tier,
            "retrieval_k": 6,
            "retrieval_category": "career_advice",
            "available_section_ids": (
                section_ids
                if generation_mode in ("role_targeted", "quick_intake")
                else _available_sections(profile)
            ),
            "section_ids": section_ids,
            "jd_keywords": jd_keywords,
            "generation_mode": generation_mode,
        }
        return {"plan": plan}


class CVBulletWriterExecutorAgent(BaseAgent):
    name = "CVBulletWriterAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict) -> dict:
        profile = state["profile_snapshot"]
        target_job = state.get("target_job_snapshot")
        plan = state["plan"]
        tone = state.get("tone", "concise")
        revision_issues = state.get("reflection_issues") or []
        generation_mode = plan.get("generation_mode", state.get("generation_mode", "profile"))

        retrieved = retrieve(
            "resume bullet writing ATS keyword quantified achievements action verbs",
            k=plan["retrieval_k"],
            category=plan["retrieval_category"],
        )
        context = format_context_for_prompt(retrieved)
        citations = citations_from_documents(retrieved)
        tier = plan["tier"]

        if settings.llm_mode == "mock" or generation_mode == "quick_intake":
            # quick_intake always uses the honest deterministic starter so local
            # Ollama cannot invent employers, degrees, or certifications.
            if generation_mode == "quick_intake":
                draft = mock_data.mock_generate_quick_intake_cv(
                    profile,
                    plan["section_ids"],
                    tone,
                    state.get("target_role_title") or "Target Role",
                    state.get("career_level") or "beginner",
                )
            elif generation_mode == "role_targeted":
                draft = mock_data.mock_generate_role_targeted_cv_content(
                    profile,
                    state.get("target_role_title") or "",
                    state.get("target_role_description"),
                    target_job,
                    plan["section_ids"],
                    tone,
                )
            else:
                draft = mock_data.mock_generate_cv_content(profile, target_job, plan["section_ids"], tone)
            draft["generation_mode"] = generation_mode
        else:
            llm = get_llm(tier)
            if generation_mode == "role_targeted":
                user_prompt = (
                    f"Numbered resume-writing best-practice context:\n{context}\n\n"
                    f"Tone requested: {tone}\n"
                    f"Sections to include (generate full content for each): {plan['section_ids']}\n"
                    f"Target role title: {state.get('target_role_title')}\n"
                    f"Target role description / JD context:\n{state.get('target_role_description') or '(none)'}\n\n"
                    f"Candidate profile for grounding (JSON):\n{profile}\n\n"
                    f"Saved target job, if any (JSON):\n{target_job or {}}\n\n"
                    "Return generated_sections with keys matching each section_id in sections_included. "
                    "summary uses {\"content\": \"...\"}; experience/projects/education/certifications/etc. use "
                    "{\"entries\": [...]}; skills uses {\"items\": [...]}."
                )
                role_directive = _ROLE_TARGETED_DIRECTIVE
                writer_role = _ROLE_TARGETED_WRITER_ROLE
            else:
                user_prompt = (
                    f"Numbered resume-writing best-practice context:\n{context}\n\n"
                    f"Tone requested: {tone}\n"
                    f"Sections to include: {plan['section_ids']}\n"
                    f"JD keywords to prioritize, if any: {plan['jd_keywords']}\n\n"
                    f"Full candidate profile (JSON):\n{profile}\n\n"
                    f"Target job (JSON, may be empty if no specific role was selected):\n{target_job or {}}"
                )
                role_directive = _FABRICATION_DIRECTIVE
                writer_role = _CV_WRITER_ROLE
            if revision_issues:
                user_prompt += (
                    "\n\nThe previous draft had these issues — fix them:\n"
                    + "\n".join(f"- {issue}" for issue in revision_issues)
                )
            spec = PromptSpec(
                system_prompt=build_system_prompt(writer_role, extra_directives=role_directive),
                user_prompt=user_prompt,
                json_schema=_CV_RESULT_SCHEMA,
                temperature=0.4 if generation_mode == "role_targeted" else 0.3,
                max_output_tokens=8192,
            )
            response = await llm.generate(spec)
            self.cost_monitor.record(response, tier=tier)
            draft = response.parsed_json or {}
            draft["sections_included"] = plan["section_ids"]
            draft["generation_mode"] = generation_mode

        draft["citations"] = citations
        return {"draft_output": draft, "citations": citations, "retrieved_context": context, "model_tier_used": tier}


class CVReflectorAgent(BaseReflectorAgent):
    name = "CVReflectorAgent"
    output_field = "draft_output"
    max_revisions = 2

    def render_for_review(self, draft: Any) -> str:
        if not isinstance(draft, dict):
            return super().render_for_review(draft)
        parts = [draft.get("professional_summary", "")]
        for group_key in ("enhanced_work_experiences", "enhanced_projects"):
            for entry in draft.get(group_key) or []:
                for bullet in entry.get("enhanced_bullets") or []:
                    parts.append(bullet.get("enhanced", ""))
        parts.extend(draft.get("prioritized_skills") or [])
        text = " ".join(str(part) for part in parts)
        # See module docstring: numbers here are the user's own facts, not
        # retrieval-grounded claims, so they're excluded from the generic
        # citation-required heuristic. `domain_checks` below verifies them
        # against the original profile instead — a much more precise check.
        return _strip_digits(text)

    async def domain_checks(self, state: dict, draft: Any) -> list[str]:
        if not isinstance(draft, dict):
            return ["Draft output is not a structured object."]

        issues: list[str] = []
        generation_mode = draft.get("generation_mode", state.get("generation_mode", "profile"))
        plan = state.get("plan") or {}
        requested_sections = set(plan.get("section_ids") or [])
        draft_sections = set(draft.get("sections_included") or [])
        missing_sections = requested_sections - draft_sections
        if missing_sections:
            issues.append(f"Output is missing requested section(s): {sorted(missing_sections)}")

        if generation_mode == "role_targeted":
            generated = draft.get("generated_sections") or {}
            for section_id in requested_sections:
                if section_id not in generated:
                    issues.append(f"Role-targeted draft is missing generated content for section '{section_id}'.")
                elif section_id == "summary" and not (generated.get("summary") or {}).get("content"):
                    issues.append("Role-targeted summary section is empty.")
                elif section_id == "skills" and not (generated.get("skills") or {}).get("items"):
                    issues.append("Role-targeted skills section is empty.")
            return issues

        if generation_mode == "quick_intake":
            if not draft.get("professional_summary"):
                issues.append("Quick intake draft is missing a professional summary.")
            if "experience" in requested_sections and not draft.get("enhanced_work_experiences"):
                issues.append("Quick intake draft is missing experience placeholders.")
            return issues

        profile = state.get("profile_snapshot") or {}
        allowed_corpus = mock_data.profile_text_blob(profile)

        if not draft.get("professional_summary") and not draft.get("needs_manual_input"):
            issues.append("Missing a professional summary.")

        for group_key in ("enhanced_work_experiences", "enhanced_projects"):
            for entry in draft.get(group_key) or []:
                for bullet in entry.get("enhanced_bullets") or []:
                    issues.extend(
                        _check_bullet_fabrication(
                            bullet.get("original", ""), bullet.get("enhanced", ""), allowed_corpus
                        )
                    )

        real_skill_names = {(s.get("name") or "").lower() for s in profile.get("skills", [])}
        invented_skills = [
            skill for skill in draft.get("prioritized_skills") or [] if skill.lower() not in real_skill_names
        ]
        if invented_skills:
            issues.append(f"Prioritized skills include name(s) not present in your profile: {invented_skills}")

        return issues


# === 2. Bullet improvement quartet ("Improve with AI") ==================================

_BULLET_ROLE = """
You are the Careerkundi resume bullet improvement assistant. Given ONE
bullet point and its role context, you rewrite it to be more impactful —
stronger verbs, tighter phrasing, better ATS keyword alignment — while
preserving every fact exactly as given.
""".strip()

_BULLET_RESULT_SCHEMA = {
    "title": "BulletImprovement",
    "type": "object",
    "properties": {
        "improved_bullet": {"type": "string"},
        "rationale": {"type": "string"},
    },
    "required": ["improved_bullet", "rationale"],
}


class BulletImprovementGuardrailAgent(BaseGuardrailAgent):
    name = "BulletImprovementGuardrailAgent"
    input_field = "raw_input"

    async def extra_checks(self, state: dict, sanitized_input: str) -> list[str]:
        if not isinstance(sanitized_input, str) or len(sanitized_input.strip()) < 3:
            return ["Bullet text is too short to improve."]
        return []


class BulletImprovementPlannerAgent(BaseAgent):
    name = "BulletImprovementPlannerAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict) -> dict:
        target_job = state.get("target_job_snapshot")
        tier = self.cost_monitor.recommend_tier(
            input_length_chars=len(state.get("bullet_text", "")),
            force_pro=bool(target_job),
        )
        plan = {"tier": tier, "retrieval_k": 3, "retrieval_category": "career_advice"}
        return {"plan": plan}


class BulletImprovementExecutorAgent(BaseAgent):
    name = "BulletImprovementAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict) -> dict:
        bullet_text = state["bullet_text"]
        context = state.get("bullet_context", {})
        target_job = state.get("target_job_snapshot")
        plan = state["plan"]
        revision_issues = state.get("reflection_issues") or []

        retrieved = retrieve(
            "resume bullet writing ATS keyword quantify achievements action verbs",
            k=plan["retrieval_k"],
            category=plan["retrieval_category"],
        )
        rag_context = format_context_for_prompt(retrieved)
        citations = citations_from_documents(retrieved)
        tier = plan["tier"]

        if settings.llm_mode == "mock":
            result = mock_data.mock_improve_bullet(bullet_text, context, target_job)
        else:
            llm = get_llm(tier)
            user_prompt = (
                f"Numbered resume-writing best-practice context:\n{rag_context}\n\n"
                f"Bullet to improve: {bullet_text}\n"
                f"Role context: {context}\n"
                f"Target job, may be empty: {target_job or {}}"
            )
            if revision_issues:
                user_prompt += (
                    "\n\nFix these issues — never invent a new fact or number:\n"
                    + "\n".join(f"- {issue}" for issue in revision_issues)
                )
            spec = PromptSpec(
                system_prompt=build_system_prompt(_BULLET_ROLE, extra_directives=_FABRICATION_DIRECTIVE),
                user_prompt=user_prompt,
                json_schema=_BULLET_RESULT_SCHEMA,
                temperature=0.3,
            )
            response = await llm.generate(spec)
            self.cost_monitor.record(response, tier=tier)
            parsed = response.parsed_json or {}
            result = {
                "original_bullet": bullet_text,
                "improved_bullet": parsed.get("improved_bullet", bullet_text),
                "rationale": parsed.get("rationale", ""),
            }

        return {"draft_output": result, "citations": citations, "retrieved_context": rag_context, "model_tier_used": tier}


class BulletImprovementReflectorAgent(BaseReflectorAgent):
    name = "BulletImprovementReflectorAgent"
    output_field = "draft_output"
    max_revisions = 2

    def render_for_review(self, draft: Any) -> str:
        if not isinstance(draft, dict):
            return super().render_for_review(draft)
        return _strip_digits(draft.get("improved_bullet", ""))

    async def domain_checks(self, state: dict, draft: Any) -> list[str]:
        if not isinstance(draft, dict) or not draft.get("improved_bullet"):
            return ["No improved bullet was generated."]
        original = state.get("bullet_text", "")
        # No broader profile context in this lightweight, single-bullet
        # pipeline — the bullet's own original wording is the entire
        # "allowed corpus" here, which is correctly stricter than the
        # full-CV pipeline above.
        return _check_bullet_fabrication(original, draft["improved_bullet"], original)
