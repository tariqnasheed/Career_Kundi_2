"""Observability middleware tests (0050-PF10-S1)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.platform.observability.correlation import (
    CORRELATION_HEADER,
    is_valid_correlation_id,
)
from app.platform.observability.events import ObservabilityEvent
from app.platform.observability.middleware import ObservabilityMiddleware


def _probe_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/probe")
    async def probe(request: Request) -> dict[str, Any]:
        return {"correlation_id": getattr(request.state, "correlation_id", None)}

    @app.post("/echo")
    async def echo(request: Request) -> dict[str, Any]:
        body = await request.body()
        return {
            "correlation_id": request.state.correlation_id,
            "body_len": len(body),
        }

    return app


def test_response_includes_x_request_id() -> None:
    client = TestClient(_probe_app())
    response = client.get("/probe")
    assert response.status_code == 200
    assert CORRELATION_HEADER in response.headers
    assert is_valid_correlation_id(response.headers[CORRELATION_HEADER])


def test_valid_incoming_x_request_id_echoed() -> None:
    client = TestClient(_probe_app())
    incoming = "client-corr-123"
    response = client.get("/probe", headers={CORRELATION_HEADER: incoming})
    assert response.headers[CORRELATION_HEADER] == incoming
    assert response.json()["correlation_id"] == incoming


def test_invalid_incoming_x_request_id_replaced() -> None:
    client = TestClient(_probe_app())
    response = client.get(
        "/probe", headers={CORRELATION_HEADER: "bad id\nwith-newline"}
    )
    echoed = response.headers[CORRELATION_HEADER]
    assert is_valid_correlation_id(echoed)
    assert echoed != "bad id\nwith-newline"
    assert response.json()["correlation_id"] == echoed


def test_request_state_correlation_available() -> None:
    client = TestClient(_probe_app())
    response = client.get("/probe", headers={CORRELATION_HEADER: "state-check-1"})
    assert response.json()["correlation_id"] == "state-check-1"


def test_request_completion_event_logged() -> None:
    client = TestClient(_probe_app())
    with patch("app.platform.observability.middleware.log_event") as mock_log:
        response = client.get("/probe", headers={CORRELATION_HEADER: "log-check-1"})
    assert mock_log.called
    event = mock_log.call_args.args[2]
    assert isinstance(event, ObservabilityEvent)
    assert event.event_name == "request_completed"
    assert event.correlation_id == "log-check-1"
    attrs = dict(event.attributes)
    assert attrs["method"] == "GET"
    assert attrs["path"] == "/probe"
    assert attrs["status_code"] == response.status_code
    assert "duration_ms" in attrs
    assert attrs["correlation_id"] == "log-check-1"


def test_logged_event_excludes_sensitive_request_data() -> None:
    client = TestClient(_probe_app())
    with patch("app.platform.observability.middleware.log_event") as mock_log:
        client.post(
            "/echo",
            headers={
                CORRELATION_HEADER: "safe-log-1",
                "Authorization": "Bearer super-secret-token",
                "Cookie": "session=abc",
            },
            content=b'{"password":"nope","cv_text":"private"}',
        )
    assert mock_log.called
    event = mock_log.call_args.args[2]
    assert isinstance(event, ObservabilityEvent)
    payload = event.to_log_dict()
    raw = str(payload)
    assert "super-secret-token" not in raw
    assert "session=abc" not in raw
    assert "private" not in raw
    attrs = payload["attributes"]
    for forbidden in (
        "authorization",
        "Authorization",
        "cookie",
        "Cookie",
        "body",
        "request_body",
        "headers",
        "password",
        "cv_text",
    ):
        assert forbidden not in attrs


def test_main_app_health_sets_correlation_header() -> None:
    from app.main import app

    @asynccontextmanager
    async def _empty_lifespan(_app):
        yield

    original = app.router.lifespan_context
    app.router.lifespan_context = _empty_lifespan
    try:
        with TestClient(app) as client:
            response = client.get("/health", headers={CORRELATION_HEADER: "health-1"})
        assert response.status_code == 200
        assert response.headers[CORRELATION_HEADER] == "health-1"
    finally:
        app.router.lifespan_context = original
