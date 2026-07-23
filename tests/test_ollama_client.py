"""
DesktopAI
Tests for the Ollama Client module.
"""

import requests

from ai.ollama_client import generate_response


def test_generate_response_returns_none_on_connection_error(monkeypatch):
    """If Ollama isn't reachable, this should return None gracefully,
    not raise. We simulate the failure directly rather than relying
    on Ollama actually being off, since it may be running on whatever
    machine runs these tests (including yours, now that it's installed)."""

    def fake_post(url, json, timeout):
        raise requests.exceptions.ConnectionError("Connection refused")

    monkeypatch.setattr(requests, "post", fake_post)

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