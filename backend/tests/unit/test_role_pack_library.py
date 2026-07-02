"""Unit tests for the role-pack document library service."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import role_pack_library as library


@pytest.fixture
def temp_documents_root(tmp_path, monkeypatch):
    docs = tmp_path / "documents"
    monkeypatch.setattr(library.settings, "documents_root", str(docs))
    library.ensure_library_layout()
    return docs


def test_normalize_role_slug():
    assert library.normalize_role_slug("Software Engineer") == "software_engineer"
    assert library.normalize_role_slug("  Electrical Design Engineer!!! ") == "electrical_design_engineer"


def test_classify_role_category():
    assert library.classify_role_category("Registered Nurse") == "healthcare"
    assert library.classify_role_category("Quantum Widget Specialist") == "custom_roles"


def test_save_and_find_role_pack(temp_documents_root: Path):
    from app.agents.job_search import mock_data

    job = {
        "title": "Data Analyst",
        "responsibilities": ["Build dashboards"],
        "requirements": ["SQL"],
        "extracted_skills": [{"skill": "SQL"}],
    }
    questions = mock_data.mock_generate_questions(job, focus_areas=[], difficulty="auto")
    assert questions

    saved = library.save_role_pack(role_name="Data Analyst", questions=questions, job_snapshot=job)
    assert saved["role_slug"] == "data_analyst"
    assert (temp_documents_root / "indexes" / "role_index.json").exists()

    found = library.find_role_pack("Data Analyst")
    assert found is not None
    assert len(found["questions"]) == len(questions)
    assert found["metadata"]["question_count"] == len(questions)


def test_fallback_for_role_none(temp_documents_root: Path):
    fb = library.fallback_for_role("Obscure Niche Role XYZ", api_unavailable=True)
    assert fb["status"] == "none"
    assert "unavailable" in fb["message"].lower()
