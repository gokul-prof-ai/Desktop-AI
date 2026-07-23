"""
DesktopAI
Ollama Client

Sends prompts to a locally running Ollama server and returns the
model's response. This lets DesktopAI use a local, offline LLM for
classification, summarization, and recommendations in later phases.
"""

import requests

from core.logger import get_logger

logger = get_logger("ai")

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2"
REQUEST_TIMEOUT_SECONDS = 60


def generate_response(prompt: str, model: str = DEFAULT_MODEL) -> str | None:
    """
    Send a prompt to the local Ollama server and return its response.

    Args:
        prompt (str):
            The text prompt to send to the model.
        model (str):
            Which Ollama model to use. Defaults to "llama3.2".
            The model must already be pulled locally
            (run: ollama pull llama3.2).

    Returns:
        str | None:
            The model's text response, or None if Ollama isn't
            running, isn't reachable, or the request otherwise
            failed. A None result means "AI unavailable right now",
            not a crash — the rest of the app should keep working
            even if Ollama isn't running.
    """

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        logger.warning(
            "Could not connect to Ollama at %s. Is Ollama installed and running?",
            OLLAMA_URL,
        )
        return None
    except requests.exceptions.Timeout:
        logger.warning("Ollama request timed out after %d seconds.", REQUEST_TIMEOUT_SECONDS)
        return None
    except requests.exceptions.RequestException as error:
        logger.warning("Ollama request failed: %s", error)
        return None

    data = response.json()
    text = data.get("response")

    if text is None:
        logger.warning("Ollama response did not include the expected 'response' field.")
        return None

    logger.info("Ollama returned %d character(s) using model '%s'.", len(text), model)

    return text.strip()