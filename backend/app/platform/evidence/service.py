"""
Evidence service helpers (0053-F2 / 0053-F3 / 0053-F5).

Private metadata create/get/list, claim-evidence link, and private attachment
bytes via LocalEvidenceStorage. Upload is not verification.
Linking or attaching evidence must not change claim support_status or
verification_status.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.career_subject import CareerSubject
from app.db.models.claim import ClaimRecord
from app.db.models.evidence import ClaimEvidenceLink, EvidenceRecord
from app.db.models.provenance import SourceRecord, SourceSnapshot
from app.db.models.user import User
from app.platform.evidence.contracts import (
    validate_claim_evidence_link_contract,
    validate_evidence_create_contract,
)
from app.platform.evidence.refs import EvidenceRefError
from app.platform.evidence.storage import (
    EvidenceStorageError,
    EvidenceStoredObject,
    LocalEvidenceStorage,
    store_evidence_file,
)
from app.platform.identity.refs import ActorRef, ActorType


def _actor_fields(
    created_by_actor: ActorRef | None,
) -> tuple[str | None, uuid.UUID | None]:
    if created_by_actor is None:
        return None, None
    if not isinstance(created_by_actor, ActorRef):
        raise EvidenceRefError("created_by_actor must be ActorRef")
    actor_type = (
        created_by_actor.actor_type.value
        if isinstance(created_by_actor.actor_type, ActorType)
        else str(created_by_actor.actor_type)
    )
    return actor_type, uuid.UUID(str(created_by_actor.actor_id))


async def create_evidence_record(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    title: object,
    evidence_kind: object,
    subject_id: uuid.UUID | None = None,
    privacy_class: object | None = None,
    source_id: uuid.UUID | None = None,
    snapshot_id: uuid.UUID | None = None,
    storage_uri: object | None = None,
    content_hash: object | None = None,
    mime_type: object | None = None,
    size_bytes: object | None = None,
    created_by_actor: ActorRef | None = None,
) -> EvidenceRecord:
    validated = validate_evidence_create_contract(
        title=title,
        evidence_kind=evidence_kind,
        privacy_class=privacy_class,
        source_id=source_id,
        snapshot_id=snapshot_id,
        storage_uri=storage_uri,
        content_hash=content_hash,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )

    user = (
        await db.execute(select(User).where(User.id == owner_user_id))
    ).scalar_one_or_none()
    if user is None:
        raise EvidenceRefError(f"owner user does not exist: {owner_user_id}")

    if subject_id is not None:
        subject = (
            await db.execute(
                select(CareerSubject).where(CareerSubject.id == subject_id)
            )
        ).scalar_one_or_none()
        if subject is None:
            raise EvidenceRefError(f"subject does not exist: {subject_id}")
        if subject.owner_user_id != owner_user_id:
            raise EvidenceRefError(
                "subject.owner_user_id does not match evidence owner_user_id"
            )

    if validated.source_id is not None:
        source = (
            await db.execute(
                select(SourceRecord).where(SourceRecord.id == validated.source_id)
            )
        ).scalar_one_or_none()
        if source is None:
            raise EvidenceRefError(f"source does not exist: {validated.source_id}")

    if validated.snapshot_id is not None:
        snapshot = (
            await db.execute(
                select(SourceSnapshot).where(
                    SourceSnapshot.id == validated.snapshot_id
                )
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise EvidenceRefError(f"snapshot does not exist: {validated.snapshot_id}")
        assert validated.source_id is not None
        if snapshot.source_id != validated.source_id:
            raise EvidenceRefError(
                "snapshot.source_id does not match supplied source_id"
            )

    actor_type, actor_id = _actor_fields(created_by_actor)
    row = EvidenceRecord(
        owner_user_id=owner_user_id,
        subject_id=subject_id,
        title=validated.title,
        evidence_kind=validated.evidence_kind.value,
        storage_uri=validated.storage_uri,
        content_hash=validated.content_hash,
        mime_type=validated.mime_type,
        size_bytes=validated.size_bytes,
        source_id=validated.source_id,
        snapshot_id=validated.snapshot_id,
        privacy_class=validated.privacy_class.value,
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_evidence_record(
    db: AsyncSession, evidence_id: uuid.UUID
) -> EvidenceRecord | None:
    result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
    )
    return result.scalar_one_or_none()


async def list_owner_evidence(
    db: AsyncSession, owner_user_id: uuid.UUID
) -> list[EvidenceRecord]:
    result = await db.execute(
        select(EvidenceRecord)
        .where(EvidenceRecord.owner_user_id == owner_user_id)
        .order_by(EvidenceRecord.created_at.asc())
    )
    return list(result.scalars().all())


async def list_subject_evidence(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[EvidenceRecord]:
    result = await db.execute(
        select(EvidenceRecord)
        .where(EvidenceRecord.subject_id == subject_id)
        .order_by(EvidenceRecord.created_at.asc())
    )
    return list(result.scalars().all())


async def link_evidence_to_claim(
    db: AsyncSession,
    *,
    claim_id: uuid.UUID,
    evidence_id: uuid.UUID,
    link_role: object,
    created_by_actor: ActorRef | None = None,
) -> ClaimEvidenceLink:
    validated = validate_claim_evidence_link_contract(
        claim_id=claim_id,
        evidence_id=evidence_id,
        link_role=link_role,
    )

    claim = (
        await db.execute(select(ClaimRecord).where(ClaimRecord.id == claim_id))
    ).scalar_one_or_none()
    if claim is None:
        raise EvidenceRefError(f"claim does not exist: {claim_id}")

    evidence = (
        await db.execute(
            select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
        )
    ).scalar_one_or_none()
    if evidence is None:
        raise EvidenceRefError(f"evidence does not exist: {evidence_id}")

    subject = (
        await db.execute(
            select(CareerSubject).where(CareerSubject.id == claim.subject_id)
        )
    ).scalar_one_or_none()
    if subject is None:
        raise EvidenceRefError(f"claim subject does not exist: {claim.subject_id}")

    if evidence.owner_user_id != subject.owner_user_id:
        raise EvidenceRefError(
            "evidence owner_user_id does not match claim subject owner_user_id"
        )
    if evidence.subject_id is not None and evidence.subject_id != claim.subject_id:
        raise EvidenceRefError(
            "evidence.subject_id does not match claim.subject_id"
        )

    prior_support = claim.support_status
    prior_verification = claim.verification_status

    existing = (
        await db.execute(
            select(ClaimEvidenceLink).where(
                ClaimEvidenceLink.claim_id == validated.claim_id,
                ClaimEvidenceLink.evidence_id == validated.evidence_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise EvidenceRefError("duplicate claim/evidence link is not allowed")

    actor_type, actor_id = _actor_fields(created_by_actor)
    link = ClaimEvidenceLink(
        claim_id=validated.claim_id,
        evidence_id=validated.evidence_id,
        link_role=validated.link_role.value,
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    # Re-read claim to prove no silent truth upgrade.
    refreshed = (
        await db.execute(select(ClaimRecord).where(ClaimRecord.id == claim_id))
    ).scalar_one()
    if refreshed.support_status != prior_support:
        raise EvidenceRefError(
            "link_evidence_to_claim must not mutate claim.support_status"
        )
    if refreshed.verification_status != prior_verification:
        raise EvidenceRefError(
            "link_evidence_to_claim must not mutate claim.verification_status"
        )
    return link


async def list_claim_evidence_links(
    db: AsyncSession, claim_id: uuid.UUID
) -> list[ClaimEvidenceLink]:
    result = await db.execute(
        select(ClaimEvidenceLink)
        .where(ClaimEvidenceLink.claim_id == claim_id)
        .order_by(ClaimEvidenceLink.created_at.asc())
    )
    return list(result.scalars().all())


async def get_evidence_for_owner(
    db: AsyncSession,
    evidence_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> EvidenceRecord | None:
    """Return evidence only when owned by owner_user_id; else None (safe 404)."""
    evidence = await get_evidence_record(db, evidence_id)
    if evidence is None or evidence.owner_user_id != owner_user_id:
        return None
    return evidence


async def get_claim_for_owner(
    db: AsyncSession,
    claim_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> ClaimRecord | None:
    """Return claim only when claim.subject.owner_user_id matches; else None."""
    claim = (
        await db.execute(select(ClaimRecord).where(ClaimRecord.id == claim_id))
    ).scalar_one_or_none()
    if claim is None:
        return None
    subject = (
        await db.execute(
            select(CareerSubject).where(CareerSubject.id == claim.subject_id)
        )
    ).scalar_one_or_none()
    if subject is None or subject.owner_user_id != owner_user_id:
        return None
    return claim


async def list_subject_evidence_for_owner(
    db: AsyncSession,
    subject_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> list[EvidenceRecord] | None:
    """
    List subject evidence when the subject belongs to owner_user_id.
    Returns None when the subject is missing or not owned (safe 404).
    """
    subject = (
        await db.execute(
            select(CareerSubject).where(CareerSubject.id == subject_id)
        )
    ).scalar_one_or_none()
    if subject is None or subject.owner_user_id != owner_user_id:
        return None
    return await list_subject_evidence(db, subject_id)


async def list_claim_evidence_links_for_owner(
    db: AsyncSession,
    claim_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> list[ClaimEvidenceLink] | None:
    """List links for an owned claim; None when claim missing/not owned."""
    claim = await get_claim_for_owner(db, claim_id, owner_user_id)
    if claim is None:
        return None
    return await list_claim_evidence_links(db, claim_id)


async def list_linkable_claims_for_owner(
    db: AsyncSession,
    owner_user_id: uuid.UUID,
) -> list[ClaimRecord]:
    """
    Read-only list of claims owned by owner_user_id (via subject ownership).

    For Evidence Library claim selector only. Does not create or mutate claims.
    """
    result = await db.execute(
        select(ClaimRecord)
        .join(CareerSubject, ClaimRecord.subject_id == CareerSubject.id)
        .where(CareerSubject.owner_user_id == owner_user_id)
        .order_by(ClaimRecord.created_at.asc())
    )
    return list(result.scalars().all())


async def list_evidence_claim_links_for_owner(
    db: AsyncSession,
    evidence_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> list[tuple[ClaimEvidenceLink, ClaimRecord]] | None:
    """
    List claim links for owned evidence.

    Returns None when evidence is missing/not owned (safe 404).
    Only includes links whose claim is also owned by owner_user_id.
    """
    evidence = await get_evidence_for_owner(db, evidence_id, owner_user_id)
    if evidence is None:
        return None
    result = await db.execute(
        select(ClaimEvidenceLink)
        .where(ClaimEvidenceLink.evidence_id == evidence_id)
        .order_by(ClaimEvidenceLink.created_at.asc())
    )
    links = list(result.scalars().all())
    owned: list[tuple[ClaimEvidenceLink, ClaimRecord]] = []
    for link in links:
        claim = await get_claim_for_owner(db, link.claim_id, owner_user_id)
        if claim is None:
            continue
        owned.append((link, claim))
    return owned


async def _linked_claim_status_snapshot(
    db: AsyncSession, evidence_id: uuid.UUID
) -> list[tuple[uuid.UUID, str, str]]:
    """Capture (claim_id, support_status, verification_status) for linked claims."""
    result = await db.execute(
        select(ClaimEvidenceLink).where(ClaimEvidenceLink.evidence_id == evidence_id)
    )
    links = list(result.scalars().all())
    snapshot: list[tuple[uuid.UUID, str, str]] = []
    for link in links:
        claim = (
            await db.execute(select(ClaimRecord).where(ClaimRecord.id == link.claim_id))
        ).scalar_one_or_none()
        if claim is None:
            continue
        snapshot.append(
            (claim.id, claim.support_status, claim.verification_status)
        )
    return snapshot


async def attach_evidence_file(
    db: AsyncSession,
    *,
    evidence_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    data: bytes,
    mime_type: str | None,
    original_filename: str | None = None,
    storage: LocalEvidenceStorage | None = None,
) -> EvidenceRecord:
    """
    Store one private attachment for an owned EvidenceRecord.

    Rejects when storage_uri is already set (no replace in F5).
    Does not mutate linked claim support/verification axes.
    """
    evidence = await get_evidence_for_owner(db, evidence_id, owner_user_id)
    if evidence is None:
        raise EvidenceRefError(f"evidence does not exist: {evidence_id}")

    if evidence.storage_uri:
        raise EvidenceRefError(
            "duplicate evidence attachment is not allowed without replace"
        )

    prior_claims = await _linked_claim_status_snapshot(db, evidence_id)

    try:
        stored: EvidenceStoredObject = store_evidence_file(
            owner_user_id=owner_user_id,
            evidence_id=evidence_id,
            data=data,
            mime_type=mime_type,
            original_filename=original_filename,
            storage=storage,
        )
    except EvidenceStorageError as exc:
        raise EvidenceRefError(str(exc)) from exc

    evidence.storage_uri = stored.storage_uri
    evidence.content_hash = stored.content_hash
    evidence.mime_type = stored.mime_type
    evidence.size_bytes = stored.size_bytes
    await db.commit()
    await db.refresh(evidence)

    after_claims = await _linked_claim_status_snapshot(db, evidence_id)
    if after_claims != prior_claims:
        raise EvidenceRefError(
            "attach_evidence_file must not mutate claim support or verification status"
        )
    return evidence
