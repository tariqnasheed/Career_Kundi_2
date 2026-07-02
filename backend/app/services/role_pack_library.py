"""
services/role_pack_library.py
================================
Persistent interview-pack document library under ``documents/interview_packs/``.

Every generated role pack is saved as structured JSON + multiple PDFs, indexed
for fast retrieval, and reused when Gemini / web search is unavailable.

Workflow integration:
  1. ``find_role_pack()`` — check saved material before regenerating
  2. ``save_role_pack()`` — persist after successful generation
  3. ``fallback_for_role()`` — serve saved PDFs when live generation fails
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.core.config import settings
from app.core.logging import get_logger
from app.tools.document_export import (
    build_interview_pack_markdown,
    build_questions_answers_markdown,
    build_study_material_markdown,
    export_interview_pack_pdf,
    export_questions_answers_pdf,
    export_study_material_pdf,
)

logger = get_logger(__name__)

Category = Literal[
    "technology",
    "engineering",
    "healthcare",
    "finance",
    "business",
    "law",
    "education",
    "science",
    "arts_media",
    "hospitality",
    "construction",
    "agriculture",
    "public_service",
    "custom_roles",
]

# Keyword → folder category (first match wins)
_CATEGORY_KEYWORDS: dict[Category, list[str]] = {
    "technology": [
        "software", "developer", "engineer", "data", "ai", "machine learning",
        "devops", "cloud", "cyber", "security", "network", "database", "it ",
        "programmer", "full stack", "frontend", "backend", "sre", "qa ",
    ],
    "engineering": [
        "electrical", "mechanical", "civil", "chemical", "biomedical", "aerospace",
        "automotive", "marine", "industrial", "electronics", "structural", "hvac",
    ],
    "healthcare": [
        "nurse", "doctor", "physician", "pharmac", "dentist", "therapist",
        "clinical", "medical", "healthcare", "hospital", "surgeon", "midwife",
    ],
    "finance": [
        "accountant", "auditor", "bank", "finance", "investment", "tax", "actuar",
        "insurance", "treasury", "credit analyst",
    ],
    "business": [
        "manager", "hr ", "human resources", "marketing", "sales", "operations",
        "supply chain", "procurement", "consultant", "business analyst", "product manager",
    ],
    "law": ["lawyer", "legal", "attorney", "paralegal", "compliance", "regulatory"],
    "education": [
        "teacher", "professor", "lecturer", "tutor", "trainer", "education",
        "academic", "instructor", "faculty",
    ],
    "science": [
        "physic", "chemist", "biolog", "research", "geolog", "environmental scientist",
        "laboratory", "scientist",
    ],
    "arts_media": [
        "designer", "architect", "journalist", "writer", "animator", "film",
        "media", "creative", "graphic", "ux ", "ui ",
    ],
    "hospitality": [
        "hotel", "chef", "restaurant", "tourism", "hospitality", "flight attendant",
        "event planner",
    ],
    "construction": [
        "construction", "electrician", "plumber", "carpenter", "welder", "technician",
        "trades", "logistics", "warehouse", "driver",
    ],
    "agriculture": ["agricultur", "farm", "forestry", "environmental", "sustainability"],
    "public_service": [
        "government", "civil service", "policy", "administrator", "public health officer",
    ],
}


def normalize_role_slug(role_name: str) -> str:
    """Convert any role title to a filesystem-safe slug."""
    slug = role_name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "custom_role"


def classify_role_category(role_name: str, stream_hint: str | None = None) -> Category:
    """Heuristic category from role title / stream — unknown roles → custom_roles."""
    haystack = f"{role_name} {stream_hint or ''}".lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            return category
    if stream_hint:
        stream_map = {
            "engineering": "engineering",
            "computer_science": "technology",
            "medicine": "healthcare",
            "nursing": "healthcare",
            "business": "business",
            "finance": "finance",
            "law": "law",
            "education": "education",
            "arts_media": "arts_media",
            "science": "science",
            "hospitality": "hospitality",
            "construction": "construction",
            "agriculture": "agriculture",
            "public_service": "public_service",
        }
        if stream_hint in stream_map:
            return stream_map[stream_hint]  # type: ignore[return-value]
    return "custom_roles"


def _documents_root() -> Path:
    return Path(settings.resolved_documents_root)


def _role_dir(category: Category, slug: str) -> Path:
    return _documents_root() / "interview_packs" / category / slug


def _indexes_dir() -> Path:
    return _documents_root() / "indexes"


def ensure_library_layout() -> None:
    """Create documents/ tree and empty index files on first use."""
    root = _documents_root()
    for sub in (
        "interview_packs",
        "source_materials/uploaded_pdfs",
        "source_materials/parsed_text",
        "source_materials/web_research",
        "indexes",
        "exports/latest",
        "exports/archive",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)

    for name in ("role_index.json", "skill_index.json", "document_index.json"):
        path = _indexes_dir() / name
        if not path.exists():
            path.write_text(json.dumps({} if name != "document_index.json" else [], indent=2), encoding="utf-8")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def find_role_pack(role_name: str, *, stream_hint: str | None = None) -> dict[str, Any] | None:
    """
    Return saved pack metadata + questions if a complete pack exists on disk.
    Searches exact slug first, then scans role_index.json.
    """
    ensure_library_layout()
    slug = normalize_role_slug(role_name)
    category = classify_role_category(role_name, stream_hint)

    for cat in (category, "custom_roles"):
        folder = _role_dir(cat, slug)
        meta_path = folder / "metadata.json"
        structured_path = folder / "structured_content.json"
        if meta_path.exists() and structured_path.exists():
            meta = _read_json(meta_path, {})
            content = _read_json(structured_path, {})
            questions = content.get("questions") or []
            if questions:
                return {
                    "role_name": meta.get("role_name", role_name),
                    "role_slug": slug,
                    "category": cat,
                    "folder": str(folder),
                    "metadata": meta,
                    "questions": questions,
                    "role_overview": content.get("role_overview", {}),
                    "pdf_files": meta.get("pdf_files", []),
                    "from_library": True,
                }

    role_index = _read_json(_indexes_dir() / "role_index.json", {})
    entry = role_index.get(slug)
    if entry:
        folder = Path(entry.get("folder", ""))
        structured_path = folder / "structured_content.json"
        if structured_path.exists():
            content = _read_json(structured_path, {})
            if content.get("questions"):
                meta = _read_json(folder / "metadata.json", {})
                return {
                    "role_name": meta.get("role_name", role_name),
                    "role_slug": slug,
                    "category": entry.get("category", "custom_roles"),
                    "folder": str(folder),
                    "metadata": meta,
                    "questions": content["questions"],
                    "role_overview": content.get("role_overview", {}),
                    "pdf_files": meta.get("pdf_files", []),
                    "from_library": True,
                }
    return None


def search_related_packs(role_name: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Find similar saved role packs by token overlap on slug / role name."""
    ensure_library_layout()
    query_tokens = set(normalize_role_slug(role_name).split("_"))
    role_index = _read_json(_indexes_dir() / "role_index.json", {})
    scored: list[tuple[int, dict]] = []
    for slug, entry in role_index.items():
        entry_tokens = set(slug.split("_"))
        overlap = len(query_tokens & entry_tokens)
        if overlap > 0:
            scored.append((overlap, {"role_slug": slug, **entry}))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def fallback_for_role(
    role_name: str,
    *,
    stream_hint: str | None = None,
    api_unavailable: bool = False,
) -> dict[str, Any]:
    """
    Best-effort retrieval when live generation fails.
    Returns exact pack, related packs, or empty with user-facing message.
    """
    exact = find_role_pack(role_name, stream_hint=stream_hint)
    if exact:
        msg = (
            "Live web search or Gemini generation is currently unavailable, so I loaded "
            "the best available saved material from the project documents folder."
            if api_unavailable
            else "Loaded saved interview pack from the project document library."
        )
        return {
            "status": "exact_match",
            "message": msg,
            "pack": exact,
            "related": [],
        }

    related = search_related_packs(role_name)
    if related:
        return {
            "status": "related_only",
            "message": (
                f'No saved pack was found for "{role_name}", but related materials exist. '
                "Use those until a dedicated pack can be generated."
            ),
            "pack": None,
            "related": related,
        }

    return {
        "status": "none",
        "message": (
            "I could not generate or retrieve useful material because Gemini API/web search "
            "is unavailable and no saved project documents were found for this role. "
            "Please restore API/web access or add source materials to the documents folder."
        ),
        "pack": None,
        "related": [],
    }


def build_role_overview(role_name: str, job_snapshot: dict[str, Any]) -> dict[str, Any]:
    from app.agents.job_search.knowledge.content_engine import get_role_context

    ctx = get_role_context(role_name)
    skills = ctx.get("required_skills") or [
        s.get("skill") if isinstance(s, dict) else s for s in job_snapshot.get("extracted_skills", [])
    ]
    skills = [s for s in skills if s]
    return {
        "role_name": role_name,
        "summary": ctx.get("summary")
        or (
            f"This interview preparation pack covers the {role_name} role with PhD-level study material, "
            "real definitions, principles, and worked examples for every question."
        ),
        "responsibilities": ctx.get("responsibilities") or job_snapshot.get("responsibilities") or [],
        "required_skills": skills,
        "what_employers_expect": ctx.get("what_employers_expect") or job_snapshot.get("requirements") or [],
        "skill_clusters": ctx.get("skill_clusters") or (list(dict.fromkeys(skills)) if skills else ["General role competencies"]),
    }


def save_role_pack(
    *,
    role_name: str,
    questions: list[dict],
    job_snapshot: dict[str, Any] | None = None,
    confidence_score: float | None = None,
    stream_hint: str | None = None,
    sources: list[dict] | None = None,
    generated_by: str = "Careerkundi multi-agent pipeline",
) -> dict[str, Any]:
    """
    Persist questions + PDFs + metadata under documents/interview_packs/.
    Updates role_index, skill_index, and document_index.
    """
    ensure_library_layout()
    slug = normalize_role_slug(role_name)
    category = classify_role_category(role_name, stream_hint)
    folder = _role_dir(category, slug)
    folder.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    job_snapshot = job_snapshot or {"title": role_name}
    role_overview = build_role_overview(role_name, job_snapshot)

    structured = {
        "role_name": role_name,
        "role_slug": slug,
        "category": category,
        "role_overview": role_overview,
        "questions": questions,
        "generated_at": now.isoformat(),
        "confidence_score": confidence_score,
    }
    _write_json(folder / "structured_content.json", structured)

    # Markdown mirrors (always saved — usable when WeasyPrint/PDF libs unavailable)
    md_exports = [
        (f"{slug}_interview_pack.md", build_interview_pack_markdown),
        (f"{slug}_study_material.md", build_study_material_markdown),
        (f"{slug}_questions_answers.md", build_questions_answers_markdown),
    ]
    markdown_files: list[str] = []
    company = job_snapshot.get("company_name")
    for filename, builder in md_exports:
        try:
            if builder is build_study_material_markdown:
                md = builder(job_title=role_name, questions=questions, generated_at=now, role_overview=role_overview)
            elif builder is build_questions_answers_markdown:
                md = builder(job_title=role_name, company_name=company, questions=questions, generated_at=now)
            else:
                md = builder(
                    job_title=role_name,
                    company_name=company,
                    questions=questions,
                    generated_at=now,
                    confidence_score=confidence_score,
                    role_overview=role_overview,
                )
            (folder / filename).write_text(md, encoding="utf-8")
            markdown_files.append(filename)
        except Exception as exc:  # noqa: BLE001
            logger.warning("role_pack_markdown_export_failed", file=filename, error=str(exc))

    (folder / "parsed_content.md").write_text(
        build_interview_pack_markdown(
            job_title=role_name,
            company_name=company,
            questions=questions,
            generated_at=now,
            confidence_score=confidence_score,
            role_overview=role_overview,
        ),
        encoding="utf-8",
    )

    # PDF exports
    pdf_names: list[str] = []
    exports = [
        (f"{slug}_interview_pack.pdf", export_interview_pack_pdf),
        (f"{slug}_study_material.pdf", export_study_material_pdf),
        (f"{slug}_questions_answers.pdf", export_questions_answers_pdf),
    ]
    for filename, exporter in exports:
        try:
            pdf_bytes = exporter(
                job_title=role_name,
                company_name=company,
                questions=questions,
                generated_at=now,
                confidence_score=confidence_score,
                role_overview=role_overview,
            )
            (folder / filename).write_bytes(pdf_bytes)
            pdf_names.append(filename)
        except Exception as exc:  # noqa: BLE001
            logger.warning("role_pack_pdf_export_failed", file=filename, error=str(exc))

    skill_tags: set[str] = set()
    for q in questions:
        if q.get("skill_tag"):
            skill_tags.add(q["skill_tag"])
        for sk in q.get("related_skills") or []:
            skill_tags.add(sk)
        study = q.get("study_material") or {}
        for concept in study.get("key_concepts") or []:
            skill_tags.add(str(concept))

    meta = {
        "role_name": role_name,
        "normalized_role_slug": slug,
        "category": category,
        "stream_or_department": stream_hint or category,
        "generated_at": now.date().isoformat(),
        "last_updated": now.date().isoformat(),
        "generated_by": generated_by,
        "question_count": len(questions),
        "question_specific_study_material_count": sum(
            1 for q in questions if (q.get("study_material") or {}).get("overview")
        ),
        "skill_count": len(skill_tags),
        "pdf_files": pdf_names,
        "markdown_files": markdown_files,
        "source_files": markdown_files + pdf_names,
        "web_sources": sources or [],
        "related_roles": [],
        "status": "complete" if questions else "incomplete",
        "version": "1.0",
        "folder": str(folder),
        "has_pdf": len(pdf_names) > 0,
        "has_markdown": len(markdown_files) > 0,
    }
    _write_json(folder / "metadata.json", meta)
    _write_json(folder / "sources.json", {"web_sources": sources or [], "project_sources": []})

    _update_indexes(slug, category, role_name, folder, questions, pdf_names, skill_tags)
    logger.info("role_pack_saved", slug=slug, category=category, questions=len(questions))
    return {"role_slug": slug, "category": category, "folder": str(folder), "metadata": meta, "pdf_files": pdf_names}


def _update_indexes(
    slug: str,
    category: str,
    role_name: str,
    folder: Path,
    questions: list[dict],
    pdf_files: list[str],
    skill_tags: set[str],
) -> None:
    role_index = _read_json(_indexes_dir() / "role_index.json", {})
    role_index[slug] = {
        "role_name": role_name,
        "category": category,
        "folder": str(folder),
        "question_count": len(questions),
        "pdf_files": pdf_files,
        "last_updated": datetime.now(timezone.utc).date().isoformat(),
    }
    _write_json(_indexes_dir() / "role_index.json", role_index)

    skill_index = _read_json(_indexes_dir() / "skill_index.json", {})
    for skill in skill_tags:
        key = normalize_role_slug(skill)
        skill_index.setdefault(key, {"skill": skill, "roles": []})
        if slug not in skill_index[key]["roles"]:
            skill_index[key]["roles"].append(slug)
    _write_json(_indexes_dir() / "skill_index.json", skill_index)

    doc_index = _read_json(_indexes_dir() / "document_index.json", [])
    doc_index = [d for d in doc_index if d.get("role_slug") != slug]
    for pdf in pdf_files:
        doc_index.append({
            "role_slug": slug,
            "role_name": role_name,
            "category": category,
            "file": pdf,
            "path": str(folder / pdf),
        })
    _write_json(_indexes_dir() / "document_index.json", doc_index)


def read_pdf_bytes(category: str, slug: str, filename: str) -> bytes | None:
    """Load a saved PDF from the library for download endpoints."""
    path = _role_dir(category, slug) / filename
    if path.is_file():
        return path.read_bytes()
    return None


def list_library_roles(*, category: str | None = None) -> list[dict[str, Any]]:
    """List indexed role packs for the library browser."""
    ensure_library_layout()
    role_index = _read_json(_indexes_dir() / "role_index.json", {})
    items = []
    for slug, entry in role_index.items():
        if category and entry.get("category") != category:
            continue
        items.append({"role_slug": slug, **entry})
    return sorted(items, key=lambda x: x.get("role_name", ""))


def load_stored_pack_for_role(role_name: str, *, stream_hint: str | None = None) -> dict[str, Any] | None:
    """Return pre-seeded pack data for a role title, or None."""
    return find_role_pack(role_name, stream_hint=stream_hint)


def regenerate_pdfs_for_catalog(*, only_missing: bool = True) -> dict[str, Any]:
    """Generate PDF files from existing structured_content.json in each role folder."""
    ensure_library_layout()
    stats = {"regenerated": 0, "skipped": 0, "failed": 0}
    role_index = _read_json(_indexes_dir() / "role_index.json", {})
    for slug, entry in role_index.items():
        folder = Path(entry["folder"])
        structured_path = folder / "structured_content.json"
        if not structured_path.exists():
            stats["skipped"] += 1
            continue
        meta_path = folder / "metadata.json"
        meta = _read_json(meta_path, {})
        if only_missing and meta.get("has_pdf") and len(meta.get("pdf_files") or []) >= 3:
            stats["skipped"] += 1
            continue
        try:
            content = _read_json(structured_path, {})
            questions = content.get("questions") or []
            role_name = content.get("role_name") or entry.get("role_name") or slug
            role_overview = content.get("role_overview") or {}
            generated_at = content.get("generated_at")
            confidence = content.get("confidence_score")
            pdf_names: list[str] = []
            exports = [
                (f"{slug}_interview_pack.pdf", export_interview_pack_pdf),
                (f"{slug}_study_material.pdf", export_study_material_pdf),
                (f"{slug}_questions_answers.pdf", export_questions_answers_pdf),
            ]
            for filename, exporter in exports:
                pdf_bytes = exporter(
                    job_title=role_name,
                    company_name=None,
                    questions=questions,
                    generated_at=generated_at,
                    confidence_score=confidence,
                    role_overview=role_overview,
                )
                (folder / filename).write_bytes(pdf_bytes)
                pdf_names.append(filename)
            meta["pdf_files"] = pdf_names
            meta["has_pdf"] = True
            meta["last_updated"] = datetime.now(timezone.utc).date().isoformat()
            _write_json(meta_path, meta)
            entry["pdf_files"] = pdf_names
            role_index[slug] = entry
            stats["regenerated"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["failed"] += 1
            logger.warning("pdf_regenerate_failed", slug=slug, error=str(exc))
    _write_json(_indexes_dir() / "role_index.json", role_index)
    return stats


def seed_catalog_role_packs(
    *,
    force: bool = False,
    only_missing: bool = True,
) -> dict[str, Any]:
    """
    Pre-generate interview packs (+ PDFs/markdown) for every role in the
    popular roles catalog. Run via ``make seed-role-packs``.
    """
    from app.agents.job_search import mock_data
    from app.data.popular_roles_catalog import catalog_role_to_job_snapshot, get_all_catalog_roles

    ensure_library_layout()
    roles = get_all_catalog_roles()
    stats: dict[str, Any] = {
        "total_catalog_roles": len(roles),
        "seeded": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
    }

    for role in roles:
        title = role["title"]
        stream = role.get("stream_id")
        try:
            if only_missing and not force and find_role_pack(title, stream_hint=stream):
                stats["skipped"] += 1
                continue

            snapshot = catalog_role_to_job_snapshot(role)
            questions = mock_data.mock_generate_questions(snapshot, focus_areas=[], difficulty="auto")
            if not questions:
                raise ValueError("no questions generated")

            save_role_pack(
                role_name=title,
                questions=questions,
                job_snapshot=snapshot,
                confidence_score=0.9,
                stream_hint=stream,
                generated_by="Careerkundi catalog pre-seed (offline pipeline)",
            )
            stats["seeded"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["failed"] += 1
            stats["errors"].append({"role": title, "error": str(exc)})
            logger.error("role_pack_seed_failed", role=title, error=str(exc))

    logger.info("role_pack_catalog_seed_complete", **{k: v for k, v in stats.items() if k != "errors"})
    return stats
