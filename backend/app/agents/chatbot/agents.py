"""
agents/chatbot/agents.py
============================
Concrete Guardrail / MemoryAgent / IntentClassifier / ActionDispatch /
Planner / Executor / Reflector agents for the AI Assistant Chatbot (§4.7).

Per the platform-wide invariant, NONE of these agents touch the database —
`app/api/routes/chatbot.py` loads recent conversation history, cross-session
long-term memory, and a flattened snapshot of the user's profile/jobs/
roadmaps/CVs into plain dicts BEFORE the graph runs, and persists this
turn's `memory_updates` (and the assistant's message) AFTER it finishes.

Live/mock split follows the same convention as every other feature:
IntentClassifierAgent and ChatbotResponseExecutorAgent are genuinely
LLM-calling stages (mock mode routes through the heuristics in
`mock_data.py`); MemoryAgent, ActionDispatchAgent, and ChatbotPlannerAgent
are deterministic in BOTH modes (no LLM call ever) but remain real, distinct
graph nodes — the same "deterministic transformation, still a real stage"
pattern as Roadmap's SkillDecomposerAgent/TimelineOptimizerAgent.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel

from app.agents.common.base import BaseAgent
from app.agents.common.cost_monitor import CostMonitor
from app.agents.common.guardrail import BaseGuardrailAgent
from app.agents.common.prompts import build_system_prompt
from app.agents.common.reflector import BaseReflectorAgent
from app.agents.common.security import scan_output_for_pii
from app.core.config import settings
from app.tools.graph_rag import get_skills_for_role
from app.tools.llm import PromptSpec, get_llm
from app.tools.rag import citations_from_documents, format_context_for_prompt, retrieve
from app.tools.search import verify_claim

from . import mock_data

# --- Guardrail ----------------------------------------------------------------------


class ChatbotGuardrailAgent(BaseGuardrailAgent):
    """Vets the raw user chat message before any retrieval/generation happens."""

    name = "ChatbotGuardrailAgent"
    input_field = "raw_input"

    async def extra_checks(self, state: dict[str, Any], sanitized_input: Any) -> list[str]:
        if not isinstance(sanitized_input, str) or not sanitized_input.strip():
            return ["Message is empty after sanitization — nothing to respond to."]
        return []


# --- Memory ---------------------------------------------------------------------------


class MemoryAgent(BaseAgent):
    """
    Synthesizes recent conversation history + cross-session long-term memory
    into a single grounding digest (`memory_context`) the Executor's prompt
    is built from, and proposes new memory facts to persist
    (`memory_updates`) by scanning the user's OWN message for explicit
    statements — never invents what the user meant. This is "Agentic
    Memory" (§2) actually implemented as a real pipeline stage rather than
    a database table nothing writes to.
    """

    name = "MemoryAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        message = state["raw_input"]
        long_term_memory = state.get("long_term_memory") or {}
        recent_messages = (state.get("session_snapshot") or {}).get("recent_messages") or []

        memory_context = mock_data.build_memory_context(long_term_memory, recent_messages)
        memory_updates = mock_data.infer_memory_updates(message, long_term_memory)

        preference = ((long_term_memory.get("chat_preferences") or {}).get("tone") or {}).get("preference")
        if preference == "concise":
            persona_directive = "Keep this reply concise, per the user's stated preference."
        elif preference == "detailed":
            persona_directive = "Feel free to go into more detail, per the user's stated preference."
        else:
            persona_directive = ""

        return {"memory_context": memory_context, "memory_updates": memory_updates, "persona_directive": persona_directive}


# --- Intent classification -------------------------------------------------------------

_INTENT_ROLE = """
You are the Intent Classifier agent for Careerkundi's AI Assistant. Read the
user's latest chat message, in light of the recent conversation and any
known long-term context about them, and classify it into EXACTLY one of:
action_request, smalltalk, cv_feedback, profile_help, job_search_guidance,
roadmap_guidance, general_question. Pick action_request when the user is
asking to be shown/counted/checked on data already on their account rather
than asking for advice. Pick general_question only when nothing more
specific genuinely fits.
""".strip()


class _IntentClassification(BaseModel):
    intent: Literal[
        "action_request", "smalltalk", "cv_feedback", "profile_help",
        "job_search_guidance", "roadmap_guidance", "general_question",
    ]
    confidence: float


class IntentClassifierAgent(BaseAgent):
    """Routes the message to one of the seven chatbot intents — heuristic keyword matching in mock mode, an LLM call in live mode (falling back to the heuristic if the model returns something off-schema)."""

    name = "IntentClassifierAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        message = state["raw_input"]
        memory_context = state.get("memory_context", "")

        if settings.llm_mode == "mock":
            intent, confidence = mock_data.classify_intent_heuristic(message)
        else:
            tier = self.cost_monitor.recommend_tier(input_length_chars=len(message))
            llm = get_llm(tier)
            spec = PromptSpec(
                system_prompt=build_system_prompt(_INTENT_ROLE),
                user_prompt=f"Context:\n{memory_context}\n\nLatest message:\n{message}",
                json_schema=_IntentClassification.model_json_schema(),
                temperature=0.0,
            )
            response = await llm.generate(spec)
            self.cost_monitor.record(response, tier=tier)
            parsed = response.parsed_json or {}
            intent = parsed.get("intent")
            confidence = parsed.get("confidence")
            if intent not in mock_data.INTENT_LABELS or not isinstance(confidence, (int, float)):
                intent, confidence = mock_data.classify_intent_heuristic(message)

        return {"intent": intent, "intent_confidence": float(confidence)}


# --- Action dispatch ---------------------------------------------------------------------

_CATEGORY_BY_INTENT: dict[str, str] = {
    "job_search_guidance": "career_advice",
    "roadmap_guidance": "skill_taxonomy",
    "cv_feedback": "career_advice",
    "profile_help": "career_advice",
}

_FRESHNESS_PATTERN = re.compile(
    r"\bcurrent(ly)?\b|\blatest\b|\bright now\b|\bstill (true|accurate|valid)\b|\bup[- ]to[- ]date\b",
    re.IGNORECASE,
)


def _resolve_retrieval_category(intent: str, message: str) -> str | None:
    """`None` means search across every seed-corpus category — used for general_question, which has no single obvious category."""
    if re.search(r"\binterview\b", message, re.IGNORECASE):
        return "interview_pattern"
    return _CATEGORY_BY_INTENT.get(intent)


def _build_action_request_facts(message: str, snapshot: dict[str, Any]) -> tuple[list[str], str]:
    """
    For the `action_request` intent, surface ONLY the account-data facts the
    message actually asked about (jobs / roadmap / CVs / profile),
    inferred from the message's own wording — falls back to a one-line
    summary of everything when no specific area is named.
    """
    text = message.lower()
    want_jobs = bool(re.search(r"\bjob[s]?\b", text))
    want_roadmap = bool(re.search(r"\broadmap\b|\bskill[s]?\b", text))
    want_cv = bool(re.search(r"\bcv[s]?\b|\bresume[s]?\b", text))
    want_profile = bool(re.search(r"\bprofile\b", text))
    want_everything = not (want_jobs or want_roadmap or want_cv or want_profile)

    facts: list[str] = []
    labels: list[str] = []

    if want_jobs or want_everything:
        count = snapshot.get("saved_job_count", 0)
        titles = snapshot.get("recent_job_titles") or []
        tail = f" — most recently '{titles[0]}'." if titles else "."
        facts.append(f"You have {count} saved job{'s' if count != 1 else ''}{tail}")
        labels.append("jobs")
    if want_roadmap or want_everything:
        role = snapshot.get("active_target_role")
        if role:
            completed = snapshot.get("completed_skill_count", 0)
            total = snapshot.get("total_skill_count", 0)
            facts.append(f"Your '{role}' roadmap has {completed} of {total} skills completed.")
        else:
            facts.append("You don't have an active roadmap yet.")
        labels.append("roadmap")
    if want_cv or want_everything:
        cv_count = snapshot.get("cv_count", 0)
        facts.append(f"You have {cv_count} generated CV{'s' if cv_count != 1 else ''} saved.")
        labels.append("cvs")
    if want_profile or want_everything:
        score = snapshot.get("profile_completeness")
        if score is not None:
            facts.append(f"Your profile is {score:.0f}% complete.")
        labels.append("profile")

    return facts, "fetched_" + "_".join(labels) + "_summary"


class ActionDispatchAgent(BaseAgent):
    """
    Gathers every piece of REAL grounding data this turn's reply will need:
    RAG retrieval against the seed-corpus category that matches the
    classified intent, GraphRAG skill traversal for roadmap questions,
    optional Search-grounded freshness verification, and — for
    `action_request` and every data-bearing intent — the literal facts
    already sitting in `user_context_snapshot` (never re-derives or
    guesses at numbers the route layer didn't supply). This is the concrete
    "ActionDispatchAgent executes intent -> action_result" behavior
    `db/models/chat.py`'s docstring promises.
    """

    name = "ActionDispatchAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        message = state["raw_input"]
        intent = state.get("intent", "general_question")
        snapshot = state.get("user_context_snapshot") or {}

        citations: list[dict] = []
        retrieved_context = ""
        source_sentence = None
        citation_marker = None
        search_grounded = False

        # action_request replies are grounded in the user's own account data
        # (facts[] from user_context_snapshot), not in RAG-retrieved sources,
        # so running retrieval produces off-topic citations that trigger the
        # Reflector's "number without citation" check on user-data facts.
        # Skip retrieval for smalltalk (no knowledge needed) AND action_request
        # (account-data-only reply); every other intent benefits from RAG grounding.
        if intent not in ("smalltalk", "action_request"):
            category = _resolve_retrieval_category(intent, message)
            retrieved = retrieve(message, k=3, category=category)
            if retrieved:
                retrieved_context = format_context_for_prompt(retrieved)
                citations = citations_from_documents(retrieved)
                source_sentence = re.split(r"(?<=[.!?])\s+", retrieved[0].page_content.strip())[0]
                citation_marker = 1

        if intent in ("job_search_guidance", "roadmap_guidance", "general_question") and _FRESHNESS_PATTERN.search(message):
            search_grounded, _results = await verify_claim(message[:200])

        action_result: dict[str, Any] = {}
        action_taken: str | None = None

        if intent == "action_request":
            facts, action_taken = _build_action_request_facts(message, snapshot)
            action_result["facts"] = facts
        elif intent == "job_search_guidance":
            action_result["saved_job_count"] = snapshot.get("saved_job_count", 0)
            action_result["recent_job_titles"] = snapshot.get("recent_job_titles", [])
            action_taken = "fetched_saved_jobs_summary"
        elif intent == "roadmap_guidance":
            target_role = snapshot.get("active_target_role")
            action_result["active_target_role"] = target_role
            action_result["completed_skill_count"] = snapshot.get("completed_skill_count")
            action_result["total_skill_count"] = snapshot.get("total_skill_count")
            if target_role:
                graph_skills = get_skills_for_role(target_role)
                if graph_skills:
                    action_result["graph_related_skills"] = [s["skill"] for s in graph_skills[:5]]
            action_taken = "fetched_roadmap_progress"
        elif intent in ("cv_feedback", "profile_help"):
            action_result["profile_completeness"] = snapshot.get("profile_completeness")
            action_result["missing_sections"] = snapshot.get("missing_sections", [])
            action_taken = "fetched_profile_summary"

        return {
            "action_result": action_result,
            "action_taken": action_taken,
            "citations": citations,
            "retrieved_context": retrieved_context,
            "source_sentence": source_sentence,
            "citation_marker": citation_marker,
            "search_grounded": search_grounded,
        }


# --- Planner ------------------------------------------------------------------------------


class ChatbotPlannerAgent(BaseAgent):
    """Decides the model tier for reply generation from combined prompt length and prior confidence — deterministic, no LLM call, same role every other feature's Planner plays."""

    name = "ChatbotPlannerAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        message = state["raw_input"]
        context_len = len(message) + len(state.get("retrieved_context") or "") + len(state.get("memory_context") or "")
        tier = self.cost_monitor.recommend_tier(
            input_length_chars=context_len, prior_confidence=state.get("confidence_score")
        )
        return {"plan": {"tier": tier}}


# --- Response generation -------------------------------------------------------------------

_CHAT_REPLY_ROLE = """
You are the AI Assistant for Careerkundi, a career platform. Answer the
user's latest message directly and specifically, grounded ONLY in the
numbered context provided and the real account data summarized below —
never invent a number, job title, skill, or fact about this user that
isn't actually present in what you were given. If nothing relevant was
retrieved, say so honestly rather than guessing. Match the requested tone
if one is specified, and suggest 1-3 genuinely relevant follow-up
questions the user could ask next.
""".strip()


class _ChatReplyDraft(BaseModel):
    reply: str
    suggested_followups: list[str] = []


class ChatbotResponseExecutorAgent(BaseAgent):
    """Generates the actual assistant reply — mock content-aware synthesis or a real grounded LLM call, per the platform-wide live/mock split."""

    name = "ChatbotResponseExecutorAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        message = state["raw_input"]
        intent = state.get("intent", "general_question")
        memory_context = state.get("memory_context", "")
        action_result = state.get("action_result") or {}
        persona_directive = state.get("persona_directive", "")
        retrieved_context = state.get("retrieved_context", "")
        tier = (state.get("plan") or {}).get("tier", "flash")
        revision_issues = state.get("reflection_issues") or []

        if settings.llm_mode == "mock":
            draft = mock_data.mock_generate_reply(
                intent=intent,
                message=message,
                memory_context=memory_context,
                action_result=action_result,
                persona_directive=persona_directive,
                source_sentence=state.get("source_sentence"),
                citation_marker=state.get("citation_marker"),
            )
        else:
            llm = get_llm(tier)
            user_prompt = (
                f"{memory_context}\n\n"
                f"Retrieved context:\n{retrieved_context or 'none retrieved'}\n\n"
                f"Account data relevant to this question: {action_result or 'none'}\n\n"
                f"User's message: {message}\n\nClassified intent: {intent}\n"
                f"Tone guidance: {persona_directive or 'none specified'}"
            )
            if revision_issues:
                user_prompt += "\n\nThe previous reply had these issues — fix them:\n" + "\n".join(
                    f"- {issue}" for issue in revision_issues
                )
            spec = PromptSpec(
                system_prompt=build_system_prompt(_CHAT_REPLY_ROLE),
                user_prompt=user_prompt,
                json_schema=_ChatReplyDraft.model_json_schema(),
                temperature=0.4,
            )
            response = await llm.generate(spec)
            self.cost_monitor.record(response, tier=tier)
            draft = response.parsed_json or {"reply": response.text, "suggested_followups": []}

        return {"draft_output": draft, "model_tier_used": tier}


# --- Reflector ------------------------------------------------------------------------------


def _flatten_fact_values(action_result: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for value in action_result.values():
        if isinstance(value, (int, float)):
            values.append(str(value))
        elif isinstance(value, str) and value:
            values.append(value)
        elif isinstance(value, list):
            values.extend(str(item) for item in value if isinstance(item, (str, int, float)))
    return values


class ChatbotReflectorAgent(BaseReflectorAgent):
    """
    Quality gate for the generated reply: standard citation/boilerplate
    checks (inherited) plus chat-specific checks — including the platform's
    first wired-up use of `scan_output_for_pii` (a conversational surface is
    the most likely place a user pastes something sensitive and an
    assistant might carelessly echo it back).
    """

    name = "ChatbotReflectorAgent"
    output_field = "draft_output"
    max_revisions = 2

    def render_for_review(self, draft: Any) -> str:
        if not isinstance(draft, dict):
            return super().render_for_review(draft)
        return draft.get("reply", "")

    async def domain_checks(self, state: dict[str, Any], draft: Any) -> list[str]:
        issues: list[str] = []
        reply = (draft or {}).get("reply", "")
        if not reply.strip():
            issues.append("Reply is empty.")
            return issues

        pii_hits = scan_output_for_pii(reply)
        if pii_hits:
            issues.append(f"Reply may echo sensitive identifier-shaped content ({', '.join(pii_hits)}) — remove it.")

        action_taken = state.get("action_taken")
        action_result = state.get("action_result") or {}
        if action_taken and action_result:
            fact_values = _flatten_fact_values(action_result)
            if fact_values and not any(value in reply for value in fact_values):
                issues.append("Reply doesn't reference any of the specific account data that was fetched for this question.")

        return issues
