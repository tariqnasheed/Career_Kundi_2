"""
api/routes/role_packs.py
=============================
Role-pack document library — browse, lookup, and download saved interview
packs from ``documents/interview_packs/``.

These endpoints serve the reusable knowledge base that persists across users
and survives Gemini / web-search outages.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.core.errors import NotFoundError
from app.db.models.user import User
from app.schemas.job_search import RolePackLibraryEntry, RolePackLookupResponse
from app.services import role_pack_library as library

router = APIRouter(prefix="/role-packs", tags=["role-packs"])


@router.get("/", response_model=list[RolePackLibraryEntry])
async def list_role_packs(
    category: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
) -> list[RolePackLibraryEntry]:
    """List all indexed role packs saved in the project documents folder."""
    library.ensure_library_layout()
    items = library.list_library_roles(category=category)
    return [RolePackLibraryEntry(**item) for item in items]


@router.get("/lookup", response_model=RolePackLookupResponse)
async def lookup_role_pack(
    role: str = Query(..., min_length=2, description="Role title to search for"),
    stream: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
) -> RolePackLookupResponse:
    """Find an exact or related saved pack before triggering live generation."""
    library.ensure_library_layout()
    exact = library.find_role_pack(role, stream_hint=stream)
    if exact:
        return RolePackLookupResponse(
            status="found",
            message=f'Saved pack found for "{role}".',
            pack=None,
            related=[RolePackLibraryEntry(
                role_slug=exact["role_slug"],
                role_name=exact["role_name"],
                category=exact["category"],
                question_count=len(exact.get("questions") or []),
                pdf_files=exact.get("pdf_files") or [],
                folder=exact.get("folder"),
            )],
        )
    fb = library.fallback_for_role(role, stream_hint=stream)
    related = [RolePackLibraryEntry(**r) for r in fb.get("related", [])]
    status = fb["status"]
    if status == "exact_match":
        status = "found"
    return RolePackLookupResponse(status=status, message=fb["message"], pack=None, related=related)


@router.get("/{category}/{slug}/export")
async def export_library_pdf(
    category: str,
    slug: str,
    file: str = Query(..., description="PDF filename from metadata.pdf_files"),
    _user: User = Depends(get_current_user),
) -> Response:
    """Download a PDF from the saved role-pack folder."""
    content = library.read_pdf_bytes(category, slug, file)
    if content is None:
        raise NotFoundError("Document not found in the role-pack library.")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{file}"'},
    )
