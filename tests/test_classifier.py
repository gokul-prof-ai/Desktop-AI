"""
DesktopAI
Tests for the File Classifier module.
"""

import ai.classifier as classifier_module
from ai.classifier import classify_file


def test_classify_file_returns_none_for_empty_text():
    """Empty or blank text should return None without calling the AI."""
    assert classify_file("") is None
    assert classify_file("   ") is None


def test_classify_file_returns_none_when_ai_unavailable(monkeypatch):
    """If the AI doesn't respond (Ollama not running), classification
    should return None gracefully, not raise."""

    def fake_generate_response(prompt):
        return None

    monkeypatch.setattr(classifier_module, "generate_response", fake_generate_response)

    result = classify_file("Some invoice text with amounts and dates.")

    assert result is None


def test_classify_file_returns_clean_label(monkeypatch):
    """A normal AI response should be returned as-is (stripped)."""

    def fake_generate_response(prompt):
        return "Invoice"

    monkeypatch.setattr(classifier_module, "generate_response", fake_generate_response)

    result = classify_file("Total due: $500. Payment terms: Net 30.")

    assert result == "Invoice"


def test_classify_file_cleans_messy_ai_output(monkeypatch):
    """If the AI adds extra punctuation, quotes, or a second line
    despite instructions, the result should still be cleaned to a
    single short label."""

    def fake_generate_response(prompt):
        return '"Resume".\nThis document appears to be a resume.'

    monkeypatch.setattr(classifier_module, "generate_response", fake_generate_response)

    result = classify_file("Experience: Software Engineer at ...")

    assert result == "Resume"


def test_classify_file_includes_text_in_prompt(monkeypatch):
    """The extracted file text should actually be sent to the AI,
    not ignored."""
    captured_prompts = []

    def fake_generate_response(prompt):
        captured_prompts.append(prompt)
        return "Report"

    monkeypatch.setattr(classifier_module, "generate_response", fake_generate_response)

    classify_file("Quarterly sales figures for Q3.")

    assert "Quarterly sales figures for Q3." in captured_prompts[0]