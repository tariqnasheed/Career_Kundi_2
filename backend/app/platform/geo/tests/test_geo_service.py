"""Geo migration + service tests (0050-PF6-S1)."""

from __future__ import annotations

import ast
import asyncio
import uuid
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.db.models  # noqa: F401
from app.db.base import Base
from app.db.migration_runner import (
    FOUNDATION_VERSION_TABLE,
    build_foundation_alembic_config,
    foundation_heads,
    prepare_database,
    read_foundation_revisions,
)
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.platform.geo import (
    GeoAreaKind,
    GeoRefError,
    JurisdictionKind,
    LocaleKind,
    WorkAuthorizationAreaKind,
)
from app.platform.geo.service import (
    create_geo_area,
    create_jurisdiction_area,
    create_locale_profile,
    create_work_authorization_area,
    get_geo_area,
    get_jurisdiction_area,
    get_locale_profile,
    get_work_authorization_area,
)

PF6_PREFIX = "ck_pf6s1_"
F0004 = "f0004_claim_foundation"
F0005 = "f0005_geo_jurisdiction_locale"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
    / "f0005_geo_jurisdiction_locale.py"
)
GEO_TABLES = {
    "geo_areas",
    "jurisdiction_areas",
    "locale_profiles",
    "work_authorization_areas",
}
FORBIDDEN_CROSS_DOMAIN = {
    "candidate_work_authorizations",
    "visa_statuses",
    "localized_strings",
    "translations",
    "job_geo_filters",
}


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


@require_disposable_postgres
def test_f0005_migration_empty_to_head() -> None:
    with temporary_database(prefix=PF6_PREFIX) as (_name, url):
        result = prepare_database(url)
        assert result.foundation_revisions == (foundation_heads()[0],)
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert GEO_TABLES.issubset(tables)
            assert not (FORBIDDEN_CROSS_DOMAIN & tables)

            geo_fks = inspect(engine).get_foreign_keys("geo_areas")
            assert any(
                fk["referred_table"] == "geo_areas"
                and fk["constrained_columns"] == ["parent_geo_id"]
                for fk in geo_fks
            )
            jur_fks = inspect(engine).get_foreign_keys("jurisdiction_areas")
            assert any(
                fk["referred_table"] == "jurisdiction_areas"
                and fk["constrained_columns"] == ["parent_jurisdiction_id"]
                for fk in jur_fks
            )
            # No cross-domain FKs on locale / work auth
            assert inspect(engine).get_foreign_keys("locale_profiles") == []
            assert inspect(engine).get_foreign_keys("work_authorization_areas") == []

            assert "ix_geo_areas_geo_kind" in {
                i["name"] for i in inspect(engine).get_indexes("geo_areas")
            }
            assert "ix_geo_areas_code" in {
                i["name"] for i in inspect(engine).get_indexes("geo_areas")
            }
            assert "ix_jurisdiction_areas_jurisdiction_kind" in {
                i["name"] for i in inspect(engine).get_indexes("jurisdiction_areas")
            }
            assert "ix_jurisdiction_areas_code" in {
                i["name"] for i in inspect(engine).get_indexes("jurisdiction_areas")
            }
            assert "ix_locale_profiles_locale_code" in {
                i["name"] for i in inspect(engine).get_indexes("locale_profiles")
            }
            assert "ix_work_authorization_areas_authorization_kind" in {
                i["name"]
                for i in inspect(engine).get_indexes("work_authorization_areas")
            }
            assert "ix_work_authorization_areas_code" in {
                i["name"]
                for i in inspect(engine).get_indexes("work_authorization_areas")
            }
        finally:
            engine.dispose()


@require_disposable_postgres
def test_f0005_downgrade_upgrade() -> None:
    with temporary_database(prefix=PF6_PREFIX) as (_name, url):
        prepare_database(url)
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0004)
            tables = set(inspect(engine).get_table_names())
            assert not (GEO_TABLES & tables)
            assert "career_claims" in tables
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            tables = set(inspect(engine).get_table_names())
            assert GEO_TABLES.issubset(tables)
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (foundation_heads()[0],)
        finally:
            engine.dispose()


@require_disposable_postgres
def test_drift_zero_at_head() -> None:
    with temporary_database(prefix=PF6_PREFIX) as (_name, url):
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


def test_f0005_no_create_all_or_orm_imports() -> None:
    tree = ast.parse(MIGRATION_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"create_all", "drop_all"}
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("app.db.models")
            assert mod != "app.db.base"


@require_disposable_postgres
def test_geo_service_semantics() -> None:
    with temporary_database(prefix=PF6_PREFIX) as (_name, url):
        prepare_database(url)
        async_engine = create_async_engine(_async_url(url), pool_pre_ping=True)
        SessionLocal = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )

        async def _count(db: AsyncSession, table: str) -> int:
            return int(
                (await db.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar_one()
            )

        async def _run() -> None:
            async with SessionLocal() as db:
                india = await create_geo_area(
                    db,
                    geo_kind=GeoAreaKind.COUNTRY,
                    name="  India  ",
                    code=" IN ",
                )
                assert india.name == "India"
                assert india.code == "IN"
                telangana = await create_geo_area(
                    db,
                    geo_kind=GeoAreaKind.REGION,
                    name="Telangana",
                    code="TG",
                    parent_geo_id=india.id,
                )
                hyderabad = await create_geo_area(
                    db,
                    geo_kind=GeoAreaKind.CITY,
                    name="Hyderabad",
                    parent_geo_id=telangana.id,
                )
                assert telangana.parent_geo_id == india.id
                assert hyderabad.parent_geo_id == telangana.id
                assert (await get_geo_area(db, hyderabad.id)) is not None
                assert await _count(db, "jurisdiction_areas") == 0

                uk = await create_jurisdiction_area(
                    db,
                    jurisdiction_kind=JurisdictionKind.COUNTRY,
                    name="United Kingdom",
                    code="GB",
                )
                england = await create_jurisdiction_area(
                    db,
                    jurisdiction_kind=JurisdictionKind.STATE_REGION,
                    name="England",
                    parent_jurisdiction_id=uk.id,
                )
                assert england.parent_jurisdiction_id == uk.id
                assert (await get_jurisdiction_area(db, england.id)) is not None
                # Creating jurisdiction did not create geo rows beyond India hierarchy
                assert await _count(db, "geo_areas") == 3

                locale = await create_locale_profile(
                    db,
                    locale_kind=LocaleKind.LANGUAGE_REGION,
                    locale_code="  en-GB  ",
                    display_name="  English (UK)  ",
                )
                assert locale.locale_code == "en-GB"
                assert locale.display_name == "English (UK)"
                assert not hasattr(locale, "geo_id")
                assert (await get_locale_profile(db, locale.id)) is not None

                auth = await create_work_authorization_area(
                    db,
                    authorization_kind=WorkAuthorizationAreaKind.COUNTRY,
                    name="United Kingdom",
                    code="GB",
                )
                assert not hasattr(auth, "geo_id")
                assert not hasattr(auth, "visa_type")
                assert not hasattr(auth, "status")
                assert not hasattr(auth, "expiry")
                assert (await get_work_authorization_area(db, auth.id)) is not None

                # Schema-level independence (no geo FK / visa status columns)
                sync_engine = create_engine(url)
                try:
                    locale_cols = {
                        c["name"]
                        for c in inspect(sync_engine).get_columns("locale_profiles")
                    }
                    auth_cols = {
                        c["name"]
                        for c in inspect(sync_engine).get_columns(
                            "work_authorization_areas"
                        )
                    }
                finally:
                    sync_engine.dispose()
                assert "geo_id" not in locale_cols
                assert "geo_id" not in auth_cols
                assert "visa_type" not in auth_cols
                assert "status" not in auth_cols
                assert "expiry" not in auth_cols

                before_geo = await _count(db, "geo_areas")
                try:
                    await create_geo_area(
                        db,
                        geo_kind=GeoAreaKind.CITY,
                        name="Orphan",
                        parent_geo_id=uuid.uuid4(),
                    )
                    raise AssertionError("bad geo parent should fail")
                except GeoRefError:
                    pass
                assert await _count(db, "geo_areas") == before_geo

                before_jur = await _count(db, "jurisdiction_areas")
                try:
                    await create_jurisdiction_area(
                        db,
                        jurisdiction_kind=JurisdictionKind.STATE_REGION,
                        name="Orphan",
                        parent_jurisdiction_id=uuid.uuid4(),
                    )
                    raise AssertionError("bad jurisdiction parent should fail")
                except GeoRefError:
                    pass
                assert await _count(db, "jurisdiction_areas") == before_jur

        try:
            asyncio.run(_run())
        finally:
            asyncio.run(async_engine.dispose())
