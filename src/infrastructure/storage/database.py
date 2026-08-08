"""
DesktopAI v2.0 — Database Manager
File: src/infrastructure/storage/database.py

Manages the SQLite database for DesktopAI v2.

Key improvements over V1:
- Versioned migrations (schema changes never lose data)
- History table is now fully wired — every operation is recorded
- Context manager support (with DatabaseManager() as db:)
- Proper connection handling with WAL mode for concurrent reads
- Every public method has a clear docstring and typed return values
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.constants import DATA_DIR, DB_FILENAME, DB_SCHEMA_VERSION
from core.exceptions import (
    DatabaseNotConnectedError,
    DatabaseMigrationError,
    RecordNotFoundError,
)
from core.logger import get_logger

logger = get_logger(__name__)

# Path to the migrations folder
_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _utcnow() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DatabaseManager:
    """
    SQLite database manager for DesktopAI v2.

    Usage:
        db = DatabaseManager()
        db.connect()
        db.record_history_entry(...)
        db.close()

    Or as a context manager:
        with DatabaseManager() as db:
            db.record_history_entry(...)

    The singleton `DB` at the bottom of this file is the recommended
    way to access the database throughout the app.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            db_path = DATA_DIR / DB_FILENAME

        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    # ── Connection management ──────────────────────────────────────────

    def connect(self) -> None:
        """
        Open the database connection and run any pending migrations.
        Call once at application startup.
        """
        logger.info("Connecting to database: %s", self._db_path)

        self._conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
        )

        # Return rows as dict-like objects (access by column name).
        self._conn.row_factory = sqlite3.Row

        # WAL mode allows concurrent reads while a write is in progress.
        self._conn.execute("PRAGMA journal_mode=WAL")

        # Enforce foreign key constraints.
        self._conn.execute("PRAGMA foreign_keys=ON")

        self._migrate()
        logger.info("Database ready at %s", self._db_path)

    def close(self) -> None:
        """Close the database connection cleanly."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    def __enter__(self) -> "DatabaseManager":
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _require_connection(self) -> sqlite3.Connection:
        """Return the connection or raise if not connected."""
        if self._conn is None:
            raise DatabaseNotConnectedError(
                "Database is not connected. Call connect() first."
            )
        return self._conn

    # ── Migrations ─────────────────────────────────────────────────────

    def _migrate(self) -> None:
        """
        Apply any SQL migration files that have not been run yet.

        Migration files are named NNN_description.sql where NNN is
        a zero-padded integer. They are applied in order.
        Files already recorded in schema_versions are skipped.
        """
        conn = self._require_connection()

        # Ensure the versions table exists before we query it.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version    INTEGER PRIMARY KEY,
                name       TEXT    NOT NULL,
                applied_at TEXT    NOT NULL DEFAULT (datetime('now', 'utc'))
            )
        """)
        conn.commit()

        # Find all .sql files, sorted by number prefix.
        migration_files = sorted(_MIGRATIONS_DIR.glob("*.sql"))

        if not migration_files:
            logger.warning("No migration files found in %s", _MIGRATIONS_DIR)
            return

        applied = self._get_applied_versions()

        for migration_file in migration_files:
            # Extract the version number from filename (e.g. "001_initial.sql" → 1)
            try:
                version_str = migration_file.stem.split("_")[0]
                version = int(version_str)
            except (ValueError, IndexError):
                logger.warning("Skipping non-standard migration file: %s", migration_file.name)
                continue

            if version in applied:
                logger.debug("Migration %d already applied — skipping", version)
                continue

            logger.info("Applying migration %d: %s", version, migration_file.name)

            try:
                sql = migration_file.read_text(encoding="utf-8")
                conn.executescript(sql)
                conn.commit()
                logger.info("Migration %d applied successfully", version)

            except sqlite3.Error as exc:
                conn.rollback()
                raise DatabaseMigrationError(
                    f"Migration {migration_file.name} failed: {exc}"
                ) from exc

    def _get_applied_versions(self) -> set[int]:
        """Return set of migration version numbers already in schema_versions."""
        conn = self._require_connection()
        try:
            rows = conn.execute("SELECT version FROM schema_versions").fetchall()
            return {row["version"] for row in rows}
        except sqlite3.Error:
            return set()

    # ── Sessions ───────────────────────────────────────────────────────

    def create_session(self, folder_path: str) -> str:
        """
        Create a new scan/organize session and return its UUID.

        The session ID is used to group all history entries from
        the same batch operation so they can be undone together.

        Args:
            folder_path: The folder being scanned/organized.

        Returns:
            A UUID string identifying this session.
        """
        conn = self._require_connection()
        session_id = str(uuid.uuid4())

        conn.execute(
            """
            INSERT INTO sessions (id, folder_path, status, started_at)
            VALUES (?, ?, 'running', ?)
            """,
            (session_id, folder_path, _utcnow()),
        )
        conn.commit()

        logger.debug("Session created: %s for %s", session_id, folder_path)
        return session_id

    def complete_session(
        self,
        session_id: str,
        file_count: int,
        action_count: int,
        status: str = "completed",
    ) -> None:
        """Mark a session as completed with final counts."""
        conn = self._require_connection()
        conn.execute(
            """
            UPDATE sessions
            SET status = ?, file_count = ?, action_count = ?, completed_at = ?
            WHERE id = ?
            """,
            (status, file_count, action_count, _utcnow(), session_id),
        )
        conn.commit()

    # ── History (audit trail) ──────────────────────────────────────────

    def record_history_entry(
        self,
        action_type: str,
        source_path: str,
        target_path: str | None = None,
        category: str | None = None,
        confidence: float | None = None,
        model: str | None = None,
        status: str = "completed",
        error_message: str | None = None,
        batch_id: str | None = None,
    ) -> int:
        """
        Write one audit entry to the history table.

        This is the method V1 never called. V2 calls it for every
        file operation: move, rename, copy, skip, and undo.

        Args:
            action_type:   'move', 'rename', 'copy', 'skip', 'undo'
            source_path:   Original file path.
            target_path:   Destination path (None for skips).
            category:      Category assigned by the classifier.
            confidence:    Classifier confidence score (0.0–1.0).
            model:         AI model that made the decision.
            status:        'completed', 'failed', or 'undone'.
            error_message: Error detail if status is 'failed'.
            batch_id:      Session UUID to group related operations.

        Returns:
            The row ID of the new history entry.
        """
        conn = self._require_connection()

        cursor = conn.execute(
            """
            INSERT INTO history (
                action_type, source_path, target_path,
                category, confidence, model,
                status, error_message, batch_id, performed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action_type, source_path, target_path,
                category, confidence, model,
                status, error_message, batch_id, _utcnow(),
            ),
        )
        conn.commit()

        logger.debug(
            "History recorded: %s %s → %s [%s]",
            action_type, source_path, target_path, status,
        )
        return cursor.lastrowid

    def get_history(
        self,
        limit: int = 100,
        batch_id: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """
        Retrieve history entries, newest first.

        Args:
            limit:    Maximum number of rows to return.
            batch_id: Filter to one specific session/batch.
            status:   Filter by status ('completed', 'failed', 'undone').

        Returns:
            List of dicts with all history columns.
        """
        conn = self._require_connection()

        conditions = []
        params: list[Any] = []

        if batch_id:
            conditions.append("batch_id = ?")
            params.append(batch_id)

        if status:
            conditions.append("status = ?")
            params.append(status)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        rows = conn.execute(
            f"""
            SELECT * FROM history
            {where}
            ORDER BY performed_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()

        return [dict(row) for row in rows]

    def mark_history_undone(self, history_id: int) -> None:
        """Mark a history entry as undone after a successful undo operation."""
        conn = self._require_connection()
        conn.execute(
            "UPDATE history SET status = 'undone' WHERE id = ?",
            (history_id,),
        )
        conn.commit()

    # ── Files ──────────────────────────────────────────────────────────

    def upsert_file(
        self,
        path: str,
        filename: str,
        extension: str,
        size_bytes: int,
        modified_at: str | None = None,
        md5_hash: str | None = None,
        category: str | None = None,
        confidence: float | None = None,
        summary: str | None = None,
        text_content: str | None = None,
    ) -> int:
        """
        Insert a new file record or update it if the path already exists.

        Returns the file's row ID.
        """
        conn = self._require_connection()

        cursor = conn.execute(
            """
            INSERT INTO files (
                path, filename, extension, size_bytes, modified_at,
                md5_hash, category, confidence, summary, text_content,
                scanned_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                filename     = excluded.filename,
                extension    = excluded.extension,
                size_bytes   = excluded.size_bytes,
                modified_at  = excluded.modified_at,
                md5_hash     = excluded.md5_hash,
                category     = COALESCE(excluded.category, files.category),
                confidence   = COALESCE(excluded.confidence, files.confidence),
                summary      = COALESCE(excluded.summary, files.summary),
                text_content = COALESCE(excluded.text_content, files.text_content),
                updated_at   = excluded.updated_at
            """,
            (
                path, filename, extension, size_bytes, modified_at,
                md5_hash, category, confidence, summary, text_content,
                _utcnow(), _utcnow(),
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def get_file_by_path(self, path: str) -> dict | None:
        """Return a file record by its path, or None if not found."""
        conn = self._require_connection()
        row = conn.execute(
            "SELECT * FROM files WHERE path = ?", (path,)
        ).fetchone()
        return dict(row) if row else None

    def get_files_by_category(self, category: str) -> list[dict]:
        """Return all file records with the given category."""
        conn = self._require_connection()
        rows = conn.execute(
            "SELECT * FROM files WHERE category = ? ORDER BY filename",
            (category,),
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_file_dirty(self, path: str) -> None:
        """
        Flag a file's embedding as stale (needs re-embedding).
        Called by the watcher when a file is modified.
        """
        conn = self._require_connection()
        conn.execute(
            """
            UPDATE embeddings SET is_dirty = 1
            WHERE file_id = (SELECT id FROM files WHERE path = ?)
            """,
            (path,),
        )
        conn.commit()

    def get_dirty_files(self) -> list[dict]:
        """Return files whose embeddings are stale and need rebuilding."""
        conn = self._require_connection()
        rows = conn.execute(
            """
            SELECT f.* FROM files f
            JOIN embeddings e ON e.file_id = f.id
            WHERE e.is_dirty = 1
            """,
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Preferences ────────────────────────────────────────────────────

    def save_preference(
        self,
        pref_type: str,
        pattern: str,
        value: str,
        confidence: float = 1.0,
    ) -> None:
        """
        Save or update a user preference.

        Called when a user manually overrides a category decision,
        teaching DesktopAI their preferences for future sessions.

        Args:
            pref_type:  'folder_preference', 'category_override', 'skip_pattern'
            pattern:    Filename pattern or extension (e.g. "invoice_*", ".pdf")
            value:      The preferred folder path or category name.
            confidence: How strongly to weight this preference (default 1.0).
        """
        conn = self._require_connection()
        conn.execute(
            """
            INSERT INTO preferences (pref_type, pattern, value, confidence, last_used_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT DO UPDATE SET
                use_count    = use_count + 1,
                last_used_at = excluded.last_used_at
            """,
            (pref_type, pattern, value, confidence, _utcnow()),
        )
        conn.commit()
        logger.debug("Preference saved: %s %s → %s", pref_type, pattern, value)

    def get_preferred_folder(self, filename: str, extension: str) -> str | None:
        """
        Look up the user's preferred folder for a given file.

        The organizer calls this BEFORE asking the AI — if a preference
        exists, the AI call is skipped entirely (faster + cheaper).

        Args:
            filename:  The file's name (e.g. "invoice_jan.pdf").
            extension: The file's extension (e.g. ".pdf").

        Returns:
            The preferred folder path, or None if no preference exists.
        """
        conn = self._require_connection()

        # Check filename pattern first (more specific), then extension.
        for pattern in (filename, extension):
            row = conn.execute(
                """
                SELECT value FROM preferences
                WHERE pref_type = 'folder_preference'
                AND pattern = ?
                ORDER BY use_count DESC, last_used_at DESC
                LIMIT 1
                """,
                (pattern,),
            ).fetchone()

            if row:
                logger.debug(
                    "Preference hit: %s → %s", pattern, row["value"]
                )
                return row["value"]

        return None

    def get_all_preferences(self) -> list[dict]:
        """Return all saved preferences, ordered by use count."""
        conn = self._require_connection()
        rows = conn.execute(
            "SELECT * FROM preferences ORDER BY use_count DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Stats ──────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """
        Return a summary of database contents for the Home view.

        Returns:
            Dict with keys: total_files, total_operations,
            categories (dict of category → count), recent_sessions (list).
        """
        conn = self._require_connection()

        total_files = conn.execute(
            "SELECT COUNT(*) FROM files"
        ).fetchone()[0]

        total_ops = conn.execute(
            "SELECT COUNT(*) FROM history WHERE status = 'completed'"
        ).fetchone()[0]

        cat_rows = conn.execute(
            """
            SELECT category, COUNT(*) as count
            FROM files
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            """
        ).fetchall()

        recent_sessions = conn.execute(
            """
            SELECT id, folder_path, file_count, action_count, status, started_at
            FROM sessions
            ORDER BY started_at DESC
            LIMIT 5
            """
        ).fetchall()

        return {
            "total_files":      total_files,
            "total_operations": total_ops,
            "categories":       {r["category"]: r["count"] for r in cat_rows},
            "recent_sessions":  [dict(r) for r in recent_sessions],
        }


# ── Singleton ──────────────────────────────────────────────────────────────
# Use this throughout the application.
# Call DB.connect() once at startup in main.py.
#
# Usage:
#   from infrastructure.storage.database import DB
#   DB.record_history_entry(action_type="move", source_path=..., ...)
#
DB = DatabaseManager()