"""Review intake hardening tests (0053-F12)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.migration_runner import prepare_database
from app.db.models.career_subject import CareerSubject
from app.db.models.claim import ClaimRecord
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.platform.claims import ClaimKind, ClaimOrigin, SupportStatus, VerificationStatus
from app.platform.claims.service import create_claim
from app.platform.evidence.service import create_evidence_record, link_evidence_to_claim
from app.platform.evidence.status import ClaimEvidenceLinkRole, EvidenceKind
from app.platform.verification.refs import VerificationRefError
from app.platform.verification.service import (
    MSG_LINKED_EVIDENCE_REQUIRED,
    MSG_NOTE_TOO_LONG,
    MSG_REASON_TOO_LONG,
    cancel_review_request,
    create_review_request,
    get_review_intake_eligibility,
    normalize_cancellation_reason,
    normalize_review_request_note,
)
from app.platform.verification.status import ReviewState

F12_PREFIX = "ck_f2svc_"


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str, email: str) -> uuid.UUID:
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    uid = uuid.uuid4()
    try:
        with Session() as session:
            session.add(
                User(
                    id=uid,
                    email=email,
                    hashed_password=hash_password("test-password-ok"),
                    full_name="F12 User",
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


async def _link_owned_evidence(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    subject_id: uuid.UUID,
    claim_id: uuid.UUID,
) -> None:
    evidence = await create_evidence_record(
        db,
        owner_user_id=owner_user_id,
        subject_id=subject_id,
        title="F12 private evidence",
        evidence_kind=EvidenceKind.CERTIFICATE,
    )
    await link_evidence_to_claim(
        db,
        claim_id=claim_id,
        evidence_id=evidence.id,
        link_role=ClaimEvidenceLinkRole.SUPPORTS,
    )


@require_disposable_postgres
def test_review_intake_eligibility_and_note_bounds() -> None:
    with temporary_database(prefix=F12_PREFIX) as (_name, url):
        prepare_database(url)
        user_a = _insert_user(url, f"a-{uuid.uuid4().hex[:8]}@example.com")
        user_b = _insert_user(url, f"b-{uuid.uuid4().hex[:8]}@example.com")

        async def _run() -> None:
            engine = create_async_engine(_async_url(url), pool_pre_ping=True)
            sessions = async_sessionmaker(
                bind=engine, expire_on_commit=False, class_=AsyncSession
            )
            try:
                async with sessions() as db:
                    subject_a = CareerSubject(owner_user_id=user_a)
                    subject_b = CareerSubject(owner_user_id=user_b)
                    db.add_all([subject_a, subject_b])
                    await db.commit()
                    await db.refresh(subject_a)
                    await db.refresh(subject_b)

                    claim_a = await create_claim(
                        db,
                        subject_id=subject_a.id,
                        claim_kind=ClaimKind.SKILL,
                        claim_key="python",
                        claim_value="Python",
                        claim_origin=ClaimOrigin.USER_ASSERTED,
                        support_status=SupportStatus.NOT_PROVIDED,
                        verification_status=VerificationStatus.UNVERIFIED,
                    )
                    claim_b = await create_claim(
                        db,
                        subject_id=subject_b.id,
                        claim_kind=ClaimKind.SKILL,
                        claim_key="java",
                        claim_value="Java",
                        claim_origin=ClaimOrigin.USER_ASSERTED,
                        support_status=SupportStatus.NOT_PROVIDED,
                        verification_status=VerificationStatus.UNVERIFIED,
                    )

                    # No linked evidence → ineligible
                    elig = await get_review_intake_eligibility(
                        db, owner_user_id=user_a, claim_id=claim_a.id
                    )
                    assert elig.eligible is False
                    assert elig.reason == MSG_LINKED_EVIDENCE_REQUIRED

                    with pytest.raises(VerificationRefError, match="linked private"):
                        await create_review_request(
                            db, owner_user_id=user_a, claim_id=claim_a.id
                        )

                    # Foreign claim → not owned
                    with pytest.raises(VerificationRefError, match="not owned"):
                        await create_review_request(
                            db, owner_user_id=user_a, claim_id=claim_b.id
                        )

                    # Foreign evidence linked via raw SQL does not satisfy ownership
                    evidence_b = await create_evidence_record(
                        db,
                        owner_user_id=user_b,
                        subject_id=subject_b.id,
                        title="Other user evidence",
                        evidence_kind=EvidenceKind.CERTIFICATE,
                    )
                    await db.execute(
                        text(
                            "INSERT INTO claim_evidence_links "
                            "(id, claim_id, evidence_id, link_role, created_at, updated_at) "
                            "VALUES (:id, :claim_id, :evidence_id, :role, NOW(), NOW())"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "claim_id": str(claim_a.id),
                            "evidence_id": str(evidence_b.id),
                            "role": ClaimEvidenceLinkRole.SUPPORTS.value,
                        },
                    )
                    await db.commit()

                    elig = await get_review_intake_eligibility(
                        db, owner_user_id=user_a, claim_id=claim_a.id
                    )
                    assert elig.eligible is False
                    assert elig.owned_linked_evidence_count == 0

                    with pytest.raises(VerificationRefError, match="linked private"):
                        await create_review_request(
                            db, owner_user_id=user_a, claim_id=claim_a.id
                        )

                    # Owned linked evidence → eligible
                    await _link_owned_evidence(
                        db,
                        owner_user_id=user_a,
                        subject_id=subject_a.id,
                        claim_id=claim_a.id,
                    )
                    prior_support = claim_a.support_status
                    prior_verification = claim_a.verification_status

                    row = await create_review_request(
                        db,
                        owner_user_id=user_a,
                        claim_id=claim_a.id,
                        request_note="  Please review privately  ",
                    )
                    assert row.review_state == ReviewState.REQUESTED.value
                    assert row.request_note == "Please review privately"

                    # Duplicate active blocked
                    with pytest.raises(VerificationRefError, match="duplicate"):
                        await create_review_request(
                            db, owner_user_id=user_a, claim_id=claim_a.id
                        )

                    # Blank note → None
                    cancelled = await cancel_review_request(
                        db,
                        request_id=row.id,
                        owner_user_id=user_a,
                        cancellation_reason="   ",
                    )
                    assert cancelled.review_state == ReviewState.CANCELLED.value
                    assert cancelled.cancellation_reason is None

                    # After cancel, new request allowed (partial unique on active)
                    row2 = await create_review_request(
                        db,
                        owner_user_id=user_a,
                        claim_id=claim_a.id,
                        request_note="",
                    )
                    assert row2.request_note is None
                    assert row2.review_state == ReviewState.REQUESTED.value

                    cancelled2 = await cancel_review_request(
                        db,
                        request_id=row2.id,
                        owner_user_id=user_a,
                        cancellation_reason="  changed mind  ",
                    )
                    assert cancelled2.cancellation_reason == "changed mind"

                    refreshed = (
                        await db.execute(
                            select(ClaimRecord).where(ClaimRecord.id == claim_a.id)
                        )
                    ).scalar_one()
                    assert refreshed.support_status == prior_support
                    assert refreshed.verification_status == prior_verification

                    # Note / reason length
                    assert normalize_review_request_note("  hi  ") == "hi"
                    assert normalize_review_request_note("   ") is None
                    with pytest.raises(VerificationRefError, match=MSG_NOTE_TOO_LONG):
                        normalize_review_request_note("x" * 1001)
                    assert normalize_cancellation_reason("  ok  ") == "ok"
                    assert normalize_cancellation_reason("  ") is None
                    with pytest.raises(VerificationRefError, match=MSG_REASON_TOO_LONG):
                        normalize_cancellation_reason("y" * 501)

                    with pytest.raises(VerificationRefError, match=MSG_NOTE_TOO_LONG):
                        await create_review_request(
                            db,
                            owner_user_id=user_a,
                            claim_id=claim_a.id,
                            request_note="n" * 1001,
                        )
            finally:
                await engine.dispose()

        asyncio.run(_run())


def test_normalize_helpers_unit() -> None:
    assert normalize_review_request_note(None) is None
    assert normalize_cancellation_reason(None) is None
    assert normalize_review_request_note("a" * 1000) == "a" * 1000
    assert normalize_cancellation_reason("b" * 500) == "b" * 500
