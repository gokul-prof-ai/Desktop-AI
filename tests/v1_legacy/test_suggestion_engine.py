"""
DesktopAI
Tests for the Watcher Suggestion Engine.
"""

import watcher.suggestion_engine as suggestion_engine_module
from watcher.suggestion_engine import build_suggestion, extract_text


def test_extract_text_reads_plain_text_file(tmp_path):
    """.txt files should be read directly, no special reader needed."""
    text_file = tmp_path / "notes.txt"
    text_file.write_text("hello world")

    assert extract_text(text_file) == "hello world"


def test_extract_text_returns_empty_string_for_unsupported_type(tmp_path):
    """A file type with no reader (e.g. .exe) should return an empty
    string, not raise or return None."""
    binary_file = tmp_path / "program.exe"
    binary_file.write_bytes(b"\x00\x01\x02")

    assert extract_text(binary_file) == ""


def test_build_suggestion_uses_classifier_and_recommender(tmp_path, monkeypatch):
    """build_suggestion() should extract text, then pass it through
    classify_file() and recommend_action(), and package the results
    into a WatchSuggestion."""
    text_file = tmp_path / "invoice.txt"
    text_file.write_text("Total due: $250. Payment terms: Net 30.")

    def fake_classify_file(text):
        assert "Total due" in text
        return "Invoice"

    def fake_recommend_action(file_name, category=None, text=""):
        assert file_name == "invoice.txt"
        assert category == "Invoice"
        return "Documents/Invoices"

    monkeypatch.setattr(suggestion_engine_module, "classify_file", fake_classify_file)
    monkeypatch.setattr(suggestion_engine_module, "recommend_action", fake_recommend_action)

    suggestion = build_suggestion(text_file)

    assert suggestion.path == text_file
    assert suggestion.category == "Invoice"
    assert suggestion.suggested_folder == "Documents/Invoices"
    assert suggestion.detected_at is not None


def test_build_suggestion_handles_ai_unavailable(tmp_path, monkeypatch):
    """If the AI is unavailable, build_suggestion() should still
    return a WatchSuggestion, just with None fields, instead of
    raising."""
    text_file = tmp_path / "random.txt"
    text_file.write_text("some content")

    monkeypatch.setattr(
        suggestion_engine_module, "classify_file", lambda text: None
    )
    monkeypatch.setattr(
        suggestion_engine_module,
        "recommend_action",
        lambda file_name, category=None, text="": None,
    )

    suggestion = build_suggestion(text_file)

    assert suggestion.category is None
    assert suggestion.suggested_folder is None