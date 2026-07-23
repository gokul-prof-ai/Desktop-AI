"""
DesktopAI
Embedder

Turns text into a vector (a list of numbers) using a local Ollama
embedding model. Similar text produces similar vectors, which is
what makes semantic search possible: a search query gets embedded
the same way, and files whose vectors are closest to the query's
vector are the best matches.

This uses a separate, much smaller model than the one used for
classification/summarization (see config.EMBEDDING_MODEL), so it
stays fast even on low-end hardware.
"""

import requests

from core import config
from core.logger import get_logger

logger = get_logger("search")


def get_embedding(text: str, model: str = config.EMBEDDING_MODEL) -> list[float] | None:
    """
    Send text to the local Ollama server and return its embedding
    vector.

    Args:
        text (str):
            The text to embed. Should already be truncated to a
            reasonable length by the caller.
        model (str):
            Which Ollama embedding model to use. Defaults to
            config.EMBEDDING_MODEL. The model must already be
            pulled locally (run: ollama pull <model-name>).

    Returns:
        list[float] | None:
            The embedding vector, or None if the text is empty,
            Ollama isn't reachable, or the request otherwise
            failed. A None result means "embedding unavailable
            right now", not a crash — the rest of the app should
            keep working even if Ollama isn't running.
    """

    if not text or not text.strip():
        logger.info("No text provided for embedding; skipping.")
        return None

    try:
        response = requests.post(
            config.OLLAMA_EMBEDDINGS_URL,
            json={
                "model": model,
                "prompt": text,
            },
            timeout=config.OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        logger.warning(
            "Could not connect to Ollama at %s. Is Ollama installed and running?",
            config.OLLAMA_EMBEDDINGS_URL,
        )
        return None
    except requests.exceptions.Timeout:
        logger.warning(
            "Ollama embedding request timed out after %d seconds.",
            config.OLLAMA_TIMEOUT_SECONDS,
        )
        return None
    except requests.exceptions.RequestException as error:
        logger.warning("Ollama embedding request failed: %s", error)
        return None

    data = response.json()
    embedding = data.get("embedding")

    if not embedding:
        logger.warning(
            "Ollama response did not include the expected 'embedding' field."
        )
        return None

    logger.info(
        "Generated a %d-dimension embedding using model '%s'.", len(embedding), model
    )

    return embedding