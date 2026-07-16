"""JOB-INT-R1 §12B/§14: honesty & provenance — no fabricated candidate history.

Two levels:
* Unit level on the claim rewriter: fabricated past events / metrics are dropped,
  but first-person *approach* statements survive in the FIRST person (they must
  never be flipped to a second-person "you could" coaching voice).
* Pack level: a thin job (no user experience) must not surface unsupported
  personal or numeric claims in any finalized model answer.
"""

from __future__ import annotations

import os

os.environ.setdefault("LLM_PROVIDER", "mock")

from app.agents.job_search import mock_data
from app.agents.job_search.quality.claim_integrity import (
    detect_unsupported_numeric_claims,
    detect_unsupported_personal_claims,
    rewrite_or_flag_unsupported_claims,
)

_THIN_JOB = {"title": "Data Analyst", "responsibilities": ["Build dashboards"]}


def test_rewrite_keeps_method_statements_first_person() -> None:
    text = "I would start by validating the data. Then I would check the join keys."
    rewritten, _meta = rewrite_or_flag_unsupported_claims(text, _THIN_JOB)
    low = rewritten.lower()
    assert "i would start by validating the data" in low
    # Must NOT be converted into second-person coaching voice.
    assert "you could" not in low
    assert "you would" not in low


def test_rewrite_drops_fabricated_event_and_metric() -> None:
    text = (
        "I would start by profiling the dataset. "
        "At my previous company I cut report runtime from 48 seconds to 6 seconds."
    )
    rewritten, meta = rewrite_or_flag_unsupported_claims(text, _THIN_JOB)
    low = rewritten.lower()
    # The honest approach statement survives, first person.
    assert "i would start by profiling the dataset" in low
    # The fabricated employer + metric is gone.
    assert "previous company" not in low
    assert "48 seconds" not in low and "6 seconds" not in low
    assert meta["rewritten_for_claim_integrity"] is True


def test_collective_history_is_personalised_not_second_person() -> None:
    text = "We rolled out the pipeline. Our team monitored it."
    rewritten, _meta = rewrite_or_flag_unsupported_claims(text, _THIN_JOB)
    low = rewritten.lower()
    assert "you could" not in low and "the team could" not in low


def test_thin_pack_has_no_unsupported_claims_in_answers() -> None:
    job = {
        "title": "Software Engineer",
        "responsibilities": ["Build and maintain backend services"],
        "requirements": ["Python", "Testing"],
        "extracted_skills": [{"skill": "Python"}, {"skill": "Testing"}],
    }
    qs = mock_data.mock_generate_questions(job, focus_areas=[], difficulty="auto")
    for q in qs:
        answer = q.get("model_answer") or ""
        if not answer.strip():
            continue
        assert not detect_unsupported_personal_claims(answer, job), (
            f"unsupported personal claim in: {answer[:160]}"
        )
        assert not detect_unsupported_numeric_claims(answer, job), (
            f"unsupported numeric claim in: {answer[:160]}"
        )
