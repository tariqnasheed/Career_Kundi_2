"""Passport API MVP integration tests (0052-F3)."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, hash_password
from app.db.migration_runner import prepare_database
from app.db.models.profile import Profile, WorkExperience
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.session import get_db
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.main import app
from app.schemas.passport import (
    PassportApiModel,
    PassportEnvelope,
    PassportExperienceCreate,
    PassportPatch,
    PassportProfilePatch,
    PassportReorder,
)
from app.tools import cache as cache_mod
from app.tools.cache import InMemoryCache

F3_PREFIX = "ck_0052f3_"

FORBIDDEN_BODY_KEYS = (
    "owner_user_id",
    "profile_id",
    "record_meta",
    "passport_record_meta",
    "verification_status",
    "support_status",
    "public_url",
    "organization_id",
    "claims",
    "evidence",
)

DEFAULT_SECTION_PREFS = [
    {"section": "profile", "order_index": 0, "enabled": True},
    {"section": "experience", "order_index": 1, "enabled": True},
    {"section": "education", "order_index": 2, "enabled": True},
    {"section": "projects", "order_index": 3, "enabled": True},
    {"section": "skills", "order_index": 4, "enabled": True},
    {"section": "credentials", "order_index": 5, "enabled": True},
    {"section": "targets", "order_index": 6, "enabled": True},
]


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str, email: str, *, with_profile: bool = True) -> uuid.UUID:
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
                    full_name="Passport User",
                    role=UserRole.USER,
                    plan=SubscriptionPlan.FREE,
                    is_active=True,
                    is_email_verified=False,
                )
            )
            session.commit()
            if with_profile:
                session.add(Profile(user_id=uid))
                session.commit()
    finally:
        engine.dispose()
    return uid


def _auth(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def _passport_operations() -> set[tuple[str, str]]:
    """Collect Passport operations via OpenAPI (FastAPI nests IncludedRouter)."""
    schema = app.openapi()
    ops: set[tuple[str, str]] = set()
    for path, methods in schema["paths"].items():
        if not path.startswith("/api/v1/passport"):
            continue
        for method in methods:
            if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                ops.add((method.upper(), path))
    return ops


def test_passport_route_surface_and_schema_guards() -> None:
    ops = _passport_operations()
    assert len(ops) == 27, sorted(ops)
    assert ("GET", "/api/v1/passport") in ops
    assert ("PATCH", "/api/v1/passport") in ops
    assert ("PATCH", "/api/v1/passport/profile") in ops
    assert ("POST", "/api/v1/passport") not in ops
    assert not any(method == "GET" and "{entry_id}" in path for method, path in ops)
    assert not any(method == "GET" and path.count("/") > 3 for method, path in ops)

    forbidden = (
        "/public",
        "/share",
        "/organizations",
        "/evidence",
        "/claims",
        "/verify",
        "/upload",
        "/export",
    )
    for path in app.openapi()["paths"]:
        if not path.startswith("/api/v1/passport"):
            continue
        for needle in forbidden:
            assert needle not in path

    assert PassportApiModel.model_config.get("extra") == "forbid"
    for cls in (
        PassportPatch,
        PassportProfilePatch,
        PassportExperienceCreate,
        PassportReorder,
        PassportEnvelope,
    ):
        assert cls.model_config.get("extra") == "forbid"

    for field in ("owner_user_id", "profile_id", "user_id", "passport_id"):
        assert field not in PassportPatch.model_fields
        assert field not in PassportExperienceCreate.model_fields

    for cls in (
        PassportExperienceCreate,
        PassportPatch,
        PassportProfilePatch,
        PassportReorder,
    ):
        assert "record_meta" not in cls.model_fields
        assert "passport_record_meta" not in cls.model_fields
        assert "verification_status" not in cls.model_fields

    assert "hashed_password" not in PassportEnvelope.model_fields
    assert "email" not in PassportEnvelope.model_fields

    passport_routers = [
        r
        for r in app.routes
        if type(r).__name__ == "_IncludedRouter"
        and any(
            "/passport" in getattr(x, "path", "")
            for x in r.original_router.routes
        )
    ]
    assert len(passport_routers) == 1


@require_disposable_postgres
def test_passport_api_mvp_journey() -> None:
    with temporary_database(prefix=F3_PREFIX) as (_name, url):
        prepare_database(url)
        user_a = _insert_user(url, f"a-{uuid.uuid4().hex[:8]}@example.com", with_profile=False)
        user_b = _insert_user(url, f"b-{uuid.uuid4().hex[:8]}@example.com", with_profile=True)

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

        sync_engine = create_engine(url)
        SyncSession = sessionmaker(bind=sync_engine)

        try:
            with TestClient(app) as client:
                headers_a = _auth(user_a)
                headers_b = _auth(user_b)

                # A. Auth boundary — representative methods
                assert client.get("/api/v1/passport").status_code == 401
                assert client.patch("/api/v1/passport", json={"expected_version": 1}).status_code == 401
                assert (
                    client.post(
                        "/api/v1/passport/experiences",
                        json={
                            "expected_version": 1,
                            "job_title": "x",
                            "company_name": "y",
                        },
                    ).status_code
                    == 401
                )
                assert (
                    client.put(
                        "/api/v1/passport/experiences/reorder",
                        json={"expected_version": 1, "ordered_ids": []},
                    ).status_code
                    == 401
                )
                assert (
                    client.delete(
                        f"/api/v1/passport/experiences/{uuid.uuid4()}",
                        params={"expected_version": 1},
                    ).status_code
                    == 401
                )

                # B. Lazy creation
                r1 = client.get("/api/v1/passport", headers=headers_a)
                assert r1.status_code == 200, r1.text
                body1 = r1.json()
                assert set(body1.keys()) == {"data"}
                data1 = body1["data"]
                passport_id = data1["id"]
                assert data1["version"] == 1
                assert data1["visibility"] == "private"
                assert data1["subject_id"] is None
                assert data1["targets"] == []
                assert data1["experiences"] == []
                assert data1["education"] == []
                assert data1["projects"] == []
                assert data1["skills"] == []
                assert data1["credentials"] == []
                assert data1["display_name"] == "Passport User"

                # C. Output filtering
                dumped = json.dumps(body1)
                for forbidden in (
                    "owner_user_id",
                    "profile_id",
                    "hashed_password",
                    "personal_api_key_encrypted",
                    "email",
                ):
                    assert forbidden not in dumped

                with SyncSession() as session:
                    profiles = session.execute(
                        text("SELECT COUNT(*) FROM profiles WHERE user_id = :u"),
                        {"u": str(user_a)},
                    ).scalar()
                    passports = session.execute(
                        text("SELECT COUNT(*) FROM career_passports WHERE owner_user_id = :u"),
                        {"u": str(user_a)},
                    ).scalar()
                    subjects = session.execute(
                        text("SELECT COUNT(*) FROM career_subjects WHERE owner_user_id = :u"),
                        {"u": str(user_a)},
                    ).scalar()
                    targets = session.execute(
                        text(
                            "SELECT COUNT(*) FROM passport_targets t "
                            "JOIN career_passports p ON p.id = t.passport_id "
                            "WHERE p.owner_user_id = :u"
                        ),
                        {"u": str(user_a)},
                    ).scalar()
                    assert profiles == 1
                    assert passports == 1
                    assert subjects == 0
                    assert targets == 0

                r2 = client.get("/api/v1/passport", headers=headers_a)
                assert r2.status_code == 200
                data2 = r2.json()["data"]
                assert data2["id"] == passport_id
                assert data2["version"] == 1

                with SyncSession() as session:
                    assert (
                        session.execute(
                            text("SELECT COUNT(*) FROM profiles WHERE user_id = :u"),
                            {"u": str(user_a)},
                        ).scalar()
                        == 1
                    )
                    assert (
                        session.execute(
                            text("SELECT COUNT(*) FROM career_passports WHERE owner_user_id = :u"),
                            {"u": str(user_a)},
                        ).scalar()
                        == 1
                    )

                # D. Existing Profile read compatibility (user B has profile + legacy row)
                with SyncSession() as session:
                    profile_b = session.execute(
                        select(Profile).where(Profile.user_id == user_b)
                    ).scalar_one()
                    session.add(
                        WorkExperience(
                            profile_id=profile_b.id,
                            job_title="Legacy Engineer",
                            company_name="Legacy Co",
                            order_index=0,
                        )
                    )
                    session.commit()

                pb = client.get("/api/v1/passport", headers=headers_b).json()["data"]
                assert len(pb["experiences"]) == 1
                assert pb["experiences"][0]["job_title"] == "Legacy Engineer"
                assert pb["experiences"][0]["record_meta"]["support_status"] == "profile_supported"
                assert pb["experiences"][0]["record_meta"]["verification_status"] == "unverified"
                version_b = pb["version"]

                # E. Profile shared-row behavior
                version = data2["version"]
                patch_prof = client.patch(
                    "/api/v1/passport/profile",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "professional_headline": "Passport Headline",
                        "bio_summary": "Passport summary text",
                        "phone": "+10000000001",
                    },
                )
                assert patch_prof.status_code == 200, patch_prof.text
                version = patch_prof.json()["data"]["version"]
                assert version == 2
                assert patch_prof.json()["data"]["headline"] == "Passport Headline"
                assert patch_prof.json()["data"]["summary"] == "Passport summary text"

                profile_get = client.get("/api/v1/profile", headers=headers_a)
                assert profile_get.status_code == 200
                assert profile_get.json()["professional_headline"] == "Passport Headline"
                assert profile_get.json()["bio_summary"] == "Passport summary text"
                assert profile_get.json()["phone"] == "+10000000001"

                profile_put = client.patch(
                    "/api/v1/profile",
                    headers=headers_a,
                    json={"address_city": "Austin"},
                )
                assert profile_put.status_code == 200
                again = client.get("/api/v1/passport", headers=headers_a).json()["data"]
                assert again["profile"]["address_city"] == "Austin"
                assert again["version"] == version  # Profile API does not bump Passport version

                with SyncSession() as session:
                    assert (
                        session.execute(
                            text("SELECT COUNT(*) FROM profiles WHERE user_id = :u"),
                            {"u": str(user_a)},
                        ).scalar()
                        == 1
                    )

                # F. Experience CRUD
                role_tax = {
                    "kind": "role",
                    "input_text": "Software Engineer",
                    "source": "unknown",
                    "confidence": "unknown",
                    "accepted_by_user": False,
                }
                exp = client.post(
                    "/api/v1/passport/experiences",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "job_title": "Backend Engineer",
                        "company_name": "Acme",
                        "is_current": True,
                        "order_index": 0,
                        "role_taxonomy": role_tax,
                    },
                )
                assert exp.status_code == 201, exp.text
                version = exp.json()["data"]["version"]
                exp_id = exp.json()["data"]["experiences"][0]["id"]
                assert exp.json()["data"]["experiences"][0]["job_title"] == "Backend Engineer"
                assert exp.json()["data"]["experiences"][0]["role_taxonomy"]["input_text"] == (
                    "Software Engineer"
                )
                assert (
                    exp.json()["data"]["experiences"][0]["record_meta"]["verification_status"]
                    == "unverified"
                )

                # current + end_date invalid
                bad_dates = client.post(
                    "/api/v1/passport/experiences",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "job_title": "X",
                        "company_name": "Y",
                        "is_current": True,
                        "end_date": "2020-01-01",
                    },
                )
                assert bad_dates.status_code == 422

                exp2 = client.post(
                    "/api/v1/passport/experiences",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "job_title": "Intern",
                        "company_name": "Acme",
                        "order_index": 1,
                    },
                )
                assert exp2.status_code == 201
                version = exp2.json()["data"]["version"]
                exp_id_2 = [
                    e["id"]
                    for e in exp2.json()["data"]["experiences"]
                    if e["job_title"] == "Intern"
                ][0]

                upd = client.patch(
                    f"/api/v1/passport/experiences/{exp_id}",
                    headers=headers_a,
                    json={"expected_version": version, "location": "Remote"},
                )
                assert upd.status_code == 200
                version = upd.json()["data"]["version"]
                assert any(
                    e["id"] == exp_id and e["location"] == "Remote"
                    for e in upd.json()["data"]["experiences"]
                )

                reo = client.put(
                    "/api/v1/passport/experiences/reorder",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "ordered_ids": [exp_id_2, exp_id],
                    },
                )
                assert reo.status_code == 200, reo.text
                version = reo.json()["data"]["version"]
                ordered = [e["id"] for e in reo.json()["data"]["experiences"]]
                assert ordered == [exp_id_2, exp_id]

                # Profile API can read the row
                prof_exp = client.get("/api/v1/profile", headers=headers_a).json()
                titles = {e["job_title"] for e in prof_exp["work_experiences"]}
                assert "Backend Engineer" in titles

                # Cross-user 404
                assert (
                    client.patch(
                        f"/api/v1/passport/experiences/{exp_id}",
                        headers=headers_b,
                        json={"expected_version": version_b, "location": "Nope"},
                    ).status_code
                    == 404
                )

                deleted = client.delete(
                    f"/api/v1/passport/experiences/{exp_id_2}",
                    headers=headers_a,
                    params={"expected_version": version},
                )
                assert deleted.status_code == 200
                version = deleted.json()["data"]["version"]
                assert all(e["id"] != exp_id_2 for e in deleted.json()["data"]["experiences"])

                # G. Education CRUD
                edu = client.post(
                    "/api/v1/passport/education",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "degree": "BSc",
                        "institution": "State U",
                        "start_date": "2015-01-01",
                        "end_date": "2019-01-01",
                    },
                )
                assert edu.status_code == 201, edu.text
                version = edu.json()["data"]["version"]
                edu_id = edu.json()["data"]["education"][0]["id"]

                bad_edu = client.post(
                    "/api/v1/passport/education",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "degree": "MSc",
                        "institution": "State U",
                        "start_date": "2020-01-01",
                        "end_date": "2019-01-01",
                    },
                )
                assert bad_edu.status_code == 422

                edu_upd = client.patch(
                    f"/api/v1/passport/education/{edu_id}",
                    headers=headers_a,
                    json={"expected_version": version, "grade": "First"},
                )
                assert edu_upd.status_code == 200
                version = edu_upd.json()["data"]["version"]

                edu2 = client.post(
                    "/api/v1/passport/education",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "degree": "A-Levels",
                        "institution": "High School",
                    },
                )
                assert edu2.status_code == 201
                version = edu2.json()["data"]["version"]
                edu_ids = [e["id"] for e in edu2.json()["data"]["education"]]
                assert (
                    client.put(
                        "/api/v1/passport/education/reorder",
                        headers=headers_a,
                        json={"expected_version": version, "ordered_ids": list(reversed(edu_ids))},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.delete(
                        f"/api/v1/passport/education/{edu_ids[-1]}",
                        headers=headers_a,
                        params={"expected_version": version},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.patch(
                        f"/api/v1/passport/education/{edu_id}",
                        headers=headers_b,
                        json={"expected_version": 1, "grade": "x"},
                    ).status_code
                    == 404
                )

                # H. Project CRUD
                skill_tax = [
                    {
                        "kind": "skill",
                        "input_text": "Python",
                        "source": "unknown",
                        "confidence": "unknown",
                        "accepted_by_user": False,
                    }
                ]
                proj = client.post(
                    "/api/v1/passport/projects",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "title": "CareerKundi",
                        "technologies": ["Python", "FastAPI"],
                        "skill_taxonomy": skill_tax,
                    },
                )
                assert proj.status_code == 201, proj.text
                version = proj.json()["data"]["version"]
                proj_id = proj.json()["data"]["projects"][0]["id"]
                assert proj.json()["data"]["projects"][0]["technologies"] == [
                    "Python",
                    "FastAPI",
                ]
                assert len(proj.json()["data"]["projects"][0]["skill_taxonomy"]) == 1

                assert (
                    client.patch(
                        f"/api/v1/passport/projects/{proj_id}",
                        headers=headers_a,
                        json={"expected_version": version, "role": "Lead"},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                proj2 = client.post(
                    "/api/v1/passport/projects",
                    headers=headers_a,
                    json={"expected_version": version, "title": "Side"},
                )
                assert proj2.status_code == 201
                version = proj2.json()["data"]["version"]
                pids = [p["id"] for p in proj2.json()["data"]["projects"]]
                assert (
                    client.put(
                        "/api/v1/passport/projects/reorder",
                        headers=headers_a,
                        json={"expected_version": version, "ordered_ids": list(reversed(pids))},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.delete(
                        f"/api/v1/passport/projects/{pids[-1]}",
                        headers=headers_a,
                        params={"expected_version": version},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.delete(
                        f"/api/v1/passport/projects/{proj_id}",
                        headers=headers_b,
                        params={"expected_version": 1},
                    ).status_code
                    == 404
                )

                # I. Skill CRUD
                sk = client.post(
                    "/api/v1/passport/skills",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "name": "Python",
                        "taxonomy": {
                            "kind": "skill",
                            "input_text": "Python",
                            "source": "unknown",
                            "confidence": "unknown",
                            "accepted_by_user": False,
                        },
                    },
                )
                assert sk.status_code == 201, sk.text
                version = sk.json()["data"]["version"]
                skill_id = sk.json()["data"]["skills"][0]["id"]
                assert sk.json()["data"]["skills"][0]["name"] == "Python"
                assert (
                    sk.json()["data"]["skills"][0]["record_meta"]["verification_status"]
                    == "unverified"
                )
                assert (
                    client.patch(
                        f"/api/v1/passport/skills/{skill_id}",
                        headers=headers_a,
                        json={"expected_version": version, "proficiency": "Expert"},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                sk2 = client.post(
                    "/api/v1/passport/skills",
                    headers=headers_a,
                    json={"expected_version": version, "name": "SQL"},
                )
                assert sk2.status_code == 201
                version = sk2.json()["data"]["version"]
                sids = [s["id"] for s in sk2.json()["data"]["skills"]]
                assert (
                    client.put(
                        "/api/v1/passport/skills/reorder",
                        headers=headers_a,
                        json={"expected_version": version, "ordered_ids": list(reversed(sids))},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.delete(
                        f"/api/v1/passport/skills/{sids[-1]}",
                        headers=headers_a,
                        params={"expected_version": version},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.patch(
                        f"/api/v1/passport/skills/{skill_id}",
                        headers=headers_b,
                        json={"expected_version": 1, "name": "x"},
                    ).status_code
                    == 404
                )

                # J. Credential CRUD
                cred = client.post(
                    "/api/v1/passport/credentials",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "credential_type": "certification",
                        "name": "AWS SAA",
                        "issuing_organization": "Amazon",
                        "credential_url": "https://example.com/cert",
                        "credential_id": "ABC-123",
                        "issue_date": "2022-01-01",
                        "expiry_date": "2025-01-01",
                    },
                )
                assert cred.status_code == 201, cred.text
                version = cred.json()["data"]["version"]
                cred_id = cred.json()["data"]["credentials"][0]["id"]
                assert (
                    cred.json()["data"]["credentials"][0]["record_meta"]["verification_status"]
                    == "unverified"
                )
                assert cred.json()["data"]["credentials"][0]["credential_type"] == "certification"

                bad_cred = client.post(
                    "/api/v1/passport/credentials",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "name": "X",
                        "issuing_organization": "Y",
                        "issue_date": "2024-01-01",
                        "expiry_date": "2020-01-01",
                    },
                )
                assert bad_cred.status_code == 422

                assert (
                    client.patch(
                        f"/api/v1/passport/credentials/{cred_id}",
                        headers=headers_a,
                        json={"expected_version": version, "name": "AWS SAA Renewed"},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                cred2 = client.post(
                    "/api/v1/passport/credentials",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "name": "Other",
                        "issuing_organization": "Org",
                    },
                )
                assert cred2.status_code == 201
                version = cred2.json()["data"]["version"]
                cids = [c["id"] for c in cred2.json()["data"]["credentials"]]
                other_id = [
                    c["id"]
                    for c in cred2.json()["data"]["credentials"]
                    if c["name"] == "Other"
                ][0]
                assert (
                    client.put(
                        "/api/v1/passport/credentials/reorder",
                        headers=headers_a,
                        json={"expected_version": version, "ordered_ids": list(reversed(cids))},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.delete(
                        f"/api/v1/passport/credentials/{other_id}",
                        headers=headers_a,
                        params={"expected_version": version},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.delete(
                        f"/api/v1/passport/credentials/{cred_id}",
                        headers=headers_b,
                        params={"expected_version": 1},
                    ).status_code
                    == 404
                )
                # Profile certs compatibility — shared Certification row
                profile_certs = client.get("/api/v1/profile", headers=headers_a).json()[
                    "certifications"
                ]
                assert any(c["name"] == "AWS SAA Renewed" for c in profile_certs)

                # K. Target CRUD
                tgt = client.post(
                    "/api/v1/passport/targets",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "target_role_text": "Staff Engineer",
                        "role_taxonomy": {
                            "kind": "role",
                            "input_text": "Staff Engineer",
                            "source": "unknown",
                            "confidence": "unknown",
                            "accepted_by_user": False,
                        },
                        "priority": 2,
                    },
                )
                assert tgt.status_code == 201, tgt.text
                version = tgt.json()["data"]["version"]
                tgt_id = tgt.json()["data"]["targets"][0]["id"]
                assert (
                    tgt.json()["data"]["targets"][0]["record_meta"]["support_status"]
                    == "not_provided"
                )
                assert (
                    tgt.json()["data"]["targets"][0]["record_meta"]["verification_status"]
                    == "unverified"
                )

                with SyncSession() as session:
                    goals = session.execute(text("SELECT COUNT(*) FROM career_goals")).scalar()
                    assert goals == 0

                assert (
                    client.patch(
                        f"/api/v1/passport/targets/{tgt_id}",
                        headers=headers_a,
                        json={"expected_version": version, "priority": 1},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                tgt2 = client.post(
                    "/api/v1/passport/targets",
                    headers=headers_a,
                    json={"expected_version": version, "target_role_text": "EM"},
                )
                assert tgt2.status_code == 201
                version = tgt2.json()["data"]["version"]
                tids = [t["id"] for t in tgt2.json()["data"]["targets"]]
                assert (
                    client.put(
                        "/api/v1/passport/targets/reorder",
                        headers=headers_a,
                        json={"expected_version": version, "ordered_ids": list(reversed(tids))},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.delete(
                        f"/api/v1/passport/targets/{tids[-1]}",
                        headers=headers_a,
                        params={"expected_version": version},
                    ).status_code
                    == 200
                )
                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]
                assert (
                    client.patch(
                        f"/api/v1/passport/targets/{tgt_id}",
                        headers=headers_b,
                        json={"expected_version": 1, "priority": 5},
                    ).status_code
                    == 404
                )

                # L. Subject linkage
                sub = client.post("/api/v1/platform/subjects", headers=headers_a)
                assert sub.status_code == 201, sub.text
                subject_id = sub.json()["data"]["id"]

                link = client.patch(
                    "/api/v1/passport",
                    headers=headers_a,
                    json={"expected_version": version, "subject_id": subject_id},
                )
                assert link.status_code == 200, link.text
                version = link.json()["data"]["version"]
                assert link.json()["data"]["subject_id"] == subject_id

                clear = client.patch(
                    "/api/v1/passport",
                    headers=headers_a,
                    json={"expected_version": version, "subject_id": None},
                )
                assert clear.status_code == 200
                version = clear.json()["data"]["version"]
                assert clear.json()["data"]["subject_id"] is None

                # User B cannot link Subject A
                version_b = client.get("/api/v1/passport", headers=headers_b).json()["data"][
                    "version"
                ]
                assert (
                    client.patch(
                        "/api/v1/passport",
                        headers=headers_b,
                        json={"expected_version": version_b, "subject_id": subject_id},
                    ).status_code
                    == 404
                )
                assert (
                    client.patch(
                        "/api/v1/passport",
                        headers=headers_a,
                        json={
                            "expected_version": version,
                            "subject_id": str(uuid.uuid4()),
                        },
                    ).status_code
                    == 404
                )
                # no automatic subject on GET
                with SyncSession() as session:
                    assert (
                        session.execute(
                            text("SELECT COUNT(*) FROM career_subjects WHERE owner_user_id = :u"),
                            {"u": str(user_a)},
                        ).scalar()
                        == 1
                    )

                # Aggregate patch section preferences
                prefs_ok = client.patch(
                    "/api/v1/passport",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "section_preferences": DEFAULT_SECTION_PREFS,
                    },
                )
                assert prefs_ok.status_code == 200
                version = prefs_ok.json()["data"]["version"]

                prefs_bad = client.patch(
                    "/api/v1/passport",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "section_preferences": DEFAULT_SECTION_PREFS[:3],
                    },
                )
                assert prefs_bad.status_code == 422

                only_version = client.patch(
                    "/api/v1/passport",
                    headers=headers_a,
                    json={"expected_version": version},
                )
                assert only_version.status_code == 422

                # M. Version conflicts
                stale = client.patch(
                    "/api/v1/passport/profile",
                    headers=headers_a,
                    json={"expected_version": 1, "phone": "+1999"},
                )
                assert stale.status_code == 409
                assert stale.json()["code"] == "CONFLICT"
                assert stale.json()["details"]["expected_version"] == 1
                assert "current_version" in stale.json()["details"]

                before = client.get("/api/v1/passport", headers=headers_a).json()["data"]
                version = before["version"]
                phone_before = before["profile"]["phone"]

                stale_create = client.post(
                    "/api/v1/passport/experiences",
                    headers=headers_a,
                    json={
                        "expected_version": version - 1,
                        "job_title": "Stale",
                        "company_name": "Nope",
                    },
                )
                assert stale_create.status_code == 409

                stale_reo = client.put(
                    "/api/v1/passport/experiences/reorder",
                    headers=headers_a,
                    json={"expected_version": version - 1, "ordered_ids": [exp_id]},
                )
                assert stale_reo.status_code == 409

                stale_del = client.delete(
                    f"/api/v1/passport/experiences/{exp_id}",
                    headers=headers_a,
                    params={"expected_version": version - 1},
                )
                assert stale_del.status_code == 409

                after = client.get("/api/v1/passport", headers=headers_a).json()["data"]
                assert after["version"] == version
                assert after["profile"]["phone"] == phone_before
                assert not any(e["job_title"] == "Stale" for e in after["experiences"])

                # N. Reorder integrity (experiences + targets)
                # exact set already tested; duplicates / missing / foreign / extra
                dup = client.put(
                    "/api/v1/passport/experiences/reorder",
                    headers=headers_a,
                    json={"expected_version": version, "ordered_ids": [exp_id, exp_id]},
                )
                assert dup.status_code == 422

                missing = client.put(
                    "/api/v1/passport/experiences/reorder",
                    headers=headers_a,
                    json={"expected_version": version, "ordered_ids": []},
                )
                assert missing.status_code == 422

                foreign = client.put(
                    "/api/v1/passport/experiences/reorder",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "ordered_ids": [exp_id, str(uuid.uuid4())],
                    },
                )
                assert foreign.status_code == 422

                # Targets reorder foreign
                current_targets = after["targets"]
                assert current_targets
                tid = current_targets[0]["id"]
                bad_tgt_reo = client.put(
                    "/api/v1/passport/targets/reorder",
                    headers=headers_a,
                    json={
                        "expected_version": version,
                        "ordered_ids": [tid, str(uuid.uuid4())],
                    },
                )
                assert bad_tgt_reo.status_code == 422
                assert (
                    client.get("/api/v1/passport", headers=headers_a).json()["data"]["version"]
                    == version
                )

                # Parametrized reorder coverage for remaining collections (exact empty/set)
                for collection, create_path, create_body, list_key in [
                    (
                        "education",
                        "/api/v1/passport/education",
                        {"degree": "X", "institution": "Y"},
                        "education",
                    ),
                    (
                        "projects",
                        "/api/v1/passport/projects",
                        {"title": "P"},
                        "projects",
                    ),
                    (
                        "skills",
                        "/api/v1/passport/skills",
                        {"name": "S"},
                        "skills",
                    ),
                    (
                        "credentials",
                        "/api/v1/passport/credentials",
                        {"name": "C", "issuing_organization": "O"},
                        "credentials",
                    ),
                ]:
                    cur = client.get("/api/v1/passport", headers=headers_a).json()["data"]
                    version = cur["version"]
                    ids = [item["id"] for item in cur[list_key]]
                    ok = client.put(
                        f"/api/v1/passport/{collection}/reorder",
                        headers=headers_a,
                        json={
                            "expected_version": version,
                            "ordered_ids": list(reversed(ids)) if ids else [],
                        },
                    )
                    assert ok.status_code == 200, (collection, ok.text)
                    version = ok.json()["data"]["version"]
                    bad = client.put(
                        f"/api/v1/passport/{collection}/reorder",
                        headers=headers_a,
                        json={
                            "expected_version": version,
                            "ordered_ids": [str(uuid.uuid4())],
                        },
                    )
                    assert bad.status_code == 422

                version = client.get("/api/v1/passport", headers=headers_a).json()["data"][
                    "version"
                ]

                # O. Mass-assignment rejection
                for key in FORBIDDEN_BODY_KEYS:
                    payload = {
                        "expected_version": version,
                        "job_title": "x",
                        "company_name": "y",
                        key: "evil",
                    }
                    resp = client.post(
                        "/api/v1/passport/experiences",
                        headers=headers_a,
                        json=payload,
                    )
                    assert resp.status_code == 422, key

                # P. Truth boundary
                with SyncSession() as session:
                    for table in (
                        "career_claims",
                        "provenance_sources",
                        "provenance_snapshots",
                    ):
                        exists = session.execute(
                            text(
                                "SELECT EXISTS ("
                                "SELECT 1 FROM information_schema.tables "
                                "WHERE table_name = :t)"
                            ),
                            {"t": table},
                        ).scalar()
                        if exists:
                            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                            assert count == 0, table

                    metas = session.execute(
                        text(
                            "SELECT passport_record_meta FROM work_experiences we "
                            "JOIN profiles p ON p.id = we.profile_id "
                            "WHERE p.user_id = :u"
                        ),
                        {"u": str(user_a)},
                    ).scalars().all()
                    for meta in metas:
                        assert meta["verification_status"] == "unverified"
                        assert meta["support_status"] == "profile_supported"

                final = client.get("/api/v1/passport", headers=headers_a).json()["data"]
                for section in (
                    "experiences",
                    "education",
                    "projects",
                    "skills",
                    "credentials",
                    "targets",
                ):
                    for item in final[section]:
                        assert item["record_meta"]["verification_status"] == "unverified"
                        assert "evidence" not in item
                        assert "claims" not in item

                # Q. Lazy-create idempotency
                ids = {
                    client.get("/api/v1/passport", headers=headers_a).json()["data"]["id"]
                    for _ in range(3)
                }
                assert len(ids) == 1
                with SyncSession() as session:
                    assert (
                        session.execute(
                            text("SELECT COUNT(*) FROM career_passports WHERE owner_user_id = :u"),
                            {"u": str(user_a)},
                        ).scalar()
                        == 1
                    )

        finally:
            app.dependency_overrides.pop(get_db, None)
            app.router.lifespan_context = original_lifespan
            cache_mod._CACHE_SINGLETON = original_cache
            sync_engine.dispose()
            asyncio.run(async_engine.dispose())
