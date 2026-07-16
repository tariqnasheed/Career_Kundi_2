"""Private evidence attachment DELETE API tests (0053-F14)."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes import evidence as evidence_routes
from app.core.security import create_access_token, hash_password
from app.db.migration_runner import prepare_database
from app.db.models.career_subject import CareerSubject
from app.db.models.claim import ClaimRecord
from app.db.models.evidence import ClaimEvidenceLink, EvidenceRecord
from app.db.models.review_request import ReviewRequest
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.session import get_db
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.main import app
from app.platform.claims import ClaimKind, ClaimOrigin, SupportStatus, VerificationStatus
from app.platform.claims.service import create_claim
from app.platform.evidence.service import (
    attach_evidence_file,
    create_evidence_record,
    link_evidence_to_claim,
)
from app.platform.evidence.status import ClaimEvidenceLinkRole, EvidenceKind
from app.platform.evidence.storage import LocalEvidenceStorage
from app.platform.verification.service import create_review_request
from app.tools import cache as cache_mod
from app.tools.cache import InMemoryCache

F14_PREFIX = "ck_f2svc_"


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
                    full_name="F14 User",
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
        "verified document",
    ):
        assert forbidden not in text_blob
    scrubbed = (
        text_blob.replace("not independently verified", "")
        .replace("or verified in this version", "")
        .replace("reviewed, or verified", "")
        .replace("unverified", "")
    )
    assert "verified" not in scrubbed
    assert "/tmp/" not in text_blob
    assert "evidence_files" not in text_blob


def test_delete_attachment_route_exists() -> None:
    openapi_paths = app.openapi().get("paths", {})
    assert "/api/v1/evidence/{evidence_id}/attachment" in openapi_paths
    methods = {
        m.lower()
        for m in openapi_paths[
            "/api/v1/evidence/{evidence_id}/attachment"
        ].keys()
    }
    assert "delete" in methods


@require_disposable_postgres
def test_evidence_attachment_delete_guards(tmp_path: Path) -> None:
    with temporary_database(prefix=F14_PREFIX) as (_name, url):
        prepare_database(url)
        user_a = _insert_user(url, f"a-{uuid.uuid4().hex[:8]}@example.com")
        user_b = _insert_user(url, f"b-{uuid.uuid4().hex[:8]}@example.com")

        storage = LocalEvidenceStorage(tmp_path / "evidence_files", max_upload_bytes=64)
        original_storage_factory = evidence_routes._storage
        evidence_routes._storage = lambda: storage

        @asynccontextmanager
        async def _empty_lifespan(_app):
            yield

        original_lifespan = app.router.lifespan_context
        app.router.lifespan_context = _empty_lifespan
        original_cache = cache_mod._CACHE_SINGLETON
        cache_mod._CACHE_SINGLETON = InMemoryCache()

        async def _seed(session_factory):
            async with session_factory() as db:
                subject = CareerSubject(owner_user_id=user_a)
                db.add(subject)
                await db.commit()
                await db.refresh(subject)
                claim = await create_claim(
                    db,
                    subject_id=subject.id,
                    claim_kind=ClaimKind.SKILL,
                    claim_key="python",
                    claim_value="Python",
                    claim_origin=ClaimOrigin.USER_ASSERTED,
                    support_status=SupportStatus.NOT_PROVIDED,
                    verification_status=VerificationStatus.UNVERIFIED,
                )
                evidence = await create_evidence_record(
                    db,
                    owner_user_id=user_a,
                    subject_id=subject.id,
                    title="F14 evidence",
                    evidence_kind=EvidenceKind.CERTIFICATE,
                )
                bare = await create_evidence_record(
                    db,
                    owner_user_id=user_a,
                    subject_id=subject.id,
                    title="No attachment",
                    evidence_kind=EvidenceKind.DOCUMENT,
                )
                await link_evidence_to_claim(
                    db,
                    claim_id=claim.id,
                    evidence_id=evidence.id,
                    link_role=ClaimEvidenceLinkRole.SUPPORTS,
                )
                await attach_evidence_file(
                    db,
                    evidence_id=evidence.id,
                    owner_user_id=user_a,
                    data=b"f14-bytes",
                    mime_type="text/plain",
                    storage=storage,
                )
                await create_review_request(
                    db,
                    owner_user_id=user_a,
                    claim_id=claim.id,
                    request_note="keep me",
                )
                return (
                    evidence.id,
                    bare.id,
                    claim.id,
                    claim.support_status,
                    claim.verification_status,
                )

        async def _seed_and_dispose():
            seed_engine = create_async_engine(_async_url(url), pool_pre_ping=True)
            seed_sessions = async_sessionmaker(
                bind=seed_engine, expire_on_commit=False, class_=AsyncSession
            )
            try:
                return await _seed(seed_sessions)
            finally:
                await seed_engine.dispose()

        (
            evidence_id,
            bare_id,
            claim_id,
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

                assert client.delete(
                    f"/api/v1/evidence/{evidence_id}/attachment"
                ).status_code in (401, 403)

                assert (
                    client.delete(
                        f"/api/v1/evidence/{uuid.uuid4()}/attachment",
                        headers=headers_a,
                    ).status_code
                    == 404
                )

                assert (
                    client.delete(
                        f"/api/v1/evidence/{evidence_id}/attachment",
                        headers=headers_b,
                    ).status_code
                    == 404
                )

                r = client.delete(
                    f"/api/v1/evidence/{bare_id}/attachment",
                    headers=headers_a,
                )
                assert r.status_code == 404
                assert "no private attachment" in r.text.lower()

                # Confirm file exists before delete
                sync_engine = create_engine(url)
                SyncSession = sessionmaker(bind=sync_engine)
                try:
                    with SyncSession() as session:
                        row = session.execute(
                            select(EvidenceRecord).where(
                                EvidenceRecord.id == evidence_id
                            )
                        ).scalar_one()
                        uri = row.storage_uri
                        assert uri
                    path = storage.open_evidence_file(
                        uri, owner_user_id=user_a, evidence_id=evidence_id
                    )
                    assert path.is_file()
                finally:
                    sync_engine.dispose()

                r = client.delete(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_a,
                )
                assert r.status_code == 200, r.text
                body = r.json()["data"]
                _assert_safe_wording(body)
                assert body["has_attachment"] is False
                assert body["storage_uri"] is None
                assert body["content_hash"] is None
                assert body["mime_type"] is None
                assert body["size_bytes"] is None
                assert body["attachment_safety_status"] == "scan_not_available"
                assert "not malware-scanned" in body["attachment_safety_warning"].lower()
                assert not path.exists()

                # Passport summary: no attachment
                r = client.get(
                    "/api/v1/evidence/private-awareness-summary",
                    headers=headers_a,
                )
                assert r.status_code == 200
                item = r.json()["data"]["items"][0]
                assert item["has_attachment"] is False
                assert item["attachment_safety_status"] == "scan_not_available"

                # Retained rows / unchanged claim statuses
                sync_engine = create_engine(url)
                SyncSession = sessionmaker(bind=sync_engine)
                try:
                    with SyncSession() as session:
                        assert (
                            session.execute(
                                select(func.count())
                                .select_from(EvidenceRecord)
                                .where(EvidenceRecord.id == evidence_id)
                            ).scalar_one()
                            == 1
                        )
                        assert (
                            session.execute(
                                select(func.count())
                                .select_from(ClaimEvidenceLink)
                                .where(ClaimEvidenceLink.evidence_id == evidence_id)
                            ).scalar_one()
                            == 1
                        )
                        assert (
                            session.execute(
                                select(func.count())
                                .select_from(ReviewRequest)
                                .where(ReviewRequest.claim_id == claim_id)
                            ).scalar_one()
                            == 1
                        )
                        claim_row = session.execute(
                            select(ClaimRecord).where(ClaimRecord.id == claim_id)
                        ).scalar_one()
                        assert claim_row.support_status == prior_support
                        assert claim_row.verification_status == prior_verification
                finally:
                    sync_engine.dispose()
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.router.lifespan_context = original_lifespan
            cache_mod._CACHE_SINGLETON = original_cache
            evidence_routes._storage = original_storage_factory
            asyncio.run(async_engine.dispose())
