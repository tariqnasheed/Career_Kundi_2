"""
agents/chatbot/mock_data.py
================================
Offline, content-aware stand-ins for the chatbot's two LLM-eligible stages
(intent classification and reply generation), plus deterministic helpers
used in BOTH mock and live mode (memory-update inference, memory-context
digesting) — mirroring `app/agents/roadmap/mock_data.py`'s split between
"genuine LLM stand-ins" and "always-deterministic pipeline stages".

Nothing here calls an LLM/RAG/search tool itself (that happens in
`agents.py`, which hands these functions already-retrieved data as plain
arguments); every function genuinely derives its output from the real
`message`/`action_result`/`memory_context` it's given, so the rest of the
pipeline (RAG retrieval, GraphRAG traversal, Reflector quality checks,
memory persistence) exercises real logic end-to-end even with zero API
keys configured.
"""

from __future__ import annotations

import re
from typing import Any

INTENT_LABELS = [
    "action_request",
    "smalltalk",
    "cv_feedback",
    "profile_help",
    "job_search_guidance",
    "roadmap_guidance",
    "general_question",
]

# Ordered most-specific-first: when a message matches more than one group
# (e.g. "roadmap" + "skills" both appearing), the FIRST group in this dict
# with the highest match count wins ties, deliberately favoring the more
# actionable/specific intents over the catch-all.
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "action_request": [
        r"\bshow me\b", r"\bhow many\b", r"\blist (my|all)\b", r"\bwhat(?:'s| is) my\b",
        r"\bcheck (my|on)\b", r"\bstatus of\b", r"\bdo i have\b", r"\bwhich (jobs|skills|roadmaps|cvs)\b",
    ],
    "smalltalk": [
        r"^\s*(hi|hello|hey|yo|sup)\b", r"\bhow are you\b", r"\bgood (morning|afternoon|evening)\b",
        r"\bthanks?\b", r"\bthank you\b", r"\bwho are you\b", r"\bwhat can you do\b",
    ],
    "cv_feedback": [
        r"\bresume\b", r"\bcv\b", r"\bcover letter\b", r"\bbullet point\b", r"\bcvbuilder\b",
    ],
    "profile_help": [
        r"\bprofile\b", r"\bcompleteness\b", r"\bheadline\b", r"\bbio\b", r"\bprofile strength\b",
    ],
    "job_search_guidance": [
        r"\bjob[s]?\b", r"\bapply\b", r"\bapplication\b", r"\binterview\b", r"\bsalary\b",
        r"\bemployer\b", r"\bcompany\b", r"\brecruiter\b", r"\bjob search\b",
    ],
    "roadmap_guidance": [
        r"\broadmap\b", r"\bskill[s]?\b", r"\blearn(ing)?\b", r"\bstudy\b", r"\bcourse\b",
        r"\bcareer path\b", r"\btransition\b", r"\bmilestone\b",
    ],
}


def classify_intent_heuristic(message: str) -> tuple[str, float]:
    """
    Score every intent's keyword group against the message and return the
    best match (ties broken by `_INTENT_KEYWORDS`'s declared order, which
    favors specific/actionable intents over the `general_question`
    catch-all). Confidence scales with how many distinct keyword groups
    matched, capped well below 1.0 since this is a heuristic, not a model.
    """
    text = message.lower()
    best_intent = "general_question"
    best_score = 0
    for intent, patterns in _INTENT_KEYWORDS.items():
        score = sum(1 for pattern in patterns if re.search(pattern, text))
        if score > best_score:
            best_score = score
            best_intent = intent

    if best_score == 0:
        # No keyword group matched at all. A question mark still signals a
        # genuine question rather than smalltalk; otherwise this is honestly
        # ambiguous and general_question is the safest default.
        confidence = 0.55 if "?" in message else 0.4
        return "general_question", confidence

    confidence = min(0.92, 0.55 + 0.12 * best_score)
    return best_intent, confidence


# --- Memory inference (deterministic in both mock and live mode) -------------------------

_TARGET_ROLE_PATTERNS = [
    re.compile(
        r"\bi(?:'m| am)\s+(?:aiming for|targeting|aiming to become)\s+(?:an?\s+)?([A-Za-z][A-Za-z0-9/&+\- ]{2,60})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:my target role is|i want to become|i want to be|i'm trying to become)\s+(?:an?\s+)?([A-Za-z][A-Za-z0-9/&+\- ]{2,60})",
        re.IGNORECASE,
    ),
]

_TONE_PATTERNS: dict[str, re.Pattern] = {
    "concise": re.compile(
        r"\b(keep (?:it|things|your answers) (?:concise|brief|short)|i prefer (?:concise|short|brief) answers|"
        r"be more concise|less verbose)\b",
        re.IGNORECASE,
    ),
    "detailed": re.compile(
        r"\b(i prefer (?:detailed|thorough|in-depth) answers|be more (?:detailed|thorough)|"
        r"give me more detail|explain in depth)\b",
        re.IGNORECASE,
    ),
}

_REMEMBER_PATTERN = re.compile(r"\bremember (?:that )?(.+)", re.IGNORECASE)
_TRAILING_PUNCT_PATTERN = re.compile(r"[.,;!?\s]+$")


def _clean_captured_phrase(text: str, *, max_len: int = 80) -> str:
    cleaned = re.split(r"[.,;\n]", text.strip(), maxsplit=1)[0]
    cleaned = _TRAILING_PUNCT_PATTERN.sub("", cleaned).strip()
    return cleaned[:max_len].strip()


def infer_memory_updates(message: str, existing_memory: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """
    Scan the user's NEW message for explicit, genuinely-stated memory-worthy
    facts (a target role, a tone preference, an explicit "remember that ..."
    instruction) — never infers anything the user didn't actually say.
    Skips proposing an update that would just re-write an identical existing
    value, so MemoryAgent doesn't spam AgentMemory with no-op upserts on
    every turn the user repeats themselves.
    """
    existing_memory = existing_memory or {}
    updates: list[dict[str, Any]] = []

    for pattern in _TARGET_ROLE_PATTERNS:
        match = pattern.search(message)
        if match:
            role = _clean_captured_phrase(match.group(1))
            if role:
                current = (existing_memory.get("career_goals") or {}).get("target_role") or {}
                if current.get("role", "").lower() != role.lower():
                    updates.append({"namespace": "career_goals", "key": "target_role", "value": {"role": role}})
            break

    for tone, pattern in _TONE_PATTERNS.items():
        if pattern.search(message):
            current = (existing_memory.get("chat_preferences") or {}).get("tone") or {}
            if current.get("preference") != tone:
                updates.append({"namespace": "chat_preferences", "key": "tone", "value": {"preference": tone}})
            break  # at most one tone signal per message

    remember_match = _REMEMBER_PATTERN.search(message)
    if remember_match:
        note = _clean_captured_phrase(remember_match.group(1), max_len=255)
        if note:
            key = f"note_{abs(hash(note.lower())) % 10_000_000:07d}"
            updates.append({"namespace": "user_notes", "key": key, "value": {"note": note}})

    return updates


def build_memory_context(
    long_term_memory: dict[str, dict[str, Any]] | None, recent_messages: list[dict[str, Any]] | None, *, max_messages: int = 8
) -> str:
    """Render long-term memory + recent turns into a compact digest spliced into the reply prompt — the ONLY way prior context reaches the Executor (it never re-reads the DB itself)."""
    parts: list[str] = []
    if long_term_memory:
        memory_lines = [
            f"{namespace}.{key} = {value}"
            for namespace, entries in sorted(long_term_memory.items())
            for key, value in sorted(entries.items())
        ]
        if memory_lines:
            parts.append("Known long-term context about this user:\n" + "\n".join(memory_lines))

    if recent_messages:
        trimmed = recent_messages[-max_messages:]
        history_lines = [f"{m.get('role', 'user')}: {m.get('content', '')}" for m in trimmed]
        parts.append("Recent conversation (most recent last):\n" + "\n".join(history_lines))

    return "\n\n".join(parts) if parts else "No prior context available — this is a new conversation."


# --- Reply generation (mock LLM stand-in) -----------------------------------------------

_FOLLOWUP_TEMPLATES: dict[str, list[str]] = {
    "general_question": ["Want me to go deeper on any part of that?"],
    "job_search_guidance": ["Want me to pull up your saved jobs that match this?", "Should I draft an interview prep pack for one of them?"],
    "cv_feedback": ["Want me to point out the weakest section of your CV first?", "Should I check your CV against a specific job posting?"],
    "roadmap_guidance": ["Want me to break down the next skill in more detail?", "Should I suggest learning resources for the skill you're stuck on?"],
    "profile_help": ["Want a prioritized list of what to fill in next?", "Should I show you exactly which sections move your strength score most?"],
    "action_request": ["Want more detail on any of those?"],
    "smalltalk": ["What would you like help with today — job search, your CV, a roadmap, or your profile?"],
}


def mock_generate_reply(
    *,
    intent: str,
    message: str,
    memory_context: str,
    action_result: dict[str, Any] | None,
    persona_directive: str,
    source_sentence: str | None = None,
    citation_marker: int | None = None,
) -> dict[str, Any]:
    """
    Build a `{"reply": str, "suggested_followups": list[str]}` dict that is
    genuinely derived from `action_result` (real numbers/names already
    fetched from the user's own data — never fabricated) and, when a RAG hit
    was found, a real `source_sentence` with its `[n]` marker attached
    (never paraphrased into something the source didn't say). When no
    curated material exists for this question, says so honestly rather than
    inventing a plausible-sounding answer.
    """
    action_result = action_result or {}
    message = message.strip()
    tone_note = f" {persona_directive}" if persona_directive else ""

    if intent == "smalltalk":
        reply = (
            "Hi — I'm your Careerkundi assistant. I can help with job search, your CV, your career "
            f"roadmap, or your profile — just tell me what you're working on.{tone_note}"
        )
    elif intent == "action_request":
        facts = action_result.get("facts") or []
        if facts:
            reply = " ".join(facts)
        else:
            reply = (
                "I checked, but there's nothing there yet for that — once you generate it, "
                "I'll be able to summarize it for you here."
            )
    else:
        grounded_answer = _grounded_answer_sentence(source_sentence, citation_marker)
        data_lead_in = _data_lead_in(intent, action_result)
        body = " ".join(part for part in [data_lead_in, grounded_answer] if part)
        if not body:
            body = (
                f"Careerkundi doesn't have curated material on '{message[:120]}' yet, so I can't ground a "
                "specific answer in a real source right now — happy to help with what I can see on your "
                "account instead, or try rephrasing with more specifics."
            )
        reply = body + tone_note

    followups = list(_FOLLOWUP_TEMPLATES.get(intent, _FOLLOWUP_TEMPLATES["general_question"]))
    return {"reply": reply.strip(), "suggested_followups": followups}


def _grounded_answer_sentence(source_sentence: str | None, citation_marker: int | None) -> str:
    if not source_sentence:
        return ""
    sentence = source_sentence.strip()
    return f"{sentence} [{citation_marker}]" if citation_marker is not None else sentence


def _data_lead_in(intent: str, action_result: dict[str, Any]) -> str:
    """A real-data-grounded opening clause specific to the intent, built ONLY from fields actually present in `action_result` — never invents a number the route layer didn't supply."""
    if intent == "job_search_guidance":
        count = action_result.get("saved_job_count")
        titles = action_result.get("recent_job_titles") or []
        if count is not None:
            lead = f"You currently have {count} saved job{'s' if count != 1 else ''}"
            return lead + (f", most recently '{titles[0]}'. " if titles else ". ")
        return ""
    if intent == "roadmap_guidance":
        target_role = action_result.get("active_target_role")
        completed = action_result.get("completed_skill_count")
        total = action_result.get("total_skill_count")
        if target_role and total:
            return f"On your '{target_role}' roadmap you've completed {completed or 0} of {total} skills. "
        return ""
    if intent in ("cv_feedback", "profile_help"):
        score = action_result.get("profile_completeness")
        missing = action_result.get("missing_sections") or []
        if score is not None:
            tail = f" The biggest gap is your {missing[0]} section." if missing else ""
            return f"Your profile is currently {score:.0f}% complete.{tail} "
        return ""
    return ""
