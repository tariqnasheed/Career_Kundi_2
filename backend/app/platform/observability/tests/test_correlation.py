"""Correlation ID contract tests (0050-PF10-S1)."""

from __future__ import annotations

from app.platform.observability.correlation import (
    MAX_CORRELATION_ID_LENGTH,
    is_valid_correlation_id,
    new_correlation_id,
    normalize_correlation_id,
)


def test_generated_id_nonempty_and_valid() -> None:
    cid = new_correlation_id()
    assert cid
    assert is_valid_correlation_id(cid)
    assert len(cid) <= MAX_CORRELATION_ID_LENGTH


def test_valid_incoming_preserved() -> None:
    incoming = "abc-DEF_012.xyz"
    assert normalize_correlation_id(incoming) == incoming


def test_missing_incoming_replaced() -> None:
    cid = normalize_correlation_id(None)
    assert is_valid_correlation_id(cid)


def test_empty_and_whitespace_replaced() -> None:
    for bad in ("", "   ", "\t"):
        cid = normalize_correlation_id(bad)
        assert is_valid_correlation_id(cid)
        assert cid != bad


def test_newline_injection_replaced() -> None:
    bad = "good-id\nInjected"
    cid = normalize_correlation_id(bad)
    assert is_valid_correlation_id(cid)
    assert "\n" not in cid
    assert cid != bad


def test_overlength_replaced() -> None:
    bad = "a" * (MAX_CORRELATION_ID_LENGTH + 1)
    cid = normalize_correlation_id(bad)
    assert is_valid_correlation_id(cid)
    assert len(cid) <= MAX_CORRELATION_ID_LENGTH
    assert cid != bad


def test_unsafe_characters_replaced() -> None:
    for bad in ("has space", "semi;colon", "slash/id", "unicode\u0000null"):
        cid = normalize_correlation_id(bad)
        assert is_valid_correlation_id(cid)
        assert cid != bad


def test_max_length_enforced() -> None:
    exact = "a" * MAX_CORRELATION_ID_LENGTH
    assert is_valid_correlation_id(exact)
    assert normalize_correlation_id(exact) == exact
    assert not is_valid_correlation_id(exact + "x")
