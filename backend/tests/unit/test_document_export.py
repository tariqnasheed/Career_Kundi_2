"""
Unit tests for deterministic CV Markdown rendering
(app/tools/document_export.py::build_markdown).

These exercise the pure Markdown intermediate representation that every export
format (PDF/DOCX/Markdown) is built from — no WeasyPrint/python-docx needed.
"""

from app.tools.document_export import build_markdown


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
