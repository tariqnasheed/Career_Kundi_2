"""
0051-F4 — Read-only Taxonomy API tests.

Uses TestClient with empty lifespan + get_current_user override so tests do not
require Postgres. Health remains public; other endpoints require auth override.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.main import app


TAXONOMY_PREFIX = "/api/v1/taxonomy"
OPENAPI_URL = "/api/openapi.json"
TAXONOMY_ROUTE = Path(__file__).resolve().parents[2] / "app" / "api" / "routes" / "taxonomy.py"
TAXONOMY_SCHEMA = Path(__file__).resolve().parents[2] / "app" / "schemas" / "taxonomy.py"


@pytest.fixture
def taxonomy_client():
    user = User(
        id=uuid.uuid4(),
        email="taxonomy-api-test@example.com",
        hashed_password="not-used",
        full_name="Taxonomy API Tester",
        role=UserRole.USER,
        plan=SubscriptionPlan.FREE,
        is_active=True,
        is_email_verified=False,
    )

    async def override_get_current_user() -> User:
        return user

    @asynccontextmanager
    async def _empty_lifespan(_app):
        yield

    original_lifespan = app.router.lifespan_context
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.router.lifespan_context = _empty_lifespan
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.router.lifespan_context = original_lifespan


def test_taxonomy_health_available_no_external_ingestion(taxonomy_client: TestClient):
    # Public health — no auth dependency on the route.
    res = taxonomy_client.get(f"{TAXONOMY_PREFIX}/health")
    assert res.status_code == 200
    body = res.json()
    assert body["available"] is True
    assert body["catalog_name"] == "internal_seed"
    assert body["external_dataset_ingestion"] is False
    assert body["role_count"] >= 4
    assert body["skill_count"] >= 4
    assert body["pathway_type_count"] == 11


def test_pathway_types_returns_eleven(taxonomy_client: TestClient):
    res = taxonomy_client.get(f"{TAXONOMY_PREFIX}/pathway-types")
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 11
    ids = {row["id"] for row in rows}
    assert "skill_gap" in ids
    assert "career_switch" in ids
    assert all(row.get("label") for row in rows)


def test_roles_match_known_title(taxonomy_client: TestClient):
    res = taxonomy_client.post(
        f"{TAXONOMY_PREFIX}/roles/match",
        json={"input_text": "Software Engineer", "source": "user_provided", "confidence": "suggested"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["matched_role_id"] == "software_engineer"
    assert body["matched_skill_id"] is None
    assert body["source"] == "user_provided"
    assert body["confidence"] == "suggested"


def test_roles_match_known_alias_normalized(taxonomy_client: TestClient):
    res = taxonomy_client.post(
        f"{TAXONOMY_PREFIX}/roles/match",
        json={"input_text": "  software   developer "},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["matched_role_id"] == "software_engineer"
    assert body["normalized_text"] == "software developer"


def test_roles_match_unknown_returns_null_unknown(taxonomy_client: TestClient):
    res = taxonomy_client.post(
        f"{TAXONOMY_PREFIX}/roles/match",
        json={"input_text": "Chief Imagination Officer"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["matched_role_id"] is None
    assert body["matched_skill_id"] is None
    assert body["source"] == "unknown"
    assert body["confidence"] == "unknown"
    assert "no deterministic seed match found" in body["explanation"]


def test_skills_match_known_alias(taxonomy_client: TestClient):
    res = taxonomy_client.post(
        f"{TAXONOMY_PREFIX}/skills/match",
        json={"input_text": "  python3 "},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["matched_skill_id"] == "python"
    assert body["matched_role_id"] is None


def test_skills_match_unknown_returns_null_unknown(taxonomy_client: TestClient):
    res = taxonomy_client.post(
        f"{TAXONOMY_PREFIX}/skills/match",
        json={"input_text": "telepathy protocols"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["matched_skill_id"] is None
    assert body["source"] == "unknown"
    assert body["confidence"] == "unknown"


def test_get_role_known(taxonomy_client: TestClient):
    res = taxonomy_client.get(f"{TAXONOMY_PREFIX}/roles/software_engineer")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "software_engineer"
    assert body["title"] == "Software Engineer"
    assert body["confidence"] != "verified"


def test_get_role_unknown_404(taxonomy_client: TestClient):
    res = taxonomy_client.get(f"{TAXONOMY_PREFIX}/roles/missing_role")
    assert res.status_code == 404
    body = res.json()
    assert body.get("error") is True
    assert body.get("code") == "NOT_FOUND"


def test_role_skills(taxonomy_client: TestClient):
    res = taxonomy_client.get(f"{TAXONOMY_PREFIX}/roles/software_engineer/skills")
    assert res.status_code == 200
    body = res.json()
    assert body["role_id"] == "software_engineer"
    skill_ids = {s["id"] for s in body["skills"]}
    assert "python" in skill_ids


def test_related_roles(taxonomy_client: TestClient):
    res = taxonomy_client.get(f"{TAXONOMY_PREFIX}/roles/software_engineer/related")
    assert res.status_code == 200
    body = res.json()
    assert body["role_id"] == "software_engineer"
    assert [r["id"] for r in body["related_roles"]] == ["project_manager"]


def test_model_inferred_cannot_be_verified_via_api(taxonomy_client: TestClient):
    res = taxonomy_client.post(
        f"{TAXONOMY_PREFIX}/roles/match",
        json={
            "input_text": "Software Engineer",
            "source": "model_inferred",
            "confidence": "verified",
        },
    )
    assert res.status_code == 422

    res_fb = taxonomy_client.post(
        f"{TAXONOMY_PREFIX}/roles/match",
        json={
            "input_text": "Software Engineer",
            "source": "fallback_default",
            "confidence": "verified",
        },
    )
    assert res_fb.status_code == 422


def test_openapi_includes_taxonomy_paths(taxonomy_client: TestClient):
    res = taxonomy_client.get(OPENAPI_URL)
    assert res.status_code == 200
    paths = set(res.json().get("paths", {}))
    expected = {
        f"{TAXONOMY_PREFIX}/health",
        f"{TAXONOMY_PREFIX}/pathway-types",
        f"{TAXONOMY_PREFIX}/roles/match",
        f"{TAXONOMY_PREFIX}/skills/match",
        f"{TAXONOMY_PREFIX}/roles/{{role_id}}",
        f"{TAXONOMY_PREFIX}/roles/{{role_id}}/skills",
        f"{TAXONOMY_PREFIX}/roles/{{role_id}}/related",
    }
    missing = expected - paths
    assert not missing, f"missing OpenAPI paths: {missing}"


def test_taxonomy_route_and_schema_have_no_forbidden_imports():
    forbidden = (
        "from sqlalchemy",
        "import sqlalchemy",
        "from openai",
        "import openai",
        "from anthropic",
        "import anthropic",
        "google.generativeai",
        "ChatOpenAI",
        "ChatGoogle",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        ".commit(",
        ".flush(",
        "session.add(",
    )
    for path in (TAXONOMY_ROUTE, TAXONOMY_SCHEMA):
        source = path.read_text(encoding="utf-8")
        lowered = source.lower()
        for snippet in forbidden:
            assert snippet.lower() not in lowered, f"{path.name} contains {snippet}"
