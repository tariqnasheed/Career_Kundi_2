from __future__ import annotations

import tempfile
from pathlib import Path

from app.agents.job_search.quality.export_quality_audit import prepare_interview_pack_export
from app.tools.document_export import export_interview_pack_pdf

PDF_TEXT_SKIP_REASON: str | None = None
PdfReader = None
try:
    from pypdf import PdfReader as _PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader as _PdfReader
    except ImportError:
        PDF_TEXT_SKIP_REASON = "pypdf/PyPDF2 not installed for PDF text extraction"
    else:
        PdfReader = _PdfReader
else:
    PdfReader = _PdfReader


def test_pdf_text_smoke() -> None:
    if PDF_TEXT_SKIP_REASON:
        print(f"SKIP PDF text extraction: {PDF_TEXT_SKIP_REASON}")
        return

    assert PdfReader is not None
    role = "DevOps Engineer"
    skill = "AWS"
    job = {
        "title": role,
        "responsibilities": [f"Deliver {skill} work safely and accurately"],
        "requirements": [skill],
        "extracted_skills": [{"skill": skill}],
    }
    _markdown, questions, role_overview = prepare_interview_pack_export(job, focus_skill=skill, difficulty="medium")

    with tempfile.TemporaryDirectory(prefix="pdf_text_smoke_") as tmp:
        pdf_path = Path(tmp) / "devops_interview_pack.pdf"
        pdf_bytes = export_interview_pack_pdf(
            job_title=role,
            company_name=None,
            questions=questions,
            role_overview=role_overview,
        )
        pdf_path.write_bytes(pdf_bytes)
        reader = PdfReader(str(pdf_path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages).lower()

    required_fragments = [
        role.lower(),
        "employer expectations",
        "skill map",
        "model answer",
        "study material",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in text]
    assert not missing, f"PDF text missing required fragments: {missing}"
