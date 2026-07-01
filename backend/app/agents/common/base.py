"""
agents/common/base.py
=========================
`BaseAgent`: the minimal common interface implemented by every Guardrail,
Planner, Executor, and Reflector agent across all four feature pipelines.

Keeping this interface tiny is deliberate. LangGraph nodes are just
callables of `(state) -> partial_state_update`; `BaseAgent.as_node()` is
all the adaptation any agent needs to become a graph node, with consistent
timing and error-to-state-field handling applied uniformly so individual
agents don't each reimplement try/except/logging boilerplate.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Callable

from app.core.logging import get_logger


class AgentError(Exception):
    """Raised by an agent's `run()` to signal a recoverable, agent-specific failure (caught by `as_node`)."""


class BaseAgent(ABC):
    """Common base for every Guardrail / Planner / Executor / Reflector agent in the system."""

    name: str = "BaseAgent"

    def __init__(self) -> None:
        self.logger = get_logger(f"agent.{self.name}")

    @abstractmethod
    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute this agent's step given the current pipeline state and
        return the PARTIAL state update to merge in. Agents should treat
        `state` as read-only and return only the keys they're changing —
        LangGraph merges returned keys into the running state, which keeps
        every transition explicit and easy to follow in logs, rather than
        agents silently mutating a shared dict in place.
        """

    def as_node(self) -> Callable[[dict[str, Any]], Any]:
        """
        Adapt this agent into a LangGraph-compatible node callable, with
        timing and error handling wrapped around every invocation so an
        unexpected exception in one agent becomes a clean `state["error"]`
        the graph can route on, instead of an unhandled exception crashing
        the whole pipeline run.
        """

        async def node(state: dict[str, Any]) -> dict[str, Any]:
            started = time.monotonic()
            self.logger.info(
                "agent_started",
                agent=self.name,
                feature=state.get("feature"),
                request_id=state.get("request_id"),
            )
            try:
                update = await self.run(state)
            except Exception as exc:  # noqa: BLE001 — converted to state["error"] rather than crashing the graph
                self.logger.error("agent_failed", agent=self.name, error=str(exc), exc_info=True)
                return {"error": f"{self.name} failed: {exc}"}

            elapsed_ms = (time.monotonic() - started) * 1000
            self.logger.info("agent_completed", agent=self.name, elapsed_ms=round(elapsed_ms, 1))
            return update

        return node
