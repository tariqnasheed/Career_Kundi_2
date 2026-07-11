"""
Unit tests for deterministic CV Markdown rendering
(app/tools/document_export.py::build_markdown).

These exercise the pure Markdown intermediate representation that every export
format (PDF/DOCX/Markdown) is built from — no WeasyPrint/python-docx needed.
"""

from app.tools.document_export import (
    build_markdown,
    resolve_pdf_template_style,
    safe_cv_export_filename,
)


def test_build_markdown_includes_name_contact_and_sections():
    rendered = {
        "personal_info": {"full_name": "Ada Lovelace", "email": "ada@example.com", "location": "London"},
        "sections": [
            {"section_id": "summary", "title": "Summary", "content": "Analytical engine pioneer."},
            {"section_id": "skills", "title": "Skills", "items": ["Mathematics", "Programming"]},
        ],
    }
    md = build_markdown(rendered)
    assert "# Ada Lovelace" in md
    assert "ada@example.com" in md
    assert "## Summary" in md
    assert "Analytical engine pioneer." in md
    assert "Mathematics, Programming" in md


def test_build_markdown_handles_empty_input_without_crashing():
    md = build_markdown({})
    assert "# Untitled" in md


def test_resolve_pdf_template_style_accepts_backend_and_frontend_ids():
    assert resolve_pdf_template_style("modern", None) == "modern"
    assert resolve_pdf_template_style("minimal-corporate", "modern") == "classic"
    assert resolve_pdf_template_style("government-ats", None) == "compact"
    assert resolve_pdf_template_style(None, "creative") == "creative"


def test_resolve_pdf_template_style_rejects_unknown():
    try:
        resolve_pdf_template_style("not-a-real-template", "modern")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "Unknown CV template_id" in str(exc)


def test_safe_cv_export_filename_sanitizes_unsafe_characters():
    name = safe_cv_export_filename(
        candidate_name="Ada Lovelace / CEO",
        template_label="Minimal Corporate",
        extension="pdf",
    )
    assert name == "CareerKundi_Ada_Lovelace_CEO_Minimal_Corporate_CV.pdf"
    assert "@" not in name
    assert "/" not in name
