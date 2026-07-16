"""Private review-request API tests (0053-F10)."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, hash_password
from app.db.migration_runner import prepare_database
from app.db.models.career_subject import CareerSubject
from app.db.models.claim import ClaimRecord
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.session import get_db
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.main import app
from app.platform.claims import ClaimKind, ClaimOrigin, SupportStatus, VerificationStatus
from app.platform.claims.service import create_claim
from app.tools import cache as cache_mod
from app.tools.cache import InMemoryCache

F10_PREFIX = "ck_f2svc_"
REPO_ROOT = Path(__file__).resolve().parents[5]
ROUTES = REPO_ROOT / "backend" / "app" / "api" / "routes"


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
                    full_name="F10 API User",
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


def _assert_safe_wording(payload: object) -> None:
    text_blob = str(payload).lower()
    for forbidden in (
        "official",
        "trusted",
        "proof of truth",
        "wallet",
        "blockchain",
        "public credential",
        "verified credential",
        "verified document",
        "verified passport",
    ):
        assert forbidden not in text_blob
    if "verified" in text_blob:
        assert "not independently verified" in text_blob


def test_no_approve_reject_or_claims_verify_routes() -> None:
    paths = set(app.openapi().get("paths", {}))
    assert "/api/v1/review-requests" in paths
    assert "/api/v1/claims/verify" not in paths
    assert "/api/v1/passport/verify" not in paths
    assert "/api/v1/verification/approve" not in paths
    assert "/api/v1/verification/reject" not in paths
    for path in paths:
        lower = path.lower()
        if path.startswith("/api/v1/") and (
            "/approve" in lower or path.endswith("/reject") or path.endswith("/verify")
        ):
            raise AssertionError(f"unexpected route: {path}")
    assert (ROUTES / "review_requests.py").exists()
    assert not (ROUTES / "verification.py").exists()
    assert not (ROUTES / "claims.py").exists()


@require_disposable_postgres
def test_review_request_api_guards() -> None:
    with temporary_database(prefix=F10_PREFIX) as (_name, url):
        prepare_database(url)
        user_a = _insert_user(url, f"a-{uuid.uuid4().hex[:8]}@example.com")
        user_b = _insert_user(url, f"b-{uuid.uuid4().hex[:8]}@example.com")

        @asynccontextmanager
        async def _empty_lifespan(_app):
            yield

        original_lifespan = app.router.lifespan_context
        app.router.lifespan_context = _empty_lifespan
        original_cache = cache_mod._CACHE_SINGLETON
        cache_mod._CACHE_SINGLETON = InMemoryCache()

        async def _seed(session_factory):
            async with session_factory() as db:
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
                return (
                    claim_a.id,
                    claim_b.id,
                    claim_a.support_status,
                    claim_a.verification_status,
                )

        async def _seed_and_dispose():
            seed_engine = create_async_engine(_async_url(url), pool_pre_ping=True)
            seed_sessions = async_sessionmaker(
                bind=seed_engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
            try:
                return await _seed(seed_sessions)
            finally:
                await seed_engine.dispose()

        (
            claim_a_id,
            claim_b_id,
            prior_support,
            prior_verification,
        ) = asyncio.run(_seed_and_dispose())

        async_engine = create_async_engine(_async_url(url), pool_pre_ping=True)
        SessionLocal = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )

        async def override_get_db() -> AsyncIterator[AsyncSession]:
            async with SessionLocal() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                token_a = create_access_token(str(user_a))
                token_b = create_access_token(str(user_b))
                headers_a = {"Authorization": f"Bearer {token_a}"}
                headers_b = {"Authorization": f"Bearer {token_b}"}

                assert client.get("/api/v1/review-requests").status_code in (401, 403)
                assert client.post(
                    "/api/v1/review-requests",
                    json={"claim_id": str(claim_a_id)},
                ).status_code in (401, 403)

                r = client.post(
                    "/api/v1/review-requests",
                    headers=headers_a,
                    json={
                        "claim_id": str(claim_a_id),
                        "request_note": "Please review privately",
                    },
                )
                assert r.status_code == 201, r.text
                body = r.json()["data"]
                _assert_safe_wording(body)
                request_id = body["id"]
                assert body["review_state"] == "requested"
                assert body["review_state_label"] == "Review requested"
                assert (
                    "not independently verified"
                    in body["claim_verification_label"].lower()
                )
                assert "not verification" in body["warning"].lower()

                r = client.post(
                    "/api/v1/review-requests",
                    headers=headers_a,
                    json={"claim_id": str(claim_a_id)},
                )
                assert r.status_code == 409

                r = client.post(
                    "/api/v1/review-requests",
                    headers=headers_a,
                    json={"claim_id": str(claim_b_id)},
                )
                assert r.status_code == 404

                r = client.get("/api/v1/review-requests", headers=headers_a)
                assert r.status_code == 200
                listed = r.json()
                _assert_safe_wording(listed)
                assert listed["meta"]["count"] == 1
                assert listed["data"][0]["id"] == request_id

                r = client.get("/api/v1/review-requests", headers=headers_b)
                assert r.status_code == 200
                assert r.json()["meta"]["count"] == 0

                r = client.get(
                    f"/api/v1/review-requests/{request_id}", headers=headers_b
                )
                assert r.status_code == 404

                r = client.post(
                    f"/api/v1/review-requests/{request_id}/cancel",
                    headers=headers_b,
                    json={"cancellation_reason": "nope"},
                )
                assert r.status_code == 404

                r = client.post(
                    f"/api/v1/review-requests/{request_id}/cancel",
                    headers=headers_a,
                    json={"cancellation_reason": "changed mind"},
                )
                assert r.status_code == 200, r.text
                cancelled = r.json()["data"]
                _assert_safe_wording(cancelled)
                assert cancelled["review_state"] == "cancelled"

                r = client.post(
                    f"/api/v1/review-requests/{request_id}/cancel",
                    headers=headers_a,
                    json={},
                )
                assert r.status_code in (400, 422, 409)

                sync_engine = create_engine(url)
                SyncSession = sessionmaker(bind=sync_engine)
                try:
                    with SyncSession() as session:
                        claim_row = session.execute(
                            select(ClaimRecord).where(ClaimRecord.id == claim_a_id)
                        ).scalar_one()
                        assert claim_row.support_status == prior_support
                        assert claim_row.verification_status == prior_verification
                finally:
                    sync_engine.dispose()
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.router.lifespan_context = original_lifespan
            cache_mod._CACHE_SINGLETON = original_cache
            asyncio.run(async_engine.dispose())
