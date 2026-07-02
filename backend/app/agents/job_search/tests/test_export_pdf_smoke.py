from __future__ import annotations

import tempfile
from pathlib import Path

from app.agents.job_search.quality.export_quality_audit import audit_export_markdown, prepare_interview_pack_export
from app.tools.document_export import export_interview_pack_pdf

MIN_MARKDOWN_BYTES = 4000
MIN_PDF_BYTES = 5000

PDF_RENDER_SKIP_REASON: str | None = None
try:
    from weasyprint import HTML  # noqa: F401
except ImportError:
    PDF_RENDER_SKIP_REASON = "weasyprint is not installed in this environment"


def _job(role: str, skill: str) -> dict:
    return {
        "title": role,
        "responsibilities": [f"Deliver {skill} work safely and accurately"],
        "requirements": [skill],
        "extracted_skills": [{"skill": skill}],
    }


def _export_role_smoke(role: str, skill: str, out_dir: Path) -> dict:
    job = _job(role, skill)
    markdown, questions, role_overview = prepare_interview_pack_export(job, focus_skill=skill, difficulty="medium")
    audit = audit_export_markdown(
        markdown,
        role=role,
        questions=questions,
        role_overview=role_overview,
    )

    slug = role.lower().replace(" ", "_")
    md_path = out_dir / f"{slug}_interview_pack.md"
    md_path.write_text(markdown, encoding="utf-8")
    assert md_path.exists(), f"{role} / export: Markdown file missing at {md_path}"
    assert md_path.stat().st_size >= MIN_MARKDOWN_BYTES, (
        f"{role} / export: Markdown file too small "
        f"(expected >= {MIN_MARKDOWN_BYTES} bytes, actual {md_path.stat().st_size})"
    )
    assert audit["passed"], f"{role} / markdown audit failed (score={audit['score']}): {audit['errors']}"

    pdf_result = {
        "role": role,
        "markdown_path": str(md_path),
        "markdown_bytes": md_path.stat().st_size,
        "markdown_audit": audit,
        "pdf_path": None,
        "pdf_bytes": 0,
        "pdf_skipped": False,
        "pdf_skip_reason": None,
    }

    pdf_path = out_dir / f"{slug}_interview_pack.pdf"
    if PDF_RENDER_SKIP_REASON:
        pdf_result["pdf_skipped"] = True
        pdf_result["pdf_skip_reason"] = PDF_RENDER_SKIP_REASON
        return pdf_result

    pdf_bytes = export_interview_pack_pdf(
        job_title=role,
        company_name=None,
        questions=questions,
        role_overview=role_overview,
    )
    pdf_path.write_bytes(pdf_bytes)
    assert pdf_path.exists(), f"{role} / export: PDF file missing at {pdf_path}"
    assert pdf_path.stat().st_size >= MIN_PDF_BYTES, (
        f"{role} / export: PDF file too small "
        f"(expected >= {MIN_PDF_BYTES} bytes, actual {pdf_path.stat().st_size})"
    )
    pdf_result["pdf_path"] = str(pdf_path)
    pdf_result["pdf_bytes"] = pdf_path.stat().st_size
    return pdf_result


def test_export_pdf_smoke_representative_roles() -> None:
    with tempfile.TemporaryDirectory(prefix="interview_pack_export_") as tmp:
        out_dir = Path(tmp)
        results = [
            _export_role_smoke("DevOps Engineer", "AWS", out_dir),
            _export_role_smoke("Barista", "Coffee Preparation", out_dir),
        ]

        for result in results:
            assert result["markdown_audit"]["passed"]
            if result["pdf_skipped"]:
                assert result["pdf_skip_reason"], "PDF skip must include an explicit environment reason"
            else:
                assert result["pdf_bytes"] >= MIN_PDF_BYTES
