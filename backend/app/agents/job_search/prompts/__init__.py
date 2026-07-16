"""Central prompt contracts for the Job Search / Interview Pack feature.

Keeping the feature-level prompt in a dedicated module (rather than an inline
string in ``agents.py``) gives us one authoritative contract that the live
Ollama executor uses and that the contract tests assert against, so the prompt
the model actually receives and the rules the finalizer/quality gates enforce
cannot silently drift apart.
"""

from app.agents.job_search.prompts.interview_pack_prompt import (
    INTERVIEW_PACK_GENERATION_SYSTEM_PROMPT,
    REQUIRED_PROMPT_CLAUSES,
    build_interview_pack_system_prompt,
)

__all__ = [
    "INTERVIEW_PACK_GENERATION_SYSTEM_PROMPT",
    "REQUIRED_PROMPT_CLAUSES",
    "build_interview_pack_system_prompt",
]
