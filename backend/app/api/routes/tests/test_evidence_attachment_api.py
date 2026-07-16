"""Private evidence attachment API tests (0053-F5)."""

from __future__ import annotations

import ast
import asyncio
import hashlib
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.api.routes import evidence as evidence_routes
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
from app.platform.evidence.storage import LocalEvidenceStorage
from app.tools import cache as cache_mod
from app.tools.cache import InMemoryCache

F5_PREFIX = "ck_f2svc_"
REPO_ROOT = Path(__file__).resolve().parents[5]
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"


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
                    full_name="F5 User",
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
    ):
        assert forbidden not in text_blob
    if "verified" in text_blob:
        assert "not independently verified" in text_blob


def test_no_public_url_or_share_routes() -> None:
    paths = set(app.openapi().get("paths", {}))
    assert "/api/v1/evidence/{evidence_id}/attachment" in paths
    for path in paths:
        lower = path.lower()
        if "/api/v1/evidence" not in lower:
            continue
        assert "/share" not in lower
        assert "/public" not in lower
        assert "signed" not in lower


def test_no_frontend_upload_ui_or_feature_domain_changes() -> None:
    """F6 may attach privately on Evidence Library; still no verify/share/public UI."""
    page = FRONTEND_SRC / "pages" / "EvidenceLibraryPage.tsx"
    assert page.exists()
    text = page.read_text(encoding="utf-8")
    assert 'type="file"' in text
    assert "Attach private file" in text
    assert "Download private attachment" in text
    assert "Upload evidence" not in text
    assert "Verify evidence" not in text
    assert "uploadEvidenceAttachment" in text or "evidenceApi" in text
    assert "Save evidence metadata" in text
    assert "Not independently verified" in text
    assert "does not verify" in text.lower()

    forbidden_imports = (
        "app.career_passport",
        "app.tools.llm",
        "app.api.routes.passport",
        "app.api.routes.cv_builder",
        "app.api.routes.roadmap",
        "app.api.routes.job_search",
        "pytesseract",
        "pdfminer",
        "pypdf",
    )
    for path in EVIDENCE_PKG.rglob("*.py"):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for prefix in forbidden_imports:
                    assert not mod.startswith(prefix), f"{path}: {mod}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_imports:
                        assert not alias.name.startswith(prefix), path


@require_disposable_postgres
def test_evidence_attachment_upload_download_guards(tmp_path: Path) -> None:
    with temporary_database(prefix=F5_PREFIX) as (_name, url):
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

        async def _seed(session_factory) -> tuple[uuid.UUID, uuid.UUID, str, str]:
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
                    title="Cert metadata",
                    evidence_kind="certificate",
                    subject_id=subject.id,
                    privacy_class="private",
                )
                await link_evidence_to_claim(
                    db,
                    claim_id=claim.id,
                    evidence_id=evidence.id,
                    link_role="supports",
                )
                return (
                    evidence.id,
                    claim.id,
                    claim.support_status,
                    claim.verification_status,
                )

        async def _seed_and_dispose() -> tuple[uuid.UUID, uuid.UUID, str, str]:
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

        evidence_id, claim_id, prior_support, prior_verification = asyncio.run(
            _seed_and_dispose()
        )

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

                # 1) upload requires auth
                r = client.post(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    files={"file": ("note.txt", b"hello", "text/plain")},
                )
                assert r.status_code in (401, 403)

                # 2) missing evidence → safe 404
                missing = uuid.uuid4()
                r = client.post(
                    f"/api/v1/evidence/{missing}/attachment",
                    headers=headers_a,
                    files={"file": ("note.txt", b"hello", "text/plain")},
                )
                assert r.status_code == 404

                # 3) other user’s evidence → safe 404
                r = client.post(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_b,
                    files={"file": ("note.txt", b"hello", "text/plain")},
                )
                assert r.status_code == 404

                # 4) empty file rejected
                r = client.post(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_a,
                    files={"file": ("empty.txt", b"", "text/plain")},
                )
                assert r.status_code == 422

                # 5) too large rejected
                r = client.post(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_a,
                    files={"file": ("big.txt", b"x" * 65, "text/plain")},
                )
                assert r.status_code == 422

                # 6) disallowed MIME rejected
                r = client.post(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_a,
                    files={
                        "file": ("x.bin", b"MZ", "application/x-msdownload")
                    },
                )
                assert r.status_code == 422

                # 7–13) accepted upload
                payload = b"allowed-content"
                r = client.post(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_a,
                    files={"file": ("note.txt", payload, "text/plain")},
                )
                assert r.status_code == 200, r.text
                body = r.json()["data"]
                _assert_safe_wording(body)
                assert "truth_warning" in body
                warning = body["truth_warning"].lower()
                assert "private metadata" in warning
                assert "not independent review" in warning
                assert body["has_attachment"] is True
                assert body["mime_type"] == "text/plain"
                assert body["size_bytes"] == len(payload)
                assert body["content_hash"] == hashlib.sha256(payload).hexdigest()
                assert body["storage_uri"].startswith("local-evidence://")
                assert not body["storage_uri"].startswith("http")
                stored_path = storage.open_evidence_file(
                    body["storage_uri"],
                    owner_user_id=user_a,
                    evidence_id=evidence_id,
                )
                assert stored_path.is_file()
                assert stored_path.resolve().is_relative_to(
                    (tmp_path / "evidence_files").resolve()
                )

                # 16) duplicate upload rejected
                r = client.post(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_a,
                    files={"file": ("note2.txt", b"again", "text/plain")},
                )
                assert r.status_code == 409

                # 17) download requires auth
                r = client.get(f"/api/v1/evidence/{evidence_id}/attachment")
                assert r.status_code in (401, 403)

                # 18) download own succeeds
                r = client.get(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_a,
                )
                assert r.status_code == 200
                assert r.content == payload
                assert r.headers.get("cache-control") == "no-store"
                assert "attachment" in (
                    r.headers.get("content-disposition") or ""
                ).lower()

                # 19) other user download → 404
                r = client.get(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_b,
                )
                assert r.status_code == 404

                # 14–15) claim axes unchanged (sync read avoids loop mismatch)
                sync_engine = create_engine(url)
                SyncSession = sessionmaker(bind=sync_engine)
                try:
                    with SyncSession() as session:
                        claim_row = session.execute(
                            select(ClaimRecord).where(ClaimRecord.id == claim_id)
                        ).scalar_one()
                        assert claim_row.support_status == prior_support
                        assert claim_row.verification_status == prior_verification
                finally:
                    sync_engine.dispose()

                # 20) missing stored file → 404
                stored_path.unlink()
                r = client.get(
                    f"/api/v1/evidence/{evidence_id}/attachment",
                    headers=headers_a,
                )
                assert r.status_code == 404

        finally:
            evidence_routes._storage = original_storage_factory
            app.dependency_overrides.pop(get_db, None)
            app.router.lifespan_context = original_lifespan
            cache_mod._CACHE_SINGLETON = original_cache
            asyncio.run(async_engine.dispose())
