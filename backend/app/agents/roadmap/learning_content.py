"""Field-adaptive, learning-science-grounded content builders for roadmap skills.

The Career Roadmap teaches ANY skill in ANY educational field, so this module
deterministically constructs a full, pedagogically-structured learning module
for a `(skill, target_role)` pair without needing the network or a strong LLM —
the local Ollama path uses these as its reliable fallback/backfill.

Design (from learning-science best practice):
- Bloom's taxonomy learning objectives (Remember -> Understand -> Apply ->
  Analyze -> Evaluate -> Create) so objectives ladder in difficulty.
- Tiered beginner -> intermediate -> advanced explanations (cognitive-load
  chunking).
- Active-recall FLASHCARDS (spaced-repetition ready).
- Multiple-choice QUIZZES as "assessment gateways".
- Project-based PROJECTS at increasing difficulty.
- Synthesis REFLECTION questions (Analyze/Evaluate level).

Content references the real skill/role text and is flavored by a light field
detector, so it adapts across engineering, healthcare, business, creative,
trades, science, finance, education, and general streams rather than being one
template with the name swapped in.
"""

from __future__ import annotations

import re

# Words that start with a vowel LETTER but a consonant SOUND ("a university",
# "a one-off", "a Unix box") — these keep "a", everything else vowel-initial
# takes "an".
_A_AN_CONSONANT_SOUND = ("uni", "use", "user", "usu", "eu", "ewe", "one", "once")


def _fix_articles(text: str) -> str:
    """Correct 'a' -> 'an' before vowel-sound words (e.g. 'a AI Engineer')."""

    def repl(m: "re.Match[str]") -> str:
        article, word = m.group(1), m.group(2)
        low = word.lower()
        vowel_sound = low[0] in "aeiou" and not any(low.startswith(x) for x in _A_AN_CONSONANT_SOUND)
        fixed = ("an" if vowel_sound else "a") if article.islower() else ("An" if vowel_sound else "A")
        return f"{fixed} {word}"

    return re.sub(r"\b([Aa]) ([A-Za-z][\w'-]*)", repl, text)


def deep_fix_articles(obj):
    """Recursively apply article correction to strings inside dicts/lists."""
    if isinstance(obj, str):
        return _fix_articles(obj)
    if isinstance(obj, list):
        return [deep_fix_articles(x) for x in obj]
    if isinstance(obj, dict):
        return {k: deep_fix_articles(v) for k, v in obj.items()}
    return obj


# field -> flavor vocabulary used to make generic structure feel domain-specific.
_FIELD_FLAVORS: dict[str, dict[str, str]] = {
    "technology": {
        "artifact": "small working program or repo",
        "tool": "the standard tooling, documentation, and tests",
        "quality": "correctness, readability, and tests passing",
        "practice": "build it, run it, and check the output",
    },
    "data": {
        "artifact": "notebook or dashboard",
        "tool": "your data, queries, and validation checks",
        "quality": "correct results, validated assumptions, and reproducibility",
        "practice": "load real data, transform it, and sanity-check the numbers",
    },
    "healthcare": {
        "artifact": "case write-up or care checklist",
        "tool": "protocols, patient records, and safety checks",
        "quality": "patient safety, accuracy, and clear documentation",
        "practice": "work a realistic case and document your reasoning",
    },
    "engineering": {
        "artifact": "calculation sheet, drawing, or test record",
        "tool": "standards, drawings, and verification tests",
        "quality": "safety, tolerance, and standards compliance",
        "practice": "work a sizing/verification example against the standard",
    },
    "business": {
        "artifact": "one-page plan or analysis",
        "tool": "frameworks, stakeholders, and metrics",
        "quality": "clear reasoning, evidence, and stakeholder value",
        "practice": "apply it to a realistic scenario and present the recommendation",
    },
    "finance": {
        "artifact": "model or reconciliation",
        "tool": "source data, controls, and checks",
        "quality": "accuracy, controls, and auditability",
        "practice": "build the calculation and reconcile it against source data",
    },
    "creative": {
        "artifact": "portfolio piece",
        "tool": "the brief, references, and your chosen tools",
        "quality": "meeting the brief, craft, and originality",
        "practice": "make a piece to a brief and critique it against references",
    },
    "trades": {
        "artifact": "completed task with a sign-off record",
        "tool": "the right tools, safety gear, and procedure",
        "quality": "safety, tidiness, and doing it to code",
        "practice": "carry out the task safely and check it against the procedure",
    },
    "science": {
        "artifact": "lab record or short report",
        "tool": "method, measurements, and controls",
        "quality": "valid method, repeatable measurements, and honest reporting",
        "practice": "run a small experiment and record method and results",
    },
    "education": {
        "artifact": "lesson plan or resource",
        "tool": "objectives, activities, and assessment",
        "quality": "clear objectives, engagement, and evidence of learning",
        "practice": "design a short lesson and plan how you'd check understanding",
    },
    "general": {
        "artifact": "small piece of finished work",
        "tool": "the right method, records, and checks",
        "quality": "getting it right, checking it, and recording what you did",
        "practice": "apply it to a realistic task and review the outcome",
    },
}

_FIELD_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("healthcare", ("nurse", "pharma", "clinical", "patient", "medic", "health", "care", "therapy", "dental", "laboratory")),
    ("finance", ("finance", "financ", "account", "audit", "bank", "invest", "tax", "actuar", "bookkeep")),
    ("data", ("data ", "data-", "dataset", "analytics", "sql", "statistic", "machine learning", "deep learning", "dashboard", "power bi", "tableau")),
    ("technology", ("software", "developer", "programming", "python", "javascript", "typescript", "devops", "cloud", "backend", "frontend", "cyber", "coding", "api", "kubernetes", "docker", "ai engineer", "ml engineer")),
    ("engineering", ("electr", "mechanical", "civil", "structural", "maintenance", "chemical", "manufactur", "cad", "hvac", "plc", "isolation")),
    ("business", ("business", "marketing", "sales", "manage", "product owner", "operations", "hr ", "human resources", "consult", "strategy")),
    ("creative", ("design", "art", "media", "content", "writer", "video", "photo", "music", "brand", "ux", "ui", "architect")),
    ("trades", ("plumb", "carpent", "weld", "construct", "technician", "mechanic", "install", "electrician", "facilities")),
    ("science", ("research", "biolog", "chem", "physic", "lab ", "scientif", "environment")),
    ("education", ("teach", "tutor", "lectur", "education", "instructor", "curriculum", "lesson")),
)


def detect_field(skill_name: str, target_role: str = "") -> str:
    """Best-effort classification of the learning stream from skill + role text."""
    text = f"{skill_name} {target_role}".lower()
    for field, keywords in _FIELD_KEYWORDS:
        if any(k in text for k in keywords):
            return field
    return "general"


def _flavor(skill_name: str, target_role: str) -> dict[str, str]:
    return _FIELD_FLAVORS[detect_field(skill_name, target_role)]


# ---------------------------------------------------------------------------
# Study material
# ---------------------------------------------------------------------------


def build_learning_objectives(skill_name: str, target_role: str) -> list[str]:
    """Bloom's-taxonomy-laddered objectives, from recall up to creation."""
    role = target_role or "your target role"
    f = _flavor(skill_name, target_role)
    return [
        f"Remember: recall what {skill_name} means and its core vocabulary.",
        f"Understand: explain in your own words how {skill_name} works and why it matters for a {role}.",
        f"Apply: use {skill_name} to complete a small, realistic {role} task.",
        f"Analyse: break a {skill_name} problem into parts and work out what's going wrong.",
        f"Evaluate: judge when {skill_name} is the right approach — and when it isn't.",
        f"Create: produce an original {f['artifact']} that shows you can use {skill_name}.",
    ]


def build_layered_explanations(skill_name: str, target_role: str) -> dict[str, str]:
    role = target_role or "your target role"
    f = _flavor(skill_name, target_role)
    return {
        "beginner_explanation": (
            f"Start simple: {skill_name} is a skill a {role} uses regularly. At this stage, focus on what it is "
            f"and the vocabulary around it — don't worry about edge cases yet. Your first move is to {f['practice']}, "
            f"even at a tiny scale, so the idea becomes concrete rather than abstract."
        ),
        "intermediate_explanation": (
            f"Once the basics click, learn the workflow: the usual steps a {role} follows to apply {skill_name} from "
            f"start to finish, using {f['tool']}. At this level you should be able to do it end-to-end on a realistic "
            f"task and know how to tell whether the result is good — judging it on {f['quality']}."
        ),
        "advanced_explanation": (
            f"Mastery is about judgement under real constraints: handling the awkward cases, weighing trade-offs, and "
            f"knowing when {skill_name} is NOT the right tool. An advanced {role} can anticipate where {skill_name} "
            f"work goes wrong, build checks to catch it early, and explain their reasoning to others."
        ),
    }


def build_concepts(skill_name: str, target_role: str) -> list[dict[str, str]]:
    """Term + plain-language definition pairs (teachable key concepts)."""
    role = target_role or "your target role"
    f = _flavor(skill_name, target_role)
    return [
        {
            "term": f"What {skill_name} is",
            "definition": f"The core idea of {skill_name} and the everyday vocabulary a {role} uses to talk about it.",
        },
        {
            "term": "The typical workflow",
            "definition": f"The usual sequence of steps to apply {skill_name} from start to finish using {f['tool']}.",
        },
        {
            "term": "How you check it's good",
            "definition": f"The quality signals that tell you {skill_name} work is done well: {f['quality']}.",
        },
        {
            "term": "Where it fits",
            "definition": f"How {skill_name} connects to the neighbouring skills and to the wider job of a {role}.",
        },
        {
            "term": "When NOT to use it",
            "definition": f"The situations where {skill_name} is the wrong approach, and what you'd reach for instead.",
        },
    ]


def build_worked_example(skill_name: str, target_role: str) -> str:
    role = target_role or "your target role"
    f = _flavor(skill_name, target_role)
    return (
        f"Worked example — take a realistic {role} task that needs {skill_name}. First, get clear on the goal and the "
        f"constraints. Next, {f['practice']}, working step by step rather than jumping ahead. Then review the result "
        f"against {f['quality']}, and note one thing you'd do differently next time. The point is to produce a real "
        f"{f['artifact']} you can point to, not just to read about it."
    )


def build_common_mistakes(skill_name: str, target_role: str) -> list[str]:
    return [
        f"Jumping to advanced tools before the basics of {skill_name} are solid.",
        f"Copying a solution without understanding why it works — it breaks the moment the situation changes.",
        f"Skipping the checks, so {skill_name} work looks finished but hasn't actually been verified.",
        f"Learning {skill_name} passively (only reading/watching) instead of practising and getting feedback.",
        f"Not connecting {skill_name} to a real {target_role or 'role'} task, so it stays abstract.",
    ]


def build_revision_notes(skill_name: str, target_role: str) -> list[str]:
    role = target_role or "your target role"
    return [
        f"{skill_name} in one line: what it is and why a {role} uses it.",
        f"The workflow: the main steps, in order.",
        f"The quality checks that tell you it's done well.",
        f"One situation where {skill_name} is the wrong choice.",
        f"Your proof: the artifact that shows you can actually do it.",
    ]


def build_prerequisites(skill_name: str, target_role: str) -> list[str]:
    return [
        f"Comfort with the absolute basics that {skill_name} builds on (no deep expertise needed to start).",
        f"A way to practise — the tools or materials a {target_role or 'learner'} would use for {skill_name}.",
        "Willingness to learn actively: try, check, and adjust rather than only reading.",
    ]


def build_why_it_matters(skill_name: str, target_role: str) -> str:
    role = target_role or "your target role"
    return (
        f"{skill_name} matters because it's one of the skills a {role} is actually expected to use — being able to do "
        f"it well (not just describe it) is what separates 'aware of it' from 'ready for the job'. Investing here pays "
        f"off directly in real tasks, interviews, and portfolio work."
    )


def enrich_study_material(base: dict, skill_name: str, target_role: str) -> dict:
    """Add the enriched, Bloom-aligned fields onto a base study-material dict.

    Only fills fields that are missing/blank so real (LLM- or RAG-sourced)
    content is preserved.
    """
    out = dict(base or {})
    layered = build_layered_explanations(skill_name, target_role)
    defaults = {
        "why_it_matters": build_why_it_matters(skill_name, target_role),
        "prerequisites": build_prerequisites(skill_name, target_role),
        "learning_objectives": build_learning_objectives(skill_name, target_role),
        "beginner_explanation": layered["beginner_explanation"],
        "intermediate_explanation": layered["intermediate_explanation"],
        "advanced_explanation": layered["advanced_explanation"],
        "concepts": build_concepts(skill_name, target_role),
        "worked_example": build_worked_example(skill_name, target_role),
        "common_mistakes": build_common_mistakes(skill_name, target_role),
        "revision_notes": build_revision_notes(skill_name, target_role),
    }
    for key, value in defaults.items():
        existing = out.get(key)
        if not existing or (isinstance(existing, list) and not any(existing)):
            out[key] = value
    return out


# ---------------------------------------------------------------------------
# Practice: flashcards, quizzes, projects, reflection
# ---------------------------------------------------------------------------


def build_flashcards(skill_name: str, target_role: str) -> list[dict[str, str]]:
    """Active-recall flashcards (front prompt -> back answer)."""
    role = target_role or "your target role"
    f = _flavor(skill_name, target_role)
    return [
        {"front": f"In one sentence, what is {skill_name}?", "back": f"A skill a {role} uses to get real work done — the core idea plus its everyday vocabulary."},
        {"front": f"Why does {skill_name} matter for a {role}?", "back": f"Because it's a skill the role actually uses; doing it well is what makes you job-ready, not just aware of it."},
        {"front": f"What is the usual workflow for {skill_name}?", "back": f"The step-by-step way a {role} applies it end to end using {f['tool']}."},
        {"front": f"How do you know {skill_name} work is good?", "back": f"You judge it on {f['quality']}."},
        {"front": f"Name a common beginner mistake with {skill_name}.", "back": "Copying a solution without understanding it, or skipping the checks so it only looks finished."},
        {"front": f"When is {skill_name} the WRONG tool?", "back": "When the situation doesn't fit its purpose — recognising this is a sign of real understanding."},
        {"front": f"What proves you can actually do {skill_name}?", "back": f"A concrete {f['artifact']} you produced, not just notes about it."},
        {"front": f"What's the fastest way to improve at {skill_name}?", "back": f"Active practice with feedback: {f['practice']}, then review and adjust."},
    ]


def build_quizzes(skill_name: str, target_role: str) -> list[dict]:
    """Multiple-choice assessment-gateway questions with explanations."""
    role = target_role or "your target role"
    f = _flavor(skill_name, target_role)
    return [
        {
            "question": f"You're starting to learn {skill_name} for a {role} role. What's the best FIRST step?",
            "options": [
                "Understand what it is and the basics, then practise on a small task",
                "Memorise every advanced feature before trying anything",
                "Copy a finished solution and move on without understanding it",
                "Avoid practising until you've read everything about it",
            ],
            "answer_index": 0,
            "explanation": "Foundations first, then active practice on a small realistic task — this is how skills actually stick.",
        },
        {
            "question": f"How can you tell {skill_name} work is done well?",
            "options": [
                "It looks finished, so it's fine",
                f"It holds up on {f['quality']}",
                "Someone else said it was okay once",
                "It took a long time to do",
            ],
            "answer_index": 1,
            "explanation": f"Quality is judged on {f['quality']}, not on appearance or effort alone.",
        },
        {
            "question": f"Which is the strongest evidence you've learned {skill_name}?",
            "options": [
                "You watched several videos about it",
                "You can recite its definition",
                f"You produced a real {f['artifact']} using it and can explain your choices",
                "You bookmarked a lot of resources",
            ],
            "answer_index": 2,
            "explanation": "Producing and explaining real work (Bloom's 'Create') is far stronger evidence than passive exposure.",
        },
        {
            "question": f"A {role} should reach for {skill_name} when…",
            "options": [
                "Always, regardless of the problem",
                "Never, if there's any alternative",
                "When the problem actually fits what it's good at",
                "Only when told to by someone else",
            ],
            "answer_index": 2,
            "explanation": "Knowing when it fits — and when it doesn't — is a mark of real understanding (Bloom's 'Evaluate').",
        },
        {
            "question": f"What most improves long-term retention of {skill_name}?",
            "options": [
                "Re-reading notes many times",
                "Active recall and spaced practice with feedback",
                "Highlighting everything in a book",
                "Cramming it all in one sitting",
            ],
            "answer_index": 1,
            "explanation": "Active recall and spaced repetition are the best-evidenced techniques for durable learning.",
        },
    ]


def build_projects(skill_name: str, target_role: str, sibling_skills: list[str] | None = None) -> list[dict]:
    """Project-based-learning briefs at increasing difficulty."""
    role = target_role or "your target role"
    f = _flavor(skill_name, target_role)
    siblings = [s for s in (sibling_skills or []) if s and s != skill_name]
    combine = f" combined with {', '.join(siblings[:2])}" if siblings else ""
    return [
        {
            "title": f"Starter: a tiny {skill_name} exercise",
            "brief": f"Apply {skill_name} to the smallest realistic task you can think of that a {role} might face. The goal is one clear, finished result.",
            "steps": [
                "Write down the goal in one sentence.",
                f"Do the task step by step and {f['practice']}.",
                f"Check the result against {f['quality']}.",
                "Note one thing you'd improve next time.",
            ],
            "deliverable": f"A small finished {f['artifact']} plus a two-line write-up of what you did.",
            "difficulty": "beginner",
        },
        {
            "title": f"Applied: an end-to-end {skill_name} task",
            "brief": f"Take a realistic {role} scenario that needs {skill_name}{combine}, and work it from start to finish, making the decisions yourself.",
            "steps": [
                "Clarify the goal, constraints, and what 'good' looks like.",
                "Plan the workflow before you start.",
                f"Execute using {f['tool']}, checking as you go.",
                "Review, then write a short note on the trade-offs you made.",
            ],
            "deliverable": f"A complete {f['artifact']} you could show and talk through in an interview.",
            "difficulty": "intermediate",
        },
        {
            "title": f"Stretch: a {skill_name} project with a twist",
            "brief": f"Build something with {skill_name} that includes a hard case or constraint — the kind a senior {role} handles. Anticipate what could go wrong and design a check for it.",
            "steps": [
                "Choose a realistic constraint or edge case up front.",
                "Design your approach and a way to catch the failure mode.",
                "Build it, verify it, and stress-test the hard case.",
                "Write up the trade-offs and what you'd do at larger scale.",
            ],
            "deliverable": f"A polished {f['artifact']} plus a short write-up of the trade-offs and checks.",
            "difficulty": "advanced",
        },
    ]


def build_reflection_questions(skill_name: str, target_role: str) -> list[str]:
    """Synthesis / self-evaluation prompts (distinct from recall self-assessment)."""
    role = target_role or "your target role"
    return [
        f"In your own words, how would you explain {skill_name} to someone starting out — and where did you struggle to keep it simple?",
        f"What surprised you about {skill_name} once you actually practised it, versus how it seemed when you read about it?",
        f"Where does {skill_name} connect to the other skills on your roadmap, and which one does it unlock next?",
        f"If a {role} task using {skill_name} went wrong, how would you work out the cause — and what check would catch it earlier next time?",
        f"On a scale of 'aware' to 'interview-ready', where are you with {skill_name} now, and what's the single next step to move up?",
    ]
