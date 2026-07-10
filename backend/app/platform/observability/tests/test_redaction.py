"""Redaction contract tests (0050-PF10-S1)."""

from __future__ import annotations

from copy import deepcopy

from app.platform.observability.redaction import REDACTED_MARKER, redact_mapping, redact_value


def test_password_redacted() -> None:
    assert redact_value("password", "secret") == REDACTED_MARKER
    assert redact_mapping({"password": "x"})["password"] == REDACTED_MARKER


def test_authorization_redacted() -> None:
    assert redact_mapping({"Authorization": "Bearer abc"})["Authorization"] == REDACTED_MARKER


def test_cookie_redacted() -> None:
    assert redact_mapping({"cookie": "a=b", "Set-Cookie": "c=d"}) == {
        "cookie": REDACTED_MARKER,
        "Set-Cookie": REDACTED_MARKER,
    }


def test_api_key_redacted() -> None:
    assert redact_mapping({"api_key": "k", "apikey": "k2", "api-key": "k3"}) == {
        "api_key": REDACTED_MARKER,
        "apikey": REDACTED_MARKER,
        "api-key": REDACTED_MARKER,
    }


def test_claim_value_redacted() -> None:
    assert redact_mapping({"claim_value": "private"})["claim_value"] == REDACTED_MARKER


def test_cv_and_resume_text_redacted() -> None:
    out = redact_mapping({"cv_text": "cv", "resume_text": "resume"})
    assert out["cv_text"] == REDACTED_MARKER
    assert out["resume_text"] == REDACTED_MARKER


def test_llm_prompt_response_redacted() -> None:
    out = redact_mapping({"llm_prompt": "p", "llm_response": "r"})
    assert out["llm_prompt"] == REDACTED_MARKER
    assert out["llm_response"] == REDACTED_MARKER


def test_nested_dict_redacted() -> None:
    out = redact_mapping({"outer": {"token": "t", "ok": 1}})
    assert out["outer"]["token"] == REDACTED_MARKER
    assert out["outer"]["ok"] == 1


def test_list_of_dicts_redacted() -> None:
    out = redact_mapping({"items": [{"password": "p"}, {"safe": True}]})
    assert out["items"][0]["password"] == REDACTED_MARKER
    assert out["items"][1]["safe"] is True


def test_input_mapping_not_mutated() -> None:
    original = {"password": "secret", "nested": {"token": "t"}}
    snapshot = deepcopy(original)
    _ = redact_mapping(original)
    assert original == snapshot


def test_safe_keys_preserved() -> None:
    out = redact_mapping({"method": "GET", "path": "/health", "status_code": 200})
    assert out == {"method": "GET", "path": "/health", "status_code": 200}
