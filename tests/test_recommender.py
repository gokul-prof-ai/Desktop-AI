"""
DesktopAI
Tests for the File Recommender module.
"""

import ai.recommender as recommender_module
from ai.recommender import recommend_action


def test_recommend_action_returns_none_for_empty_file_name():
    """No file name should return None without calling the AI."""
    assert recommend_action("") is None
    assert recommend_action("   ") is None


def test_recommend_action_returns_none_when_ai_unavailable(monkeypatch):
    """If the AI doesn't respond, recommendation should return None
    gracefully, not raise."""

    def fake_generate_response(prompt):
        return None

    monkeypatch.setattr(recommender_module, "generate_response", fake_generate_response)

    result = recommend_action("invoice.pdf", category="Invoice")

    assert result is None


def test_recommend_action_returns_clean_suggestion(monkeypatch):
    """A normal AI response should be returned as a clean folder path."""

    def fake_generate_response(prompt):
        return "Documents/Invoices"

    monkeypatch.setattr(recommender_module, "generate_response", fake_generate_response)

    result = recommend_action("invoice_march.pdf", category="Invoice")

    assert result == "Documents/Invoices"


def test_recommend_action_cleans_messy_ai_output(monkeypatch):
    """Extra punctuation or explanation from the AI should be
    stripped down to a single clean suggestion."""

    def fake_generate_response(prompt):
        return '"Work/Contracts".\nThis file appears to be a contract.'

    monkeypatch.setattr(recommender_module, "generate_response", fake_generate_response)

    result = recommend_action("contract.docx", category="Contract")

    assert result == "Work/Contracts"


def test_recommend_action_works_without_category_or_text(monkeypatch):
    """A recommendation should still be attempted even if only a
    file name is available (no category or text yet)."""

    def fake_generate_response(prompt):
        return "Misc"

    monkeypatch.setattr(recommender_module, "generate_response", fake_generate_response)

    result = recommend_action("random_file.txt")

    assert result == "Misc"


def test_recommend_action_includes_file_name_in_prompt(monkeypatch):
    """The file name should actually be sent to the AI as context."""
    captured_prompts = []

    def fake_generate_response(prompt):
        captured_prompts.append(prompt)
        return "Misc"

    monkeypatch.setattr(recommender_module, "generate_response", fake_generate_response)

    recommend_action("unique_marker_file.pdf", category="Report")

    assert "unique_marker_file.pdf" in captured_prompts[0]
    assert "Report" in captured_prompts[0]