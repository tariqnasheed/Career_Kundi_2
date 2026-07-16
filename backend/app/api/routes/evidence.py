"""
Private evidence API (0053-F3 / 0053-F5).

Authenticated, current-user scoped metadata + private attachment bytes.
Upload/download is not verification. No public sharing, OCR, or claim axis mutation.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError, ValidationFailedError
from app.db.models.claim import ClaimRecord
from app.db.models.evidence import ClaimEvidenceLink, EvidenceRecord
from app.db.models.user import User
from app.db.session import get_db
from app.platform.claims.display import (
    support_status_label,
    verification_status_label,
)
from app.platform.evidence.display import (
    claim_evidence_link_role_label,
    evidence_kind_label,
    evidence_privacy_label,
    evidence_truth_warning,
)
from app.platform.evidence.refs import EvidenceRefError
from app.platform.evidence.service import (
    attach_evidence_file,
    create_evidence_record,
    get_claim_for_owner,
    get_evidence_for_owner,
    link_evidence_to_claim,
    list_claim_evidence_links_for_owner,
    list_owner_evidence,
    list_subject_evidence_for_owner,
)
from app.platform.evidence.storage import (
    EvidenceStorageError,
    LocalEvidenceStorage,
    open_evidence_file,
    sanitize_download_filename,
)
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import parse_entity_id
from app.schemas.evidence import (
    ApiListMeta,
    ClaimEvidenceLinkCreate,
    ClaimEvidenceLinkEnvelope,
    ClaimEvidenceLinkListEnvelope,
    ClaimEvidenceLinkRead,
    EvidenceCreate,
    EvidenceEnvelope,
    EvidenceListEnvelope,
    EvidenceRead,
    EvidenceSummary,
)

router = APIRouter(prefix="/evidence", tags=["evidence"])


def _map_evidence_error(exc: EvidenceRefError) -> Exception:
    message = str(exc)
    lowered = message.lower()
    if "duplicate" in lowered:
        return ConflictError(message)
    if "does not exist" in lowered or "does not match" in lowered:
        # Ownership / existence mismatches → safe not-found (no cross-user leak).
        if "subject" in lowered:
            return NotFoundError("Career subject not found.")
        if "claim" in lowered:
            return NotFoundError("Claim not found.")
        if "evidence" in lowered:
            return NotFoundError("Evidence not found.")
        return NotFoundError("Resource not found.")
    return ValidationFailedError(message)


def _evidence_read(row: EvidenceRecord) -> EvidenceRead:
    return EvidenceRead(
        id=row.id,
        subject_id=row.subject_id,
        title=row.title,
        evidence_kind=row.evidence_kind,
        privacy_class=row.privacy_class,
        storage_uri=row.storage_uri,
        content_hash=row.content_hash,
        mime_type=row.mime_type,
        size_bytes=row.size_bytes,
        source_id=row.source_id,
        snapshot_id=row.snapshot_id,
        has_attachment=bool(row.storage_uri),
        evidence_kind_label=evidence_kind_label(row.evidence_kind),
        privacy_label=evidence_privacy_label(row.privacy_class),
        truth_warning=evidence_truth_warning(),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _link_read(
    link: ClaimEvidenceLink,
    *,
    evidence: EvidenceRecord,
    claim: ClaimRecord,
) -> ClaimEvidenceLinkRead:
    return ClaimEvidenceLinkRead(
        id=link.id,
        claim_id=link.claim_id,
        evidence_id=link.evidence_id,
        link_role=link.link_role,
        link_role_label=claim_evidence_link_role_label(link.link_role),
        created_at=link.created_at,
        evidence=EvidenceSummary(
            id=evidence.id,
            title=evidence.title,
            evidence_kind=evidence.evidence_kind,
            evidence_kind_label=evidence_kind_label(evidence.evidence_kind),
            privacy_class=evidence.privacy_class,
        ),
        truth_warning=evidence_truth_warning(),
        claim_support_status=claim.support_status,
        claim_verification_status=claim.verification_status,
        claim_support_label=support_status_label(claim.support_status),
        claim_verification_label=verification_status_label(
            claim.verification_status
        ),
    )


def _storage() -> LocalEvidenceStorage:
    return LocalEvidenceStorage(
        settings.resolved_evidence_storage_root,
        max_upload_bytes=settings.evidence_max_upload_bytes,
        allowed_mime_types=settings.evidence_allowed_mime_types_set,
    )


async def _read_upload_bytes(file: UploadFile, *, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValidationFailedError(
                f"File exceeds maximum size of {max_bytes} bytes."
            )
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data:
        raise ValidationFailedError("Empty file rejected.")
    return data


@router.post("", response_model=EvidenceEnvelope, status_code=201)
async def create_evidence(
    body: EvidenceCreate,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> EvidenceEnvelope:
    """Create private evidence metadata owned by the current user."""
    try:
        actor = ActorRef(
            actor_type=ActorType.USER,
            actor_id=parse_entity_id(user.id),
        )
        row = await create_evidence_record(
            db,
            owner_user_id=user.id,
            title=body.title,
            evidence_kind=body.evidence_kind,
            subject_id=body.subject_id,
            privacy_class=body.privacy_class,
            source_id=body.source_id,
            snapshot_id=body.snapshot_id,
            storage_uri=body.storage_uri,
            content_hash=body.content_hash,
            mime_type=body.mime_type,
            size_bytes=body.size_bytes,
            created_by_actor=actor,
        )
    except EvidenceRefError as exc:
        raise _map_evidence_error(exc) from exc
    return EvidenceEnvelope(data=_evidence_read(row))


@router.get("", response_model=EvidenceListEnvelope)
async def list_evidence(
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> EvidenceListEnvelope:
    """List evidence metadata owned by the current user."""
    rows = await list_owner_evidence(db, user.id)
    data = [_evidence_read(r) for r in rows]
    return EvidenceListEnvelope(data=data, meta=ApiListMeta(count=len(data)))


@router.get(
    "/subjects/{subject_id}",
    response_model=EvidenceListEnvelope,
)
async def list_subject_evidence_api(
    subject_id: uuid.UUID,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> EvidenceListEnvelope:
    """List evidence for a subject owned by the current user."""
    rows = await list_subject_evidence_for_owner(db, subject_id, user.id)
    if rows is None:
        raise NotFoundError("Career subject not found.")
    data = [_evidence_read(r) for r in rows]
    return EvidenceListEnvelope(data=data, meta=ApiListMeta(count=len(data)))


@router.post("/links", response_model=ClaimEvidenceLinkEnvelope, status_code=201)
async def create_claim_evidence_link(
    body: ClaimEvidenceLinkCreate,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ClaimEvidenceLinkEnvelope:
    """Link owned evidence to an owned claim without mutating claim status axes."""
    claim = await get_claim_for_owner(db, body.claim_id, user.id)
    if claim is None:
        raise NotFoundError("Claim not found.")
    evidence = await get_evidence_for_owner(db, body.evidence_id, user.id)
    if evidence is None:
        raise NotFoundError("Evidence not found.")

    prior_support = claim.support_status
    prior_verification = claim.verification_status
    try:
        actor = ActorRef(
            actor_type=ActorType.USER,
            actor_id=parse_entity_id(user.id),
        )
        link = await link_evidence_to_claim(
            db,
            claim_id=body.claim_id,
            evidence_id=body.evidence_id,
            link_role=body.link_role,
            created_by_actor=actor,
        )
    except EvidenceRefError as exc:
        raise _map_evidence_error(exc) from exc

    refreshed_claim = await get_claim_for_owner(db, body.claim_id, user.id)
    if refreshed_claim is None:
        raise NotFoundError("Claim not found.")
    if (
        refreshed_claim.support_status != prior_support
        or refreshed_claim.verification_status != prior_verification
    ):
        raise ValidationFailedError(
            "Evidence link must not mutate claim support or verification status."
        )
    refreshed_evidence = await get_evidence_for_owner(db, body.evidence_id, user.id)
    if refreshed_evidence is None:
        raise NotFoundError("Evidence not found.")
    return ClaimEvidenceLinkEnvelope(
        data=_link_read(
            link, evidence=refreshed_evidence, claim=refreshed_claim
        )
    )


@router.get(
    "/claims/{claim_id}/links",
    response_model=ClaimEvidenceLinkListEnvelope,
)
async def list_claim_links_api(
    claim_id: uuid.UUID,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ClaimEvidenceLinkListEnvelope:
    """List evidence links for a claim owned by the current user."""
    claim = await get_claim_for_owner(db, claim_id, user.id)
    if claim is None:
        raise NotFoundError("Claim not found.")
    links = await list_claim_evidence_links_for_owner(db, claim_id, user.id)
    if links is None:
        raise NotFoundError("Claim not found.")

    data: list[ClaimEvidenceLinkRead] = []
    for link in links:
        evidence = await get_evidence_for_owner(db, link.evidence_id, user.id)
        if evidence is None:
            continue
        data.append(_link_read(link, evidence=evidence, claim=claim))
    return ClaimEvidenceLinkListEnvelope(
        data=data, meta=ApiListMeta(count=len(data))
    )


@router.post(
    "/{evidence_id}/attachment",
    response_model=EvidenceEnvelope,
    status_code=200,
)
async def upload_evidence_attachment(
    evidence_id: uuid.UUID,
    file: UploadFile = File(...),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> EvidenceEnvelope:
    """
    Upload one private attachment for owned evidence metadata.

    Not verification. Duplicate attachment without replace is rejected.
    """
    storage = _storage()
    data = await _read_upload_bytes(file, max_bytes=storage.max_upload_bytes)
    try:
        row = await attach_evidence_file(
            db,
            evidence_id=evidence_id,
            owner_user_id=user.id,
            data=data,
            mime_type=file.content_type,
            original_filename=file.filename,
            storage=storage,
        )
    except EvidenceRefError as exc:
        raise _map_evidence_error(exc) from exc
    return EvidenceEnvelope(data=_evidence_read(row))


@router.get("/{evidence_id}/attachment")
async def download_evidence_attachment(
    evidence_id: uuid.UUID,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> FileResponse:
    """Stream private attachment bytes for owned evidence (auth + ownership)."""
    row = await get_evidence_for_owner(db, evidence_id, user.id)
    if row is None or not row.storage_uri:
        raise NotFoundError("Evidence attachment not found.")

    storage = _storage()
    try:
        path = open_evidence_file(
            row.storage_uri,
            owner_user_id=user.id,
            evidence_id=evidence_id,
            storage=storage,
        )
    except EvidenceStorageError:
        raise NotFoundError("Evidence attachment not found.") from None

    mime = row.mime_type or "application/octet-stream"
    filename = sanitize_download_filename(
        evidence_id=evidence_id,
        mime_type=mime if row.mime_type else "application/octet-stream",
        original_filename=None,
    )
    return FileResponse(
        path,
        media_type=mime,
        filename=filename,
        content_disposition_type="attachment",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/{evidence_id}", response_model=EvidenceEnvelope)
async def get_evidence(
    evidence_id: uuid.UUID,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> EvidenceEnvelope:
    """Get one evidence record owned by the current user (404 if not owned)."""
    row = await get_evidence_for_owner(db, evidence_id, user.id)
    if row is None:
        raise NotFoundError("Evidence not found.")
    return EvidenceEnvelope(data=_evidence_read(row))
