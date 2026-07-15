"""
agents/roadmap/mock_data.py
================================
Offline, content-aware stand-ins for the four LLM calls in this feature
(required-skill inference for novel roles, study-material prose, practice
activities, and the lightweight single-skill refresh), used when
`settings.llm_mode == "mock"`.

Mirroring `app/agents/job_search/mock_data.py`'s design: this module never
calls an LLM/RAG/search tool itself (that happens in `agents.py`, which
hands these functions already-retrieved data as plain arguments) and never
returns canned, input-independent placeholders. Every function genuinely
derives its output from the real `skill_name`/`target_role`/role-title text
it's given, so the rest of the pipeline (GraphRAG traversal, RAG retrieval,
Reflector quality checks, persistence) exercises real logic end-to-end even
with zero API keys configured.
"""

from __future__ import annotations

import re

# A role-archetype-flavored skill keyword map: skill_name -> list of
# (regex, importance-if-matched) pairs, scanned against a target role title
# (plus any free-text personalization context). Broader than the 16-skill
# GraphRAG seed set on purpose — novel/non-seeded roles (Product Manager, UX
# Designer, DevOps Engineer's specific cloud skills, ...) still get a real,
# input-derived skill set rather than falling through to a generic guess
# every time. Importance reflects how central the skill typically is to a
# role matching that pattern; `infer_required_skills` takes the highest
# (most critical) importance across every pattern that actually matches.
ROLE_SKILL_KEYWORDS: dict[str, list[tuple[str, str]]] = {
    # --- Data & ML ---
    "SQL": [(r"\bdata (analyst|engineer|scientist)\b", "critical"), (r"\banalytics\b", "high"), (r"\bbusiness intelligence\b|\bbi\b", "high")],
    "Python": [(r"\bdata (scien|engineer)\b", "critical"), (r"\bmachine learning\b|\bml engineer\b", "critical"), (r"\bbackend\b", "high"), (r"\bautomation\b", "medium")],
    "Statistics": [(r"\bdata scientist\b", "critical"), (r"\bmachine learning\b|\bml engineer\b", "high"), (r"\bquant\b", "critical")],
    "Machine Learning": [(r"\bmachine learning\b|\bml engineer\b", "critical"), (r"\bdata scientist\b", "high"), (r"\bai engineer\b", "critical")],
    "Data Visualization": [(r"\bdata analyst\b", "critical"), (r"\bbusiness intelligence\b|\bbi\b", "high"), (r"\bdashboard\b", "high")],
    "ETL Pipelines": [(r"\bdata engineer\b", "critical"), (r"\betl\b", "critical"), (r"\bdata pipeline\b", "high")],
    # --- Backend / Infra ---
    "Distributed Systems": [(r"\bsenior backend\b|\bstaff (backend|software)\b", "critical"), (r"\bbackend\b", "high"), (r"\bsite reliability\b|\bsre\b", "high"), (r"\bplatform engineer\b", "high")],
    "System Design": [(r"\bsenior\b|\bstaff\b|\bprincipal\b", "high"), (r"\barchitect\b", "critical"), (r"\bbackend\b", "high")],
    "REST API Design": [(r"\bbackend\b", "critical"), (r"\bfull[- ]?stack\b", "high"), (r"\bapi\b", "critical")],
    "Docker": [(r"\bdevops\b|\bsre\b|\bplatform engineer\b", "critical"), (r"\bbackend\b", "medium"), (r"\binfrastructure\b", "high")],
    "Kubernetes": [(r"\bdevops\b|\bsre\b|\bplatform engineer\b", "critical"), (r"\bcloud\b", "high"), (r"\binfrastructure\b", "high")],
    "CI/CD": [(r"\bdevops\b|\bsre\b|\bplatform engineer\b", "critical"), (r"\bbackend\b", "medium")],
    "Cloud Infrastructure (AWS/GCP/Azure)": [(r"\bdevops\b|\bsre\b|\bplatform engineer\b|\bcloud engineer\b", "critical"), (r"\baws\b|\bgcp\b|\bazure\b", "critical")],
    "Networking Fundamentals": [(r"\bnetwork engineer\b|\bsysadmin\b", "critical"), (r"\bdevops\b|\bsre\b", "medium")],
    # --- Frontend ---
    "React": [(r"\bfrontend\b|\bfront-end\b", "critical"), (r"\bfull[- ]?stack\b", "high"), (r"\breact\b", "critical"), (r"\bui engineer\b", "high")],
    "TypeScript": [(r"\bfrontend\b|\bfront-end\b", "high"), (r"\bfull[- ]?stack\b", "high"), (r"\btypescript\b", "critical")],
    # --- Leadership ---
    "Technical Leadership": [(r"\bengineering manager\b|\bem\b", "critical"), (r"\bsenior\b|\bstaff\b|\bprincipal\b|\blead\b", "high"), (r"\bhead of\b|\bdirector\b", "critical")],
    "Mentoring": [(r"\bengineering manager\b|\bem\b", "critical"), (r"\bsenior\b|\bstaff\b|\blead\b", "medium")],
    # --- Mobile ---
    "Mobile UI Development": [(r"\bios\b|\bandroid\b|\bmobile\b", "critical")],
    "Swift": [(r"\bios\b", "critical")],
    "Kotlin": [(r"\bandroid\b", "critical")],
    # --- Product ---
    "Product Strategy": [(r"\bproduct manager\b|\bproduct owner\b|\bpm\b", "critical")],
    "User Research": [(r"\bproduct manager\b|\bux\b|\bproduct design\b", "high")],
    "Roadmap Planning & Prioritization": [(r"\bproduct manager\b|\bproduct owner\b", "critical")],
    "Data-Informed Decision Making": [(r"\bproduct manager\b|\bgrowth\b", "high")],
    "Stakeholder & Cross-functional Management": [(r"\bproduct manager\b|\bprogram manager\b|\bproject manager\b", "critical")],
    # --- Design ---
    "Wireframing & Prototyping": [(r"\bux\b|\bui designer\b|\bproduct design\b", "critical")],
    "Visual & Interaction Design": [(r"\bui designer\b|\bproduct design\b|\bgraphic design\b", "critical")],
    "Usability Testing": [(r"\bux\b|\busability\b", "high")],
    # --- DevOps/Security/QA already partly covered above; add Security/QA specific ---
    "Security Fundamentals": [(r"\bsecurity\b|\bcybersecurity\b", "critical"), (r"\bsoc analyst\b|\bpenetration\b", "critical")],
    "Incident Response": [(r"\bsecurity\b|\bsoc analyst\b|\bincident\b", "high"), (r"\bsre\b", "medium")],
    "Test Automation": [(r"\bqa\b|\bquality assurance\b|\bsdet\b|\btest engineer\b", "critical")],
    "Manual Testing & Test Case Design": [(r"\bqa\b|\bquality assurance\b|\btester\b", "high")],
    # --- Marketing/Sales ---
    "Content Strategy": [(r"\bmarketing\b|\bcontent\b", "critical")],
    "SEO": [(r"\bmarketing\b|\bseo\b|\bgrowth\b", "high")],
    "Campaign Analytics": [(r"\bmarketing\b|\bgrowth\b|\bdigital marketing\b", "high")],
    "CRM & Pipeline Management": [(r"\bsales\b|\baccount executive\b|\bsdr\b|\bsales engineer\b", "critical")],
    "Negotiation & Closing": [(r"\bsales\b|\baccount executive\b", "high")],
    # --- Writing ---
    "Technical Writing": [(r"\btechnical writer\b|\bdocumentation\b", "critical")],
}

# Words that carry no domain signal and should be stripped before deriving a
# fallback skill set from a role title we have zero keyword coverage for.
_SENIORITY_AND_STOPWORDS = {
    "senior", "junior", "staff", "principal", "lead", "head", "of", "the", "and", "a", "an",
    "i", "ii", "iii", "iv", "associate", "intern", "internship", "entry", "level", "manager",
    "specialist", "for",
}

_IMPORTANCE_ORDER = {"critical": 0, "high": 1, "medium": 2, "nice-to-have": 3}


def infer_required_skills(target_role: str, additional_context: str = "") -> list[dict]:
    """
    Scan the target role title (plus any free-text personalization context)
    for known skill-archetype keywords and return every skill that
    genuinely matches, sorted critical-first — mirroring
    `tools/graph_rag.py::get_skills_for_role`'s output shape so
    `RoleTaxonomyAgent` can treat graph-sourced and heuristic-sourced skills
    identically. Falls back to `_fallback_skills_from_role_words` only when
    NOTHING matches (a genuinely novel role with no recognizable keywords).
    """
    text = f"{target_role} {additional_context}".lower()
    matches: list[dict] = []
    for skill, patterns in ROLE_SKILL_KEYWORDS.items():
        best: str | None = None
        for pattern, importance in patterns:
            if re.search(pattern, text):
                if best is None or _IMPORTANCE_ORDER[importance] < _IMPORTANCE_ORDER[best]:
                    best = importance
        if best is not None:
            matches.append({"skill": skill, "importance": best})

    if not matches:
        return _fallback_skills_from_role_words(target_role)
    return sorted(matches, key=lambda m: _IMPORTANCE_ORDER.get(m["importance"], 2))


def _fallback_skills_from_role_words(target_role: str) -> list[dict]:
    """
    For a role with no keyword-dictionary coverage at all, derive a skill
    set from the role title's OWN significant words rather than returning a
    fixed, input-independent list — e.g. "Localization Program Manager"
    yields skills built around "Localization", not a generic placeholder.
    `RoleTaxonomyAgent` flags roles that reach this path as `is_novel_role`
    so the UI can be honest that this is a best-effort heuristic guess.
    """
    words = [w for w in re.findall(r"[A-Za-z]+", target_role) if w.lower() not in _SENIORITY_AND_STOPWORDS]
    domain = " ".join(w.capitalize() for w in words) if words else target_role.strip().title()
    return [
        {"skill": f"{domain} Domain Fundamentals", "importance": "critical"},
        {"skill": f"{domain} Tools & Workflows", "importance": "high"},
        {"skill": "Stakeholder & Cross-functional Communication", "importance": "medium"},
        {"skill": "Data-Informed Decision Making", "importance": "medium"},
    ]


_BASE_HOURS_BY_IMPORTANCE = {"critical": 45.0, "high": 30.0, "medium": 18.0, "nice-to-have": 10.0}
_LEVEL_MULTIPLIER = {"beginner": 1.3, "intermediate": 1.0, "advanced": 0.65}


def estimate_base_hours(importance: str | None, starting_skill_level: str | None) -> float:
    """Deterministic hour estimate from importance tier and self-reported starting level — no LLM call, no fabricated precision."""
    base = _BASE_HOURS_BY_IMPORTANCE.get(importance or "medium", 18.0)
    multiplier = _LEVEL_MULTIPLIER.get(starting_skill_level or "intermediate", 1.0)
    return round(base * multiplier, 1)


def build_study_overview(
    skill_name: str,
    target_role: str,
    *,
    source_sentence: str | None = None,
    citation_marker: int | None = None,
) -> dict:
    """
    Build a `RoadmapStudyMaterial`-shaped dict. When a real RAG-retrieved
    sentence is available (passed in by `StudyMaterialAgent` after it
    queries `tools/rag.py`), the overview IS that sentence with its `[n]`
    citation marker attached — never paraphrased into something the source
    didn't actually say. When no matching seed-corpus material exists yet,
    the overview is built from the real `skill_name`/`target_role` inputs
    and deliberately avoids numeric claims (so it cannot trip the
    Reflector's unsupported-claims heuristic) rather than inventing a
    plausible-sounding statistic.
    """
    if source_sentence:
        overview = source_sentence.strip()
        if citation_marker is not None:
            overview = f"{overview} [{citation_marker}]"
    else:
        overview = (
            f"{skill_name} is a practical capability this roadmap flags as relevant for a "
            f"{target_role}. This overview is foundational/local-generated study guidance "
            f"(not independently source-verified): focus on what {skill_name} means day to day, "
            f"which tools and workflows show up in {target_role} work, and how you demonstrate "
            f"progress through small exercises and a mini-project."
        )

    key_concepts = [
        f"What {skill_name} actually involves day-to-day in a {target_role} role",
        f"Core tools, packages, or terminology associated with {skill_name}",
        f"How {skill_name} connects to neighboring skills on this roadmap",
        f"Common mistakes beginners make with {skill_name} and how to avoid them",
        f"How to show {skill_name} readiness in a {target_role} interview or portfolio",
    ]
    word_count = len(overview.split())
    estimated_reading_time_minutes = max(3, round(word_count / 200 * 60))

    return {
        "overview": overview,
        "key_concepts": key_concepts,
        "estimated_reading_time_minutes": estimated_reading_time_minutes,
    }


def build_practice_activities(skill_name: str, target_role: str, sibling_skills: list[str]) -> dict:
    """
    Build a `RoadmapPracticeActivities`-shaped dict, content-aware of both
    the skill itself and (for the project idea) any other active skills
    elsewhere in this roadmap — so the project idea genuinely combines real
    sibling skills rather than being skill-isolated. (Milestone grouping
    happens later, in `TimelineOptimizerAgent`, so `sibling_skills` here is
    every other not-already-known skill in the whole roadmap, not just the
    eventual same-milestone subset.)
    """
    exercises = [
        f"Spend a focused session applying {skill_name} to a small, self-contained problem you pick yourself "
        f"rather than a textbook exercise — explain your reasoning out loud or in writing as you go.",
        f"Find one real example of {skill_name} used in a production {target_role} workflow (blog, open-source "
        f"repo, or public write-up) and summarize the specific decisions it made.",
        f"Teach {skill_name} back to yourself in 5 minutes as if explaining it to a new {target_role} hire — "
        f"this surfaces gaps a passive read-through will miss.",
        f"Write a short checklist of quality checks you would run before calling {skill_name} work "
        f"'done enough' for a {target_role} deliverable.",
    ]

    other = [s for s in sibling_skills if s != skill_name]
    if other:
        project_idea = (
            f"Build a small project that combines {skill_name} with {', '.join(other[:2])} — pick something "
            f"a {target_role} would plausibly ship, even at toy scale. Document what you learned."
        )
    else:
        project_idea = (
            f"Build a small, end-to-end project centered on {skill_name} that you could describe in a "
            f"{target_role} interview, including a short write-up of tradeoffs."
        )

    self_assessment_questions = [
        f"Could you explain {skill_name} to someone unfamiliar with it, with a concrete example, in under two minutes?",
        f"Could you identify a situation where {skill_name} would be the WRONG tool or approach to use?",
        f"What is one concrete artifact (snippet, notebook, checklist, demo) that proves you practiced {skill_name}?",
        f"Which neighboring skill on this roadmap most depends on {skill_name}, and why?",
        f"What would you practice next week to move {skill_name} from 'familiar' to 'interview-ready'?",
    ]

    return {
        "exercises": exercises,
        "project_idea": project_idea,
        "self_assessment_questions": self_assessment_questions,
    }


_PHASE_LABELS = ["Foundations", "Core Skills", "Advanced Skills", "Specialization & Mastery"]


def phase_label(index: int) -> str:
    """Deterministic milestone phase naming — `TimelineOptimizerAgent` calls this once per bucket it builds, regardless of mock/live mode."""
    if index < len(_PHASE_LABELS):
        return _PHASE_LABELS[index]
    return f"{_PHASE_LABELS[-1]} (Part {index - len(_PHASE_LABELS) + 2})"


def resource_type_for_url(url: str | None) -> str:
    """Cheap heuristic classification of a discovered resource link's `resource_type`, from the URL itself — never guesses beyond what the URL/domain actually signals."""
    if not url:
        return "article"
    lowered = url.lower()
    if "youtube.com" in lowered or "vimeo.com" in lowered:
        return "video"
    if "docs." in lowered or "/docs" in lowered or "documentation" in lowered:
        return "documentation"
    if "coursera.org" in lowered or "udemy.com" in lowered or "edx.org" in lowered or "pluralsight.com" in lowered:
        return "course"
    if "internal://" in lowered:
        return "article"
    return "article"
