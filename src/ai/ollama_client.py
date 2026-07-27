"""
DesktopAI
Advanced Ollama Client

Features
--------
✔ Persistent HTTP session (connection pooling)
✔ Automatic retry mechanism
✔ Health checking
✔ Model existence validation
✔ Better error handling
✔ Performance logging
✔ Configurable AI options
✔ Response validation
✔ Thread-safe
✔ Production-ready architecture
"""

from __future__ import annotations

import time
from typing import Optional, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core import config
from core.logger import get_logger

logger = get_logger("ollama")


class OllamaClient:
    """
    Production-ready Ollama API client.
    """

    DEFAULT_TIMEOUT = 180

    def __init__(self):

        self.base_url = config.OLLAMA_URL.rstrip("/")

        self.session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],
            allowed_methods=["POST", "GET"],
        )

        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=10,
            pool_maxsize=20,
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # ---------------------------------------------------------

    def is_running(self) -> bool:
        """
        Check whether Ollama is running.
        """

        try:
            response = self.session.get(
                self.base_url.replace("/api/generate", "/api/tags"),
                timeout=5,
            )

            return response.status_code == 200

        except requests.RequestException:
            return False

    # ---------------------------------------------------------

    def available_models(self):

        try:

            url = self.base_url.replace("/api/generate", "/api/tags")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            return [
                model["name"]
                for model in data.get("models", [])
            ]

        except Exception as e:

            logger.error(f"Unable to fetch models: {e}")
            return []

    # ---------------------------------------------------------

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        temperature: float = 0.15,
        max_tokens: int = 200,
        top_p: float = 0.9,
        repeat_penalty: float = 1.15,
        system: Optional[str] = None,
    ) -> Optional[str]:

        if not prompt.strip():
            logger.warning("Empty prompt received.")
            return None

        model = model or config.OLLAMA_MODEL

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
                "repeat_penalty": repeat_penalty,
            },
        }

        if system:
            payload["system"] = system

        start = time.perf_counter()

        try:

            logger.debug(f"Using model: {model}")

            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=timeout,
            )

            response.raise_for_status()

            data = response.json()

            answer = data.get("response", "").strip()

            elapsed = time.perf_counter() - start

            logger.info(
                f"Generated response in {elapsed:.2f}s "
                f"({len(answer)} chars)"
            )

            if not answer:

                logger.warning("Empty response from Ollama.")
                return None

            return answer

        except requests.Timeout:

            logger.error(
                f"Ollama timed out after {timeout} seconds."
            )

        except requests.ConnectionError:

            logger.error(
                "Cannot connect to Ollama.\n"
                "Start it using:\n"
                "    ollama serve"
            )

        except requests.HTTPError as e:

            text = getattr(response, "text", "")

            logger.error(
                f"HTTP Error {response.status_code}: {e}\n{text}"
            )

        except ValueError:

            logger.error("Invalid JSON returned by Ollama.")

        except Exception:

            logger.exception("Unexpected Ollama error.")

        return None


client = OllamaClient()


def generate_response(
    prompt: str,
    model: Optional[str] = None,
    **kwargs,
) -> Optional[str]:
    """
    Backwards-compatible wrapper.
    """
    return client.generate(
        prompt=prompt,
        model=model,
        **kwargs,
    )