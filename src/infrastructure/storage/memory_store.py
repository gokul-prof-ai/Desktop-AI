"""
DesktopAI v2.0 — Memory Store (User Preference Service)
File: src/infrastructure/storage/memory_store.py

A clean facade over the preferences table in DatabaseManager.

In V1, MemoryStore existed but the organizer never consulted it.
In V2, the organizer calls MemoryStore.get_preferred_folder() BEFORE
asking the AI. If a preference exists, the AI call is skipped.

This means DesktopAI learns from user corrections and gets faster
and more accurate over time without any ML training.

Usage:
    from infrastructure.storage.memory_store import MemoryStore

    # During organization — check preference first:
    folder = MemoryStore.get_preferred_folder("invoice.pdf", ".pdf")
    if folder:
        # Use the preference, skip the AI call
    else:
        # Ask the AI

    # After user corrects a decision:
    MemoryStore.remember_folder("invoice.pdf", "/Documents/Finance/")
"""

from __future__ import annotations

from core.logger import get_logger
from infrastructure.storage.database import DB

logger = get_logger(__name__)


class _MemoryStore:
    """
    User preference memory service.

    Access via the module-level `MemoryStore` singleton.
    """

    # ── Folder preferences ─────────────────────────────────────────────

    def remember_folder(
        self,
        filename_or_extension: str,
        folder_path: str,
        confidence: float = 1.0,
    ) -> None:
        """
        Record that the user wants this file/extension to go to folder_path.

        Call this when:
        - The user drags a file to a different folder than DesktopAI suggested.
        - The user edits a category in the Results view.
        - The user confirms a manual override.

        Args:
            filename_or_extension: Exact filename ("invoice_jan.pdf")
                                   or extension (".pdf") to match.
            folder_path:           The folder the user wants it to go to.
            confidence:            Weight of this preference (default 1.0).
        """
        DB.save_preference(
            pref_type="folder_preference",
            pattern=filename_or_extension,
            value=folder_path,
            confidence=confidence,
        )
        logger.info(
            "Memory: learned folder preference %s → %s",
            filename_or_extension, folder_path,
        )

    def get_preferred_folder(
        self, filename: str, extension: str
    ) -> str | None:
        """
        Return the user's preferred folder for this file, or None.

        Checks filename pattern first (most specific), then extension.
        Returns None if no preference has been recorded.

        Args:
            filename:  The full filename including extension.
            extension: Just the extension (e.g. ".pdf").
        """
        return DB.get_preferred_folder(filename, extension)

    # ── Category overrides ─────────────────────────────────────────────

    def remember_category(
        self,
        filename_or_extension: str,
        category: str,
    ) -> None:
        """
        Record that the user wants this file/extension always categorized
        as a specific category — overriding the AI's decision.

        Args:
            filename_or_extension: Filename or extension to match.
            category:              Category name to assign.
        """
        DB.save_preference(
            pref_type="category_override",
            pattern=filename_or_extension,
            value=category,
        )
        logger.info(
            "Memory: learned category override %s → %s",
            filename_or_extension, category,
        )

    def get_category_override(
        self, filename: str, extension: str
    ) -> str | None:
        """
        Return a user-defined category override for this file, or None.
        """
        conn = DB._require_connection()
        for pattern in (filename, extension):
            row = conn.execute(
                """
                SELECT value FROM preferences
                WHERE pref_type = 'category_override' AND pattern = ?
                ORDER BY use_count DESC LIMIT 1
                """,
                (pattern,),
            ).fetchone()
            if row:
                return row["value"]
        return None

    # ── Skip patterns ──────────────────────────────────────────────────

    def remember_skip(self, pattern: str) -> None:
        """
        Record that files matching this pattern should always be skipped.

        Example: user always skips ".tmp" files or "~$*" Office temp files.

        Args:
            pattern: Filename pattern or extension to always skip.
        """
        DB.save_preference(
            pref_type="skip_pattern",
            pattern=pattern,
            value="skip",
        )
        logger.info("Memory: learned skip pattern %s", pattern)

    def should_skip(self, filename: str) -> bool:
        """
        Return True if this file matches a user-defined skip pattern.
        """
        conn = DB._require_connection()
        row = conn.execute(
            """
            SELECT 1 FROM preferences
            WHERE pref_type = 'skip_pattern'
            AND ? LIKE pattern
            LIMIT 1
            """,
            (filename,),
        ).fetchone()
        return row is not None

    # ── Summary ────────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        """Return all stored preferences for the Settings/Memory view."""
        return DB.get_all_preferences()

    def clear_all(self) -> None:
        """
        Delete all learned preferences.
        Used from Settings view: 'Reset DesktopAI memory'.
        """
        conn = DB._require_connection()
        conn.execute("DELETE FROM preferences")
        conn.commit()
        logger.info("Memory: all preferences cleared")


# ── Singleton ──────────────────────────────────────────────────────────────
MemoryStore = _MemoryStore()