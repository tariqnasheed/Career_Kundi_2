"""Private Passport evidence summary API tests (0053-F8)."""

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
from app.platform.evidence.service import create_evidence_record, link_evidence_to_claim
from app.tools import cache as cache_mod
from app.tools.cache import InMemoryCache

# Reuse approved disposable prefix (cannot extend pf1_test_db allowlist in F8 scope).
F8_PREFIX = "ck_f2svc_"
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
                    full_name="F8 User",
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
    scrubbed = (
        text_blob.replace("not independently verified", "")
        .replace("or verified in this version", "")
        .replace("reviewed, or verified", "")
        .replace("does not verify", "")
        .replace("is not verification", "")
        .replace("not verification", "")
        .replace("'unverified'", "")
        .replace('"unverified"', "")
        .replace("unverified", "")
    )
    assert "verified" not in scrubbed
    assert "verify" not in scrubbed


def test_no_claims_or_passport_mutation_routes_for_f8() -> None:
    assert not (ROUTES / "claims.py").exists()
    paths = set(app.openapi().get("paths", {}))
    assert "/api/v1/evidence/private-awareness-summary" in paths
    assert "/api/v1/evidence/passport-summary" not in paths
    assert "/api/v1/claims" not in paths
    assert "/api/v1/passport/evidence/upload" not in paths
    assert "/api/v1/passport/verify" not in paths
    assert "/api/v1/passport/public" not in paths
    for path in paths:
        if path.startswith("/api/v1/claims"):
            raise AssertionError(f"unexpected claims route: {path}")
        if path.startswith("/api/v1/evidence/") and "/passport" in path:
            raise AssertionError(
                f"evidence path must not contain /passport substring: {path}"
            )


@require_disposable_postgres
def test_evidence_passport_summary_api_guards() -> None:
    with temporary_database(prefix=F8_PREFIX) as (_name, url):
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
                evidence_a = await create_evidence_record(
                    db,
                    owner_user_id=user_a,
                    title="Cert metadata",
                    evidence_kind="certificate",
                    subject_id=subject_a.id,
                    privacy_class="private",
                )
                evidence_b = await create_evidence_record(
                    db,
                    owner_user_id=user_b,
                    title="Other evidence",
                    evidence_kind="document",
                    subject_id=subject_b.id,
                    privacy_class="private",
                )
                await link_evidence_to_claim(
                    db,
                    claim_id=claim_a.id,
                    evidence_id=evidence_a.id,
                    link_role="supports",
                )
                await link_evidence_to_claim(
                    db,
                    claim_id=claim_b.id,
                    evidence_id=evidence_b.id,
                    link_role="context",
                )
                return (
                    claim_a.id,
                    claim_b.id,
                    evidence_a.id,
                    evidence_b.id,
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
            evidence_a_id,
            evidence_b_id,
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

                # 1) auth required
                assert client.get(
                    "/api/v1/evidence/private-awareness-summary"
                ).status_code in (401, 403)

                # 2–6) current-user links only + safe labels + truth warning
                r = client.get(
                    "/api/v1/evidence/private-awareness-summary", headers=headers_a
                )
                assert r.status_code == 200, r.text
                body = r.json()
                _assert_safe_wording(body)
                data = body["data"]
                assert data["linked_claims_count"] == 1
                assert data["evidence_records_count"] == 1
                assert len(data["items"]) == 1
                item = data["items"][0]
                assert item["claim_id"] == str(claim_a_id)
                assert item["evidence_id"] == str(evidence_a_id)
                assert item["claim_value"] == "Python"
                assert item["evidence_title"] == "Cert metadata"
                assert item["link_role"] == "supports"
                assert (
                    "not independently verified"
                    in item["claim_verification_label"].lower()
                )
                assert item["attachment_safety_status"] == "scan_not_available"
                assert item["attachment_safety_label"] == "Scan not available"
                assert (
                    "not malware-scanned"
                    in item["attachment_safety_warning"].lower()
                )
                assert "not independently verified" in data["truth_warning"].lower()
                assert str(claim_b_id) not in str(body)
                assert str(evidence_b_id) not in str(body)

                # 7–8) no public URL / raw filesystem path
                blob = str(body).lower()
                assert "http://" not in blob
                assert "https://" not in blob
                assert "/tmp/" not in blob
                assert "evidence_files" not in blob
                assert "storage_uri" not in blob

                # 4) empty summary for user with no evidence records
                user_c = _insert_user(url, f"c-{uuid.uuid4().hex[:8]}@example.com")
                headers_c = {
                    "Authorization": f"Bearer {create_access_token(str(user_c))}"
                }
                r = client.get(
                    "/api/v1/evidence/private-awareness-summary", headers=headers_c
                )
                assert r.status_code == 200
                empty = r.json()["data"]
                assert empty["linked_claims_count"] == 0
                assert empty["evidence_records_count"] == 0
                assert empty["items"] == []
                _assert_safe_wording(empty)

                # 3) user B does not see user A links
                r = client.get(
                    "/api/v1/evidence/private-awareness-summary", headers=headers_b
                )
                assert r.status_code == 200
                b_data = r.json()["data"]
                ids = {row["claim_id"] for row in b_data["items"]}
                assert str(claim_a_id) not in ids
                assert str(claim_b_id) in ids

                # 9–10) summary does not mutate claim axes
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
