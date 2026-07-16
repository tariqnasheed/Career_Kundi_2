"""0053-F15 — badge seed startup reliability (idempotent + bounded)."""

from __future__ import annotations

import ast
import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.data.badges_seed import BADGE_DEFINITIONS
from app.db.migration_runner import foundation_heads, prepare_database
from app.db.models.badges import BadgeDefinition
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.main import (
    BADGE_SEED_STARTUP_TIMEOUT_SECONDS,
    _run_badge_seed_startup,
    create_app,
    lifespan,
)
from app.services.badges import seed_badge_definitions

# Reuse an already-approved disposable prefix (pf1 allow-list); no new DB policy.
F15_PREFIX = "ck_f2svc_"
F0011 = "f0011_attachment_scan_queue"
SERVICES_BADGES = (
    Path(__file__).resolve().parents[3] / "services" / "badges.py"
)
MAIN_PY = Path(__file__).resolve().parents[3] / "main.py"


def _async_url(sync_url: str) -> str:
    if sync_url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + sync_url.removeprefix(
            "postgresql+psycopg2://"
        )
    if sync_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + sync_url.removeprefix("postgresql://")
    return sync_url


def test_migration_head_is_f0011() -> None:
    assert foundation_heads() == [F0011]


def test_app_openapi_builds_without_hang() -> None:
    """OpenAPI schema build must not require lifespan / external services."""
    t0 = time.perf_counter()
    app = create_app()
    schema = app.openapi()
    elapsed = time.perf_counter() - t0
    assert "paths" in schema
    assert "/api/openapi.json" in {app.openapi_url} or app.openapi_url.endswith(
        "openapi.json"
    )
    assert elapsed < 5.0


def test_badge_seed_source_has_no_llm_or_evidence_side_effects() -> None:
    tree = ast.parse(SERVICES_BADGES.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
            imports.add(node.module)
    blob = SERVICES_BADGES.read_text(encoding="utf-8").lower()
    assert "ollama" not in blob
    assert "openai" not in blob
    assert "anthropic" not in blob
    assert "gemini" not in blob
    assert "evidence_files" not in blob
    assert "app.tools.llm" not in imports
    assert "app.platform.evidence" not in imports
    assert "app.platform.verification" not in imports
    assert "app.platform.claims" not in imports


def test_lifespan_bounds_badge_seed_timeout_constant() -> None:
    assert BADGE_SEED_STARTUP_TIMEOUT_SECONDS > 0
    assert BADGE_SEED_STARTUP_TIMEOUT_SECONDS <= 30
    main_src = MAIN_PY.read_text(encoding="utf-8")
    assert "wait_for" in main_src
    assert "_run_badge_seed_startup" in main_src
    assert "badge_seed_startup_timeout" in main_src


def test_lifespan_continues_when_badge_seed_times_out() -> None:
    """Timeout must not prevent lifespan from yielding (OpenAPI readiness)."""

    async def _slow_seed() -> dict[str, int]:
        await asyncio.sleep(60)
        return {"inserted": 0, "updated": 0, "unchanged": 0, "count": 0}

    async def _run() -> None:
        with (
            patch("app.tools.rag.get_vector_store", return_value=object()),
            patch("app.tools.graph_rag.get_knowledge_graph", return_value=object()),
            patch(
                "app.services.role_pack_library.ensure_library_layout",
                return_value=None,
            ),
            patch(
                "app.services.role_pack_library.list_library_roles",
                return_value=["x"],
            ),
            patch("app.main._run_badge_seed_startup", side_effect=_slow_seed),
            patch("app.main.BADGE_SEED_STARTUP_TIMEOUT_SECONDS", 0.05),
        ):
            app = create_app()
            t0 = time.perf_counter()
            async with lifespan(app):
                elapsed = time.perf_counter() - t0
                assert elapsed < 2.0

    asyncio.run(_run())


@require_disposable_postgres
def test_badge_seed_idempotent_and_bounded() -> None:
    with temporary_database(prefix=F15_PREFIX) as (_name, url):
        prepare_database(url)
        assert foundation_heads() == [F0011]

        async def _run() -> None:
            engine = create_async_engine(_async_url(url), pool_pre_ping=True)
            sessions = async_sessionmaker(
                bind=engine, expire_on_commit=False, class_=AsyncSession
            )
            try:
                async with sessions() as db:
                    t0 = time.perf_counter()
                    first = await seed_badge_definitions(db)
                    first_s = time.perf_counter() - t0
                    assert first["count"] == len(BADGE_DEFINITIONS)
                    assert first["inserted"] == len(BADGE_DEFINITIONS)
                    assert first["updated"] == 0
                    assert first_s < 5.0

                async with sessions() as db:
                    count = (
                        await db.execute(select(func.count()).select_from(BadgeDefinition))
                    ).scalar_one()
                    assert count == len(BADGE_DEFINITIONS)

                async with sessions() as db:
                    t0 = time.perf_counter()
                    second = await seed_badge_definitions(db)
                    second_s = time.perf_counter() - t0
                    assert second["inserted"] == 0
                    assert second["updated"] == 0
                    assert second["unchanged"] == len(BADGE_DEFINITIONS)
                    assert second_s < 2.0

                async with sessions() as db:
                    count = (
                        await db.execute(select(func.count()).select_from(BadgeDefinition))
                    ).scalar_one()
                    assert count == len(BADGE_DEFINITIONS)

                # No claim/evidence/review mutation surface from seed
                sync_engine = create_engine(url)
                try:
                    with sync_engine.connect() as conn:
                        for table in (
                            "career_claims",
                            "evidence_records",
                            "claim_evidence_links",
                            "review_requests",
                        ):
                            n = conn.execute(
                                text(f"SELECT COUNT(*) FROM {table}")
                            ).scalar_one()
                            assert n == 0
                finally:
                    sync_engine.dispose()
            finally:
                await engine.dispose()

        asyncio.run(_run())


@require_disposable_postgres
def test_run_badge_seed_startup_helper_uses_session_factory_path() -> None:
    """Smoke that the lifespan helper function is importable and returns a summary."""
    # This test only checks the helper signature against a disposable DB by
    # patching AsyncSessionLocal — avoids touching the primary careerkundi_f4 DB.
    with temporary_database(prefix=F15_PREFIX) as (_name, url):
        prepare_database(url)

        async def _run() -> None:
            engine = create_async_engine(_async_url(url), pool_pre_ping=True)
            sessions = async_sessionmaker(
                bind=engine, expire_on_commit=False, class_=AsyncSession
            )

            class _CM:
                def __init__(self, session: AsyncSession) -> None:
                    self._session = session

                async def __aenter__(self) -> AsyncSession:
                    return self._session

                async def __aexit__(self, *args: object) -> None:
                    await self._session.close()

            async with sessions() as session:
                with patch(
                    "app.db.session.AsyncSessionLocal",
                    return_value=_CM(session),
                ):
                    summary = await _run_badge_seed_startup()
                    assert summary["count"] == len(BADGE_DEFINITIONS)
                    assert summary["inserted"] + summary["unchanged"] + summary[
                        "updated"
                    ] == len(BADGE_DEFINITIONS)

            await engine.dispose()

        asyncio.run(_run())
