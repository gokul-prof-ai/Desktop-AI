"""
DesktopAI v2.0 — Settings Service
File: src/infrastructure/config/settings.py

The single source of truth for all runtime configuration.

Replaces V1's flat src/core/config.py with a proper service that:
- Reads config/app.toml and config/categories.toml at startup
- Provides typed getters for every setting
- Writes user changes back to app.toml
- Emits AppEvents.settings_changed when settings are saved
- Falls back to safe defaults if a key is missing from the TOML file

Usage anywhere in the codebase:
    from infrastructure.config.settings import Settings

    model = Settings.ai.model
    Settings.ai.model = "llama3.2:1b"
    Settings.save()
"""

from __future__ import annotations

import toml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from core.constants import DEFAULT_APP_TOML, DEFAULT_CATEGORIES_TOML
from core.exceptions import ConfigFileNotFoundError, ConfigValidationError
from core.logger import get_logger

logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════════════════════
# TYPED SETTINGS SECTIONS
# Each dataclass maps to one [section] in app.toml
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class AppSettings:
    name: str = "DesktopAI"
    version: str = "2.0.0"
    theme: str = "dark"
    first_run: bool = True


@dataclass
class AISettings:
    model: str = "llama3.2"
    model_fast: str = "llama3.2:1b"
    host: str = "http://localhost:11434"
    timeout: int = 60
    max_retries: int = 3

    @property
    def api_url(self) -> str:
        """Full Ollama generate endpoint URL."""
        return f"{self.host}/api/generate"

    @property
    def embed_url(self) -> str:
        """Full Ollama embeddings endpoint URL."""
        return f"{self.host}/api/embeddings"


@dataclass
class ScannerSettings:
    max_depth: int = 10
    max_workers: int = 4
    skip_hidden: bool = True
    skip_system: bool = True


@dataclass
class OCRSettings:
    enabled: bool = True
    engine: str = "tesseract"
    languages: list[str] = field(default_factory=lambda: ["eng"])


@dataclass
class SearchSettings:
    max_results: int = 50
    min_score: float = 0.3
    embedding_model: str = "all-MiniLM-L6-v2"


@dataclass
class StorageSettings:
    db_filename: str = "desktop_ai.db"


@dataclass
class LoggingSettings:
    level: str = "WARNING"
    max_mb: int = 5
    backup_count: int = 3


@dataclass
class WindowSettings:
    width: int = 1280
    height: int = 800
    remember_geometry: bool = True


# ══════════════════════════════════════════════════════════════════════════
# CATEGORY RULE
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class CategoryRule:
    """
    Represents one entry from config/categories.toml.

    Example:
        CategoryRule(
            name="Finance",
            extensions={".xlsx", ".xls", ".csv"},
            keywords={"invoice", "receipt", "payment"},
        )
    """
    name: str
    extensions: frozenset[str] = field(default_factory=frozenset)
    keywords: frozenset[str] = field(default_factory=frozenset)

    def matches_extension(self, ext: str) -> bool:
        """Return True if the file extension matches this category."""
        return ext.lower() in self.extensions

    def matches_filename(self, filename: str) -> bool:
        """Return True if any keyword appears in the filename."""
        lower = filename.lower()
        return any(kw in lower for kw in self.keywords)


# ══════════════════════════════════════════════════════════════════════════
# SETTINGS SERVICE
# ══════════════════════════════════════════════════════════════════════════

class _Settings:
    """
    Application settings service.

    Access via the module-level `Settings` singleton.
    Never instantiate this class directly.
    """

    def __init__(self) -> None:
        self._config_path: Path = DEFAULT_APP_TOML
        self._categories_path: Path = DEFAULT_CATEGORIES_TOML
        self._raw: dict[str, Any] = {}

        # Typed section objects — populated by load()
        self.app: AppSettings = AppSettings()
        self.ai: AISettings = AISettings()
        self.scanner: ScannerSettings = ScannerSettings()
        self.ocr: OCRSettings = OCRSettings()
        self.search: SearchSettings = SearchSettings()
        self.storage: StorageSettings = StorageSettings()
        self.logging: LoggingSettings = LoggingSettings()
        self.window: WindowSettings = WindowSettings()

        # Category rules from categories.toml
        self.categories: list[CategoryRule] = []

        self._loaded: bool = False

    # ── Loading ────────────────────────────────────────────────────────

    def load(
        self,
        config_path: Path | None = None,
        categories_path: Path | None = None,
    ) -> None:
        """
        Load settings from TOML files.

        Call once at startup (in main.py). If the files do not exist,
        they are created from built-in defaults automatically.

        Args:
            config_path:      Override path to app.toml.
            categories_path:  Override path to categories.toml.
        """
        if config_path:
            self._config_path = config_path
        if categories_path:
            self._categories_path = categories_path

        self._ensure_config_files_exist()
        self._load_app_toml()
        self._load_categories_toml()
        self._loaded = True

        logger.info(
            "Settings loaded — model=%s host=%s workers=%d",
            self.ai.model,
            self.ai.host,
            self.scanner.max_workers,
        )

    def _ensure_config_files_exist(self) -> None:
        """Create default TOML files if they don't exist yet."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._config_path.exists():
            logger.warning(
                "app.toml not found at %s — creating defaults",
                self._config_path,
            )
            self._write_default_app_toml()

        if not self._categories_path.exists():
            logger.warning(
                "categories.toml not found at %s — creating defaults",
                self._categories_path,
            )
            self._write_default_categories_toml()

    def _load_app_toml(self) -> None:
        """Parse app.toml into typed dataclass instances."""
        try:
            self._raw = toml.load(self._config_path)
        except Exception as exc:
            raise ConfigValidationError(
                f"Cannot parse {self._config_path}: {exc}"
            ) from exc

        def _section(key: str) -> dict[str, Any]:
            return self._raw.get(key, {})

        # Merge TOML values into dataclasses.
        # Missing keys fall back to dataclass defaults — no KeyError.
        self.app     = _merge(AppSettings,     _section("app"))
        self.ai      = _merge(AISettings,      _section("ai"))
        self.scanner = _merge(ScannerSettings, _section("scanner"))
        self.ocr     = _merge(OCRSettings,     _section("ocr"))
        self.search  = _merge(SearchSettings,  _section("search"))
        self.storage = _merge(StorageSettings, _section("storage"))
        self.logging = _merge(LoggingSettings, _section("logging"))
        self.window  = _merge(WindowSettings,  _section("window"))

    def _load_categories_toml(self) -> None:
        """Parse categories.toml into CategoryRule objects."""
        try:
            raw = toml.load(self._categories_path)
        except Exception as exc:
            raise ConfigValidationError(
                f"Cannot parse {self._categories_path}: {exc}"
            ) from exc

        cats_raw = raw.get("categories", {})
        self.categories = []

        for name, rules in cats_raw.items():
            self.categories.append(CategoryRule(
                name=name,
                extensions=frozenset(rules.get("extensions", [])),
                keywords=frozenset(rules.get("keywords", [])),
            ))

        logger.info("Loaded %d category rules", len(self.categories))

    # ── Saving ─────────────────────────────────────────────────────────

    def save(self) -> None:
        """
        Write current settings back to app.toml.

        Call after the user changes a setting in the Settings view.
        Emits AppEvents.settings_changed so the UI can react.
        """
        data = {
            "app":     _to_dict(self.app),
            "ai":      _to_dict(self.ai),
            "scanner": _to_dict(self.scanner),
            "ocr":     _to_dict(self.ocr),
            "search":  _to_dict(self.search),
            "storage": _to_dict(self.storage),
            "logging": _to_dict(self.logging),
            "window":  _to_dict(self.window),
        }

        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                toml.dump(data, f)
        except Exception as exc:
            logger.error("Failed to save settings: %s", exc)
            raise

        logger.info("Settings saved to %s", self._config_path)

        # Notify the rest of the app that settings changed.
        # Import here to avoid circular imports at module load time.
        try:
            from core.events import AppEvents
            AppEvents.settings_changed.emit()
        except Exception:
            pass  # Events not available in headless/test mode

    # ── Convenience helpers ────────────────────────────────────────────

    def find_category_for_extension(self, ext: str) -> str | None:
        """
        Return the category name for a file extension, or None if
        no rule matches.

        Example:
            Settings.find_category_for_extension(".pdf") → "PDFs"
            Settings.find_category_for_extension(".xyz") → None
        """
        for rule in self.categories:
            if rule.matches_extension(ext):
                return rule.name
        return None

    def find_category_for_filename(self, filename: str) -> str | None:
        """
        Return the first category whose keywords match the filename,
        or None if nothing matches.
        """
        for rule in self.categories:
            if rule.matches_filename(filename):
                return rule.name
        return None

    def is_loaded(self) -> bool:
        """Return True if load() has been called successfully."""
        return self._loaded

    # ── Default file writers ───────────────────────────────────────────

    def _write_default_app_toml(self) -> None:
        """Write a minimal default app.toml if none exists."""
        default = {
            "app":     _to_dict(AppSettings()),
            "ai":      _to_dict(AISettings()),
            "scanner": _to_dict(ScannerSettings()),
            "ocr":     _to_dict(OCRSettings()),
            "search":  _to_dict(SearchSettings()),
            "storage": _to_dict(StorageSettings()),
            "logging": _to_dict(LoggingSettings()),
            "window":  _to_dict(WindowSettings()),
        }
        with open(self._config_path, "w", encoding="utf-8") as f:
            toml.dump(default, f)

    def _write_default_categories_toml(self) -> None:
        """Write a minimal default categories.toml if none exists."""
        default = {
            "categories": {
                "Finance":       {"extensions": [".xlsx", ".xls", ".csv"], "keywords": ["invoice", "receipt", "payment", "budget", "tax"]},
                "Documents":     {"extensions": [".docx", ".doc", ".rtf"], "keywords": ["report", "letter", "memo", "contract"]},
                "PDFs":          {"extensions": [".pdf"], "keywords": []},
                "Presentations": {"extensions": [".pptx", ".ppt"], "keywords": ["slides", "deck", "pitch"]},
                "Code":          {"extensions": [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml"], "keywords": ["script", "code"]},
                "Images":        {"extensions": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"], "keywords": ["photo", "screenshot"]},
                "Videos":        {"extensions": [".mp4", ".mkv", ".avi", ".mov"], "keywords": ["video", "recording"]},
                "Audio":         {"extensions": [".mp3", ".wav", ".flac", ".aac"], "keywords": ["audio", "music"]},
                "Archives":      {"extensions": [".zip", ".rar", ".7z", ".tar", ".gz"], "keywords": ["archive", "backup"]},
                "Miscellaneous": {"extensions": [], "keywords": []},
            }
        }
        with open(self._categories_path, "w", encoding="utf-8") as f:
            toml.dump(default, f)


# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════

def _merge(cls: type, data: dict[str, Any]) -> Any:
    """
    Create a dataclass instance from a dict, ignoring unknown keys.
    Missing keys fall back to the dataclass field defaults.
    """
    import dataclasses
    valid_fields = {f.name for f in dataclasses.fields(cls)}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return cls(**filtered)


def _to_dict(obj: Any) -> dict[str, Any]:
    """
    Convert a dataclass to a plain dict for TOML serialization.
    Skips properties (only serializes actual fields).
    """
    import dataclasses
    return {
        f.name: getattr(obj, f.name)
        for f in dataclasses.fields(obj)
    }


# ══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ══════════════════════════════════════════════════════════════════════════

# Import and use this everywhere. Never instantiate _Settings yourself.
#
# Usage:
#   from infrastructure.config.settings import Settings
#   Settings.load()           # once at startup
#   model = Settings.ai.model
#   Settings.ai.model = "llama3.2:1b"
#   Settings.save()
#
Settings = _Settings()