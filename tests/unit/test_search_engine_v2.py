"""
M8 unit tests — src/domain/search/engine.py (public API)

Tests the two public functions:
    build_index()  → returns a stats dict
    search()       → returns a list of dicts with 'path' and 'score'

All tests patch IncrementalSearchIndex so no real FAISS or Ollama needed.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.ai.gateway import AIGateway
from infrastructure.ai.mock_provider import MockProvider


@pytest.fixture(autouse=True)
def use_mock_provider():
    AIGateway.set_provider(MockProvider(delay_ms=0))
    yield


# ── build_index() ─────────────────────────────────────────────────────────────

def test_build_index_returns_stats_dict():
    from domain.search.engine import build_index
    expected = {"indexed": 3, "skipped": 0, "removed": 0, "total": 3, "error": None}

    with patch("domain.search.engine._index") as mock_idx:
        mock_idx.build.return_value = expected
        result = build_index()

    assert result == expected
    mock_idx.build.assert_called_once()


def test_build_index_propagates_error_in_stats():
    from domain.search.engine import build_index
    error_stats = {
        "indexed": 0, "skipped": 5, "removed": 0, "total": 0,
        "error": "Ollama not available"
    }
    with patch("domain.search.engine._index") as mock_idx:
        mock_idx.build.return_value = error_stats
        result = build_index()

    assert result["error"] == "Ollama not available"


def test_build_index_zero_stats_on_empty_db():
    from domain.search.engine import build_index
    empty = {"indexed": 0, "skipped": 0, "removed": 0, "total": 0, "error": None}
    with patch("domain.search.engine._index") as mock_idx:
        mock_idx.build.return_value = empty
        result = build_index()
    assert result["indexed"] == 0
    assert result["error"] is None


# ── search() ──────────────────────────────────────────────────────────────────

def test_search_returns_list_of_dicts():
    from domain.search.engine import search
    fake_results = [
        {"path": "/docs/report.pdf", "score": 0.91},
        {"path": "/docs/budget.xlsx", "score": 0.78},
    ]
    with patch("domain.search.engine._index") as mock_idx:
        mock_idx.search.return_value = fake_results
        results = search("quarterly report", top_k=5)

    assert results == fake_results
    mock_idx.search.assert_called_once_with("quarterly report", top_k=5)


def test_search_empty_query_returns_empty_without_hitting_index():
    from domain.search.engine import search
    with patch("domain.search.engine._index") as mock_idx:
        results = search("", top_k=5)
    assert results == []
    mock_idx.search.assert_not_called()


def test_search_whitespace_query_returns_empty():
    from domain.search.engine import search
    with patch("domain.search.engine._index") as mock_idx:
        results = search("   ", top_k=5)
    assert results == []
    mock_idx.search.assert_not_called()


def test_search_default_top_k():
    """search() must work without specifying top_k."""
    from domain.search.engine import search
    with patch("domain.search.engine._index") as mock_idx:
        mock_idx.search.return_value = []
        search("find something")
    mock_idx.search.assert_called_once()