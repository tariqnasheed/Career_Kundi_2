"""
test_llm_authored_preservation.py
=================================
Regression tests for the "Gemini authors; templates ground & validate" redesign
(see docs/reports/interview_pack_llm_authoring.md).

The interview-pack pipeline used to overwrite every question's model_answer and
common_mistakes with a deterministic, role-FAMILY-keyed template engine. That is
why every question in a role showed the SAME three "common mistakes" and
near-identical answers. These tests lock in the new contract:

1. LIVE mode: distinct LLM-authored `model_answer` / `common_mistakes` survive
   finalization instead of being replaced by the family template, and
   `content_source` records the provenance.
2. LIVE mode, no LLM content (e.g. a coverage-plan filler question): the
   deterministic engine still authors it, tagged `deterministic_fallback`.
3. MOCK mode: behaviour is unchanged — deterministic authoring runs and the
   preservation guards are inert (`deterministic_mock`).
4. The Reflector's cross-question gate flags reused common_mistakes and
   near-duplicate answers in LIVE mode, and stays silent in MOCK mode.
"""

from __future__ import annotations

import pytest

from app.agents.job_search import mock_data
from app.agents.job_search.agents import InterviewPackReflectorAgent
from app.core.config import settings

# A hardcoded family-template mistake — its ABSENCE proves the LLM list won.
FAMILY_TEMPLATE_MISTAKE = "Deploying without a rollback plan."


@pytest.fixture
def se_job() -> dict:
    return {
        "title": "Software Engineer",
        "description_raw": "Build and ship features in JavaScript and TypeScript.",
        "responsibilities": ["Build and ship product features", "Review pull requests"],
        "requirements": ["Strong JavaScript", "Testing discipline"],
        "extracted_skills": [{"skill": "JavaScript"}, {"skill": "TypeScript"}],
    }


def _force_mode(monkeypatch: pytest.MonkeyPatch, *, live: bool) -> None:
    """Force settings.llm_mode by pinning the provider explicitly (robust to an
    `LLM_PROVIDER=ollama` override in .env)."""
    monkeypatch.setattr(settings, "llm_provider", "gemini" if live else "mock")
    monkeypatch.setattr(settings, "gemini_api_key", "AQ.test-key" if live else "")
    assert settings.llm_mode == ("live" if live else "mock")


def _llm_question(skill: str, answer: str, mistakes: list[str]) -> dict:
    return {
        "category": "technical",
        "question": f"Explain how {skill} works and a tricky bug you fixed with it.",
        "why_asked": f"Probes real hands-on depth with {skill}.",
        "skill_tag": skill,
        "model_answer": answer,
        "common_mistakes": mistakes,
        "study_material": {
            "overview": (
                f"{skill} is a core language feature. This overview explains the "
                f"underlying execution model, the runtime semantics, and worked "
                f"examples so a candidate can reason about {skill} from first principles."
            ),
            "definitions": [{"term": skill, "definition": f"A precise definition of {skill}."}],
        },
    }


CLOSURE_ANSWER = (
    "A closure is a function bundled together with references to its surrounding "
    "lexical scope. In JavaScript the inner function keeps access to the outer "
    "function's variables even after the outer function returns. The classic bug I "
    "fixed was a loop that created handlers with var: every handler captured the same "
    "binding and read the final loop value. Switching to let gave each iteration its "
    "own block-scoped binding, so each handler captured the correct value. I verified "
    "the fix with a unit test that asserted each handler returned its own index."
)
CLOSURE_MISTAKES = [
    "Assuming each loop iteration gets its own variable when using var.",
    "Believing a closure copies values instead of capturing a live reference.",
]

ASYNC_ANSWER = (
    "async/await is syntax over promises. An async function always returns a promise, "
    "and await pauses that function until the awaited promise settles, without blocking "
    "the event loop. A production bug I fixed was a forgotten await inside a try/catch: "
    "the promise rejected after the try block had already exited, so the error escaped as "
    "an unhandled rejection. Adding the await let the catch see it. I also parallelised two "
    "independent awaits with Promise.all to cut latency roughly in half."
)
ASYNC_MISTAKES = [
    "Forgetting await so errors escape the surrounding try/catch.",
    "Awaiting independent promises sequentially instead of with Promise.all.",
]


def test_live_mode_preserves_distinct_llm_content(monkeypatch, se_job):
    _force_mode(monkeypatch, live=True)

    q = _llm_question("JavaScript closures", CLOSURE_ANSWER, list(CLOSURE_MISTAKES))
    out = mock_data._finalize_question(q, se_job, "auto", 0)

    # Provenance says the content is LLM-authored.
    assert out["content_source"] in ("gemini", "gemini_partial"), out["content_source"]

    # The question-specific mistakes survived; the family template did NOT win.
    joined = " ".join(out["common_mistakes"]).lower()
    assert "var" in joined or "closure" in joined, out["common_mistakes"]
    assert FAMILY_TEMPLATE_MISTAKE.lower() not in joined

    # The model answer is still the LLM's distinctive prose, not the family opener.
    assert "lexical scope" in out["model_answer"].lower()
    assert "building and operating cloud services" not in out["model_answer"].lower()


def test_live_mode_authors_filler_questions_deterministically(monkeypatch, se_job):
    """A draft with no LLM content (e.g. a coverage filler) is still authored by templates."""
    _force_mode(monkeypatch, live=True)

    draft = {
        "category": "technical",
        "question": "What is a REST API and how would you design one for this role?",
        "why_asked": "Checks API fundamentals.",
        "skill_tag": "APIs",
    }
    out = mock_data._finalize_question(draft, se_job, "auto", 0)

    assert out["content_source"] == "deterministic_fallback", out["content_source"]
    assert (out.get("model_answer") or "").strip(), "filler question should still get an authored answer"


def test_mock_mode_is_unchanged(monkeypatch, se_job):
    _force_mode(monkeypatch, live=False)

    # Even if content is present, mock mode authors deterministically (no preservation).
    q = _llm_question("JavaScript closures", CLOSURE_ANSWER, list(CLOSURE_MISTAKES))
    out = mock_data._finalize_question(q, se_job, "auto", 0)

    assert out["content_source"] == "deterministic_mock", out["content_source"]
    assert (out.get("model_answer") or "").strip()


@pytest.mark.asyncio
async def test_reflector_flags_cross_question_duplicates_live(monkeypatch, se_job):
    _force_mode(monkeypatch, live=True)

    reflector = InterviewPackReflectorAgent()
    same_answer = CLOSURE_ANSWER
    same_mistakes = list(CLOSURE_MISTAKES)
    draft = {
        "questions": [
            _llm_question("JavaScript closures", same_answer, same_mistakes),
            _llm_question("Scope chains", same_answer, list(same_mistakes)),
        ]
    }
    issues = await reflector.domain_checks({}, draft)
    text = " ".join(issues).lower()
    assert "identical common_mistakes" in text, issues
    assert "near-duplicate" in text, issues


@pytest.mark.asyncio
async def test_reflector_silent_on_duplicates_in_mock(monkeypatch, se_job):
    _force_mode(monkeypatch, live=False)

    reflector = InterviewPackReflectorAgent()
    draft = {
        "questions": [
            _llm_question("JavaScript closures", CLOSURE_ANSWER, list(CLOSURE_MISTAKES)),
            _llm_question("Scope chains", CLOSURE_ANSWER, list(CLOSURE_MISTAKES)),
        ]
    }
    issues = await reflector.domain_checks({}, draft)
    text = " ".join(issues).lower()
    assert "identical common_mistakes" not in text
    assert "near-duplicate" not in text


@pytest.mark.asyncio
async def test_reflector_passes_distinct_questions_live(monkeypatch, se_job):
    """Genuinely distinct answers/mistakes must NOT be flagged as duplicates."""
    _force_mode(monkeypatch, live=True)

    reflector = InterviewPackReflectorAgent()
    draft = {
        "questions": [
            _llm_question("JavaScript closures", CLOSURE_ANSWER, list(CLOSURE_MISTAKES)),
            _llm_question("async/await", ASYNC_ANSWER, list(ASYNC_MISTAKES)),
        ]
    }
    issues = await reflector.domain_checks({}, draft)
    text = " ".join(issues).lower()
    assert "identical common_mistakes" not in text, issues
    assert "near-duplicate" not in text, issues
