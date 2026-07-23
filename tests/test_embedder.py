"""
DesktopAI
Tests for the Embedder module.
"""

import requests

from search.embedder import get_embedding


def test_get_embedding_returns_none_for_empty_text():
    """Empty text should short-circuit rather than call Ollama at all."""
    assert get_embedding("") is None
    assert get_embedding("   ") is None


def test_get_embedding_returns_none_on_connection_error(monkeypatch):
    """If Ollama isn't reachable, this should return None gracefully,
    not raise."""

    def fake_post(url, json, timeout):
        raise requests.exceptions.ConnectionError("Connection refused")

    monkeypatch.setattr(requests, "post", fake_post)

    result = get_embedding("some file text")

    assert result is None


def test_get_embedding_returns_vector_on_success(monkeypatch):
    """When Ollama responds successfully, the embedding vector should
    be extracted and returned. Ollama's real HTTP call is replaced
    with a fake one, so this test doesn't need Ollama running."""

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"embedding": [0.1, 0.2, 0.3]}

    def fake_post(url, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    result = get_embedding("some file text")

    assert result == [0.1, 0.2, 0.3]


def test_get_embedding_returns_none_on_missing_embedding_field(monkeypatch):
    """If Ollama's reply doesn't contain the expected 'embedding'
    field, this should return None rather than raise or return
    garbage."""

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"unexpected_field": "no embedding here"}

    def fake_post(url, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    result = get_embedding("some file text")

    assert result is None