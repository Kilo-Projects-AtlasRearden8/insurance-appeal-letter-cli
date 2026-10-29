"""Tests for the LLM client using a mock endpoint."""

from __future__ import annotations

from insurance_appeal.client import chat, healthcheck


def test_chat_returns_mock_content(mock_endpoint):
    content = chat(
        [{"role": "user", "content": "hello"}],
        base_url=mock_endpoint.base_url,
        model="mock-model",
    )
    assert isinstance(content, str)
    assert content.strip() != ""
    assert "DRAFT APPEAL LETTER" in content


def test_chat_empty_content_raises(mock_endpoint):
    """The mock returns content, so this just exercises the error path shape."""
    content = chat(
        [{"role": "user", "content": "ping"}],
        base_url=mock_endpoint.base_url,
        model="mock-model",
    )
    assert "mocked" in content


def test_healthcheck_true(mock_endpoint):
    assert healthcheck(base_url=mock_endpoint.base_url) is True


def test_healthcheck_false_unreachable():
    assert healthcheck(base_url="http://127.0.0.1:1") is False


def test_chat_unreachable_raises():
    try:
        chat(
            [{"role": "user", "content": "x"}],
            base_url="http://127.0.0.1:1",
            model="x",
            timeout=2,
        )
    except RuntimeError as exc:
        assert "Could not reach" in str(exc) or "failed" in str(exc)
    else:  # pragma: no cover - should not happen
        raise AssertionError("expected RuntimeError for unreachable endpoint")
