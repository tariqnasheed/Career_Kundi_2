"""CareerSubject foundation migration + API ownership tests (0050-PF3-S1)."""

from __future__ import annotations

import ast
import asyncio
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.migration_runner import (
    FOUNDATION_VERSION_TABLE,
    build_foundation_alembic_config,
    foundation_heads,
    prepare_database,
    read_foundation_revisions,
)
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.session import get_db
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.main import app

PF3_PREFIX = "ck_pf3s1_"
F0001 = "f0001_foundation_baseline"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
    / "f0002_identity_subject_stub.py"
)


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


@require_disposable_postgres
def test_f0002_migration_empty_to_head() -> None:
    with temporary_database(prefix=PF3_PREFIX) as (_name, url):
        result = prepare_database(url)
        assert result.foundation_revisions == (foundation_heads()[0],)
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert "career_subjects" in tables
            fks = inspect(engine).get_foreign_keys("career_subjects")
            assert any(fk["referred_table"] == "users" for fk in fks)
            idxs = {i["name"] for i in inspect(engine).get_indexes("career_subjects")}
            assert "ix_career_subjects_owner_user_id" in idxs
            assert not any(
                i.get("unique") for i in inspect(engine).get_indexes("career_subjects")
            )
        finally:
            engine.dispose()


@require_disposable_postgres
def test_f0002_downgrade_upgrade() -> None:
    with temporary_database(prefix=PF3_PREFIX) as (_name, url):
        prepare_database(url)
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0001)
            assert "career_subjects" not in inspect(engine).get_table_names()
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            assert "career_subjects" in inspect(engine).get_table_names()
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (foundation_heads()[0],)
        finally:
            engine.dispose()


@require_disposable_postgres
def test_drift_zero_at_head() -> None:
    with temporary_database(prefix=PF3_PREFIX) as (_name, url):
        prepare_database(url)
        engine = create_engine(url)

        def _include_object(object, name, type_, reflected, compare_to):
            if type_ == "table" and name == FOUNDATION_VERSION_TABLE:
                return False
            return True

        try:
            with engine.connect() as conn:
                mc = MigrationContext.configure(
                    conn,
                    opts={
                        "version_table": FOUNDATION_VERSION_TABLE,
                        "version_table_schema": "public",
                        "include_object": _include_object,
                    },
                )
                diffs = compare_metadata(mc, Base.metadata)
            assert diffs == [], diffs
        finally:
            engine.dispose()


def test_f0002_no_create_all_or_orm_imports() -> None:
    tree = ast.parse(MIGRATION_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"create_all", "drop_all"}
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("app.db.models")
            assert mod != "app.db.base"


def _insert_user(sync_url: str, email: str) -> uuid.UUID:
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    uid = uuid.uuid4()
    try:
        with Session() as session:
            user = User(
                id=uid,
                email=email,
                hashed_password=hash_password("test-password-ok"),
                full_name="Test User",
                role=UserRole.USER,
                plan=SubscriptionPlan.FREE,
                is_active=True,
                is_email_verified=False,
            )
            session.add(user)
            session.commit()
    finally:
        engine.dispose()
    return uid


@require_disposable_postgres
def test_api_auth_create_read_isolation_multi_subject() -> None:
    with temporary_database(prefix=PF3_PREFIX) as (_name, url):
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
        # Bypass app lifespan so badge seeding never touches the primary legacy DB.
        from contextlib import asynccontextmanager

        from app.tools import cache as cache_mod
        from app.tools.cache import InMemoryCache

        @asynccontextmanager
        async def _empty_lifespan(_app):
            yield

        original_lifespan = app.router.lifespan_context
        app.router.lifespan_context = _empty_lifespan
        # Avoid Redis client bound to a closed TestClient event loop across requests.
        original_cache = cache_mod._CACHE_SINGLETON
        cache_mod._CACHE_SINGLETON = InMemoryCache()
        try:
            with TestClient(app) as client:
                assert client.post("/api/v1/platform/subjects").status_code == 401
                assert (
                    client.get(f"/api/v1/platform/subjects/{uuid.uuid4()}").status_code
                    == 401
                )

                headers_a = {
                    "Authorization": f"Bearer {create_access_token(str(user_a))}"
                }
                headers_b = {
                    "Authorization": f"Bearer {create_access_token(str(user_b))}"
                }

                r1 = client.post("/api/v1/platform/subjects", headers=headers_a)
                assert r1.status_code == 201, r1.text
                body1 = r1.json()
                assert "data" in body1
                data1 = body1["data"]
                assert data1["owner_user_id"] == str(user_a)
                assert set(data1.keys()) == {
                    "id",
                    "owner_user_id",
                    "created_at",
                    "updated_at",
                }
                assert "email" not in data1
                assert "full_name" not in data1
                assert "skills" not in data1

                sid = data1["id"]
                r_get = client.get(
                    f"/api/v1/platform/subjects/{sid}", headers=headers_a
                )
                assert r_get.status_code == 200
                assert r_get.json()["data"]["id"] == sid

                r_other = client.get(
                    f"/api/v1/platform/subjects/{sid}", headers=headers_b
                )
                assert r_other.status_code == 404

                r2 = client.post("/api/v1/platform/subjects", headers=headers_a)
                assert r2.status_code == 201
                assert r2.json()["data"]["id"] != sid
                assert r2.json()["data"]["owner_user_id"] == str(user_a)

                r_list = client.get("/api/v1/platform/subjects", headers=headers_a)
                assert r_list.status_code == 200
                listed = r_list.json()
                assert listed["meta"]["count"] == 2
                assert {row["id"] for row in listed["data"]} == {
                    sid,
                    r2.json()["data"]["id"],
                }
                r_list_b = client.get("/api/v1/platform/subjects", headers=headers_b)
                assert r_list_b.status_code == 200
                assert r_list_b.json()["meta"]["count"] == 0
                assert r_list_b.json()["data"] == []

                engine = create_engine(url)
                try:
                    cols = {
                        c["name"]
                        for c in inspect(engine).get_columns("career_subjects")
                    }
                    assert cols == {"id", "owner_user_id", "created_at", "updated_at"}
                finally:
                    engine.dispose()
        finally:
            cache_mod._CACHE_SINGLETON = original_cache
            app.router.lifespan_context = original_lifespan
            app.dependency_overrides.clear()
            asyncio.run(async_engine.dispose())
