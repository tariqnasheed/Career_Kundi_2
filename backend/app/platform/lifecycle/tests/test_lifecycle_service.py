"""Lifecycle migration + service tests (0050-PF7-S1)."""

from __future__ import annotations

import ast
import asyncio
import inspect as pyinspect
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401
from app.core.security import hash_password
from app.db.base import Base
from app.db.migration_runner import (
    FOUNDATION_VERSION_TABLE,
    build_foundation_alembic_config,
    foundation_heads,
    prepare_database,
    read_foundation_revisions,
)
from app.db.models.career_subject import CareerSubject
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.platform.lifecycle import (
    AttemptKind,
    FeedbackKind,
    GoalKind,
    LifecycleRefError,
    LifecycleStatus,
    OutcomeKind,
    RecommendationKind,
)
from app.platform.lifecycle import service as lifecycle_service
from app.platform.lifecycle.service import (
    create_attempt,
    create_feedback,
    create_goal,
    create_outcome,
    create_recommendation,
    list_subject_attempts,
    list_subject_feedback,
    list_subject_goals,
    list_subject_outcomes,
    list_subject_recommendations,
)
from app.platform.provenance import SourceKind
from app.platform.provenance.service import create_snapshot, create_source

PF7_PREFIX = "ck_pf7s1_"
F0005 = "f0005_geo_jurisdiction_locale"
F0006 = "f0006_lifecycle_loop_foundation"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
    / "f0006_lifecycle_loop_foundation.py"
)
LIFECYCLE_TABLES = {
    "career_goals",
    "career_recommendations",
    "career_attempts",
    "career_outcomes",
    "career_feedback",
}
FORBIDDEN_WORKFLOW_TABLES = {
    "workflow_runs",
    "scheduled_tasks",
    "agent_plans",
    "recommendation_scores",
    "job_matches",
    "application_automations",
}
FORBIDDEN_FN_NAMES = {
    "run_workflow",
    "execute_workflow",
    "schedule_task",
    "enqueue_task",
    "agent_plan",
    "auto_apply",
}


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str) -> uuid.UUID:
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    uid = uuid.uuid4()
    try:
        with Session() as session:
            session.add(
                User(
                    id=uid,
                    email=f"pf7-{uid.hex[:8]}@example.com",
                    hashed_password=hash_password("test-password-ok"),
                    full_name="PF7 User",
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
def test_f0006_migration_empty_to_head() -> None:
    with temporary_database(prefix=PF7_PREFIX) as (_name, url):
        result = prepare_database(url)
        assert result.foundation_revisions == (foundation_heads()[0],)
        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert LIFECYCLE_TABLES.issubset(tables)
            assert not (FORBIDDEN_WORKFLOW_TABLES & tables)
            goal_fks = {
                fk["referred_table"]
                for fk in inspect(engine).get_foreign_keys("career_goals")
            }
            assert "career_subjects" in goal_fks
            assert "ix_career_goals_subject_id" in {
                i["name"] for i in inspect(engine).get_indexes("career_goals")
            }
            assert "ix_career_recommendations_subject_id" in {
                i["name"]
                for i in inspect(engine).get_indexes("career_recommendations")
            }
            assert "ix_career_attempts_subject_id" in {
                i["name"] for i in inspect(engine).get_indexes("career_attempts")
            }
            assert "ix_career_outcomes_subject_id" in {
                i["name"] for i in inspect(engine).get_indexes("career_outcomes")
            }
            assert "ix_career_feedback_subject_id" in {
                i["name"] for i in inspect(engine).get_indexes("career_feedback")
            }
        finally:
            engine.dispose()


@require_disposable_postgres
def test_f0006_downgrade_upgrade() -> None:
    with temporary_database(prefix=PF7_PREFIX) as (_name, url):
        prepare_database(url)
        cfg = build_foundation_alembic_config()
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.downgrade(cfg, F0005)
            tables = set(inspect(engine).get_table_names())
            assert not (LIFECYCLE_TABLES & tables)
            assert "geo_areas" in tables
            with engine.begin() as conn:
                cfg.attributes["connection"] = conn
                command.upgrade(cfg, "head")
            assert LIFECYCLE_TABLES.issubset(set(inspect(engine).get_table_names()))
            with engine.connect() as conn:
                assert read_foundation_revisions(conn) == (foundation_heads()[0],)
        finally:
            engine.dispose()


@require_disposable_postgres
def test_drift_zero_at_head() -> None:
    with temporary_database(prefix=PF7_PREFIX) as (_name, url):
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


def test_f0006_no_create_all_or_orm_imports() -> None:
    tree = ast.parse(MIGRATION_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"create_all", "drop_all"}
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("app.db.models")
            assert mod != "app.db.base"


def test_no_workflow_behavior_in_lifecycle_package() -> None:
    names = {
        name
        for name, obj in pyinspect.getmembers(lifecycle_service)
        if pyinspect.isfunction(obj) or pyinspect.isclass(obj)
    }
    assert not (FORBIDDEN_FN_NAMES & names)
    pkg = Path(__file__).resolve().parents[1]
    for path in pkg.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text_src = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_FN_NAMES:
            assert f"def {forbidden}" not in text_src
            assert f"class {forbidden}" not in text_src
            assert f"class {forbidden.title().replace('_', '')}" not in text_src


@require_disposable_postgres
def test_lifecycle_service_semantics() -> None:
    with temporary_database(prefix=PF7_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
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
                subject_a = CareerSubject(owner_user_id=user_id)
                subject_b = CareerSubject(owner_user_id=user_id)
                db.add_all([subject_a, subject_b])
                await db.commit()
                await db.refresh(subject_a)
                await db.refresh(subject_b)

                goal = await create_goal(
                    db,
                    subject_id=subject_a.id,
                    goal_kind=GoalKind.JOB_SEARCH,
                    title="  Land backend role  ",
                    status=LifecycleStatus.ACTIVE,
                )
                assert goal.title == "Land backend role"
                rec = await create_recommendation(
                    db,
                    subject_id=subject_a.id,
                    goal_id=goal.id,
                    recommendation_kind=RecommendationKind.JOB,
                    title="Apply to Acme",
                    status=LifecycleStatus.ACTIVE,
                )
                started = datetime.now(UTC)
                attempt = await create_attempt(
                    db,
                    subject_id=subject_a.id,
                    goal_id=goal.id,
                    recommendation_id=rec.id,
                    attempt_kind=AttemptKind.APPLICATION,
                    title="Submitted Acme application",
                    status=LifecycleStatus.COMPLETED,
                    started_at=started,
                    completed_at=started + timedelta(hours=1),
                )
                outcome = await create_outcome(
                    db,
                    subject_id=subject_a.id,
                    attempt_id=attempt.id,
                    outcome_kind=OutcomeKind.PENDING,
                    title="Awaiting response",
                )
                feedback = await create_feedback(
                    db,
                    subject_id=subject_a.id,
                    outcome_id=outcome.id,
                    feedback_kind=FeedbackKind.USER_FEEDBACK,
                    message="Felt good about the application",
                )
                assert rec.goal_id == goal.id
                assert attempt.recommendation_id == rec.id
                assert outcome.attempt_id == attempt.id
                assert feedback.outcome_id == outcome.id
                assert {
                    goal.subject_id,
                    rec.subject_id,
                    attempt.subject_id,
                    outcome.subject_id,
                    feedback.subject_id,
                } == {subject_a.id}

                before = await _count(db, "career_attempts")
                try:
                    await create_attempt(
                        db,
                        subject_id=subject_b.id,
                        recommendation_id=rec.id,
                        attempt_kind=AttemptKind.APPLICATION,
                        title="Cross subject",
                        status=LifecycleStatus.ACTIVE,
                    )
                    raise AssertionError("cross-subject attempt should fail")
                except LifecycleRefError:
                    pass
                assert await _count(db, "career_attempts") == before

                before_fb = await _count(db, "career_feedback")
                try:
                    await create_feedback(
                        db,
                        subject_id=subject_b.id,
                        outcome_id=outcome.id,
                        feedback_kind=FeedbackKind.USER_FEEDBACK,
                        message="Wrong subject",
                    )
                    raise AssertionError("cross-subject feedback should fail")
                except LifecycleRefError:
                    pass
                assert await _count(db, "career_feedback") == before_fb

                source_a = await create_source(
                    db, source_kind=SourceKind.URL, uri="https://a.example"
                )
                source_b = await create_source(
                    db, source_kind=SourceKind.URL, uri="https://b.example"
                )
                snap_b = await create_snapshot(db, source_id=source_b.id)
                before_rec = await _count(db, "career_recommendations")
                try:
                    await create_recommendation(
                        db,
                        subject_id=subject_a.id,
                        recommendation_kind=RecommendationKind.COURSE,
                        title="Mismatch",
                        status=LifecycleStatus.ACTIVE,
                        source_id=source_a.id,
                        snapshot_id=snap_b.id,
                    )
                    raise AssertionError("source/snapshot mismatch should fail")
                except LifecycleRefError:
                    pass
                try:
                    await create_recommendation(
                        db,
                        subject_id=subject_a.id,
                        recommendation_kind=RecommendationKind.COURSE,
                        title="Snap only",
                        status=LifecycleStatus.ACTIVE,
                        snapshot_id=snap_b.id,
                    )
                    raise AssertionError("snapshot without source should fail")
                except LifecycleRefError:
                    pass
                assert await _count(db, "career_recommendations") == before_rec

                try:
                    await create_attempt(
                        db,
                        subject_id=subject_a.id,
                        attempt_kind=AttemptKind.PRACTICE,
                        title="Bad dates",
                        status=LifecycleStatus.ACTIVE,
                        started_at=started,
                        completed_at=started - timedelta(minutes=1),
                    )
                    raise AssertionError("completed_at before started_at should fail")
                except LifecycleRefError:
                    pass

                ok_attempt = await create_attempt(
                    db,
                    subject_id=subject_a.id,
                    attempt_kind=AttemptKind.PRACTICE,
                    title="Good dates",
                    status=LifecycleStatus.COMPLETED,
                    started_at=started,
                    completed_at=started + timedelta(minutes=5),
                )
                assert ok_attempt.completed_at is not None

                goal_b = await create_goal(
                    db,
                    subject_id=subject_b.id,
                    goal_kind=GoalKind.EDUCATION,
                    title="B goal",
                    status=LifecycleStatus.ACTIVE,
                )
                assert {g.id for g in await list_subject_goals(db, subject_a.id)} == {
                    goal.id
                }
                assert {g.id for g in await list_subject_goals(db, subject_b.id)} == {
                    goal_b.id
                }
                assert {
                    r.id for r in await list_subject_recommendations(db, subject_a.id)
                } == {rec.id}
                assert {
                    a.id for a in await list_subject_attempts(db, subject_a.id)
                } == {attempt.id, ok_attempt.id}
                assert {
                    o.id for o in await list_subject_outcomes(db, subject_a.id)
                } == {outcome.id}
                assert {
                    f.id for f in await list_subject_feedback(db, subject_a.id)
                } == {feedback.id}
                assert await list_subject_recommendations(db, subject_b.id) == []
                assert await list_subject_attempts(db, subject_b.id) == []
                assert await list_subject_outcomes(db, subject_b.id) == []
                assert await list_subject_feedback(db, subject_b.id) == []

        try:
            asyncio.run(_run())
        finally:
            asyncio.run(async_engine.dispose())
