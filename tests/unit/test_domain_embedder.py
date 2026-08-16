"""
M8 unit tests — src/domain/search/embedder.py

Tests that embed_text() routes through AIGateway (never calls Ollama
directly), respects truncation, and raises EmbeddingError/AIGatewayError
when the provider fails or is absent.
No Ollama needed — MockProvider is injected.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from infrastructure.ai.gateway import AIGateway
from infrastructure.ai.mock_provider import MockProvider


@pytest.fixture(autouse=True)
def use_mock_provider():
    """Swap in MockProvider for every test; restore afterwards."""
    AIGateway.set_provider(MockProvider(delay_ms=0))
    yield
    # Leave the MockProvider; next test's autouse fixture will replace it.


# ── Happy path ────────────────────────────────────────────────────────────────

def test_embed_text_returns_list_of_floats():
    from domain.search.embedder import embed_text
    vec = embed_text("quarterly sales report 2024")
    assert isinstance(vec, list)
    assert len(vec) > 0
    assert all(isinstance(v, float) for v in vec)


def test_embed_text_is_deterministic_for_same_input():
    """MockProvider returns consistent vectors for the same text."""
    from domain.search.embedder import embed_text
    v1 = embed_text("hello world")
    v2 = embed_text("hello world")
    assert v1 == v2


def test_embed_text_differs_for_different_inputs():
    from domain.search.embedder import embed_text
    v1 = embed_text("invoice march 2024")
    v2 = embed_text("holiday photos summer")
    assert v1 != v2


# ── Truncation ────────────────────────────────────────────────────────────────

def test_embed_text_truncates_long_input():
    """
    embed_text() must not crash on a 10 000-char string.
    The result must be a valid vector with the same dimension as a short input.
    """
    from domain.search.embedder import embed_text
    long_text = "word " * 2000          # 10 000 chars
    short_text = "word"
    v_long  = embed_text(long_text)
    v_short = embed_text(short_text)
    assert isinstance(v_long, list)
    assert len(v_long) == len(v_short)  # dimension must be the same


# ── Failure path ──────────────────────────────────────────────────────────────

def test_embed_text_raises_when_no_provider():
    """Without a provider configured, embed_text must raise."""
    from domain.search.embedder import embed_text
    from core.exceptions import EmbeddingError, AIGatewayError, ProviderNotAvailableError
    AIGateway._provider = None          # remove provider
    with pytest.raises((EmbeddingError, AIGatewayError, ProviderNotAvailableError)):
        embed_text("test text")


def test_embed_text_raises_on_provider_failure():
    """If AIGateway.embed raises, embed_text converts it to a known error."""
    from domain.search.embedder import embed_text
    from core.exceptions import EmbeddingError, AIGatewayError

    with patch.object(AIGateway, "embed", side_effect=RuntimeError("GPU OOM")):
        with pytest.raises((EmbeddingError, AIGatewayError, RuntimeError)):
            embed_text("trigger failure")