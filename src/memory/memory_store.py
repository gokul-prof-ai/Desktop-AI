"""
DesktopAI
Memory Store

Persists user preferences and suggestion feedback across sessions,
so DesktopAI learns from past actions instead of starting fresh
every time. Backed by SQLite, same pattern as the database module.

Two things are stored:
  1. Folder preferences   — "Invoices go in Documents/Invoices"
  2. Suggestion feedback  — accepted / rejected, per suggestion
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from core.exceptions import DatabaseNotConnectedError
from core.logger import get_logger

logger = get_logger("memory")

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class MemoryStore:
    """Stores and retrieves user preferences and suggestion feedback."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Open the memory database and create tables if needed."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path)

        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS folder_preferences (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category    TEXT NOT NULL,
                folder      TEXT NOT NULL,
                use_count   INTEGER NOT NULL DEFAULT 1,
                last_used   TEXT NOT NULL,
                UNIQUE(category, folder)
            );

            CREATE TABLE IF NOT EXISTS suggestion_feedback (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name        TEXT NOT NULL,
                category         TEXT,
                suggested_folder TEXT,
                accepted         INTEGER NOT NULL,
                recorded_at      TEXT NOT NULL
            );
            """
        )
        self._connection.commit()
        logger.info("Memory store connected: %s", self.db_path)

    def close(self) -> None:
        """Close the memory database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Memory store closed.")

    def record_folder_choice(self, category: str, folder: str) -> None:
        """
        Record that the user moved a file of this category into this
        folder. Increments the use count if it already exists.
        """
        conn = self._require_connection()
        now = datetime.now().strftime(DATE_FORMAT)

        conn.execute(
            """
            INSERT INTO folder_preferences (category, folder, use_count, last_used)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(category, folder) DO UPDATE SET
                use_count = use_count + 1,
                last_used = excluded.last_used
            """,
            (category, folder, now),
        )
        conn.commit()
        logger.info("Recorded folder choice: %s -> %s", category, folder)

    def get_preferred_folder(self, category: str) -> str | None:
        """
        Return the most-used folder for a given category, or None if
        there is no history for that category yet.
        """
        conn = self._require_connection()

        row = conn.execute(
            """
            SELECT folder FROM folder_preferences
            WHERE category = ?
            ORDER BY use_count DESC, last_used DESC
            LIMIT 1
            """,
            (category,),
        ).fetchone()

        return row[0] if row else None

    def get_all_preferences(self) -> list[dict]:
        """Return all stored folder preferences, most-used first."""
        conn = self._require_connection()

        rows = conn.execute(
            """
            SELECT category, folder, use_count, last_used
            FROM folder_preferences
            ORDER BY use_count DESC, last_used DESC
            """
        ).fetchall()

        return [
            {
                "category": row[0],
                "folder": row[1],
                "use_count": row[2],
                "last_used": row[3],
            }
            for row in rows
        ]

    def record_feedback(
        self,
        file_name: str,
        accepted: bool,
        category: str | None = None,
        suggested_folder: str | None = None,
    ) -> None:
        """Record whether the user accepted or rejected a suggestion."""
        conn = self._require_connection()
        now = datetime.now().strftime(DATE_FORMAT)

        conn.execute(
            """
            INSERT INTO suggestion_feedback
                (file_name, category, suggested_folder, accepted, recorded_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file_name, category, suggested_folder, int(accepted), now),
        )
        conn.commit()
        logger.info(
            "Recorded feedback for %s: %s",
            file_name,
            "accepted" if accepted else "rejected",
        )

    def get_acceptance_rate(self, category: str) -> float | None:
        """
        Return the fraction of suggestions for this category that
        were accepted (0.0–1.0), or None if there's no history.
        """
        conn = self._require_connection()

        row = conn.execute(
            """
            SELECT COUNT(*), SUM(accepted)
            FROM suggestion_feedback
            WHERE category = ?
            """,
            (category,),
        ).fetchone()

        total, accepted = row
        if not total:
            return None

        return round(accepted / total, 2)

    def _require_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise DatabaseNotConnectedError(
                "MemoryStore is not connected. Call connect() first."
            )
        return self._connection