"""
DesktopAI v2.0 — Mock AI Provider
File: src/infrastructure/ai/mock_provider.py

A fake AI provider for testing and development.

Why this exists:
    - Unit tests must run without Ollama installed or running.
    - You can develop and test the UI with instant AI responses.
    - CI/CD pipelines (GitHub Actions) have no GPU or Ollama.

Usage in tests:
    from infrastructure.ai.gateway import AIGateway
    from infrastructure.ai.mock_provider import MockProvider

    AIGateway.set_provider(MockProvider())
    response = AIGateway.generate(GenerateRequest(prompt="test"))
    assert response.text == "Finance"   # returns preset response

Usage for UI development (fast, no waiting):
    AIGateway.set_provider(MockProvider(delay_ms=200))
"""

from __future__ import annotations

import time
from typing import Iterator

from infrastructure.ai.gateway import (
    AIProvider,
    GenerateRequest,
    GenerateResponse,
    EmbedRequest,
    EmbedResponse,
)
from core.logger import get_logger

logger = get_logger(__name__)


class MockProvider(AIProvider):
    """
    Fake AI provider that returns preset responses instantly.

    Args:
        default_response: Text returned for every generate() call.
                          Defaults to "Finance" (a valid category name
                          so classifier tests pass automatically).
        delay_ms:         Milliseconds to wait before returning.
                          Use 0 for instant responses in tests.
                          Use 200-500 to simulate realistic latency in UI dev.
        embedding_dim:    Dimension of fake embedding vectors. Default 384
                          matches all-MiniLM-L6-v2.
        fail_after:       If set, raises ProviderNotAvailableError after
                          this many successful calls. Used to test error handling.
    """

    def __init__(
        self,
        default_response: str = "Finance",
        delay_ms: float = 0,
        embedding_dim: int = 384,
        fail_after: int | None = None,
    ) -> None:
        self._default_response = default_response
        self._delay_ms = delay_ms
        self._embedding_dim = embedding_dim
        self._fail_after = fail_after
        self._call_count = 0

        # Preset responses: map a keyword in the prompt to a custom response.
        # Example: MockProvider().set_response("invoice", "Finance")
        self._preset_responses: dict[str, str] = {}

        logger.info(
            "MockProvider initialized — response='%s' delay=%dms",
            default_response, delay_ms,
        )

    @property
    def provider_name(self) -> str:
        return "MockProvider"

    def set_response(self, keyword: str, response: str) -> None:
        """
        Register a keyword → response mapping.

        If the prompt contains `keyword`, generate() returns `response`
        instead of the default.

        Example:
            mock = MockProvider()
            mock.set_response("invoice", "Finance")
            mock.set_response("photo", "Images")
        """
        self._preset_responses[keyword.lower()] = response

    def health_check(self) -> bool:
        """Mock is always healthy."""
        return True

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Return a preset or default response after optional delay."""
        self._call_count += 1
        self._maybe_fail()

        if self._delay_ms > 0:
            time.sleep(self._delay_ms / 1000)

        # Check for keyword matches in the prompt.
        prompt_lower = request.prompt.lower()
        response_text = self._default_response

        for keyword, preset in self._preset_responses.items():
            if keyword in prompt_lower:
                response_text = preset
                break

        logger.debug(
            "MockProvider.generate() → '%s' (call #%d)",
            response_text, self._call_count,
        )

        return GenerateResponse(
            text=response_text,
            model="mock-model",
            input_tokens=len(request.prompt.split()),
            output_tokens=len(response_text.split()),
            duration_ms=self._delay_ms,
        )

    def embed(self, request: EmbedRequest) -> EmbedResponse:
        """Return a deterministic fake embedding vector."""
        self._call_count += 1
        self._maybe_fail()

        if self._delay_ms > 0:
            time.sleep(self._delay_ms / 1000)

        # Generate a deterministic vector based on text hash.
        # Same text always produces the same vector — useful for tests.
        seed = hash(request.text) % 10000
        vector = [
            ((seed + i) % 100) / 100.0
            for i in range(self._embedding_dim)
        ]

        return EmbedResponse(
            vector=vector,
            model="mock-embedder",
        )

    def stream(self, request: GenerateRequest) -> Iterator[str]:
        """Yield the response word by word to simulate streaming."""
        response = self.generate(request)
        words = response.text.split()
        for i, word in enumerate(words):
            if self._delay_ms > 0:
                time.sleep(self._delay_ms / 1000 / len(words))
            yield word + (" " if i < len(words) - 1 else "")

    def _maybe_fail(self) -> None:
        """Raise an error if fail_after threshold is reached."""
        if self._fail_after is not None and self._call_count > self._fail_after:
            from core.exceptions import ProviderNotAvailableError
            raise ProviderNotAvailableError(
                f"MockProvider deliberately failing after {self._fail_after} calls."
            )

    @property
    def call_count(self) -> int:
        """How many times generate() or embed() has been called."""
        return self._call_count

    def reset(self) -> None:
        """Reset call count and preset responses. Useful between tests."""
        self._call_count = 0
        self._preset_responses.clear()