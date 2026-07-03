"""Study-material source metadata and default source ladder (Iteration 004A foundation)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.agents.job_search.quality.surface_text_normalize import normalize_surface_text

StudySourceType = Literal["web", "model", "document_library", "local_fallback"]
StudySourceStatus = Literal["used", "available_not_used", "failed", "not_configured"]

_SOURCE_LABELS: dict[StudySourceType, str] = {
    "web": "Web research",
    "model": "Model knowledge",
    "document_library": "Document library",
    "local_fallback": "Local deterministic study material",
}


def _normalize_source_text(text: str) -> str:
    return normalize_surface_text(text or "")


def _normalize_source_entry(entry: dict[str, Any]) -> dict[str, Any]:
    out = dict(entry)
    for key in ("label", "note", "url", "document_path"):
        if isinstance(out.get(key), str):
            out[key] = _normalize_source_text(out[key])
    return out


def normalize_study_source_dict(study_sources: dict[str, Any]) -> dict[str, Any]:
    """Normalize study source metadata prose for export-safe spacing."""
    out = dict(study_sources or {})
    if isinstance(out.get("summary"), str):
        out["summary"] = _normalize_source_text(out["summary"])
    out["sources"] = [
        _normalize_source_entry(s) if isinstance(s, dict) else s for s in (out.get("sources") or [])
    ]
    return out


@dataclass
class StudySource:
    source_type: StudySourceType
    label: str
    status: StudySourceStatus
    url: str | None = None
    document_path: str | None = None
    confidence: float | None = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "source_type": self.source_type,
            "label": self.label,
            "status": self.status,
            "note": self.note,
        }
        if self.url:
            out["url"] = self.url
        if self.document_path:
            out["document_path"] = self.document_path
        if self.confidence is not None:
            out["confidence"] = self.confidence
        return out


@dataclass
class StudySourceBundle:
    sources: list[StudySource] = field(default_factory=list)
    summary: str = ""

    @property
    def used_source_types(self) -> list[StudySourceType]:
        return [s.source_type for s in self.sources if s.status == "used"]

    def to_dict(self) -> dict[str, Any]:
        return normalize_study_source_dict(
            {
                "used_source_types": self.used_source_types,
                "sources": [s.to_dict() for s in self.sources],
                "summary": _normalize_source_text(self.summary),
            }
        )


def _role_has_document_library_pack(role_title: str) -> tuple[bool, str | None]:
    """Return whether a saved role pack exists in documents/interview_packs/."""
    try:
        from app.services.role_pack_library import find_role_pack

        pack = find_role_pack(role_title)
    except Exception:
        return False, None
    if not pack:
        return False, None
    folder = pack.get("folder")
    return True, str(folder) if folder else None


def build_default_study_source_bundle(
    *,
    role_title: str,
    generation_mode: str = "deterministic",
    document_retrieval: Any | None = None,
    model_knowledge: Any | None = None,
) -> StudySourceBundle:
    """
    Build the default four-step source ladder for deterministic generation.

    Web and model retrieval are not enabled in this iteration; local compiler
    content is marked as used. Document library status reflects retrieval result
    when provided.
    """
    from app.agents.job_search.knowledge.document_library_retriever import (
        DocumentLibraryRetrievalResult,
    )

    retrieval = document_retrieval
    if retrieval is None:
        has_library, library_path = _role_has_document_library_pack(role_title)
        pack_exists = has_library
        doc_status: StudySourceStatus = "available_not_used" if has_library else "not_configured"
        doc_path = _relative_library_path_for_display(library_path) if library_path else None
        doc_note = (
            "Saved role pack exists in the document library but is not used for this question yet."
            if has_library
            else "No saved role pack found in the document library for this role."
        )
        doc_score = None
    elif isinstance(retrieval, DocumentLibraryRetrievalResult):
        pack_exists = retrieval.pack_exists
        doc_status = retrieval.status
        doc_path = retrieval.document_path
        doc_note = retrieval.note
        doc_score = retrieval.relevance_score if retrieval.matched else None
    else:
        pack_exists = bool(getattr(retrieval, "pack_exists", False))
        doc_status = getattr(retrieval, "status", "not_configured")
        doc_path = getattr(retrieval, "document_path", None)
        doc_note = getattr(retrieval, "note", "")
        doc_score = getattr(retrieval, "relevance_score", None)

    web = StudySource(
        source_type="web",
        label=_SOURCE_LABELS["web"],
        status="not_configured",
        note="Web research retrieval is not configured in this iteration.",
    )
    from app.agents.job_search.knowledge.model_knowledge import (
        ModelKnowledgeResult,
        generate_model_knowledge,
        model_knowledge_study_source_status,
    )

    if generation_mode == "llm":
        model = StudySource(
            source_type="model",
            label=_SOURCE_LABELS["model"],
            status="available_not_used",
            note="LLM generation may be active for answers; study modules still use local compiler paths.",
        )
    else:
        mk_result = model_knowledge if isinstance(model_knowledge, ModelKnowledgeResult) else None
        if mk_result is None:
            mk_result = generate_model_knowledge({}, {"title": role_title})
        mk_status, mk_note = model_knowledge_study_source_status(mk_result)
        model = StudySource(
            source_type="model",
            label=_SOURCE_LABELS["model"],
            status=mk_status,  # type: ignore[arg-type]
            note=mk_note,
        )
    if pack_exists or doc_path:
        document = StudySource(
            source_type="document_library",
            label=_SOURCE_LABELS["document_library"],
            status=doc_status,
            document_path=doc_path,
            confidence=doc_score,
            note=doc_note,
        )
    else:
        document = StudySource(
            source_type="document_library",
            label=_SOURCE_LABELS["document_library"],
            status="not_configured",
            note="No saved role pack found in the document library for this role.",
        )
    local = StudySource(
        source_type="local_fallback",
        label=_SOURCE_LABELS["local_fallback"],
        status="used",
        confidence=1.0,
        note="Study module compiled from local deterministic templates and role/skill knowledge.",
    )

    sources = [web, model, document, local]
    summary = summarize_source_status(sources)
    return StudySourceBundle(sources=sources, summary=summary)


def _relative_library_path_for_display(path: str | None) -> str | None:
    if not path:
        return None
    from pathlib import Path

    from app.core.config import settings

    root = Path(settings.resolved_documents_root)
    p = Path(path)
    try:
        return str(Path("documents") / p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def summarize_source_status(sources: list[StudySource]) -> str:
    used = [s.label for s in sources if s.status == "used"]
    if used:
        used_text = ", ".join(used)
        unused_ladder = [
            s.label.lower()
            for s in sources
            if s.source_type in {"web", "model"} and s.status == "not_configured"
        ]
        tail = (
            f" {' and '.join(unused_ladder)} retrieval are not configured."
            if unused_ladder
            else " Web and model retrieval are not fully enabled yet."
        )
        return f"Generated from {used_text.lower()}.{tail}"
    return "No study sources marked as used; content may be incomplete."


def attach_study_source_metadata(
    question: dict[str, Any],
    job: dict[str, Any],
    *,
    generation_mode: str = "deterministic",
) -> dict[str, Any]:
    """Attach backward-compatible study source metadata to a question dict."""
    from app.agents.job_search.knowledge.document_library_retriever import (
        apply_document_library_support,
    )

    role_title = job.get("title") or "this role"
    mode = generation_mode
    if question.get("answer_source") in {"llm", "live_llm"}:
        mode = "llm"
    retrieval = apply_document_library_support(question, job)
    from app.agents.job_search.knowledge.model_knowledge import (
        ModelKnowledgeResult,
        ModelKnowledgeStatus,
        apply_model_knowledge_support,
    )

    existing_mk = question.get("model_knowledge_support")
    if existing_mk:
        model_result = ModelKnowledgeResult(
            status=str(existing_mk.get("status") or ModelKnowledgeStatus.NOT_CONFIGURED.value),
            used=bool(existing_mk.get("used")),
            insight=existing_mk.get("insight"),
            provider_name=existing_mk.get("provider_name"),
            reason=str(existing_mk.get("reason") or ""),
            warnings=list(existing_mk.get("warnings") or []),
        )
    else:
        model_result = apply_model_knowledge_support(question, job)
    bundle = build_default_study_source_bundle(
        role_title=role_title,
        generation_mode=mode,
        document_retrieval=retrieval,
        model_knowledge=model_result,
    )
    question["study_sources"] = bundle.to_dict()
    return question


def render_study_source_markdown(study_sources: dict[str, Any] | None) -> list[str]:
    """Render compact source/fallback status for Markdown/PDF export."""
    if not study_sources:
        return [
            "### Source / fallback status",
            "",
            "- **Used:** Local deterministic study material (metadata not recorded for this pack)",
            "- **Web research:** Not configured in this iteration",
            "- **Model knowledge:** Not configured in this iteration",
            "- **Document library:** Unknown",
            "",
        ]

    lines = ["### Source / fallback status", ""]
    sources = study_sources.get("sources") or []

    used_parts: list[str] = []
    for entry in sources:
        if entry.get("status") != "used":
            continue
        if entry.get("source_type") == "document_library":
            used_parts.append("Document-library role material")
        else:
            label = entry.get("label") or entry.get("source_type", "").replace("_", " ").title()
            if label:
                used_parts.append(label)
    if used_parts:
        lines.append(f"- **Used:** {'; '.join(used_parts)}")

    status_labels = {
        "not_configured": "Not configured in this iteration",
        "available_not_used": "Available but not used for this question",
        "failed": "Retrieval failed",
        "used": "Used",
    }
    for entry in sources:
        source_type = entry.get("source_type")
        if source_type == "local_fallback":
            continue
        label = entry.get("label") or str(source_type or "Source").replace("_", " ").title()
        status = entry.get("status", "not_configured")
        status_text = status_labels.get(status, status.replace("_", " ").title())
        note = _normalize_source_text((entry.get("note") or "").strip())
        doc_path = entry.get("document_path")
        if source_type == "document_library" and status == "used" and doc_path:
            line = f"- **{label}:** Used — matched saved role-pack material from `{doc_path}`"
            if note:
                line += f" — {note}"
        elif status == "used":
            continue
        elif source_type == "model" and status == "failed":
            line = (
                f"- **{label}:** Failed fallback — {note}"
                if note
                else f"- **{label}:** Failed fallback"
            )
        elif source_type == "model" and status == "not_configured" and note.lower().startswith("disabled"):
            line = f"- **{label}:** {note}"
        else:
            line = f"- **{label}:** {status_text}"
            if note:
                line += f" — {note}"
        lines.append(_normalize_source_text(line))

    summary = _normalize_source_text((study_sources.get("summary") or "").strip())
    if summary:
        lines.append("")
        lines.append(f"_{summary}_")
    lines.append("")
    return lines
