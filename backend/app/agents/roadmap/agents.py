"""
agents/roadmap/agents.py
=============================
Concrete agents for the Career Roadmap feature (§4.5): the full generation
pipeline's nine nodes (Guardrail, Planner, RoleTaxonomy, SkillDecomposer,
ResourceFinder, StudyMaterial, PracticeGenerator, TimelineOptimizer,
Reflector) plus the lightweight single-skill refresh pipeline's four nodes.

Every node that needs real-world data calls through the same tool
chokepoints every other feature uses — `tools/graph_rag.py` for skill/role
traversal, `tools/rag.py` for grounded study material, `tools/search.py`
for learning-resource discovery — and every node that needs generative text
follows the platform-wide live/mock split: `settings.llm_mode == "mock"`
routes through the content-aware builders in `mock_data.py`, anything else
calls `get_llm()` with a JSON schema. RoleTaxonomyAgent, ResourceFinderAgent,
StudyMaterialAgent, and PracticeGeneratorAgent are all genuinely
LLM/tool-calling stages; SkillDecomposerAgent and TimelineOptimizerAgent are
deterministic (no LLM call in either mode) but remain real graph nodes
because §4.5 names both as distinct conceptual stages of roadmap generation.
"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.documents import Document

from app.agents.common.base import BaseAgent
from app.agents.common.cost_monitor import CostMonitor
from app.agents.common.guardrail import BaseGuardrailAgent
from app.agents.common.prompts import build_system_prompt
from app.agents.common.reflector import BaseReflectorAgent
from app.core.config import settings
from app.schemas.roadmap import RoadmapPracticeActivities, RoadmapStudyMaterial
from app.tools.graph_rag import (
    add_skill_resource_edge,
    ensure_role_node,
    get_industries_for_role,
    get_prerequisites,
    get_related_skills,
    get_skills_for_role,
)
from app.tools.llm import PromptSpec, get_llm
from app.tools.rag import retrieve
from app.tools.search import get_search_provider

from app.core.logging import get_logger

from . import mock_data
from .content_quality import normalize_practice_activities, normalize_study_material

logger = get_logger(__name__)

_IMPORTANCE_ORDER = {"critical": 0, "high": 1, "medium": 2, "nice-to-have": 3}


async def _fetch_skill_resources(
    skill_name: str, target_role: str = "", *, num_results: int = 3
) -> list[dict[str, Any]]:
    """Fetch learning resources for a skill without ever crashing the pipeline.

    Live web search (SerpAPI) can fail — rate limits (429), no key, network
    errors — and previously any such failure raised straight out of the
    resource step and aborted ALL content generation for the skill, leaving the
    user with an empty study card. This helper isolates that: on any failure, or
    when search returns nothing, it falls back to deterministic curated
    resources so the Resources section is always populated and, crucially, study
    material / flashcards / quizzes / projects are never lost to a search error.
    """
    try:
        provider = get_search_provider()
        results = await provider.search(
            f"{skill_name} tutorial learning resource", num_results=num_results
        )
    except Exception as exc:  # noqa: BLE001 — degrade gracefully, never abort content
        logger.warning("roadmap_resource_search_failed", skill=skill_name, error=str(exc))
        results = []

    resources: list[dict[str, Any]] = []
    for r in results:
        resources.append(
            {
                "title": r.title,
                "url": r.url,
                "resource_type": mock_data.resource_type_for_url(r.url),
                "source": r.url,
                "verified": r.verified,
            }
        )
        if r.verified and r.url and r.url.startswith("http"):
            try:
                add_skill_resource_edge(r.title, r.url, skill_name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("roadmap_resource_edge_failed", skill=skill_name, error=str(exc))

    if not resources:
        resources = mock_data.curated_resources(skill_name, target_role)
    return resources


def _register_citation(citations: list[dict], *, title: str, source: str) -> int:
    """
    Append a new citation to the shared registry, or return the existing
    marker number if this exact `source` was already cited earlier in this
    same roadmap generation. Roadmap content is built skill-by-skill across
    several nodes, so without a shared, globally-numbered registry each
    skill's RAG retrieval would re-use `[1]`, `[2]`, ... independently,
    breaking `reflector.py::check_citation_integrity`'s assumption that
    every `[n]` marker in the FINAL rendered draft maps to one shared,
    globally-numbered citation list.
    """
    for entry in citations:
        if entry.get("source") == source:
            return entry["n"]
    n = len(citations) + 1
    citations.append({"n": n, "title": title, "source": source})
    return n


def _grounded_context_block(documents: list[Document], citations: list[dict]) -> str:
    """Format retrieved documents into a numbered context block whose `[n]` markers are the SAME global registry numbers `_register_citation` hands out, not a locally re-numbered 1..k block."""
    lines = []
    for doc in documents:
        marker = _register_citation(citations, title=doc.metadata.get("title", "Untitled"), source=doc.metadata.get("source", ""))
        lines.append(f"[{marker}] Source: {doc.metadata.get('source', 'unknown source')}\n{doc.page_content.strip()}")
    return "\n\n".join(lines)


_STUDY_MATERIAL_ROLE = """
You are Careerkundi's Career Roadmap Study Material author. Act as a patient
PhD-level scholar and master teacher who can make ANY skill in ANY educational
field understandable to a complete beginner and useful all the way to advanced
practice.

Given one skill name, the target role it supports, and numbered skill-taxonomy
context, teach that exact skill. Produce:
- a clear, specific overview (never empty, never a refusal);
- why_it_matters for the target role;
- prerequisites (what to know first, kept beginner-friendly);
- learning_objectives laddered by Bloom's taxonomy (remember -> understand ->
  apply -> analyse -> evaluate -> create);
- three tiered explanations: beginner_explanation, intermediate_explanation,
  advanced_explanation;
- key_concepts and concepts (term + plain-language definition);
- a concrete worked_example;
- common_mistakes and short revision_notes.

Adapt the content to the skill's real field (engineering, healthcare, data,
business, creative, trades, science, education, finance, ...). Be concrete and
specific to the actual skill and role — no generic filler. Ground factual claims
in the provided context using the EXACT [n] citation markers shown. If the
context doesn't cover this skill, still teach it from established fundamentals,
but do not invent statistics, sources, or citations.
""".strip()

_PRACTICE_ROLE = """
You are Careerkundi's Career Roadmap Practice author. Act as a patient master
teacher building active, effective practice for one skill, grounded in learning
science (active recall, spaced repetition, assessment gateways, project-based
learning).

Given a skill name, the target role, and sibling skills, produce:
- exercises: several concrete, do-able practice tasks;
- flashcards: active-recall cards (front prompt -> back answer);
- quizzes: multiple-choice check questions, each with options, the correct
  answer_index, and a short explanation;
- projects: a few hands-on project briefs at increasing difficulty
  (beginner -> intermediate -> advanced) with steps and a deliverable;
- self_assessment_questions and reflection_questions (synthesis / self-evaluation).

Everything must be specific to the real skill and role, and useful for a learner
who is starting from scratch but wants to reach interview-ready. Never return
empty lists, generic filler, or invented facts/metrics.
""".strip()

_ROLE_TAXONOMY_ROLE = """
You are the Role Taxonomy agent for Careerkundi's Career Roadmap feature.
Given a target role title with no entry in the internal skills taxonomy,
infer the realistic set of skills someone in that role needs, each tagged
with an importance level (critical, high, medium, or nice-to-have) based on
how central it typically is to the role in practice.
""".strip()

_ROLE_SKILLS_SCHEMA = {
    "title": "RoleTaxonomySkills",
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"skill": {"type": "string"}, "importance": {"type": "string"}},
                "required": ["skill", "importance"],
            },
        }
    },
    "required": ["skills"],
}


# --- Main roadmap generation pipeline --------------------------------------------------


class RoadmapGuardrailAgent(BaseGuardrailAgent):
    name = "RoadmapGuardrailAgent"
    input_field = "raw_input"

    async def extra_checks(self, state: dict[str, Any], sanitized_input: Any) -> list[str]:
        if not isinstance(sanitized_input, str) or len(sanitized_input.strip()) < 5:
            return ["Roadmap request is missing a usable target role."]
        if not (state.get("target_role") or "").strip():
            return ["No target role was provided."]
        return []


class RoadmapPlannerAgent(BaseAgent):
    """Decides model tier from how much real input there is to ground generation in (a longer `additional_context` warrants the stronger tier)."""

    name = "RoadmapPlannerAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        additional_context = (state.get("personalization_inputs") or {}).get("additional_context") or ""
        input_len = len(state.get("target_role", "")) + len(additional_context)
        tier = self.cost_monitor.recommend_tier(input_length_chars=input_len)
        return {"plan": {"tier": tier}}


class RoleTaxonomyAgent(BaseAgent):
    """
    Resolves the target role against the GraphRAG skill taxonomy
    (`get_skills_for_role`). When the role isn't in the static seed graph
    (a "novel" role), infers a realistic skill set instead — via real
    keyword-pattern matching in mock mode, or an LLM call in live mode —
    and grows the graph with `ensure_role_node` so future traversal queries
    (and other users targeting the same role) benefit from it too.
    """

    name = "RoleTaxonomyAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        target_role = state["target_role"].strip()
        plan = state.get("plan") or {}
        tier = plan.get("tier", "flash")
        additional_context = (state.get("personalization_inputs") or {}).get("additional_context") or ""

        graph_skills = get_skills_for_role(target_role)
        is_novel = not graph_skills
        used_llm = False

        if not is_novel:
            required_skills = [
                {"skill": s["skill"], "importance": s.get("importance", "medium")} for s in graph_skills
            ]
        elif settings.llm_mode == "mock":
            required_skills = mock_data.infer_required_skills(target_role, additional_context)
        else:
            used_llm = True
            try:
                llm = get_llm(tier)
                spec = PromptSpec(
                    system_prompt=build_system_prompt(_ROLE_TAXONOMY_ROLE),
                    user_prompt=f"Target role: {target_role}\nAdditional context: {additional_context or 'none provided'}",
                    json_schema=_ROLE_SKILLS_SCHEMA,
                    temperature=0.3,
                )
                response = await llm.generate(spec)
                self.cost_monitor.record(response, tier=tier)
                required_skills = (response.parsed_json or {}).get("skills") or mock_data.infer_required_skills(
                    target_role, additional_context
                )
            except Exception:
                # Live LLM outage must not persist empty roadmaps (ROAD-F4 checkpoint).
                used_llm = False
                required_skills = mock_data.infer_required_skills(target_role, additional_context)

        if is_novel:
            # Grow the persistent knowledge graph with this role so it's no
            # longer "novel" the next time anyone (this user or another)
            # targets it — the heuristic/LLM-derived skill set becomes real
            # traversable graph structure, not just this run's output.
            ensure_role_node(target_role, skills=[s["skill"] for s in required_skills])

        industries = get_industries_for_role(target_role)
        role_taxonomy = {
            "canonical_role": target_role,
            "is_novel_role": is_novel,
            "industries": industries,
            "required_skills": required_skills,
        }
        result: dict[str, Any] = {"role_taxonomy": role_taxonomy}
        if used_llm:
            result["model_tier_used"] = tier
        return result


class SkillDecomposerAgent(BaseAgent):
    """
    Turns the role taxonomy's required-skill list into the roadmap's actual
    working skill set: pulls in any GraphRAG-known prerequisite skills the
    user doesn't already have (`get_prerequisites`), marks skills already
    present on the user's profile as already-known (`status="completed"`,
    zero estimated hours, no generated content needed), attaches lateral
    connections (`get_related_skills`), and de-duplicates — deterministic,
    no LLM call, but a real distinct pipeline stage per §4.5.
    """

    name = "SkillDecomposerAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        required = (state.get("role_taxonomy") or {}).get("required_skills") or []
        known = {s.strip().lower() for s in state.get("existing_profile_skills") or []}
        starting_level = state.get("starting_skill_level")

        importance_by_skill: dict[str, str] = {}
        order: list[str] = []
        for item in required:
            name = item["skill"]
            if name not in order:
                order.append(name)
            importance_by_skill[name] = item.get("importance", "medium")

        # Pull in prerequisite skills the user doesn't already have — e.g.
        # requiring "Machine Learning" without "Statistics" already known
        # inserts "Statistics" as its own milestone skill rather than
        # silently assuming the learner already has it.
        for name in list(order):
            for prereq in get_prerequisites(name):
                if prereq.strip().lower() in known or prereq in importance_by_skill:
                    continue
                order.insert(order.index(name), prereq)
                importance_by_skill[prereq] = "high"

        seen_lower: set[str] = set()
        deduped_order: list[str] = []
        for name in order:
            key = name.strip().lower()
            if key in seen_lower:
                continue
            seen_lower.add(key)
            deduped_order.append(name)

        skills: list[dict[str, Any]] = []
        for name in deduped_order:
            already_known = name.strip().lower() in known
            importance = importance_by_skill.get(name, "medium")
            skills.append(
                {
                    "skill_name": name,
                    "importance": importance,
                    "estimated_hours": 0.0 if already_known else mock_data.estimate_base_hours(importance, starting_level),
                    "status": "completed" if already_known else "not_started",
                    "resources": [],
                    "study_material": {},
                    "practice_activities": {},
                    "lateral_connections": get_related_skills(name),
                    "already_known": already_known,
                }
            )

        return {"roadmap_skills": skills}


class ResourceFinderAgent(BaseAgent):
    """
    Finds learning resources for every skill the user doesn't already know,
    via the same search-provider chokepoint every other feature uses
    (`tools/search.py` — live SerpAPI or honest, clearly-`verified=False`
    mock results). Genuinely-verified resources also grow the knowledge
    graph (`add_skill_resource_edge`), per that helper's own docstring
    naming this agent as its intended caller.
    """

    name = "ResourceFinderAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        skills = state.get("roadmap_skills") or []
        target_role = state.get("target_role", "")

        updated: list[dict[str, Any]] = []
        for skill in skills:
            if skill.get("already_known"):
                updated.append(skill)
                continue

            resources = await _fetch_skill_resources(skill["skill_name"], target_role)
            updated.append({**skill, "resources": resources})

        return {"roadmap_skills": updated}


class StudyMaterialAgent(BaseAgent):
    """RAG-grounded study overview + key concepts for every skill the user doesn't already know."""

    name = "StudyMaterialAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        skills = state.get("roadmap_skills") or []
        plan = state.get("plan") or {}
        tier = plan.get("tier", "flash")
        target_role = state["target_role"]
        citations: list[dict] = list(state.get("citations") or [])
        used_llm = False

        updated: list[dict[str, Any]] = []
        for skill in skills:
            name = skill["skill_name"]
            if skill.get("already_known"):
                # Fill short review content so the skill modal is not a blank card.
                study_material = normalize_study_material(
                    {
                        "overview": (
                            f"You marked {name} as already known for a {target_role} path. "
                            f"Use this as optional review — foundational/local-generated, "
                            f"not independently source-verified."
                        ),
                        "key_concepts": [
                            f"Refresh the day-to-day use of {name} in a {target_role} role",
                            f"Spot gaps between 'I know {name}' and interview-ready examples",
                        ],
                        "estimated_reading_time_minutes": 3,
                    },
                    name,
                    target_role,
                )
                updated.append({**skill, "study_material": study_material})
                continue

            retrieved = retrieve(name, k=2, category="skill_taxonomy")

            if settings.llm_mode == "mock":
                marker = None
                source_sentence = None
                if retrieved:
                    doc = retrieved[0]
                    marker = _register_citation(
                        citations, title=doc.metadata.get("title", "Untitled"), source=doc.metadata.get("source", "")
                    )
                    source_sentence = re.split(r"(?<=[.!?])\s+", doc.page_content.strip())[0]
                study_material = normalize_study_material(
                    None,
                    name,
                    target_role,
                    source_sentence=source_sentence,
                    citation_marker=marker,
                )
            else:
                used_llm = True
                context = (
                    _grounded_context_block(retrieved, citations)
                    if retrieved
                    else "(no matching material retrieved for this skill)"
                )
                llm = get_llm(tier)
                spec = PromptSpec(
                    system_prompt=build_system_prompt(_STUDY_MATERIAL_ROLE),
                    user_prompt=(
                        f"Skill: {name}\nTarget role: {target_role}\n"
                        f"Numbered context (cite using these EXACT bracket numbers):\n{context}\n\n"
                        "Return a useful study overview (non-empty), at least 4 key concepts, "
                        "and a reading-time estimate. Do not return empty strings or empty lists."
                    ),
                    json_schema=RoadmapStudyMaterial.model_json_schema(),
                    temperature=0.4,
                )
                response = await llm.generate(spec)
                self.cost_monitor.record(response, tier=tier)
                marker = None
                source_sentence = None
                if retrieved:
                    doc = retrieved[0]
                    marker = _register_citation(
                        citations, title=doc.metadata.get("title", "Untitled"), source=doc.metadata.get("source", "")
                    )
                    source_sentence = re.split(r"(?<=[.!?])\s+", doc.page_content.strip())[0]
                study_material = normalize_study_material(
                    response.parsed_json,
                    name,
                    target_role,
                    source_sentence=source_sentence,
                    citation_marker=marker,
                )

            updated.append({**skill, "study_material": study_material})

        result: dict[str, Any] = {"roadmap_skills": updated, "citations": citations}
        if used_llm:
            result["model_tier_used"] = tier
        return result


class PracticeGeneratorAgent(BaseAgent):
    """Hands-on exercises, a project idea, and self-assessment questions for every skill the user doesn't already know."""

    name = "PracticeGeneratorAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        skills = state.get("roadmap_skills") or []
        plan = state.get("plan") or {}
        tier = plan.get("tier", "flash")
        target_role = state["target_role"]
        used_llm = False

        active_names = [s["skill_name"] for s in skills if not s.get("already_known")]

        updated: list[dict[str, Any]] = []
        for skill in skills:
            name = skill["skill_name"]
            siblings = [s for s in active_names if s != name]
            if skill.get("already_known"):
                practice = normalize_practice_activities(
                    {
                        "exercises": [
                            f"Write one concrete example of how you used {name} in a real or portfolio context.",
                            f"List one limitation of {name} you would discuss in a {target_role} interview.",
                        ],
                        "project_idea": (
                            f"Optional review: package a short demo or write-up that proves {name} "
                            f"for a {target_role} conversation."
                        ),
                        "self_assessment_questions": [
                            f"Can you teach {name} with a concrete example in under two minutes?",
                            f"What would you practice next to keep {name} sharp for {target_role} work?",
                        ],
                    },
                    name,
                    target_role,
                    siblings,
                )
                updated.append({**skill, "practice_activities": practice})
                continue

            if settings.llm_mode == "mock":
                practice = normalize_practice_activities(None, name, target_role, siblings)
            else:
                used_llm = True
                llm = get_llm(tier)
                spec = PromptSpec(
                    system_prompt=build_system_prompt(_PRACTICE_ROLE),
                    user_prompt=(
                        f"Skill: {name}\nTarget role: {target_role}\n"
                        f"Other skills in this roadmap: {', '.join(siblings) or 'none'}\n\n"
                        "Return at least 4 practical exercises, a non-empty mini-project idea, "
                        "and at least 5 self-assessment questions. Do not return empty lists."
                    ),
                    json_schema=RoadmapPracticeActivities.model_json_schema(),
                    temperature=0.5,
                )
                response = await llm.generate(spec)
                self.cost_monitor.record(response, tier=tier)
                practice = normalize_practice_activities(
                    response.parsed_json, name, target_role, siblings
                )

            updated.append({**skill, "practice_activities": practice})

        result: dict[str, Any] = {"roadmap_skills": updated}
        if used_llm:
            result["model_tier_used"] = tier
        return result


_PACE_WEEKLY_HOURS_DEFAULT = {"fast": 20.0, "normal": 10.0, "thorough": 6.0}
_PACE_MONTHS_PER_MILESTONE = {"fast": 2, "normal": 3, "thorough": 4}
_WEEKS_PER_MONTH = 4.33


class TimelineOptimizerAgent(BaseAgent):
    """
    Deterministic scheduling: greedily buckets the dependency-ordered skill
    list into milestones sized by the user's pace and weekly-hours budget,
    converting cumulative estimated hours into month-ranged timeframe
    labels. No LLM call in either mode (this is the platform-wide
    "deterministic transformations" pattern) — but kept as a real, distinct
    pipeline node because §4.5 names "Timeline Optimization" as its own
    conceptual stage of roadmap generation.
    """

    name = "TimelineOptimizerAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        skills = state.get("roadmap_skills") or []
        pace = state.get("pace", "normal")
        personalization = state.get("personalization_inputs") or {}
        weekly_hours = personalization.get("weekly_hours_available") or _PACE_WEEKLY_HOURS_DEFAULT.get(pace, 10.0)
        months_per_bucket = _PACE_MONTHS_PER_MILESTONE.get(pace, 3)
        hours_per_bucket = weekly_hours * months_per_bucket * _WEEKS_PER_MONTH

        milestones: list[dict[str, Any]] = []
        current_skills: list[dict[str, Any]] = []
        current_hours = 0.0
        cumulative_month = 0.0

        def flush() -> None:
            nonlocal current_skills, current_hours, cumulative_month
            if not current_skills:
                return
            bucket_months = max(1, round(current_hours / weekly_hours / _WEEKS_PER_MONTH)) if weekly_hours else months_per_bucket
            start = round(cumulative_month)
            end = round(cumulative_month + bucket_months)
            milestones.append(
                {
                    "title": f"Month {start}-{end}: {mock_data.phase_label(len(milestones))}",
                    "timeframe_label": f"Month {start}-{end}",
                    "skills": current_skills,
                }
            )
            cumulative_month = end
            current_skills = []
            current_hours = 0.0

        for skill in skills:
            hours = skill.get("estimated_hours") or 0.0
            if current_skills and current_hours + hours > hours_per_bucket:
                flush()
            current_skills.append(skill)
            current_hours += hours
        flush()

        if not milestones:
            milestones = [
                {
                    "title": f"Month 0-{months_per_bucket}: {mock_data.phase_label(0)}",
                    "timeframe_label": f"Month 0-{months_per_bucket}",
                    "skills": [],
                }
            ]

        draft_output = {"role_taxonomy": state.get("role_taxonomy") or {}, "milestones": milestones}
        return {"milestones": milestones, "draft_output": draft_output}


class RoadmapReflectorAgent(BaseReflectorAgent):
    """Quality gate for the full roadmap draft, beyond the generic citation/boilerplate/unsupported-claims checks."""

    name = "RoadmapReflectorAgent"
    output_field = "draft_output"
    max_revisions = 2

    def render_for_review(self, draft: Any) -> str:
        if not isinstance(draft, dict):
            return super().render_for_review(draft)
        parts: list[str] = []
        for milestone in draft.get("milestones", []):
            for skill in milestone.get("skills", []):
                study = skill.get("study_material") or {}
                if study.get("overview"):
                    parts.append(study["overview"])
                practice = skill.get("practice_activities") or {}
                if practice.get("project_idea"):
                    parts.append(practice["project_idea"])
        return " ".join(parts)

    async def domain_checks(self, state: dict[str, Any], draft: Any) -> list[str]:
        issues: list[str] = []
        milestones = (draft or {}).get("milestones", [])
        if not milestones:
            issues.append("No milestones were generated.")

        seen_skill_names: set[str] = set()
        any_skill = False
        for milestone in milestones:
            if not milestone.get("skills"):
                issues.append(f"Milestone '{milestone.get('title', 'Untitled')}' has no skills assigned.")
            for skill in milestone.get("skills", []):
                any_skill = True
                name = (skill.get("skill_name") or "").strip().lower()
                if not name:
                    issues.append("A roadmap skill is missing its skill_name.")
                    continue
                if name in seen_skill_names:
                    issues.append(f"Duplicate skill across the roadmap: '{skill.get('skill_name')}'")
                seen_skill_names.add(name)
                if skill.get("importance") not in _IMPORTANCE_ORDER:
                    issues.append(f"Skill '{skill.get('skill_name')}' has an invalid importance value.")
                for resource in skill.get("resources") or []:
                    if not resource.get("url"):
                        issues.append(f"A resource for skill '{skill.get('skill_name')}' is missing a URL.")

        if not any_skill:
            issues.append("Roadmap contains no skills at all.")

        return issues


# --- Lightweight single-skill content refresh pipeline ---------------------------------


class SkillRefreshGuardrailAgent(BaseGuardrailAgent):
    name = "SkillRefreshGuardrailAgent"
    input_field = "raw_input"

    async def extra_checks(self, state: dict[str, Any], sanitized_input: Any) -> list[str]:
        if not (state.get("skill_name") or "").strip():
            return ["No skill_name provided to regenerate content for."]
        return []


class SkillRefreshPlannerAgent(BaseAgent):
    name = "SkillRefreshPlannerAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        tier = self.cost_monitor.recommend_tier(input_length_chars=len(state.get("raw_input", "")))
        return {"plan": {"tier": tier}}


class SkillRefreshExecutorAgent(BaseAgent):
    """
    The single-skill counterpart of ResourceFinder + StudyMaterial +
    PracticeGenerator combined into one node, used when a user wants to
    regenerate just one skill's content (e.g. for fresher resources)
    without re-running the full roadmap pipeline.
    """

    name = "SkillRefreshExecutorAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        skill_name = state["skill_name"]
        target_role = state["target_role"]
        plan = state.get("plan") or {}
        tier = plan.get("tier", "flash")
        citations: list[dict] = list(state.get("citations") or [])
        used_llm = False

        retrieved = retrieve(skill_name, k=2, category="skill_taxonomy")

        if settings.llm_mode == "mock":
            marker = None
            source_sentence = None
            if retrieved:
                doc = retrieved[0]
                marker = _register_citation(
                    citations, title=doc.metadata.get("title", "Untitled"), source=doc.metadata.get("source", "")
                )
                source_sentence = re.split(r"(?<=[.!?])\s+", doc.page_content.strip())[0]
            study_material = normalize_study_material(
                None,
                skill_name,
                target_role,
                source_sentence=source_sentence,
                citation_marker=marker,
            )
            practice_activities = normalize_practice_activities(
                None, skill_name, target_role, []
            )
        else:
            used_llm = True
            context = (
                _grounded_context_block(retrieved, citations)
                if retrieved
                else "(no matching material retrieved for this skill)"
            )
            llm = get_llm(tier)

            study_response = await llm.generate(
                PromptSpec(
                    system_prompt=build_system_prompt(_STUDY_MATERIAL_ROLE),
                    user_prompt=(
                        f"Skill: {skill_name}\nTarget role: {target_role}\n"
                        f"Numbered context (cite using these EXACT bracket numbers):\n{context}\n\n"
                        "Return a useful study overview (non-empty), at least 4 key concepts, "
                        "and a reading-time estimate. Do not return empty strings or empty lists."
                    ),
                    json_schema=RoadmapStudyMaterial.model_json_schema(),
                    temperature=0.4,
                )
            )
            self.cost_monitor.record(study_response, tier=tier)
            marker = None
            source_sentence = None
            if retrieved:
                doc = retrieved[0]
                marker = _register_citation(
                    citations, title=doc.metadata.get("title", "Untitled"), source=doc.metadata.get("source", "")
                )
                source_sentence = re.split(r"(?<=[.!?])\s+", doc.page_content.strip())[0]
            study_material = normalize_study_material(
                study_response.parsed_json,
                skill_name,
                target_role,
                source_sentence=source_sentence,
                citation_marker=marker,
            )

            practice_response = await llm.generate(
                PromptSpec(
                    system_prompt=build_system_prompt(_PRACTICE_ROLE),
                    user_prompt=(
                        f"Skill: {skill_name}\nTarget role: {target_role}\n"
                        "Other skills in this roadmap: none specified\n\n"
                        "Return at least 4 practical exercises, a non-empty mini-project idea, "
                        "and at least 5 self-assessment questions. Do not return empty lists."
                    ),
                    json_schema=RoadmapPracticeActivities.model_json_schema(),
                    temperature=0.5,
                )
            )
            self.cost_monitor.record(practice_response, tier=tier)
            practice_activities = normalize_practice_activities(
                practice_response.parsed_json, skill_name, target_role, []
            )

        resources = await _fetch_skill_resources(skill_name, target_role)

        draft_output = {
            "resources": resources,
            "study_material": study_material,
            "practice_activities": practice_activities,
            "lateral_connections": get_related_skills(skill_name),
        }
        result: dict[str, Any] = {"draft_output": draft_output, "citations": citations}
        if used_llm:
            result["model_tier_used"] = tier
        return result


class SkillRefreshReflectorAgent(BaseReflectorAgent):
    name = "SkillRefreshReflectorAgent"
    output_field = "draft_output"
    max_revisions = 1

    def render_for_review(self, draft: Any) -> str:
        if not isinstance(draft, dict):
            return super().render_for_review(draft)
        study = draft.get("study_material") or {}
        practice = draft.get("practice_activities") or {}
        parts = [study.get("overview", "")]
        if practice.get("project_idea"):
            parts.append(practice["project_idea"])
        return " ".join(p for p in parts if p)

    async def domain_checks(self, state: dict[str, Any], draft: Any) -> list[str]:
        if not draft or not (draft.get("study_material") or {}).get("overview"):
            return ["Generated content is missing a study material overview."]
        return []
