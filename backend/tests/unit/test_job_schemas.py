"""
Unit tests for job-search request schemas:
  - SavedJobCreate coerces the blank strings the frontend form sends
  - JobStatusUpdate only accepts the five valid tracker states
"""

import pytest
from pydantic import ValidationError

from app.schemas.job_search import JobStatusUpdate, SavedJobCreate


def test_blank_salary_becomes_none_and_numeric_string_coerces():
    m = SavedJobCreate(title="Backend Engineer", salary_min="", salary_max="120000")
    assert m.salary_min is None
    assert m.salary_max == 120000.0


def test_extra_fields_are_ignored():
    m = SavedJobCreate(title="X", some_unexpected_field="ignored")
    assert not hasattr(m, "some_unexpected_field")


def test_missing_title_defaults():
    assert SavedJobCreate().title == "Untitled Role"


def test_status_update_accepts_valid():
    assert JobStatusUpdate(status="applied").status == "applied"


def test_status_update_rejects_invalid():
    with pytest.raises(ValidationError):
        JobStatusUpdate(status="not-a-real-status")
