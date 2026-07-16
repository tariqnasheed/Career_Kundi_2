"""JOB-INT-R1 §4/§14: the active interview-pack prompt is a formal contract.

These tests assert the prompt the live executor actually hands to the LLM
contains every required clause, and that the executor is wired to the central
prompt module (not an ad-hoc inline string). If a clause is dropped the contract
regresses and these tests fail.
"""

from __future__ import annotations

import inspect

from app.agents.job_search import agents as job_search_agents
from app.agents.job_search.prompts import (
    INTERVIEW_PACK_GENERATION_SYSTEM_PROMPT,
    REQUIRED_PROMPT_CLAUSES,
    build_interview_pack_system_prompt,
)


def _norm(text: str) -> str:
    """Whitespace-normalized prompt so clause checks are line-wrap agnostic."""
    return " ".join((text or "").split())


PROMPT = _norm(INTERVIEW_PACK_GENERATION_SYSTEM_PROMPT)


def test_all_required_clauses_present_in_contract() -> None:
    for name, marker in REQUIRED_PROMPT_CLAUSES.items():
        assert _norm(marker) in PROMPT, f"missing clause: {name}"


def test_prompt_has_patient_phd_scholar_master_teacher() -> None:
    assert "patient PhD-level scholar, master teacher" in PROMPT


def test_prompt_supports_all_streams() -> None:
    low = PROMPT.lower()
    assert "across all professional and educational streams" in PROMPT
    # A spread of streams is enumerated, not just tech.
    for stream in ("healthcare", "finance", "law", "hospitality", "trades", "education"):
        assert stream in low, f"stream missing from prompt: {stream}"


def test_prompt_requires_realistic_candidate_answer() -> None:
    assert "the ACTUAL words a candidate could speak in an interview" in PROMPT
    assert "It must NOT be coaching." in PROMPT


def test_prompt_forbids_fake_experience() -> None:
    assert "Never invent past employers, degrees, certifications" in PROMPT
    assert "haven't claimed direct production experience" in PROMPT


def test_prompt_requires_question_specific_study_material() -> None:
    assert "Each question must have its OWN study_material object" in PROMPT


def test_prompt_requires_local_ollama_no_cloud() -> None:
    assert "local Ollama" in PROMPT
    assert "Do not call Gemini, OpenAI, Anthropic, Groq," in PROMPT


def test_prompt_requires_json_only() -> None:
    assert "Return valid JSON only" in PROMPT
    assert "Do not use markdown code fences" in PROMPT


def test_composed_prompt_wraps_shared_directives() -> None:
    composed = _norm(build_interview_pack_system_prompt())
    # Contract text is present…
    assert "CareerKundi's Interview Pack Authoring Agent" in composed
    # …and so are the shared anti-hallucination / rejection scaffolds.
    assert "rejected" in composed.lower()


def test_executor_uses_central_prompt_not_inline_string() -> None:
    src = inspect.getsource(job_search_agents)
    assert "build_interview_pack_system_prompt()" in src
    # The old compressed inline role constant must be gone.
    assert "_INTERVIEW_ROLE" not in src


def test_prompt_persona_phrases_are_confined_to_the_prompt() -> None:
    # The persona is fine inside the SYSTEM prompt, but the prompt itself must
    # instruct the model never to surface it in the answer.
    assert 'never write "PhD-level scholar"' in PROMPT
