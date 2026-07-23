"""
DesktopAI
Tests for the File Summarizer module.
"""

import ai.summarizer as summarizer_module
from ai.summarizer import summarize_file


def test_summarize_file_returns_none_for_empty_text():
    """Empty or blank text should return None without calling the AI."""
    assert summarize_file("") is None
    assert summarize_file("   ") is None


def test_summarize_file_returns_none_when_ai_unavailable(monkeypatch):
    """If the AI doesn't respond (Ollama not running), summarization
    should return None gracefully, not raise."""

    def fake_generate_response(prompt):
        return None

    monkeypatch.setattr(summarizer_module, "generate_response", fake_generate_response)

    result = summarize_file("Some long document text to summarize.")

    assert result is None


def test_summarize_file_returns_ai_summary(monkeypatch):
    """A normal AI response should be returned as the summary."""

    def fake_generate_response(prompt):
        return "This document discusses quarterly sales performance."

    monkeypatch.setattr(summarizer_module, "generate_response", fake_generate_response)

    result = summarize_file("Q3 sales rose 12% year over year, driven by...")

    assert result == "This document discusses quarterly sales performance."


def test_summarize_file_includes_text_in_prompt(monkeypatch):
    """The extracted file text should actually be sent to the AI."""
    captured_prompts = []

    def fake_generate_response(prompt):
        captured_prompts.append(prompt)
        return "Summary text."

    monkeypatch.setattr(summarizer_module, "generate_response", fake_generate_response)

    summarize_file("Unique marker text ABC123.")

    assert "Unique marker text ABC123." in captured_prompts[0]


def test_summarize_file_truncates_very_long_text(monkeypatch):
    """Extremely long text should be truncated before being sent to
    the AI, so requests stay fast and reliable."""
    captured_prompts = []

    def fake_generate_response(prompt):
        captured_prompts.append(prompt)
        return "Summary."

    monkeypatch.setattr(summarizer_module, "generate_response", fake_generate_response)

    very_long_text = "word " * 10000
    summarize_file(very_long_text)

    # The prompt should not contain the full 50,000-character input.
    assert len(captured_prompts[0]) < len(very_long_text)
    