"""
DesktopAI v2.0 — Search Embedder
File: src/domain/search/embedder.py

Converts text into a vector (a list of numbers) by routing through
the AIGateway. This replaces the old embedder.py that called Ollama
directly via requests.post — the domain layer must never talk to
Ollama (or any AI provider) directly.

Why this matters:
    - Tests can inject MockProvider — no Ollama required to run tests.
    - Swapping the embedding model (e.g. Ollama → OpenAI) requires
      changing one line in main.py, not touching this file.
    - The old embedder silently returned None on failure. This one
      raises a clear exception so callers can decide how to handle it.

Usage:
    from domain.search.embedder import embed_text

    vector = embed_text("tax return for 2024")
    # Returns list[float], or raises EmbeddingError
"""

from __future__ import annotations

from infrastructure.ai.gateway import AIGateway, EmbedRequest
from core.exceptions import AIGatewayError
from core.logger import get_logger

logger = get_logger(__name__)

# Maximum characters of text to send for embedding.
# Embedding models have token limits (~512 tokens ≈ 2000 chars).
# Text longer than this is truncated — the beginning of a document
# usually contains the most identifying information anyway.
MAX_EMBED_CHARS = 2000


def embed_text(text: str, model: str | None = None) -> list[float]:
    """
    Convert text to a vector embedding via the active AI provider.

    Args:
        text:
            The text to embed. Will be stripped and truncated to
            MAX_EMBED_CHARS automatically.
        model:
            Optional override for the embedding model. If None,
            the provider uses its default embedding model (usually
            whatever is set in Settings.search.embedding_model).

    Returns:
        list[float]: The embedding vector.

    Raises:
        ValueError:      If text is empty or whitespace-only.
        AIGatewayError:  If the provider is unavailable or fails.
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text.")

    truncated = text.strip()[:MAX_EMBED_CHARS]

    logger.debug("Embedding %d chars (original: %d chars)", len(truncated), len(text))

    request = EmbedRequest(text=truncated, model=model)

    try:
        response = AIGateway.embed(request)
    except AIGatewayError:
        raise  # Already the right type — let the caller handle it
    except Exception as exc:
        # Shouldn't happen (gateway wraps everything), but be safe
        raise AIGatewayError(f"Unexpected error during embedding: {exc}") from exc

    logger.debug(
        "Embedding complete: %d-dimensional vector from model '%s'",
        response.dimension,
        response.model,
    )

    return response.vector