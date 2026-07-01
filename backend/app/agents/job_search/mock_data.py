"""
agents/job_search/mock_data.py
==================================
Offline, content-aware stand-ins for the two LLM calls in this feature
(job-field extraction, interview-question generation), used when
`settings.llm_mode == "mock"`.

Per the architectural principle stated in `app/tools/llm.py`, generic
mock plumbing (latency simulation, token accounting) lives in
`MockGeminiProvider`; the DOMAIN-SPECIFIC synthesis that actually inspects
the real input and produces a structurally and substantively realistic
result lives here. Both functions below genuinely parse/scan the real job
text handed to them — they do not return canned, input-independent
placeholders — which is what lets the rest of the pipeline (RAG retrieval,
GraphRAG enrichment, Reflector checks, persistence) exercise real logic
end-to-end even with zero API keys configured.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

# A broader, job-posting-flavored skill keyword list than the small
# GraphRAG seed graph (which is tuned for roadmap traversal) — this is
# specifically for scanning raw job description text for mentioned skills.
JOB_SKILL_KEYWORDS: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript": [r"\btypescript\b"],
    "React": [r"\breact(\.js)?\b"],
    "Node.js": [r"\bnode(\.js)?\b"],
    "SQL": [r"\bsql\b", r"\bpostgres(ql)?\b", r"\bmysql\b"],
    "Distributed Systems": [r"\bdistributed systems?\b"],
    "System Design": [r"\bsystem design\b", r"\barchitecture\b"],
    "Docker": [r"\bdocker\b", r"\bcontaineri[sz]ation\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "CI/CD": [r"\bci\/cd\b", r"\bcontinuous (integration|deployment)\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Azure": [r"\bazure\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Statistics": [r"\bstatistics\b", r"\bstatistical\b"],
    "Data Visualization": [r"\bdata visuali[sz]ation\b", r"\btableau\b", r"\bpower ?bi\b"],
    "ETL Pipelines": [r"\betl\b", r"\bdata pipelines?\b"],
    "REST API Design": [r"\brest(ful)? apis?\b", r"\bapi design\b"],
    "GraphQL": [r"\bgraphql\b"],
    "Technical Leadership": [r"\btechnical leadership\b", r"\btech lead\b"],
    "Mentoring": [r"\bmentor(ing|ship)?\b"],
    "Agile": [r"\bagile\b", r"\bscrum\b"],
    "Testing": [r"\bunit test(ing|s)?\b", r"\btest-driven\b", r"\btdd\b"],
    "Security": [r"\bsecurity\b", r"\bowasp\b"],
}

_SECTION_HEADERS: dict[str, list[str]] = {
    "responsibilities": [r"responsibilit(y|ies)", r"what you.?ll do", r"the role", r"duties"],
    "requirements": [r"requirements", r"qualifications", r"what you.?ll need", r"skills?(?! we)"],
    "benefits": [r"benefits", r"perks", r"what we offer", r"compensation"],
}


def _detect_title(text: str) -> str | None:
    """First non-empty, reasonably short line is usually the job title in a pasted posting."""
    for line in text.splitlines():
        stripped = line.strip(" \t-•*#")
        if 3 < len(stripped) <= 100 and not stripped.endswith("."):
            return stripped
    return None


def _detect_company(text: str) -> str | None:
    match = re.search(r"\bat\s+([A-Z][A-Za-z0-9&.,' ]{1,60}?)(?:[.,\n]|\s+is\s|\s+in\s)", text)
    if match:
        return match.group(1).strip()
    match = re.search(r"^company:\s*(.+)$", text, re.I | re.M)
    return match.group(1).strip() if match else None


def _detect_employment_type(text: str) -> str | None:
    lowered = text.lower()
    for kind in ("full-time", "part-time", "contract", "internship", "temporary"):
        if kind in lowered or kind.replace("-", " ") in lowered:
            return kind
    return None


def _detect_remote(text: str) -> bool | None:
    lowered = text.lower()
    if "fully remote" in lowered or re.search(r"\bremote\b", lowered):
        return True
    if "on-site" in lowered or "onsite" in lowered or "in office" in lowered or "in-office" in lowered:
        return False
    return None


def _extract_sections(text: str) -> dict[str, list[str]]:
    """
    Walk the text line by line; when a line matches a known section header,
    start collecting subsequent bullet-ish lines into that bucket until the
    next recognized header. Lines outside any recognized section are
    discarded (they're prose/boilerplate, not list items).
    """
    buckets: dict[str, list[str]] = {key: [] for key in _SECTION_HEADERS}
    current: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched_header = None
        for section, patterns in _SECTION_HEADERS.items():
            if any(re.search(p, line, re.I) for p in patterns) and len(line) < 60:
                matched_header = section
                break
        if matched_header:
            current = matched_header
            continue

        if current and len(line) > 8:
            cleaned = line.lstrip("-•*● \t")
            if cleaned and cleaned not in buckets[current]:
                buckets[current].append(cleaned)

    return buckets


def _extract_skills(text: str) -> list[dict]:
    """
    Scan for known skill keywords; a skill mentioned inside the detected
    "requirements" section is tagged `importance="critical"`, one mentioned
    elsewhere in the posting is tagged `"medium"` — a simple but genuinely
    input-dependent importance signal.
    """
    sections = _extract_sections(text)
    requirements_text = " ".join(sections.get("requirements", [])).lower()
    found = []
    for skill, patterns in JOB_SKILL_KEYWORDS.items():
        if any(re.search(p, text, re.I) for p in patterns):
            importance = "critical" if any(re.search(p, requirements_text, re.I) for p in patterns) else "medium"
            found.append({"skill": skill, "category": "technical", "importance": importance})
    return found


def mock_parse_job(text: str) -> dict:
    """Build a `JobEnrichmentResult`-shaped dict (minus citations/confidence, added by the Executor) purely from real text scanning — no fabricated fields."""
    sections = _extract_sections(text)
    return {
        "title": _detect_title(text) or "Untitled Role (title not detected in pasted text)",
        "company_name": _detect_company(text),
        "company_url": None,
        "location": "Remote" if _detect_remote(text) else None,
        "employment_type": _detect_employment_type(text),
        "is_remote": _detect_remote(text),
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "responsibilities": sections.get("responsibilities", []),
        "requirements": sections.get("requirements", []),
        "benefits": sections.get("benefits", []),
        "extracted_skills": _extract_skills(text),
    }


# --- Interview pack synthesis --------------------------------------------------------

_GENERIC_BEHAVIORAL_TEMPLATES = [
    "Tell me about a time you disagreed with a teammate's technical decision. How did you handle it?",
    "Describe a project where the requirements changed significantly midway through. What did you do?",
    "Walk me through a time you had to learn an unfamiliar technology quickly to deliver a project.",
    "Tell me about a mistake you made in a past role and what you learned from it.",
]


def _technical_questions_for_skill(skill: str) -> list[dict]:
    return [
        {
            "category": "technical",
            "question": f"Walk me through how you would explain {skill} to a teammate who has never used it.",
            "why_asked": f"Tests genuine conceptual understanding of {skill}, not just résumé familiarity.",
            "ideal_answer_points": [
                f"Clear, jargon-light explanation of what {skill} is and the problem it solves",
                "A concrete example from real experience, not a textbook definition",
                "Honest acknowledgment of limitations or tradeoffs",
            ],
            "follow_ups": [f"What's a situation where {skill} was the WRONG choice?"],
            "skill_tag": skill,
        },
        {
            "category": "technical",
            "question": f"Describe the most complex problem you've solved using {skill}.",
            "why_asked": f"Probes depth of hands-on, applied experience with {skill} under real constraints.",
            "ideal_answer_points": [
                "Specific, real scenario with concrete scale/constraints",
                "Clear articulation of the approach and why it was chosen over alternatives",
                "A measurable or observable result",
            ],
            "follow_ups": ["What would you do differently if you tackled it again today?"],
            "skill_tag": skill,
        },
    ]


def mock_generate_questions(
    job: dict,
    *,
    focus_areas: list[str],
    difficulty: str,
) -> list[dict]:
    """
    Generate an interview pack sized by how much real signal the job
    actually contains — every extracted skill yields its own pair of
    technical questions, every responsibility/requirement informs a
    tailored behavioral prompt, and a system-design question is added only
    when the role's own skills genuinely warrant one. No fixed question
    count is hardcoded anywhere in this function.
    """
    questions: list[dict] = []

    skills = [s["skill"] for s in job.get("extracted_skills", [])]
    if focus_areas:
        # Focus areas the user explicitly asked about get priority placement and are
        # included even if the scraper/parser didn't independently detect them.
        skills = list(dict.fromkeys(focus_areas + skills))

    for skill in skills:
        questions.extend(_technical_questions_for_skill(skill))

    if any(s in ("System Design", "Distributed Systems", "Architecture") for s in skills):
        questions.append(
            {
                "category": "system_design",
                "question": (
                    f"Design a system that fulfills the core responsibilities of this "
                    f"{job.get('title', 'role')} posting at scale. Walk through your approach."
                ),
                "why_asked": "Tests structured design thinking and tradeoff articulation under ambiguity.",
                "ideal_answer_points": [
                    "Clarifies requirements and scale targets before designing",
                    "Presents a high-level architecture before diving into one component",
                    "Explicitly discusses at least one tradeoff (consistency vs. availability, latency vs. cost)",
                ],
                "follow_ups": ["How would this design change at 10x the load?"],
                "skill_tag": "System Design",
            }
        )

    for responsibility in job.get("responsibilities", [])[:6]:
        questions.append(
            {
                "category": "behavioral",
                "question": f"This role involves '{responsibility}'. Tell me about a time you did something similar.",
                "why_asked": "Behavioral question tailored to a specific responsibility actually listed in this posting, using the STAR structure.",
                "ideal_answer_points": ["Situation", "Task", "Action (most detail here)", "Result (quantified)"],
                "follow_ups": ["What would you do differently with more time or resources?"],
                "skill_tag": None,
            }
        )

    for template in _GENERIC_BEHAVIORAL_TEMPLATES:
        questions.append(
            {
                "category": "behavioral",
                "question": template,
                "why_asked": "Standard behavioral probe using the STAR method, included regardless of job specifics.",
                "ideal_answer_points": ["Situation", "Task", "Action (most detail here)", "Result (quantified)"],
                "follow_ups": [],
                "skill_tag": None,
            }
        )

    questions.append(
        {
            "category": "role_specific",
            "question": f"What excites you specifically about this {job.get('title', 'role')} position, based on what you've read?",
            "why_asked": "Tests genuine engagement with the actual posting rather than a rehearsed generic answer.",
            "ideal_answer_points": ["References specific responsibilities or requirements from the real posting"],
            "follow_ups": [],
            "skill_tag": None,
        }
    )

    if job.get("company_name"):
        questions.append(
            {
                "category": "company_specific",
                "question": f"What do you know about {job['company_name']}, and why do you want to work there specifically?",
                "why_asked": "Tests genuine research into the company rather than a generic answer that could apply anywhere.",
                "ideal_answer_points": ["Specific, verifiable facts about the company, not guesses"],
                "follow_ups": [],
                "skill_tag": None,
            }
        )

    return questions


def mock_company_profile(company_name: str | None) -> dict:
    """
    Deliberately returns an EMPTY profile rather than fabricating company
    facts (industry, size, funding) the platform has no real source for in
    mock mode — per the zero-hallucination mandate, "I don't know" beats a
    plausible-sounding guess. Live mode populates this via Google Search
    grounding instead (see app/agents/job_search/agents.py).
    """
    return {} if company_name else {}


def mock_timestamp() -> datetime:
    return datetime.now(timezone.utc)
