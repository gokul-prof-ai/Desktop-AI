"""
DesktopAI v2.0 — AI Gateway
File: src/infrastructure/ai/gateway.py

The single point of contact between the domain layer and any AI provider.

How it works:
    1. Every domain module imports AIGateway (this file).
    2. AIGateway holds a reference to the active AIProvider.
    3. The provider is set once at startup in main.py.
    4. Domain modules call AIGateway.generate() or AIGateway.embed().
    5. They never know or care whether Ollama, OpenAI, or Mock is running.

Adding a new AI provider in the future:
    1. Create a new file: src/infrastructure/ai/my_provider.py
    2. Subclass AIProvider and implement generate() and embed().
    3. Set it in main.py: AIGateway.set_provider(MyProvider())
    4. Zero changes needed in any domain module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator

from core.exceptions import AIGatewayError, ProviderNotAvailableError
from core.logger import get_logger

logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE DATACLASSES
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class GenerateRequest:
    """
    Everything needed to ask the AI to generate text.

    Args:
        prompt:      The full prompt text sent to the model.
        model_hint:  "default" uses Settings.ai.model.
                     "fast"    uses Settings.ai.model_fast.
                     "vision"  uses a vision-capable model (Phase 4).
                     Any other string is treated as an explicit model name.
        temperature: Controls randomness. 0.0 = deterministic, 1.0 = creative.
        max_tokens:  Maximum number of tokens in the response. None = provider default.
        system:      Optional system prompt prepended before the user prompt.
    """
    prompt: str
    model_hint: str = "default"
    temperature: float = 0.1
    max_tokens: int | None = None
    system: str | None = None


@dataclass
class GenerateResponse:
    """
    The AI's response to a GenerateRequest.

    Args:
        text:         The generated text content.
        model:        The actual model name that produced this response.
        input_tokens: Approximate input token count (for monitoring).
        output_tokens: Approximate output token count (for monitoring).
        duration_ms:  How long the provider took to respond, in milliseconds.
    """
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: float = 0.0


@dataclass
class EmbedRequest:
    """
    A request to convert text into a vector embedding.

    Args:
        text:  The text to embed. Keep under ~512 tokens for best results.
        model: Override embedding model. None = use Settings.search.embedding_model.
    """
    text: str
    model: str | None = None


@dataclass
class EmbedResponse:
    """
    The vector embedding returned by the provider.

    Args:
        vector:    The embedding as a list of floats.
        model:     The model that produced the embedding.
        dimension: Length of the vector (same as len(vector)).
    """
    vector: list[float]
    model: str
    dimension: int = field(init=False)

    def __post_init__(self) -> None:
        self.dimension = len(self.vector)


# ══════════════════════════════════════════════════════════════════════════
# ABSTRACT PROVIDER INTERFACE
# ══════════════════════════════════════════════════════════════════════════

class AIProvider(ABC):
    """
    Abstract base class for all AI providers.

    To add a new provider:
        1. Create a subclass of AIProvider.
        2. Implement generate() and embed().
        3. Optionally implement health_check() and stream().
        4. Set it as the active provider: AIGateway.set_provider(MyProvider())
    """

    @abstractmethod
    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        Send a prompt and return the model's response.
        Must raise AIGatewayError (or a subclass) on failure.
        Must never return None.
        """

    @abstractmethod
    def embed(self, request: EmbedRequest) -> EmbedResponse:
        """
        Convert text to a vector embedding.
        Must raise AIGatewayError (or a subclass) on failure.
        """

    def health_check(self) -> bool:
        """
        Return True if the provider is reachable and ready.
        Override in each provider for a real connectivity check.
        Default implementation returns True (assumes always available).
        """
        return True

    def stream(self, request: GenerateRequest) -> Iterator[str]:
        """
        Stream the response token by token.
        Override in providers that support streaming.
        Default falls back to generate() and yields the full text at once.
        """
        response = self.generate(request)
        yield response.text

    @property
    def provider_name(self) -> str:
        """Human-readable name for logging and UI display."""
        return self.__class__.__name__


# ══════════════════════════════════════════════════════════════════════════
# GATEWAY
# ══════════════════════════════════════════════════════════════════════════

class _AIGateway:
    """
    The active gateway that routes AI requests to the current provider.

    Access via the module-level `AIGateway` singleton.
    Never instantiate this class directly.

    Startup sequence (in main.py):
        from infrastructure.ai.ollama_provider import OllamaProvider
        from infrastructure.ai.gateway import AIGateway
        AIGateway.set_provider(OllamaProvider())

    Domain usage:
        from infrastructure.ai.gateway import AIGateway

        response = AIGateway.generate(GenerateRequest(
            prompt="Classify this file: budget_2026.xlsx",
            model_hint="fast",
        ))
        print(response.text)
    """

    def __init__(self) -> None:
        self._provider: AIProvider | None = None

    # ── Provider management ────────────────────────────────────────────

    def set_provider(self, provider: AIProvider) -> None:
        """
        Set the active AI provider.

        Call once at startup. Can be called again to hot-swap providers
        (for example, switching from Ollama to Mock in tests).

        Args:
            provider: Any object that subclasses AIProvider.
        """
        self._provider = provider
        logger.info("AI provider set: %s", provider.provider_name)

    def get_provider(self) -> AIProvider:
        """
        Return the active provider, or raise if none has been set.
        """
        if self._provider is None:
            raise ProviderNotAvailableError(
                "No AI provider has been configured. "
                "Call AIGateway.set_provider() before using the gateway."
            )
        return self._provider

    @property
    def is_ready(self) -> bool:
        """True if a provider is set and reports itself as healthy."""
        if self._provider is None:
            return False
        try:
            return self._provider.health_check()
        except Exception:
            return False

    # ── Core operations ────────────────────────────────────────────────

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        Send a text generation request to the active provider.

        Args:
            request: A GenerateRequest with prompt and options.

        Returns:
            GenerateResponse with the model's text output.

        Raises:
            ProviderNotAvailableError: If no provider is set.
            AIGatewayError:            If the provider fails.
        """
        provider = self.get_provider()

        logger.debug(
            "generate() → provider=%s model_hint=%s prompt_len=%d",
            provider.provider_name,
            request.model_hint,
            len(request.prompt),
        )

        try:
            response = provider.generate(request)
            logger.debug(
                "generate() ← %d chars in %.0fms",
                len(response.text),
                response.duration_ms,
            )
            return response

        except AIGatewayError:
            raise  # Re-raise as-is — already the right type

        except Exception as exc:
            # Wrap unexpected errors so callers only need to catch AIGatewayError
            logger.error("Unexpected error from provider: %s", exc, exc_info=True)
            raise AIGatewayError(
                f"Provider {provider.provider_name} raised an unexpected error: {exc}"
            ) from exc

    def embed(self, request: EmbedRequest) -> EmbedResponse:
        """
        Convert text to a vector embedding using the active provider.

        Args:
            request: An EmbedRequest with the text to embed.

        Returns:
            EmbedResponse with the vector and dimension.

        Raises:
            ProviderNotAvailableError: If no provider is set.
            EmbeddingError:            If embedding generation fails.
        """
        provider = self.get_provider()

        logger.debug(
            "embed() → provider=%s text_len=%d",
            provider.provider_name,
            len(request.text),
        )

        try:
            response = provider.embed(request)
            logger.debug(
                "embed() ← dimension=%d",
                response.dimension,
            )
            return response

        except AIGatewayError:
            raise

        except Exception as exc:
            logger.error("Unexpected embedding error: %s", exc, exc_info=True)
            raise AIGatewayError(
                f"Provider {provider.provider_name} raised an unexpected error: {exc}"
            ) from exc

    def stream(self, request: GenerateRequest) -> Iterator[str]:
        """
        Stream a text generation response token by token.

        Args:
            request: A GenerateRequest with prompt and options.

        Yields:
            str: Successive chunks of the model's response.
        """
        provider = self.get_provider()
        yield from provider.stream(request)

    def health_check(self) -> bool:
        """
        Check if the active provider is reachable.

        Returns:
            True if healthy, False if not reachable or no provider set.
        """
        return self.is_ready


# ── Singleton ──────────────────────────────────────────────────────────────
AIGateway = _AIGateway()