"""
agents/common/guardrail.py
==============================
`BaseGuardrailAgent`: the first stage of every pipeline. Runs BEFORE any
LLM call or tool invocation, enforcing the input side of §3.5 Security
Architecture — sanitization and prompt-injection detection — plus a hook
for feature-specific structural validation (e.g. "is this actually a
well-formed URL", "does this profile have enough data to build a CV from").

A Guardrail rejection short-circuits the LangGraph straight to a final
error response (see `graph_utils.py`'s `_guardrail_router`) — Planner,
Executor, and Reflector never run on input that failed this stage, which
is the cheapest possible place to fail fast, before a single token is
spent.
"""

from __future__ import annotations

from typing import Any

from app.agents.common.base import BaseAgent
from app.agents.common.security import check_for_injection, sanitize_input
from app.core.errors import GuardrailRejectionError


class BaseGuardrailAgent(BaseAgent):
    """
    Generic input guardrail. Feature pipelines subclass this and override
    `extra_checks()` to add domain-specific validation while reusing the
    sanitization + injection-detection logic for free.
    """

    name = "GuardrailAgent"
    input_field: str = "raw_input"  # which state key holds the primary free-text input to vet

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        raw_value = state.get(self.input_field, "")
        issues: list[str] = []
        sanitized: Any = raw_value

        if isinstance(raw_value, str) and raw_value.strip():
            sanitized = sanitize_input(raw_value)
            injection_hits = check_for_injection(sanitized)
            if injection_hits:
                issues.append(f"Potential prompt injection detected: {injection_hits[0]}")

        issues.extend(await self.extra_checks(state, sanitized))

        passed = not issues
        if not passed:
            self.logger.warning("guardrail_rejected", issues=issues)

        return {
            self.input_field: sanitized,
            "guardrail_passed": passed,
            "guardrail_issues": issues,
        }

    async def extra_checks(self, state: dict[str, Any], sanitized_input: Any) -> list[str]:
        """
        Override in feature-specific subclasses for additional structural
        validation (URL format, minimum profile completeness, etc). Return
        a list of human-readable issue strings; an empty list means no
        additional problems were found.
        """
        return []


def raise_if_guardrail_failed(state: dict[str, Any]) -> None:
    """
    Convenience for route handlers: after invoking a compiled graph,
    calling this on the resulting state converts a guardrail rejection
    into the standard `GUARDRAIL_REJECTED` HTTP error envelope, instead of
    every route re-checking `state["guardrail_passed"]` by hand.
    """
    if not state.get("guardrail_passed", True):
        raise GuardrailRejectionError(
            "Your input did not pass safety/validation checks.",
            details={"issues": state.get("guardrail_issues", [])},
        )
