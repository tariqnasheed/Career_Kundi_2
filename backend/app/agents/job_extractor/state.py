"""
agents/job_extractor/state.py
================================
LangGraph state for the job URL extraction pipeline.
"""

from __future__ import annotations
from typing import Any
from app.agents.common.state import BaseAgentState


class JobExtractorState(BaseAgentState):
    # Input
    job_url: str | None

    # Scraper output
    raw_page_text: str | None
    scrape_success: bool

    # Extractor output
    extracted_fields: dict[str, Any]
    extraction_incomplete: bool
    missing_fields: list[str]
    source_url: str | None
