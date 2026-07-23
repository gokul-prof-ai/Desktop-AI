"""
DesktopAI
Tests for the Ollama Client module.
"""

import requests

from ai.ollama_client import generate_response


def test_generate_response_returns_none_when_ollama_not_running():
    """If nothing is listening on the Ollama port, this should
    return None gracefully, not raise an exception. This test does
    NOT require Ollama to be installed — it specifically checks
    that the app survives Ollama being unavailable."""
    result = generate_response("Hello, are you there?")

    assert result is None


def test_generate_response_returns_text_on_success(monkeypatch):
    """When Ollama responds successfully, the text should be
    extracted and returned. Ollama's real HTTP call is replaced
    with a fake one, so this test doesn't need Ollama running."""

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"response": "  This is a fake AI response.  "}

    def fake_post(url, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    result = generate_response("Hello")

    assert result == "This is a fake AI response."


def test_generate_response_returns_none_on_missing_response_field(monkeypatch):
    """If Ollama's reply doesn't contain the expected 'response'
    field, this should return None rather than raise or return
    garbage."""

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"unexpected_field": "no response here"}

    def fake_post(url, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    result = generate_response("Hello")

    assert result is None