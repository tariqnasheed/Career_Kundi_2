"""
agents/common/cost_monitor.py
=================================
`CostMonitor`: implements §3.3's cost-optimization mandates as shared,
reusable logic rather than something each feature reimplements:

- **Tiered model selection** — `recommend_tier()` escalates "flash" ->
  "pro" only when task complexity signals warrant it (long input, a prior
  low-confidence reflection round, or an explicit complexity hint), rather
  than defaulting every call to the most expensive model.
- **Token budget enforcement** — `assert_within_budget()` raises
  `TokenBudgetExceededError` the moment a request exceeds
  `settings.token_budget_per_request`, so a runaway revision loop fails
  loudly instead of silently accumulating cost.
- **Usage accounting** — `record()` accumulates token counts from every
  `LLMResponse` seen during a pipeline run; `persist()` optionally writes a
  `TokenUsageRecord` row for the usage analytics dashboard.

One `CostMonitor` instance is created per pipeline run (per HTTP request)
and threaded through the LangGraph state so every agent's LLM calls feed
the same running total.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import settings
from app.core.errors import TokenBudgetExceededError
from app.core.logging import get_logger
from app.tools.llm import LLMResponse, ModelTier

logger = get_logger(__name__)

# Rough per-1M-token USD pricing used ONLY to populate the cost dashboard
# estimate shown to admins — never used for actual billing. Mock-mode usage
# is always recorded at $0 regardless of these figures, since no real API
# call occurred.
_PRICE_PER_MILLION_TOKENS_USD: dict[str, float] = {
    "flash": 0.15,
    "pro": 2.50,
    "mock": 0.0,
}


class CostMonitor:
    """Per-pipeline-run token/cost accumulator and tier-escalation policy."""

    def __init__(self, feature: str, *, token_budget: int | None = None) -> None:
        self.feature = feature
        self.token_budget = token_budget or settings.token_budget_per_request
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.estimated_cost_usd = 0.0
        self.calls: list[dict] = []

    def record(self, response: LLMResponse, *, tier: str) -> None:
        """Accumulate token usage from one LLM call, update the running cost estimate, and re-check the budget."""
        self.prompt_tokens += response.prompt_tokens
        self.completion_tokens += response.completion_tokens

        price_key = "mock" if "mock" in response.model else tier
        price = _PRICE_PER_MILLION_TOKENS_USD.get(price_key, 0.0)
        call_cost = ((response.prompt_tokens + response.completion_tokens) / 1_000_000) * price
        self.estimated_cost_usd += call_cost

        self.calls.append(
            {
                "model": response.model,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "cache_hit": response.cache_hit,
            }
        )
        self.assert_within_budget()

    def assert_within_budget(self) -> None:
        total = self.prompt_tokens + self.completion_tokens
        if total > self.token_budget:
            logger.error("token_budget_exceeded", feature=self.feature, total=total, budget=self.token_budget)
            raise TokenBudgetExceededError(
                f"This request exceeded its token budget ({total}/{self.token_budget} tokens).",
                details={"feature": self.feature, "total_tokens": total, "budget": self.token_budget},
            )

    def recommend_tier(
        self,
        *,
        input_length_chars: int,
        prior_confidence: float | None = None,
        force_pro: bool = False,
    ) -> ModelTier:
        """
        Escalate to the "pro" tier only when warranted: long input (>6000
        chars — a dense job description or a full profile export), a
        previous reflection round flagged low confidence (<0.6) and the
        Executor needs a stronger rewrite, or the caller explicitly
        requests it for a known-complex sub-task (e.g. system-design
        interview question generation). Otherwise stays on "flash" — the
        cheap default for routine generation.
        """
        if force_pro:
            return "pro"
        if prior_confidence is not None and prior_confidence < 0.6:
            return "pro"
        if input_length_chars > 6000:
            return "pro"
        return "flash"

    def summary(self) -> dict:
        """Snapshot dict suitable for embedding in an API response or audit log entry."""
        return {
            "feature": self.feature,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "num_calls": len(self.calls),
            "budget": self.token_budget,
        }

    async def persist(self, db, user_id: str | None, model_used: str) -> None:
        """
        Persist a `TokenUsageRecord` row for the usage analytics dashboard.
        Takes an AsyncSession explicitly rather than acquiring its own —
        callers without a DB session handy (unit tests, dry runs) simply
        skip calling this; every other method on this class works without
        a database.
        """
        from app.db.models.audit import TokenUsageRecord

        record = TokenUsageRecord(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            feature=self.feature,
            model_used=model_used,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            cache_hit=any(c["cache_hit"] for c in self.calls),
            estimated_cost_usd=self.estimated_cost_usd,
        )
        db.add(record)
        await db.flush()
