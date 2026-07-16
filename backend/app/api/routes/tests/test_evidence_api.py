"""Private evidence API boundary tests (0053-F3)."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, hash_password
from app.db.migration_runner import prepare_database
from app.db.models.career_subject import CareerSubject
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.session import get_db
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.main import app
from app.platform.claims import (
    ClaimKind,
    ClaimOrigin,
    SupportStatus,
    VerificationStatus,
)
from app.platform.claims.service import create_claim
from app.platform.evidence.service import create_evidence_record
from app.platform.provenance import SourceKind
from app.platform.provenance.service import create_snapshot, create_source
from app.tools import cache as cache_mod
from app.tools.cache import InMemoryCache

F3_PREFIX = "ck_f2svc_"  # approved disposable prefix
ROUTES = Path(__file__).resolve().parents[1]
FRONTEND_SRC = Path(__file__).resolve().parents[5] / "frontend" / "src"


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
                    full_name="F3 User",
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
        "verified by careerkundi",
        "proof of truth",
        "trusted credential",
        "public credential",
        "wallet",
        "blockchain",
    ):
        assert forbidden not in text_blob
    # Bare "verified" only allowed inside the safe phrase.
    if "verified" in text_blob:
        assert "not independently verified" in text_blob


def test_no_upload_download_or_public_routes() -> None:
    """Public share routes forbidden; private /attachment is allowed since F5."""
    paths = set(app.openapi().get("paths", {}))
    assert any(p.startswith("/api/v1/evidence") for p in paths)
    for path in paths:
        lower = path.lower()
        if "/api/v1/evidence" not in lower:
            continue
        assert "/upload" not in lower
        assert "/download" not in lower
        assert "/share" not in lower
        assert "/public" not in lower
        assert "verification" not in lower
    assert not (ROUTES / "claims.py").exists()
    assert (ROUTES / "evidence.py").exists()


def test_frontend_evidence_library_remains_metadata_only_ui() -> None:
    """F4 library page may exist; F5 must not add file upload controls there."""
    if not FRONTEND_SRC.exists():
        return
    page = FRONTEND_SRC / "pages" / "EvidenceLibraryPage.tsx"
    assert page.exists()
    text = page.read_text(encoding="utf-8")
    assert 'type="file"' not in text
    assert "Upload evidence" not in text
    assert "uploadEvidence" not in text


@require_disposable_postgres
def test_evidence_api_auth_ownership_and_links() -> None:
    with temporary_database(prefix=F3_PREFIX) as (_name, url):
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

        async def _seed(session_factory) -> tuple[
            uuid.UUID,
            uuid.UUID,
            uuid.UUID,
            uuid.UUID,
            uuid.UUID,
            uuid.UUID,
            uuid.UUID,
            uuid.UUID,
            uuid.UUID,
        ]:
            async with session_factory() as db:
                subject_a = CareerSubject(owner_user_id=user_a)
                subject_b = CareerSubject(owner_user_id=user_b)
                subject_a2 = CareerSubject(owner_user_id=user_a)
                db.add_all([subject_a, subject_b, subject_a2])
                await db.commit()
                await db.refresh(subject_a)
                await db.refresh(subject_b)
                await db.refresh(subject_a2)

                source_a = await create_source(
                    db, source_kind=SourceKind.DOCUMENT, uri="doc://a"
                )
                source_b = await create_source(
                    db, source_kind=SourceKind.URL, uri="https://b.example"
                )
                snap_a = await create_snapshot(db, source_id=source_a.id)
                snap_b = await create_snapshot(db, source_id=source_b.id)

                claim_a = await create_claim(
                    db,
                    subject_id=subject_a.id,
                    claim_kind=ClaimKind.EDUCATION,
                    claim_key="degree",
                    claim_value="MSc",
                    claim_origin=ClaimOrigin.USER_ASSERTED,
                    support_status=SupportStatus.PROFILE_SUPPORTED,
                    verification_status=VerificationStatus.UNVERIFIED,
                )
                claim_b = await create_claim(
                    db,
                    subject_id=subject_b.id,
                    claim_kind=ClaimKind.SKILL,
                    claim_key="python",
                    claim_value="Python",
                    claim_origin=ClaimOrigin.USER_ASSERTED,
                    support_status=SupportStatus.NOT_PROVIDED,
                    verification_status=VerificationStatus.UNVERIFIED,
                )
                foreign_evidence = await create_evidence_record(
                    db,
                    owner_user_id=user_b,
                    subject_id=subject_b.id,
                    title="B material",
                    evidence_kind="document",
                )
                return (
                    subject_a.id,
                    subject_b.id,
                    subject_a2.id,
                    claim_a.id,
                    claim_b.id,
                    foreign_evidence.id,
                    source_a.id,
                    snap_a.id,
                    snap_b.id,
                )

        async def _seed_and_dispose() -> tuple:
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
            sid_a,
            sid_b,
            sid_a2,
            claim_a_id,
            claim_b_id,
            foreign_evidence_id,
            source_a_id,
            snap_a_id,
            snap_b_id,
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
                assert client.get("/api/v1/evidence").status_code == 401
                assert (
                    client.post(
                        "/api/v1/evidence",
                        json={"title": "x", "evidence_kind": "document"},
                    ).status_code
                    == 401
                )

                headers_a = {
                    "Authorization": f"Bearer {create_access_token(str(user_a))}"
                }
                headers_b = {
                    "Authorization": f"Bearer {create_access_token(str(user_b))}"
                }

                # Reject caller owner_user_id (extra forbid)
                reject_owner = client.post(
                    "/api/v1/evidence",
                    headers=headers_a,
                    json={
                        "title": "Owned by me",
                        "evidence_kind": "document",
                        "owner_user_id": str(user_b),
                    },
                )
                assert reject_owner.status_code == 422

                # Other user's subject
                other_subject = client.post(
                    "/api/v1/evidence",
                    headers=headers_a,
                    json={
                        "title": "Wrong subject",
                        "evidence_kind": "document",
                        "subject_id": str(sid_b),
                    },
                )
                assert other_subject.status_code == 404

                # Public / shared privacy
                assert (
                    client.post(
                        "/api/v1/evidence",
                        headers=headers_a,
                        json={
                            "title": "Public",
                            "evidence_kind": "document",
                            "privacy_class": "public",
                        },
                    ).status_code
                    == 422
                )
                assert (
                    client.post(
                        "/api/v1/evidence",
                        headers=headers_a,
                        json={
                            "title": "Shared",
                            "evidence_kind": "document",
                            "privacy_class": "shared",
                        },
                    ).status_code
                    == 422
                )

                # Empty title / unknown kind
                assert (
                    client.post(
                        "/api/v1/evidence",
                        headers=headers_a,
                        json={"title": "  ", "evidence_kind": "document"},
                    ).status_code
                    == 422
                )
                assert (
                    client.post(
                        "/api/v1/evidence",
                        headers=headers_a,
                        json={"title": "X", "evidence_kind": "not_a_kind"},
                    ).status_code
                    == 422
                )

                # Snapshot without source / mismatch
                assert (
                    client.post(
                        "/api/v1/evidence",
                        headers=headers_a,
                        json={
                            "title": "Snap only",
                            "evidence_kind": "source_snapshot",
                            "snapshot_id": str(snap_a_id),
                        },
                    ).status_code
                    == 422
                )
                assert (
                    client.post(
                        "/api/v1/evidence",
                        headers=headers_a,
                        json={
                            "title": "Mismatch",
                            "evidence_kind": "source_snapshot",
                            "source_id": str(source_a_id),
                            "snapshot_id": str(snap_b_id),
                        },
                    ).status_code
                    in {404, 422}
                )

                created = client.post(
                    "/api/v1/evidence",
                    headers=headers_a,
                    json={
                        "title": "  Degree scan  ",
                        "evidence_kind": "transcript",
                        "subject_id": str(sid_a),
                        "storage_uri": "s3://meta/only",
                    },
                )
                assert created.status_code == 201, created.text
                env = created.json()
                assert set(env.keys()) == {"data"}
                evidence = env["data"]
                eid = evidence["id"]
                assert evidence["title"] == "Degree scan"
                assert evidence["privacy_class"] == "private"
                assert "owner_user_id" not in evidence
                _assert_safe_wording(evidence)
                assert "not independent review" in evidence["truth_warning"].lower()

                listed = client.get("/api/v1/evidence", headers=headers_a)
                assert listed.status_code == 200
                assert listed.json()["meta"]["count"] == 1
                assert listed.json()["data"][0]["id"] == eid

                listed_b = client.get("/api/v1/evidence", headers=headers_b)
                assert listed_b.status_code == 200
                assert listed_b.json()["meta"]["count"] == 1  # foreign seed evidence
                assert all(item["id"] != eid for item in listed_b.json()["data"])

                got = client.get(f"/api/v1/evidence/{eid}", headers=headers_a)
                assert got.status_code == 200
                assert (
                    client.get(f"/api/v1/evidence/{eid}", headers=headers_b).status_code
                    == 404
                )

                subj_list = client.get(
                    f"/api/v1/evidence/subjects/{sid_a}", headers=headers_a
                )
                assert subj_list.status_code == 200
                assert subj_list.json()["meta"]["count"] == 1
                assert (
                    client.get(
                        f"/api/v1/evidence/subjects/{sid_a}", headers=headers_b
                    ).status_code
                    == 404
                )

                # Cross-subject evidence for later link failure
                other_subj_ev = client.post(
                    "/api/v1/evidence",
                    headers=headers_a,
                    json={
                        "title": "Other subject material",
                        "evidence_kind": "document",
                        "subject_id": str(sid_a2),
                    },
                )
                assert other_subj_ev.status_code == 201
                eid_a2 = other_subj_ev.json()["data"]["id"]

                link = client.post(
                    "/api/v1/evidence/links",
                    headers=headers_a,
                    json={
                        "claim_id": str(claim_a_id),
                        "evidence_id": eid,
                        "link_role": "supports",
                    },
                )
                assert link.status_code == 201, link.text
                link_data = link.json()["data"]
                assert link_data["claim_support_status"] == "profile_supported"
                assert link_data["claim_verification_status"] == "unverified"
                assert (
                    link_data["claim_verification_label"]
                    == "Not independently verified"
                )
                _assert_safe_wording(link_data)

                dup = client.post(
                    "/api/v1/evidence/links",
                    headers=headers_a,
                    json={
                        "claim_id": str(claim_a_id),
                        "evidence_id": eid,
                        "link_role": "context",
                    },
                )
                assert dup.status_code == 409

                assert (
                    client.post(
                        "/api/v1/evidence/links",
                        headers=headers_a,
                        json={
                            "claim_id": str(claim_b_id),
                            "evidence_id": eid,
                            "link_role": "supports",
                        },
                    ).status_code
                    == 404
                )
                assert (
                    client.post(
                        "/api/v1/evidence/links",
                        headers=headers_a,
                        json={
                            "claim_id": str(claim_a_id),
                            "evidence_id": str(foreign_evidence_id),
                            "link_role": "supports",
                        },
                    ).status_code
                    == 404
                )
                assert (
                    client.post(
                        "/api/v1/evidence/links",
                        headers=headers_a,
                        json={
                            "claim_id": str(claim_a_id),
                            "evidence_id": eid_a2,
                            "link_role": "supports",
                        },
                    ).status_code
                    in {404, 422}
                )

                links = client.get(
                    f"/api/v1/evidence/claims/{claim_a_id}/links",
                    headers=headers_a,
                )
                assert links.status_code == 200
                assert links.json()["meta"]["count"] == 1
                assert (
                    client.get(
                        f"/api/v1/evidence/claims/{claim_a_id}/links",
                        headers=headers_b,
                    ).status_code
                    == 404
                )

                # Claim axes unchanged in DB (sync check avoids cross-loop issues)
                sync_engine = create_engine(url)
                try:
                    with sync_engine.connect() as conn:
                        row = conn.execute(
                            text(
                                "SELECT support_status, verification_status "
                                "FROM career_claims WHERE id = :id"
                            ),
                            {"id": claim_a_id},
                        ).one()
                    assert str(row[0]) == "profile_supported"
                    assert str(row[1]) == "unverified"
                finally:
                    sync_engine.dispose()
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.router.lifespan_context = original_lifespan
            cache_mod._CACHE_SINGLETON = original_cache
            asyncio.run(async_engine.dispose())
