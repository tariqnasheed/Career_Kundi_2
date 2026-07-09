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


def test_normal_save_does_not_generate_pdfs(temp_documents_root: Path):
    """CP2-B: normal save/seed path writes JSON/MD only; metadata stays truthful."""
    from app.agents.job_search import mock_data

    job = {
        "title": "Electrician",
        "responsibilities": ["Install wiring"],
        "requirements": ["Safety"],
        "extracted_skills": [{"skill": "Electrical"}],
    }
    questions = mock_data.mock_generate_questions(job, focus_areas=[], difficulty="auto")
    assert questions

    saved = library.save_role_pack(role_name="Electrician", questions=questions, job_snapshot=job)
    folder = Path(saved["folder"])
    assert list(folder.glob("*.pdf")) == []
    assert saved["pdf_files"] == []
    meta = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    assert meta["pdf_files"] == []
    assert meta["has_pdf"] is False
    assert not any(str(f).endswith(".pdf") for f in meta.get("source_files") or [])
    assert (folder / "structured_content.json").is_file()
    assert meta.get("has_markdown") is True

    found = library.find_role_pack("Electrician")
    assert found is not None
    assert found["questions"]
    assert (found.get("metadata") or {}).get("pdf_files") == []


def test_explicit_pdf_regeneration_remains_available(temp_documents_root: Path, monkeypatch):
    """CP2-B: explicit regenerate_pdfs_for_catalog still writes PDFs when invoked."""
    from app.agents.job_search import mock_data

    job = {
        "title": "Software Engineer",
        "responsibilities": ["Ship features"],
        "requirements": ["Python"],
        "extracted_skills": [{"skill": "Python"}],
    }
    questions = mock_data.mock_generate_questions(job, focus_areas=[], difficulty="auto")
    saved = library.save_role_pack(role_name="Software Engineer", questions=questions, job_snapshot=job)
    folder = Path(saved["folder"])
    assert list(folder.glob("*.pdf")) == []

    def _fake_pdf(**_kwargs):
        return b"%PDF-1.4 fake"

    monkeypatch.setattr(library, "export_interview_pack_pdf", _fake_pdf)
    monkeypatch.setattr(library, "export_study_material_pdf", _fake_pdf)
    monkeypatch.setattr(library, "export_questions_answers_pdf", _fake_pdf)

    stats = library.regenerate_pdfs_for_catalog(only_missing=True)
    assert stats["regenerated"] >= 1
    assert stats["failed"] == 0
    pdfs = sorted(p.name for p in folder.glob("*.pdf"))
    assert len(pdfs) == 3
    meta = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    assert meta["has_pdf"] is True
    assert len(meta["pdf_files"]) == 3


def test_seed_catalog_does_not_generate_pdfs(temp_documents_root: Path, monkeypatch):
    """CP2-B: seed_catalog_role_packs never creates PDF files."""
    from app.agents.job_search import mock_data

    catalog_roles = [
        {
            "title": "Babysitter Nanny",
            "stream_id": "education_childcare",
            "responsibilities": ["Supervise children"],
            "requirements": ["Patience"],
            "skills": ["Childcare"],
        }
    ]

    monkeypatch.setattr(
        "app.data.popular_roles_catalog.get_all_catalog_roles",
        lambda: catalog_roles,
    )
    monkeypatch.setattr(
        "app.data.popular_roles_catalog.catalog_role_to_job_snapshot",
        lambda role: {
            "title": role["title"],
            "responsibilities": role.get("responsibilities") or [],
            "requirements": role.get("requirements") or [],
            "extracted_skills": [{"skill": s} for s in (role.get("skills") or [])],
        },
    )

    # Guard: if PDF exporters are called, fail the test.
    def _boom(**_kwargs):
        raise AssertionError("PDF exporter must not be called during normal seed")

    monkeypatch.setattr(library, "export_interview_pack_pdf", _boom)
    monkeypatch.setattr(library, "export_study_material_pdf", _boom)
    monkeypatch.setattr(library, "export_questions_answers_pdf", _boom)

    stats = library.seed_catalog_role_packs(force=True, only_missing=False)
    assert stats["failed"] == 0
    assert stats["seeded"] == 1
    assert list(temp_documents_root.rglob("*.pdf")) == []

    found = library.find_role_pack("Babysitter Nanny")
    assert found is not None
    meta = found.get("metadata") or {}
    assert meta.get("pdf_files") == []
    assert meta.get("has_pdf") is False


def test_fallback_for_role_none(temp_documents_root: Path):
    fb = library.fallback_for_role("Obscure Niche Role XYZ", api_unavailable=True)
    assert fb["status"] == "none"
    assert "unavailable" in fb["message"].lower()
