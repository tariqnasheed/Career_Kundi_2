"""Platform API foundation tests (0050-PF8-S1)."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, hash_password
from app.db.migration_runner import prepare_database
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.session import get_db
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.main import app
from app.tools import cache as cache_mod
from app.tools.cache import InMemoryCache

PF8_PREFIX = "ck_pf8s1_"
FOUNDATION_VERSIONS = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
)


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
                    full_name="PF8 User",
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


def test_no_new_foundation_migration_for_pf8() -> None:
    names = {p.name for p in FOUNDATION_VERSIONS.glob("*.py") if p.name != "__init__.py"}
    assert not any("pf8" in n.lower() or "api_foundation" in n.lower() for n in names)
    assert "f0006_lifecycle_loop_foundation.py" in names
    # PF8 itself added no migration; later slices may advance the head.


def test_no_public_claim_provenance_geo_lifecycle_write_routes() -> None:
    paths = {getattr(r, "path", "") for r in app.routes}
    forbidden_substrings = (
        "/platform/claims",
        "/platform/provenance",
        "/platform/geo",
        "/platform/sources",
        "/platform/snapshots",
        "/platform/jurisdictions",
        "/platform/locales",
        "/recommendations",
        "/attempts",
        "/outcomes",
        "/feedback",
    )
    for path in paths:
        for needle in forbidden_substrings:
            assert needle not in path, f"unexpected route {path!r} contains {needle!r}"


@require_disposable_postgres
def test_platform_api_subjects_and_goals() -> None:
    # Extend disposable prefix support inline if needed via pf1 helper
    from app.db.tests import pf1_test_db

    if "ck_pf8s1_" not in pf1_test_db.APPROVED_DISPOSABLE_PREFIXES:
        # Should already be added; fail loudly if not
        raise AssertionError("ck_pf8s1_ must be an approved disposable prefix")

    with temporary_database(prefix=PF8_PREFIX) as (_name, url):
        prepare_database(url)
        user_a = _insert_user(url, f"a-{uuid.uuid4().hex[:8]}@example.com")
        user_b = _insert_user(url, f"b-{uuid.uuid4().hex[:8]}@example.com")

        async_engine = create_async_engine(_async_url(url), pool_pre_ping=True)
        SessionLocal = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )

        async def override_get_db() -> AsyncIterator[AsyncSession]:
            async with SessionLocal() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        @asynccontextmanager
        async def _empty_lifespan(_app):
            yield

        original_lifespan = app.router.lifespan_context
        app.router.lifespan_context = _empty_lifespan
        original_cache = cache_mod._CACHE_SINGLETON
        cache_mod._CACHE_SINGLETON = InMemoryCache()
        try:
            with TestClient(app) as client:
                # A. Auth
                assert client.get("/api/v1/platform/subjects").status_code == 401
                assert client.post("/api/v1/platform/subjects").status_code == 401
                assert (
                    client.post(
                        f"/api/v1/platform/subjects/{uuid.uuid4()}/goals",
                        json={
                            "goal_kind": "career",
                            "title": "x",
                        },
                    ).status_code
                    == 401
                )

                headers_a = {
                    "Authorization": f"Bearer {create_access_token(str(user_a))}"
                }
                headers_b = {
                    "Authorization": f"Bearer {create_access_token(str(user_b))}"
                }

                # B. Subjects — no auto-create on list
                empty_list = client.get("/api/v1/platform/subjects", headers=headers_a)
                assert empty_list.status_code == 200
                assert empty_list.json() == {"data": [], "meta": {"count": 0}}

                created = client.post("/api/v1/platform/subjects", headers=headers_a)
                assert created.status_code == 201
                env = created.json()
                assert set(env.keys()) == {"data"}
                subject = env["data"]
                sid = subject["id"]
                assert subject["owner_user_id"] == str(user_a)
                assert "email" not in subject
                assert "hashed_password" not in subject

                listed = client.get("/api/v1/platform/subjects", headers=headers_a)
                assert listed.status_code == 200
                assert listed.json()["meta"]["count"] == 1
                assert listed.json()["data"][0]["id"] == sid

                got = client.get(f"/api/v1/platform/subjects/{sid}", headers=headers_a)
                assert got.status_code == 200
                assert got.json()["data"]["id"] == sid

                assert (
                    client.get(
                        f"/api/v1/platform/subjects/{sid}", headers=headers_b
                    ).status_code
                    == 404
                )

                # C. Goals
                g_create = client.post(
                    f"/api/v1/platform/subjects/{sid}/goals",
                    headers=headers_a,
                    json={
                        "goal_kind": "job_search",
                        "title": "  Land a role  ",
                        "description": "Backend",
                    },
                )
                assert g_create.status_code == 201, g_create.text
                g_env = g_create.json()
                assert set(g_env.keys()) == {"data"}
                goal = g_env["data"]
                assert goal["subject_id"] == sid
                assert goal["title"] == "Land a role"
                assert goal["status"] == "active"
                assert goal["goal_kind"] == "job_search"
                gid = goal["id"]

                g_list = client.get(
                    f"/api/v1/platform/subjects/{sid}/goals", headers=headers_a
                )
                assert g_list.status_code == 200
                assert g_list.json()["meta"]["count"] == 1
                assert g_list.json()["data"][0]["id"] == gid

                g_get = client.get(
                    f"/api/v1/platform/subjects/{sid}/goals/{gid}",
                    headers=headers_a,
                )
                assert g_get.status_code == 200
                assert g_get.json()["data"]["id"] == gid

                # User B cannot create under A's subject
                assert (
                    client.post(
                        f"/api/v1/platform/subjects/{sid}/goals",
                        headers=headers_b,
                        json={"goal_kind": "career", "title": "Nope"},
                    ).status_code
                    == 404
                )

                # Subject B + goal under A accessed via B's subject → 404
                sub_b = client.post(
                    "/api/v1/platform/subjects", headers=headers_b
                ).json()["data"]["id"]
                assert (
                    client.get(
                        f"/api/v1/platform/subjects/{sub_b}/goals/{gid}",
                        headers=headers_b,
                    ).status_code
                    == 404
                )

                # Invalid kind / empty title / invalid status
                bad_kind = client.post(
                    f"/api/v1/platform/subjects/{sid}/goals",
                    headers=headers_a,
                    json={"goal_kind": "not_a_kind", "title": "x"},
                )
                assert bad_kind.status_code == 422

                bad_title = client.post(
                    f"/api/v1/platform/subjects/{sid}/goals",
                    headers=headers_a,
                    json={"goal_kind": "career", "title": "   "},
                )
                assert bad_title.status_code == 422

                bad_status = client.post(
                    f"/api/v1/platform/subjects/{sid}/goals",
                    headers=headers_a,
                    json={
                        "goal_kind": "career",
                        "title": "ok",
                        "status": "bogus",
                    },
                )
                assert bad_status.status_code == 422
        finally:
            cache_mod._CACHE_SINGLETON = original_cache
            app.router.lifespan_context = original_lifespan
            app.dependency_overrides.clear()
            asyncio.run(async_engine.dispose())
