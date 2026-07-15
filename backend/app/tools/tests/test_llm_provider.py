"""LLM provider selector + Ollama HTTP contract tests (no live Ollama required)."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import Settings
from app.tools.llm import (
    DeterministicMockProvider,
    OllamaProvider,
    PromptSpec,
    clear_llm_provider_cache,
    get_llm,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_llm_provider_cache()
    yield
    clear_llm_provider_cache()


def test_default_settings_use_ollama_8b():
    assert Settings.model_fields["llm_provider"].default == "ollama"
    assert Settings.model_fields["ollama_base_url"].default == "http://127.0.0.1:11434"
    assert Settings.model_fields["ollama_model_flash"].default == "llama3.1:8b"
    assert Settings.model_fields["ollama_model_pro"].default == "llama3.1:8b"
    s = Settings.model_construct(llm_provider="ollama", gemini_api_key="should-not-matter")
    assert s.llm_mode == "local"
    s_mock = Settings.model_construct(llm_provider="mock", gemini_api_key="should-not-matter")
    assert s_mock.llm_mode == "mock"


def test_gemini_api_key_does_not_select_provider(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.llm_provider", "mock")
    monkeypatch.setattr("app.tools.llm.settings.gemini_api_key", "AIza-fake-key")
    clear_llm_provider_cache()
    provider = get_llm("flash")
    assert isinstance(provider, DeterministicMockProvider)
    assert "gemini" not in provider.model_name.lower()


def test_get_llm_returns_ollama_for_flash_and_pro(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.llm_provider", "ollama")
    monkeypatch.setattr("app.tools.llm.settings.ollama_model_flash", "llama3.1:8b")
    monkeypatch.setattr("app.tools.llm.settings.ollama_model_pro", "llama3.1:8b")
    monkeypatch.setattr("app.tools.llm.settings.ollama_base_url", "http://127.0.0.1:11434")
    clear_llm_provider_cache()
    assert isinstance(get_llm("flash"), OllamaProvider)
    assert isinstance(get_llm("pro"), OllamaProvider)


def test_get_llm_returns_mock_when_provider_mock(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.llm_provider", "mock")
    clear_llm_provider_cache()
    assert isinstance(get_llm("flash"), DeterministicMockProvider)


def test_cache_key_changes_by_model_and_base_url(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.llm_provider", "ollama")
    monkeypatch.setattr("app.tools.llm.settings.ollama_model_flash", "llama3.1:8b")
    monkeypatch.setattr("app.tools.llm.settings.ollama_base_url", "http://127.0.0.1:11434")
    clear_llm_provider_cache()
    a = get_llm("flash")
    monkeypatch.setattr("app.tools.llm.settings.ollama_base_url", "http://127.0.0.1:11435")
    b = get_llm("flash")
    assert a is not b


def _mock_response(payload: dict[str, Any], status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        json=payload,
        request=httpx.Request("POST", "http://127.0.0.1:11434/api/generate"),
    )


def test_ollama_generate_posts_expected_payload(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.ollama_base_url", "http://127.0.0.1:11434")
    monkeypatch.setattr("app.tools.llm.settings.ollama_model_flash", "llama3.1:8b")
    monkeypatch.setattr("app.tools.llm.settings.ollama_request_timeout_seconds", 30.0)

    captured: dict[str, Any] = {}

    async def fake_post(url, json=None):  # noqa: A002
        captured["url"] = url
        captured["json"] = json
        return _mock_response(
            {
                "model": "llama3.1:8b",
                "response": "hello world",
                "prompt_eval_count": 11,
                "eval_count": 2,
            }
        )

    provider = OllamaProvider("flash")

    async def run():
        with patch("httpx.AsyncClient") as client_cls:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.__aexit__.return_value = None
            instance.post = AsyncMock(side_effect=fake_post)
            client_cls.return_value = instance
            return await provider.generate(
                PromptSpec(system_prompt="sys", user_prompt="user", temperature=0.2)
            )

    result = asyncio.run(run())
    assert captured["url"] == "http://127.0.0.1:11434/api/generate"
    assert captured["json"]["model"] == "llama3.1:8b"
    assert captured["json"]["system"] == "sys"
    assert captured["json"]["prompt"] == "user"
    assert captured["json"]["stream"] is False
    assert captured["json"]["options"]["temperature"] == 0.2
    assert result.text == "hello world"
    assert result.prompt_tokens == 11
    assert result.completion_tokens == 2
    assert result.model == "llama3.1:8b"


def test_ollama_generate_sends_json_schema_format(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.ollama_model_flash", "llama3.1:8b")
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    captured: dict[str, Any] = {}

    async def fake_post(url, json=None):  # noqa: A002
        captured["json"] = json
        return _mock_response(
            {
                "model": "llama3.1:8b",
                "response": '{"ok": true}',
                "prompt_eval_count": 5,
                "eval_count": 3,
            }
        )

    provider = OllamaProvider("flash")

    async def run():
        with patch("httpx.AsyncClient") as client_cls:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.__aexit__.return_value = None
            instance.post = AsyncMock(side_effect=fake_post)
            client_cls.return_value = instance
            return await provider.generate(
                PromptSpec(system_prompt="sys", user_prompt="user", json_schema=schema)
            )

    result = asyncio.run(run())
    assert captured["json"]["format"] == schema
    assert "valid JSON" in captured["json"]["prompt"]
    assert result.parsed_json == {"ok": True}


def test_ollama_connection_error_message(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.ollama_base_url", "http://127.0.0.1:11434")
    provider = OllamaProvider("flash")

    async def run():
        with patch("httpx.AsyncClient") as client_cls:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.__aexit__.return_value = None
            instance.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
            client_cls.return_value = instance
            await provider.generate(PromptSpec(system_prompt="s", user_prompt="u"))

    with pytest.raises(RuntimeError, match="Local Ollama is not reachable"):
        asyncio.run(run())


def test_ollama_missing_model_message(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.ollama_model_flash", "missing-model:8b")
    provider = OllamaProvider("flash")

    async def fake_post(url, json=None):  # noqa: A002
        return httpx.Response(
            404,
            text="model 'missing-model:8b' not found",
            request=httpx.Request("POST", url),
        )

    async def run():
        with patch("httpx.AsyncClient") as client_cls:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.__aexit__.return_value = None
            instance.post = AsyncMock(side_effect=fake_post)
            client_cls.return_value = instance
            await provider.generate(PromptSpec(system_prompt="s", user_prompt="u"))

    with pytest.raises(RuntimeError, match="ollama pull missing-model:8b"):
        asyncio.run(run())


def test_ollama_stream_yields_chunks(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.ollama_model_flash", "llama3.1:8b")
    provider = OllamaProvider("flash")

    lines = [
        json.dumps({"response": "Hel", "done": False}),
        json.dumps({"response": "lo", "done": True}),
    ]

    async def aiter_lines():
        for line in lines:
            yield line

    stream_cm = MagicMock()
    stream_resp = MagicMock()
    stream_resp.raise_for_status = MagicMock()
    stream_resp.aiter_lines = aiter_lines
    stream_cm.__aenter__ = AsyncMock(return_value=stream_resp)
    stream_cm.__aexit__ = AsyncMock(return_value=None)

    async def run():
        with patch("httpx.AsyncClient") as client_cls:
            instance = AsyncMock()
            instance.__aenter__.return_value = instance
            instance.__aexit__.return_value = None
            instance.stream = MagicMock(return_value=stream_cm)
            client_cls.return_value = instance
            chunks = []
            async for piece in provider.stream(PromptSpec(system_prompt="s", user_prompt="u")):
                chunks.append(piece)
            return chunks

    assert asyncio.run(run()) == ["Hel", "lo"]
