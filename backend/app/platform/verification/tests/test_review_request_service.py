"""Review request service tests (0053-F10 / F12)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import create_engine, select
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
    cancel_review_request,
    create_review_request,
    get_review_request_for_owner,
    list_review_requests_for_owner,
)
from app.platform.verification.status import ReviewState

F10_PREFIX = "ck_f2svc_"


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
                    full_name="F10 User",
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
def test_review_request_service_ownership_and_no_claim_mutation() -> None:
    with temporary_database(prefix=F10_PREFIX) as (_name, url):
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
                    prior_support = claim_a.support_status
                    prior_verification = claim_a.verification_status

                    # F12: must link owned evidence before request
                    evidence_a = await create_evidence_record(
                        db,
                        owner_user_id=user_a,
                        subject_id=subject_a.id,
                        title="Owned evidence",
                        evidence_kind=EvidenceKind.CERTIFICATE,
                    )
                    await link_evidence_to_claim(
                        db,
                        claim_id=claim_a.id,
                        evidence_id=evidence_a.id,
                        link_role=ClaimEvidenceLinkRole.SUPPORTS,
                    )

                    row = await create_review_request(
                        db,
                        owner_user_id=user_a,
                        claim_id=claim_a.id,
                        request_note="Please review",
                    )
                    assert row.review_state == ReviewState.REQUESTED.value
                    assert row.owner_user_id == user_a
                    assert row.claim_id == claim_a.id

                    with pytest.raises(VerificationRefError):
                        await create_review_request(
                            db,
                            owner_user_id=user_a,
                            claim_id=claim_a.id,
                        )

                    with pytest.raises(VerificationRefError):
                        await create_review_request(
                            db,
                            owner_user_id=user_a,
                            claim_id=claim_b.id,
                        )

                    listed = await list_review_requests_for_owner(db, user_a)
                    assert len(listed) == 1
                    assert listed[0].id == row.id
                    assert await list_review_requests_for_owner(db, user_b) == []

                    assert (
                        await get_review_request_for_owner(db, row.id, user_b) is None
                    )

                    cancelled = await cancel_review_request(
                        db,
                        request_id=row.id,
                        owner_user_id=user_a,
                        cancellation_reason="changed mind",
                    )
                    assert cancelled.review_state == ReviewState.CANCELLED.value
                    assert cancelled.cancellation_reason == "changed mind"
                    assert cancelled.cancelled_at is not None

                    with pytest.raises(VerificationRefError):
                        await cancel_review_request(
                            db,
                            request_id=row.id,
                            owner_user_id=user_a,
                        )

                    with pytest.raises(VerificationRefError):
                        await cancel_review_request(
                            db,
                            request_id=row.id,
                            owner_user_id=user_b,
                        )

                    refreshed = (
                        await db.execute(
                            select(ClaimRecord).where(ClaimRecord.id == claim_a.id)
                        )
                    ).scalar_one()
                    assert refreshed.support_status == prior_support
                    assert refreshed.verification_status == prior_verification
            finally:
                await engine.dispose()

        asyncio.run(_run())
