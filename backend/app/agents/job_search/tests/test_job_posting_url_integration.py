"""Integration tests for job posting URL extraction in interview-pack flow (004E-B)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE", "false")

from app.agents.job_search.job_coverage_audit import audit_pack_coverage
from app.agents.job_search.job_intelligence import build_job_intelligence_profile
from app.agents.job_search.job_posting_extractor import enrich_job_snapshot_from_posting_url
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.agents.job_search.quality.silly_question_guard import is_silly_question

JSON_LD_HTML = """
<html><head><script type="application/ld+json">
{
  "@type": "JobPosting",
  "title": "Data Analyst",
  "description": "Analytics role for retail KPI reporting.",
  "hiringOrganization": {"name": "Northline Analytics"},
  "responsibilities": ["SQL dashboard creation", "Daily data quality checks"],
  "qualifications": ["Strong SQL", "Preferred: Python automation"],
  "skills": ["SQL", "Power BI"]
}
</script></head><body></body></html>
"""


@pytest.mark.asyncio
async def test_url_extraction_feeds_intelligence_profile():
    merged, extraction = await enrich_job_snapshot_from_posting_url(
        {"title": "Data Analyst", "source_url": "https://example.com/jobs/da"},
        html=JSON_LD_HTML,
    )
    assert extraction is not None
    assert extraction.extraction_confidence == "high"
    profile = build_job_intelligence_profile(merged)
    assert profile.job_posting_url
    assert profile.extracted_link_content
    assert profile.source_status["link_extraction"] == "used"
    assert len(profile.responsibilities) >= 2 or len(profile.required_skills) >= 2


@pytest.mark.asyncio
async def test_manual_plus_url_merge_coverage():
    merged, _ = await enrich_job_snapshot_from_posting_url(
        {
            "title": "Data Analyst",
            "company_name": "User Override Corp",
            "requirements": ["User-listed stakeholder communication skill"],
            "source_url": "https://example.com/jobs/da",
        },
        html=JSON_LD_HTML,
    )
    assert merged["company_name"] == "User Override Corp"
    questions = mock_generate_questions(merged, focus_areas=[], difficulty="auto")
    profile = build_job_intelligence_profile(merged)
    audit = audit_pack_coverage(profile, questions)
    assert audit.total_items >= 1
    assert audit.coverage_score >= 0


@pytest.mark.asyncio
async def test_no_fake_urls_in_pack_output():
    merged, extraction = await enrich_job_snapshot_from_posting_url(
        {"title": "Data Analyst"},
        "https://example.com/jobs/da",
        html=JSON_LD_HTML,
    )
    assert extraction.source_url.startswith("https://")
    questions = mock_generate_questions(merged, focus_areas=[], difficulty="auto")
    blob = " ".join(
        str(q.get("question", "")) + str(q.get("model_answer", ""))
        for q in questions
        if not q.get("export_blocked")
    )
    assert "http://fake" not in blob.lower()
    assert "example.com/fake" not in blob.lower()


@pytest.mark.asyncio
async def test_silly_and_blocked_phrases_not_in_url_pack():
    merged, _ = await enrich_job_snapshot_from_posting_url(
        {"title": "Data Analyst"},
        "https://example.com/jobs/da",
        html=JSON_LD_HTML,
    )
    questions = mock_generate_questions(merged, focus_areas=[], difficulty="auto")
    for q in questions:
        if q.get("export_blocked"):
            continue
        assert not is_silly_question(q.get("question", ""))
    answers = [q.get("model_answer", "") for q in questions if q.get("model_answer")]
    assert export_blocked_phrase_count("\n".join(answers)) == 0
