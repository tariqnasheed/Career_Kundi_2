"""
tools/llm.py
================
LLM provider abstraction — the single chokepoint every agent in the system
calls through to talk to a language model.

Why this exists
----------------
Every Executor agent needs to (a) send a system+user prompt, optionally with
few-shot examples, (b) get back either free text or schema-validated JSON,
(c) optionally stream tokens to the caller, and (d) record how many tokens
it cost. Rather than scattering `google.generativeai` calls across a dozen
agent files, every agent calls `get_llm(tier)` and gets back an object with
the same `.generate()` / `.stream()` interface regardless of whether we're
hitting the real Gemini API or running fully offline.

Live vs. mock mode
-------------------
`app.core.config.settings.llm_mode` is "live" only when GEMINI_API_KEY is
set. In mock mode, `MockGeminiProvider` produces deterministic, clearly
labeled, structurally realistic output (including simulated token-by-token
streaming) so the entire platform — every feature, every agent — runs
end-to-end with zero API cost. This is intentional: it lets a developer
clone the repo and see the full multi-agent pipeline execute (Guardrail ->
Planner -> Executor -> Reflector, with real revision cycles) without ever
touching a billing page. Swapping in a real `GEMINI_API_KEY` later requires
no code changes anywhere else in the codebase.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

ModelTier = Literal["flash", "pro"]


@dataclass
class LLMResponse:
    """Normalized response shape returned by every provider, live or mock."""

    text: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    cache_hit: bool = False
    parsed_json: Any | None = None


@dataclass
class PromptSpec:
    """
    Everything needed to issue one LLM call, built by a feature's prompt
    template (see app/prompts/) and handed to a provider unchanged. Keeping
    this as a flat dataclass (rather than passing five positional args
    around) means CostMonitorAgent, the cache layer, and both providers all
    share one contract.
    """

    system_prompt: str
    user_prompt: str
    temperature: float = 0.4
    max_output_tokens: int = 4096
    json_schema: dict | None = None  # JSON-schema the output must conform to, if any
    few_shot_examples: list[dict] = field(default_factory=list)


def _estimate_tokens(text: str) -> int:
    """
    Cheap token estimator (~4 chars/token, the widely-used rule of thumb for
    English text) used in mock mode and as a sanity fallback in live mode if
    the API doesn't report usage metadata. Good enough for cost dashboards
    and budget enforcement; NOT used for anything billing-critical.
    """
    return max(1, len(text) // 4)


class BaseLLMProvider(ABC):
    """Common interface implemented by both the live Gemini provider and the mock provider."""

    model_name: str

    @abstractmethod
    async def generate(self, spec: PromptSpec) -> LLMResponse:
        """Issue one non-streaming generation call."""

    @abstractmethod
    async def stream(self, spec: PromptSpec) -> AsyncIterator[str]:
        """Issue a streaming generation call, yielding text chunks as they arrive."""


class GeminiProvider(BaseLLMProvider):
    """
    Real Gemini provider, used when `settings.llm_mode == "live"`.

    Wraps `langchain_google_genai.ChatGoogleGenerativeAI` so we get
    LangChain's retry/streaming/tool-calling integration for free, plus
    structured output via `with_structured_output(json_schema)` when a
    JSON schema is supplied — this is how every agent enforces
    `response_mime_type="application/json"`-style structured output
    without hand-rolling JSON parsing + repair logic.
    """

    def __init__(self, tier: ModelTier):
        self.tier = tier
        self.model_name = settings.gemini_model_pro if tier == "pro" else settings.gemini_model_flash

    def _client(self, spec: PromptSpec):
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=settings.gemini_api_key,
            temperature=spec.temperature,
            max_output_tokens=spec.max_output_tokens,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def generate(self, spec: PromptSpec) -> LLMResponse:
        from langchain_core.messages import HumanMessage, SystemMessage

        client = self._client(spec)
        messages = [SystemMessage(content=spec.system_prompt), HumanMessage(content=spec.user_prompt)]

        if spec.json_schema:
            # Structured output enforcement (§3.3 "Structured Output Enforcement") —
            # binds the Gemini response schema so the model MUST return valid JSON
            # matching the agent's Pydantic contract, with one self-correction retry
            # on a parse failure (handled by the `retry` decorator above).
            structured_client = client.with_structured_output(spec.json_schema, include_raw=True)
            result = await structured_client.ainvoke(messages)
            raw = result["raw"]
            parsed = result["parsed"]
            text = raw.content if isinstance(raw.content, str) else json.dumps(parsed)
            usage = getattr(raw, "usage_metadata", None) or {}
            return LLMResponse(
                text=text,
                parsed_json=parsed,
                prompt_tokens=usage.get("input_tokens", _estimate_tokens(spec.system_prompt + spec.user_prompt)),
                completion_tokens=usage.get("output_tokens", _estimate_tokens(text)),
                model=self.model_name,
            )

        result = await client.ainvoke(messages)
        usage = getattr(result, "usage_metadata", None) or {}
        return LLMResponse(
            text=result.content,
            prompt_tokens=usage.get("input_tokens", _estimate_tokens(spec.system_prompt + spec.user_prompt)),
            completion_tokens=usage.get("output_tokens", _estimate_tokens(result.content)),
            model=self.model_name,
        )

    async def stream(self, spec: PromptSpec) -> AsyncIterator[str]:
        from langchain_core.messages import HumanMessage, SystemMessage

        client = self._client(spec)
        messages = [SystemMessage(content=spec.system_prompt), HumanMessage(content=spec.user_prompt)]
        async for chunk in client.astream(messages):
            if chunk.content:
                yield chunk.content


class MockGeminiProvider(BaseLLMProvider):
    """
    Deterministic offline stand-in for Gemini.

    Rather than returning lorem-ipsum, this mock is *content-aware*: it
    inspects `spec.json_schema` and `spec.user_prompt` to synthesize
    structurally valid, plausibly-shaped JSON (matching whatever Pydantic
    schema the calling agent requested) so downstream Reflector/Aggregator
    logic — which expects real fields like "questions", "citations",
    "confidence_score" — has something real to validate against. The actual
    domain-specific synthesis lives in each feature's `mock_data.py` (see
    app/agents/job_search/mock_data.py etc.); this class just provides the
    generic plumbing (token accounting, simulated latency, streaming).
    """

    def __init__(self, tier: ModelTier):
        self.tier = tier
        self.model_name = f"mock-gemini-{tier}"

    async def generate(self, spec: PromptSpec) -> LLMResponse:
        # Tiny simulated latency so the UI's streaming/progress states are
        # exercised in demos exactly as they would be against a real API.
        await asyncio.sleep(random.uniform(0.05, 0.15))

        text = self._synthesize(spec)
        parsed = None
        if spec.json_schema:
            parsed = self._coerce_to_schema(text, spec.json_schema)
            text = json.dumps(parsed)

        return LLMResponse(
            text=text,
            parsed_json=parsed,
            prompt_tokens=_estimate_tokens(spec.system_prompt + spec.user_prompt),
            completion_tokens=_estimate_tokens(text),
            model=self.model_name,
        )

    async def stream(self, spec: PromptSpec) -> AsyncIterator[str]:
        response = await self.generate(spec)
        # Simulate token-by-token streaming by chunking on whitespace — this
        # is what drives the frontend's "real-time token streaming" neural
        # progress visualization (§2 "Streaming Responses") even offline.
        words = response.text.split(" ")
        for i, word in enumerate(words):
            await asyncio.sleep(0.005)
            yield word + (" " if i < len(words) - 1 else "")

    @staticmethod
    def _synthesize(spec: PromptSpec) -> str:
        """
        Produce deterministic placeholder prose keyed off a hash of the
        prompt, so repeated calls with the SAME input return the SAME
        output (useful for tests and for the prompt cache's "is this a
        repeat request" semantics) while DIFFERENT inputs return visibly
        different text.
        """
        digest = hashlib.sha256((spec.system_prompt + spec.user_prompt).encode()).hexdigest()[:8]
        return (
            f"[mock-llm:{digest}] This is a deterministic offline response standing in for a real "
            f"Gemini call. Configure GEMINI_API_KEY in your .env to replace this with live, "
            f"grounded generation. Prompt context length: {len(spec.user_prompt)} chars."
        )

    @staticmethod
    def _coerce_to_schema(_text: str, schema: dict) -> dict:
        """
        Walk a JSON schema and produce a minimally valid instance. Feature
        agents that need realistic (not just schema-valid) mock content
        override this entirely via their own `mock_data.py` builders rather
        than relying on this generic fallback — see job_search/mock_data.py
        for the richer example.
        """

        def build(node: dict) -> Any:
            node_type = node.get("type")
            if node_type == "object":
                return {
                    key: build(sub)
                    for key, sub in node.get("properties", {}).items()
                }
            if node_type == "array":
                return [build(node.get("items", {"type": "string"}))]
            if node_type == "string":
                return "mock-value"
            if node_type in ("number", "integer"):
                return 0
            if node_type == "boolean":
                return False
            return None

        return build(schema)


def _hoist_defs_to_root(schema: dict) -> dict:
    """
    Return a copy of `schema` with every nested `$defs` block merged into a
    single top-level `$defs`, so `#/$defs/Name` references resolve. Needed
    because Ollama's structured-output schema converter only looks for `$defs`
    at the document root, while Pydantic nests them under the array item.
    """
    import copy

    schema = copy.deepcopy(schema)
    collected: dict[str, Any] = {}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            defs = node.pop("$defs", None)
            if isinstance(defs, dict):
                collected.update(defs)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)
    if collected:
        schema["$defs"] = collected
    return schema


class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama provider — free, no API quota — used when
    `settings.resolved_llm_provider == "ollama"`.

    Talks to a native Ollama server over its REST `/api/chat` endpoint (via
    httpx, which is already a dependency), so it needs no extra package and no
    LangChain client. Structured output is enforced with Ollama's `format`
    field set to the requested JSON schema — the local-model equivalent of
    Gemini's `with_structured_output`. Because this is a *real* model, the
    pipeline treats it as a live path (`llm_mode == "live"`), so the per-question
    content it produces is preserved rather than overwritten by the template
    engine (see mock_data._finalize_question).
    """

    def __init__(self, tier: ModelTier):
        self.tier = tier
        # One local model serves both tiers — quality tiers don't apply to a
        # single self-hosted model, and this keeps the test setup simple.
        self.model_name = settings.ollama_model
        self._base_url = settings.ollama_base_url.rstrip("/")

    def _payload(self, spec: PromptSpec, *, stream: bool) -> dict:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": spec.system_prompt},
                {"role": "user", "content": spec.user_prompt},
            ],
            "stream": stream,
            "options": {"temperature": spec.temperature, "num_predict": spec.max_output_tokens},
        }
        if spec.json_schema:
            # Ollama's JSON-schema converter only resolves "#/$defs/X" refs when
            # $defs sits at the schema ROOT. Pydantic emits $defs nested under the
            # array item, so Ollama 400s ("$defs not in {root}"). Hoisting the
            # definitions to the top level makes the refs resolve. (Gemini handles
            # the original nested schema fine, so this transform is Ollama-only.)
            payload["format"] = _hoist_defs_to_root(spec.json_schema)
        return payload

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def generate(self, spec: PromptSpec) -> LLMResponse:
        import httpx

        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
            resp = await client.post(f"{self._base_url}/api/chat", json=self._payload(spec, stream=False))
            resp.raise_for_status()
            data = resp.json()

        text = (data.get("message") or {}).get("content", "") or ""
        parsed = None
        if spec.json_schema and text:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None  # let the caller's retry/reflection loop handle malformed JSON
        return LLMResponse(
            text=text,
            parsed_json=parsed,
            prompt_tokens=data.get("prompt_eval_count") or _estimate_tokens(spec.system_prompt + spec.user_prompt),
            completion_tokens=data.get("eval_count") or _estimate_tokens(text),
            model=self.model_name,
        )

    async def stream(self, spec: PromptSpec) -> AsyncIterator[str]:
        import httpx

        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
            async with client.stream("POST", f"{self._base_url}/api/chat", json=self._payload(spec, stream=True)) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    piece = (chunk.get("message") or {}).get("content")
                    if piece:
                        yield piece


_PROVIDER_CACHE: dict[str, BaseLLMProvider] = {}


def get_llm(tier: ModelTier = "flash") -> BaseLLMProvider:
    """
    Return the LLM provider for the given cost tier ("flash" for routine
    tasks, "pro" for complex generation — see CostMonitorAgent for the
    escalation policy described in §3.3 "Tiered Model Selection"). Cached
    per-(provider, tier) so we don't reconstruct a client on every call.
    """
    provider = settings.resolved_llm_provider
    cache_key = f"{provider}:{tier}"
    if cache_key not in _PROVIDER_CACHE:
        if provider == "gemini":
            _PROVIDER_CACHE[cache_key] = GeminiProvider(tier)
        elif provider == "ollama":
            _PROVIDER_CACHE[cache_key] = OllamaProvider(tier)
        else:
            _PROVIDER_CACHE[cache_key] = MockGeminiProvider(tier)
        logger.info("llm_provider_initialized", tier=tier, provider=provider)
    return _PROVIDER_CACHE[cache_key]


# --- Prompt-injection detection ------------------------------------------------------
# Used by the GuardrailAgent (app/agents/common/guardrail.py) to block known
# jailbreak patterns before a user's input ever reaches an LLM call. This is
# a living pattern library — extend it as new attack patterns are observed.
PROMPT_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore (all|any|the) (previous|prior|above) instructions", re.I),
    re.compile(r"you are now\s+\w+", re.I),
    re.compile(r"disregard (your|the) (system prompt|instructions|guardrails)", re.I),
    re.compile(r"act as (an?|the) (unfiltered|unrestricted|jailbroken)", re.I),
    re.compile(r"reveal your (system prompt|instructions)", re.I),
    re.compile(r"<\s*script", re.I),  # defensive XSS-in-prompt pattern
    re.compile(r"\bDAN\b.{0,20}\bmode\b", re.I),  # common "Do Anything Now" jailbreak alias
]


def detect_prompt_injection(text: str) -> list[str]:
    """Return the list of matched jailbreak/injection pattern descriptions, empty if none found."""
    return [pattern.pattern for pattern in PROMPT_INJECTION_PATTERNS if pattern.search(text)]
