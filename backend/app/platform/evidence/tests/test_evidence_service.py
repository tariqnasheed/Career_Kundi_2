"""Evidence service semantics (0053-F2)."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.migration_runner import prepare_database
from app.db.models.career_subject import CareerSubject
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.platform.claims import (
    ClaimKind,
    ClaimOrigin,
    SupportStatus,
    VerificationStatus,
)
from app.platform.claims.service import create_claim
from app.platform.evidence import (
    ClaimEvidenceLinkRole,
    EvidenceKind,
    EvidencePrivacyClass,
    EvidenceRefError,
)
from app.platform.evidence.service import (
    create_evidence_record,
    get_evidence_record,
    link_evidence_to_claim,
    list_claim_evidence_links,
    list_owner_evidence,
    list_subject_evidence,
)
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import new_entity_id
from app.platform.provenance import SourceKind
from app.platform.provenance.service import create_snapshot, create_source

F2_PREFIX = "ck_f2svc_"


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str, *, email_prefix: str = "f2") -> uuid.UUID:
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    uid = uuid.uuid4()
    try:
        with Session() as session:
            session.add(
                User(
                    id=uid,
                    email=f"{email_prefix}-{uid.hex[:8]}@example.com",
                    hashed_password=hash_password("test-password-ok"),
                    full_name="F2 User",
                    role=UserRole.USER,
                    plan=SubscriptionPlan.FREE,
                    is_active=True,
                    is_email_verified=False,
                )
            )
            session.commit()
    finally:
        engine.dispose()
    return uid


@require_disposable_postgres
def test_evidence_service_semantics() -> None:
    with temporary_database(prefix=F2_PREFIX) as (_name, url):
        prepare_database(url)
        user_a = _insert_user(url, email_prefix="f2a")
        user_b = _insert_user(url, email_prefix="f2b")
        async_engine = create_async_engine(_async_url(url), pool_pre_ping=True)
        SessionLocal = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )

        async def _run() -> None:
            async with SessionLocal() as db:
                subject_a = CareerSubject(owner_user_id=user_a)
                subject_b = CareerSubject(owner_user_id=user_b)
                db.add_all([subject_a, subject_b])
                await db.commit()
                await db.refresh(subject_a)
                await db.refresh(subject_b)
                sid_a = subject_a.id
                sid_b = subject_b.id

                actor = ActorRef(actor_type=ActorType.USER, actor_id=new_entity_id())
                evidence = await create_evidence_record(
                    db,
                    owner_user_id=user_a,
                    subject_id=sid_a,
                    title="  Degree scan  ",
                    evidence_kind=EvidenceKind.TRANSCRIPT,
                    created_by_actor=actor,
                )
                assert evidence.title == "Degree scan"
                assert evidence.privacy_class == EvidencePrivacyClass.PRIVATE.value
                assert evidence.evidence_kind == EvidenceKind.TRANSCRIPT.value
                assert (await get_evidence_record(db, evidence.id)) is not None
                assert {e.id for e in await list_owner_evidence(db, user_a)} == {
                    evidence.id
                }
                assert {e.id for e in await list_subject_evidence(db, sid_a)} == {
                    evidence.id
                }

                try:
                    await create_evidence_record(
                        db,
                        owner_user_id=user_a,
                        subject_id=sid_b,
                        title="Mismatch",
                        evidence_kind=EvidenceKind.DOCUMENT,
                    )
                    raise AssertionError("owner/subject mismatch should fail")
                except EvidenceRefError:
                    pass

                source_a = await create_source(
                    db, source_kind=SourceKind.DOCUMENT, uri="doc://a"
                )
                source_b = await create_source(
                    db, source_kind=SourceKind.URL, uri="https://b.example"
                )
                snap_a = await create_snapshot(db, source_id=source_a.id)
                snap_b = await create_snapshot(db, source_id=source_b.id)

                try:
                    await create_evidence_record(
                        db,
                        owner_user_id=user_a,
                        title="Snap only",
                        evidence_kind=EvidenceKind.SOURCE_SNAPSHOT,
                        snapshot_id=snap_a.id,
                    )
                    raise AssertionError("snapshot without source should fail")
                except EvidenceRefError:
                    pass

                try:
                    await create_evidence_record(
                        db,
                        owner_user_id=user_a,
                        title="Mismatch snap",
                        evidence_kind=EvidenceKind.SOURCE_SNAPSHOT,
                        source_id=source_a.id,
                        snapshot_id=snap_b.id,
                    )
                    raise AssertionError("source/snapshot mismatch should fail")
                except EvidenceRefError:
                    pass

                linked_meta = await create_evidence_record(
                    db,
                    owner_user_id=user_a,
                    subject_id=sid_a,
                    title="Source-linked material",
                    evidence_kind=EvidenceKind.DOCUMENT,
                    source_id=source_a.id,
                    snapshot_id=snap_a.id,
                    storage_uri="s3://bucket/meta-only",
                    content_hash="abc",
                    mime_type="application/pdf",
                    size_bytes=12,
                )
                assert linked_meta.source_id == source_a.id
                assert linked_meta.snapshot_id == snap_a.id

                claim = await create_claim(
                    db,
                    subject_id=sid_a,
                    claim_kind=ClaimKind.EDUCATION,
                    claim_key="degree",
                    claim_value="MSc",
                    claim_origin=ClaimOrigin.USER_ASSERTED,
                    support_status=SupportStatus.PROFILE_SUPPORTED,
                    verification_status=VerificationStatus.UNVERIFIED,
                )
                claim_id = claim.id
                evidence_id = evidence.id
                prior_support = claim.support_status
                prior_verification = claim.verification_status

                link = await link_evidence_to_claim(
                    db,
                    claim_id=claim_id,
                    evidence_id=evidence_id,
                    link_role=ClaimEvidenceLinkRole.SUPPORTS,
                    created_by_actor=actor,
                )
                assert link.link_role == ClaimEvidenceLinkRole.SUPPORTS.value
                refreshed = await db.get(type(claim), claim_id)
                assert refreshed is not None
                assert refreshed.support_status == prior_support
                assert refreshed.verification_status == prior_verification
                assert refreshed.support_status != SupportStatus.EVIDENCE_BACKED.value
                assert refreshed.verification_status != VerificationStatus.VERIFIED.value

                listed = await list_claim_evidence_links(db, claim_id)
                assert {row.id for row in listed} == {link.id}

                try:
                    await link_evidence_to_claim(
                        db,
                        claim_id=claim_id,
                        evidence_id=evidence_id,
                        link_role=ClaimEvidenceLinkRole.CONTEXT,
                    )
                    raise AssertionError("duplicate link should fail")
                except EvidenceRefError:
                    pass

                foreign_evidence = await create_evidence_record(
                    db,
                    owner_user_id=user_b,
                    subject_id=sid_b,
                    title="Other owner",
                    evidence_kind=EvidenceKind.DOCUMENT,
                )
                try:
                    await link_evidence_to_claim(
                        db,
                        claim_id=claim_id,
                        evidence_id=foreign_evidence.id,
                        link_role=ClaimEvidenceLinkRole.SUPPORTS,
                    )
                    raise AssertionError("cross-owner link should fail")
                except EvidenceRefError:
                    pass

                try:
                    await link_evidence_to_claim(
                        db,
                        claim_id=uuid.uuid4(),
                        evidence_id=evidence_id,
                        link_role=ClaimEvidenceLinkRole.SUPPORTS,
                    )
                    raise AssertionError("missing claim should fail")
                except EvidenceRefError:
                    pass

                try:
                    await link_evidence_to_claim(
                        db,
                        claim_id=claim_id,
                        evidence_id=uuid.uuid4(),
                        link_role=ClaimEvidenceLinkRole.SUPPORTS,
                    )
                    raise AssertionError("missing evidence should fail")
                except EvidenceRefError:
                    pass

                # Cross-subject: evidence scoped to another subject cannot link this claim.
                subject_a2 = CareerSubject(owner_user_id=user_a)
                db.add(subject_a2)
                await db.commit()
                await db.refresh(subject_a2)
                sid_a2 = subject_a2.id
                evidence_a2 = await create_evidence_record(
                    db,
                    owner_user_id=user_a,
                    subject_id=sid_a2,
                    title="Other subject",
                    evidence_kind=EvidenceKind.DOCUMENT,
                )
                try:
                    await link_evidence_to_claim(
                        db,
                        claim_id=claim_id,
                        evidence_id=evidence_a2.id,
                        link_role=ClaimEvidenceLinkRole.SUPPORTS,
                    )
                    raise AssertionError("cross-subject link should fail")
                except EvidenceRefError:
                    pass

                count = int(
                    (
                        await db.execute(text("SELECT COUNT(*) FROM claim_evidence_links"))
                    ).scalar_one()
                )
                assert count == 1

        asyncio.run(_run())
        asyncio.run(async_engine.dispose())
