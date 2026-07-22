"""
DesktopAI
Database Module

Stores and retrieves file metadata using SQLite, so scan results
persist between runs instead of being lost when the app closes.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from core.exceptions import DatabaseNotConnectedError
from core.logger import get_logger
from scanner.file_info import FileInfo

logger = get_logger("database")

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class DatabaseManager:
    """Manages a SQLite database of scanned file metadata."""

    def __init__(self, db_path: Path):
        """
        Args:
            db_path (Path):
                Where the SQLite database file should live. The file
                (and its parent folder) is created automatically the
                first time connect() is called.
        """
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> None:
        """
        Open the database connection and ensure the `files` table
        exists. Safe to call more than once.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = sqlite3.connect(self.db_path)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                extension TEXT,
                size INTEGER NOT NULL,
                created TEXT NOT NULL,
                modified TEXT NOT NULL,
                file_hash TEXT,
                detected_type TEXT,
                scanned_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

        logger.info("Connected to database: %s", self.db_path)

    def close(self) -> None:
        """Close the database connection, if one is open."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed.")

    def save_file(self, file_info: FileInfo) -> None:
        """
        Save a FileInfo record. If a file with the same path already
        exists, its record is updated instead of duplicated.

        Args:
            file_info (FileInfo):
                The scanned file metadata to store.
        """
        connection = self._require_connection()

        connection.execute(
            """
            INSERT INTO files
                (path, name, extension, size, created, modified,
                 file_hash, detected_type, scanned_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                name = excluded.name,
                extension = excluded.extension,
                size = excluded.size,
                created = excluded.created,
                modified = excluded.modified,
                file_hash = excluded.file_hash,
                detected_type = excluded.detected_type,
                scanned_at = excluded.scanned_at
            """,
            (
                str(file_info.path),
                file_info.name,
                file_info.extension,
                file_info.size,
                file_info.created.strftime(DATE_FORMAT),
                file_info.modified.strftime(DATE_FORMAT),
                file_info.file_hash,
                file_info.detected_type,
                datetime.now().strftime(DATE_FORMAT),
            ),
        )
        connection.commit()

    def load_files(self) -> list[FileInfo]:
        """
        Load every stored file record.

        Returns:
            list[FileInfo]:
                All files currently stored in the database.
        """
        connection = self._require_connection()

        cursor = connection.execute(
            """
            SELECT path, name, extension, size, created, modified,
                   file_hash, detected_type
            FROM files
            """
        )

        results: list[FileInfo] = []
        for row in cursor.fetchall():
            (
                path,
                name,
                extension,
                size,
                created,
                modified,
                file_hash,
                detected_type,
            ) = row

            results.append(
                FileInfo(
                    name=name,
                    path=Path(path),
                    extension=extension,
                    size=size,
                    created=datetime.strptime(created, DATE_FORMAT),
                    modified=datetime.strptime(modified, DATE_FORMAT),
                    file_hash=file_hash,
                    detected_type=detected_type,
                )
            )

        return results

    def delete_file(self, path: Path) -> None:
        """
        Delete a file's record by its path. Deleting a path that
        isn't in the database is a no-op, not an error.

        Args:
            path (Path):
                The path of the record to delete.
        """
        connection = self._require_connection()

        connection.execute("DELETE FROM files WHERE path = ?", (str(path),))
        connection.commit()

    def _require_connection(self) -> sqlite3.Connection:
        """
        Return the active connection, or raise a clear error if
        connect() hasn't been called yet.
        """
        if self._connection is None:
            raise DatabaseNotConnectedError(
                "Database is not connected. Call connect() first."
            )
        return self._connection