"""
DesktopAI v2.0 — Ollama AI Provider
File: src/infrastructure/ai/ollama_provider.py

Implements the AIProvider interface for Ollama.

This is the production provider — the one used when the real app runs.
It replaces V1's src/ai/ollama_client.py with a clean implementation
that talks to AIGateway instead of being called directly.

V1 ollama_client.py is NOT deleted — it still serves V1 modules.
This file is the V2 replacement that V2 modules will use.
"""

from __future__ import annotations

import time
import requests

from infrastructure.ai.gateway import (
    AIProvider,
    GenerateRequest,
    GenerateResponse,
    EmbedRequest,
    EmbedResponse,
)
from infrastructure.config.settings import Settings
from core.exceptions import (
    ProviderNotAvailableError,
    ProviderTimeoutError,
    ProviderResponseError,
    ModelNotFoundError,
    EmbeddingError,
)
from core.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(AIProvider):
    """
    AI provider backed by a locally running Ollama server.

    Ollama must be running and the required models must be pulled
    before this provider can be used.

    Check Ollama status: http://localhost:11434
    Pull a model:        ollama pull llama3.2
    """

    def __init__(self) -> None:
        # Read host and timeout from Settings — never hardcoded.
        self._host: str = Settings.ai.host
        self._timeout: int = Settings.ai.timeout
        self._max_retries: int = Settings.ai.max_retries

        # Resolve model hints to actual model names.
        self._model_map: dict[str, str] = {
            "default": Settings.ai.model,
            "fast":    Settings.ai.model_fast,
        }

        logger.info(
            "OllamaProvider initialized — host=%s model=%s fast=%s",
            self._host,
            Settings.ai.model,
            Settings.ai.model_fast,
        )

    @property
    def provider_name(self) -> str:
        return "OllamaProvider"

    # ── Model resolution ───────────────────────────────────────────────

    def _resolve_model(self, hint: str) -> str:
        """
        Convert a model hint to an actual Ollama model string.

        "default" → Settings.ai.model     (e.g. "llama3.2")
        "fast"    → Settings.ai.model_fast (e.g. "llama3.2:1b")
        anything else → used as-is (e.g. "llava", "mistral")
        """
        return self._model_map.get(hint, hint)

    # ── Health check ───────────────────────────────────────────────────

    def health_check(self) -> bool:
        """
        Return True if the Ollama server is reachable.
        Sends a lightweight GET to the root endpoint.
        """
        try:
            response = requests.get(
                self._host,
                timeout=5,
            )
            is_healthy = response.status_code == 200
            if not is_healthy:
                logger.warning(
                    "Ollama health check failed — status %d",
                    response.status_code,
                )
            return is_healthy
        except requests.exceptions.ConnectionError:
            logger.warning("Ollama not reachable at %s", self._host)
            return False
        except Exception as exc:
            logger.warning("Ollama health check error: %s", exc)
            return False

    # ── Generate ───────────────────────────────────────────────────────

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        Send a prompt to Ollama and return the response.

        Retries up to Settings.ai.max_retries times on transient failures.
        Raises ProviderTimeoutError if every attempt times out.
        Raises ProviderNotAvailableError if Ollama is not running.
        """
        model = self._resolve_model(request.model_hint)

        # Build the Ollama /api/generate payload.
        payload: dict = {
            "model":  model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
            },
        }

        if request.system:
            payload["system"] = request.system

        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        url = Settings.ai.api_url
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.debug(
                    "Ollama generate attempt %d/%d — model=%s",
                    attempt, self._max_retries, model,
                )

                start = time.perf_counter()
                http_response = requests.post(
                    url,
                    json=payload,
                    timeout=self._timeout,
                )
                duration_ms = (time.perf_counter() - start) * 1000

                # Handle HTTP errors.
                if http_response.status_code == 404:
                    raise ModelNotFoundError(
                        f"Model '{model}' not found in Ollama. "
                        f"Run: ollama pull {model}"
                    )

                if http_response.status_code != 200:
                    raise ProviderResponseError(
                        f"Ollama returned HTTP {http_response.status_code}: "
                        f"{http_response.text[:200]}"
                    )

                # Parse the JSON response.
                try:
                    data = http_response.json()
                except Exception as parse_exc:
                    raise ProviderResponseError(
                        f"Ollama response could not be parsed as JSON: {parse_exc}"
                    ) from parse_exc

                text = data.get("response", "").strip()

                if not text:
                    raise ProviderResponseError(
                        "Ollama returned an empty response."
                    )

                return GenerateResponse(
                    text=text,
                    model=model,
                    input_tokens=data.get("prompt_eval_count", 0),
                    output_tokens=data.get("eval_count", 0),
                    duration_ms=duration_ms,
                )

            except (ProviderResponseError, ModelNotFoundError):
                raise  # Don't retry these — they won't self-heal

            except requests.exceptions.Timeout as exc:
                logger.warning(
                    "Ollama timeout on attempt %d/%d",
                    attempt, self._max_retries,
                )
                last_error = exc

            except requests.exceptions.ConnectionError as exc:
                logger.warning(
                    "Ollama connection error on attempt %d/%d: %s",
                    attempt, self._max_retries, exc,
                )
                last_error = exc

            except Exception as exc:
                logger.error(
                    "Unexpected error on attempt %d/%d: %s",
                    attempt, self._max_retries, exc,
                )
                last_error = exc

        # All retries exhausted.
        if isinstance(last_error, requests.exceptions.Timeout):
            raise ProviderTimeoutError(
                f"Ollama did not respond within {self._timeout}s "
                f"after {self._max_retries} attempts."
            ) from last_error

        raise ProviderNotAvailableError(
            f"Could not connect to Ollama at {self._host} "
            f"after {self._max_retries} attempts. "
            f"Is Ollama running? Last error: {last_error}"
        ) from last_error

    # ── Embed ──────────────────────────────────────────────────────────

    def embed(self, request: EmbedRequest) -> EmbedResponse:
        """
        Generate a vector embedding using Ollama's /api/embeddings endpoint.

        The embedding model defaults to Settings.search.embedding_model.
        This is separate from the generation model.
        """
        model = request.model or Settings.search.embedding_model

        payload = {
            "model":  model,
            "prompt": request.text,
        }

        url = Settings.ai.embed_url

        try:
            start = time.perf_counter()
            http_response = requests.post(
                url,
                json=payload,
                timeout=self._timeout,
            )
            duration_ms = (time.perf_counter() - start) * 1000

            if http_response.status_code == 404:
                raise ModelNotFoundError(
                    f"Embedding model '{model}' not found in Ollama. "
                    f"Run: ollama pull {model}"
                )

            if http_response.status_code != 200:
                raise EmbeddingError(
                    f"Ollama embeddings returned HTTP {http_response.status_code}"
                )

            data = http_response.json()
            vector = data.get("embedding", [])

            if not vector:
                raise EmbeddingError(
                    "Ollama returned an empty embedding vector."
                )

            logger.debug(
                "embed() ← dim=%d model=%s %.0fms",
                len(vector), model, duration_ms,
            )

            return EmbedResponse(vector=vector, model=model)

        except (EmbeddingError, ModelNotFoundError):
            raise

        except requests.exceptions.Timeout as exc:
            raise ProviderTimeoutError(
                f"Ollama embedding timed out after {self._timeout}s"
            ) from exc

        except requests.exceptions.ConnectionError as exc:
            raise ProviderNotAvailableError(
                f"Cannot reach Ollama at {self._host}"
            ) from exc

        except Exception as exc:
            raise EmbeddingError(
                f"Unexpected error during embedding: {exc}"
            ) from exc

    # ── Stream ─────────────────────────────────────────────────────────

    def stream(self, request: GenerateRequest):
        """
        Stream a response from Ollama token by token.

        Yields successive text chunks as they arrive.
        Used by ChatView for real-time streaming display.
        """
        model = self._resolve_model(request.model_hint)

        payload = {
            "model":  model,
            "prompt": request.prompt,
            "stream": True,          # Enable streaming
            "options": {
                "temperature": request.temperature,
            },
        }

        if request.system:
            payload["system"] = request.system

        url = Settings.ai.api_url

        try:
            with requests.post(
                url,
                json=payload,
                stream=True,
                timeout=self._timeout,
            ) as http_response:

                if http_response.status_code != 200:
                    raise ProviderResponseError(
                        f"Ollama stream returned HTTP {http_response.status_code}"
                    )

                import json
                for line in http_response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.ConnectionError as exc:
            raise ProviderNotAvailableError(
                f"Cannot reach Ollama at {self._host}"
            ) from exc