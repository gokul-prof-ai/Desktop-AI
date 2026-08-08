"""
DesktopAI v2.0 — File Classifier
File: src/domain/classifier/classifier.py

Assigns a category to a FileInfo using a three-stage pipeline:

  Stage 1 — Memory check (fastest, ~0ms)
    Checks if the user has a saved preference for this file/extension.
    If yes, returns immediately. No AI call needed.

  Stage 2 — Fast rule check (~0ms)
    Checks extension and filename against categories.toml rules.
    Handles 80%+ of common files instantly.

  Stage 3 — AI classification (slowest, 1–5s)
    Sends file metadata + content snippet to the AI Gateway.
    Used only when stages 1 and 2 both fail to match.

This pipeline is the V2 fix for V1's classifier.py which:
- Called Ollama for EVERY file (including obvious ones like .pdf → PDFs)
- Never checked user preferences
- Had no confidence scoring for rule-based matches
"""

from __future__ import annotations

from core.exceptions import AIGatewayError
from core.logger import get_logger
from domain.scanner.file_info import AnalysisResult, FileInfo
from infrastructure.ai.gateway import AIGateway, GenerateRequest
from infrastructure.config.settings import Settings
from infrastructure.storage.memory_store import MemoryStore

logger = get_logger(__name__)

# Confidence scores assigned to each classification method.
# AI is not always the most confident — a rule match is deterministic.
_CONFIDENCE = {
    "memory":    1.00,   # User explicitly set this — always trust it
    "fast_rule": 0.95,   # Extension match is deterministic
    "ai":        0.85,   # AI is good but not perfect (overridden by model output)
    "fallback":  0.30,   # Last resort — low confidence, may need review
}

# Category used when nothing else matches.
_FALLBACK_CATEGORY = "Miscellaneous"

# Maximum characters of text content sent to the AI.
# Keeps prompts short and fast. The first 500 chars are usually enough.
_MAX_CONTENT_CHARS = 500


class FileClassifier:
    """
    Classifies files into categories using a three-stage pipeline.

    Usage:
        classifier = FileClassifier()
        result = classifier.classify(file_info)
        print(result.category)      # "Finance"
        print(result.confidence)    # 0.95
        print(result.method)        # "fast_rule"
    """

    def classify(self, file_info: FileInfo) -> AnalysisResult:
        """
        Classify a single file through the three-stage pipeline.

        Args:
            file_info: The FileInfo to classify.

        Returns:
            AnalysisResult with category, confidence, and method.
            Never raises — returns a fallback result on any error.
        """
        logger.debug("Classifying: %s", file_info.filename)

        # Stage 1 — Memory check
        result = self._check_memory(file_info)
        if result:
            return result

        # Stage 2 — Fast rule check
        result = self._check_fast_rules(file_info)
        if result:
            return result

        # Stage 3 — AI classification
        return self._classify_with_ai(file_info)

    def classify_batch(self, files: list[FileInfo]) -> list[AnalysisResult]:
        """
        Classify a list of files, emitting progress events as we go.

        Args:
            files: List of FileInfo objects to classify.

        Returns:
            List of AnalysisResult objects in the same order as input.
        """
        results = []
        total = len(files)

        for i, file_info in enumerate(files, 1):
            result = self.classify(file_info)
            results.append(result)

            # Emit progress for the GUI progress bar.
            self._emit_classified(result, i, total)

        return results

    # ── Stage 1: Memory check ──────────────────────────────────────────

    def _check_memory(self, file_info: FileInfo) -> AnalysisResult | None:
        """
        Check if the user has a saved preference for this file.

        This is the fix for V1's biggest miss: MemoryStore existed
        but was never consulted during classification.
        """
        try:
            # Check for a category override first (explicit user correction).
            category = MemoryStore.get_category_override(
                file_info.filename, file_info.extension
            )

            if not category:
                return None

            logger.debug(
                "Memory hit: %s → %s",
                file_info.filename, category,
            )

            enriched = file_info.with_category(
                category, _CONFIDENCE["memory"]
            )

            return AnalysisResult(
                file_info=enriched,
                category=category,
                confidence=_CONFIDENCE["memory"],
                method="memory",
            )

        except Exception as exc:
            logger.warning("Memory check failed for %s: %s", file_info.filename, exc)
            return None

    # ── Stage 2: Fast rule check ───────────────────────────────────────

    def _check_fast_rules(self, file_info: FileInfo) -> AnalysisResult | None:
        """
        Check extension and filename against rules in categories.toml.

        Tries extension match first (faster), then keyword match.
        """
        try:
            # Extension match — most reliable
            category = Settings.find_category_for_extension(file_info.extension)

            if not category:
                # Keyword match — checks filename against category keywords
                category = Settings.find_category_for_filename(file_info.filename)

            if not category:
                return None

            # Skip the catch-all Miscellaneous from fast rules —
            # let the AI try before we give up.
            if category == _FALLBACK_CATEGORY:
                return None

            logger.debug(
                "Fast rule hit: %s → %s",
                file_info.filename, category,
            )

            enriched = file_info.with_category(
                category, _CONFIDENCE["fast_rule"]
            )

            return AnalysisResult(
                file_info=enriched,
                category=category,
                confidence=_CONFIDENCE["fast_rule"],
                method="fast_rule",
            )

        except Exception as exc:
            logger.warning(
                "Fast rule check failed for %s: %s",
                file_info.filename, exc,
            )
            return None

    # ── Stage 3: AI classification ─────────────────────────────────────

    def _classify_with_ai(self, file_info: FileInfo) -> AnalysisResult:
        """
        Ask the AI Gateway to classify the file.

        Builds a prompt from the file's metadata and content snippet,
        sends it to the gateway, and parses the response.

        Falls back to Miscellaneous if the AI call fails.
        """
        category_names = [r.name for r in Settings.categories]
        prompt = self._build_prompt(file_info, category_names)

        try:
            response = AIGateway.generate(GenerateRequest(
                prompt=prompt,
                model_hint="fast",   # Use the faster model for classification
                temperature=0.1,     # Low temperature = deterministic output
                max_tokens=50,       # We only need the category name
            ))

            category = self._parse_ai_response(
                response.text, category_names
            )
            confidence = _CONFIDENCE["ai"]

            logger.debug(
                "AI classified: %s → %s (%.0f%%)",
                file_info.filename, category, confidence * 100,
            )

            enriched = file_info.with_category(category, confidence)

            return AnalysisResult(
                file_info=enriched,
                category=category,
                confidence=confidence,
                method="ai",
                model_used=response.model,
            )

        except AIGatewayError as exc:
            logger.warning(
                "AI classification failed for %s: %s — using fallback",
                file_info.filename, exc,
            )
            return self._fallback_result(file_info)

        except Exception as exc:
            logger.error(
                "Unexpected classification error for %s: %s",
                file_info.filename, exc,
                exc_info=True,
            )
            return self._fallback_result(file_info)

    def _build_prompt(
        self,
        file_info: FileInfo,
        category_names: list[str],
    ) -> str:
        """
        Build a concise classification prompt for the AI.

        Includes filename, extension, size, and a content snippet.
        Keeps it short so the fast model responds quickly.
        """
        categories_str = ", ".join(category_names)

        content_snippet = ""
        if file_info.has_text:
            snippet = file_info.text_content[:_MAX_CONTENT_CHARS].strip()
            content_snippet = f"\nContent preview: {snippet}"

        return (
            f"Classify this file into exactly one of these categories: "
            f"{categories_str}\n\n"
            f"File name: {file_info.filename}\n"
            f"Extension: {file_info.extension}\n"
            f"Size: {file_info.display_size}"
            f"{content_snippet}\n\n"
            f"Reply with ONLY the category name. No explanation. No punctuation."
        )

    def _parse_ai_response(
        self,
        response_text: str,
        valid_categories: list[str],
    ) -> str:
        """
        Extract the category name from the AI's response.

        The AI is prompted to return just a category name, but sometimes
        adds extra words. This method finds the best match.

        Args:
            response_text:    The raw AI response string.
            valid_categories: List of valid category names.

        Returns:
            The matched category name, or Miscellaneous if nothing matches.
        """
        cleaned = response_text.strip().strip(".,!?\"'")

        # Direct match (most common case)
        for cat in valid_categories:
            if cleaned.lower() == cat.lower():
                return cat

        # Partial match — AI might say "Finance category" instead of "Finance"
        for cat in valid_categories:
            if cat.lower() in cleaned.lower():
                return cat

        logger.warning(
            "AI returned unrecognized category: '%s' — using fallback",
            cleaned,
        )
        return _FALLBACK_CATEGORY

    def _fallback_result(self, file_info: FileInfo) -> AnalysisResult:
        """Return a low-confidence Miscellaneous result when all stages fail."""
        enriched = file_info.with_category(
            _FALLBACK_CATEGORY, _CONFIDENCE["fallback"]
        )
        return AnalysisResult(
            file_info=enriched,
            category=_FALLBACK_CATEGORY,
            confidence=_CONFIDENCE["fallback"],
            method="fallback",
        )

    # ── Event emission ─────────────────────────────────────────────────

    def _emit_classified(
        self,
        result: AnalysisResult,
        done: int,
        total: int,
    ) -> None:
        try:
            from core.events import AppEvents
            AppEvents.file_classified.emit(
                str(result.file_info.path),
                result.category,
                result.confidence,
            )
            AppEvents.scan_progress.emit(done, total)
        except Exception:
            pass