"""
DesktopAI
Tests for the Database module.
"""

from datetime import datetime
from pathlib import Path

import pytest

from core.exceptions import DatabaseNotConnectedError
from database.database import DatabaseManager
from scanner.file_info import FileInfo


def make_file_info(path: Path, name: str = "test.txt") -> FileInfo:
    """Helper to build a sample FileInfo for tests."""
    return FileInfo(
        name=name,
        path=path,
        extension=".txt",
        size=123,
        created=datetime(2026, 1, 1, 10, 0, 0),
        modified=datetime(2026, 1, 2, 11, 0, 0),
        file_hash="abc123",
        detected_type="text/plain",
    )


def test_connect_creates_database_file(tmp_path):
    """Calling connect() should create the database file."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(db_path)
    db.connect()

    assert db_path.exists()
    db.close()


def test_save_and_load_file(tmp_path):
    """A saved file should be retrievable via load_files()."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(db_path)
    db.connect()

    file_info = make_file_info(tmp_path / "test.txt")
    db.save_file(file_info)

    loaded = db.load_files()

    assert len(loaded) == 1
    assert loaded[0].name == "test.txt"
    assert loaded[0].file_hash == "abc123"
    db.close()


def test_save_file_updates_existing_record(tmp_path):
    """Saving a file with a path that's already stored should update
    the existing record instead of creating a duplicate."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(db_path)
    db.connect()

    path = tmp_path / "test.txt"
    db.save_file(make_file_info(path, name="original_name.txt"))
    db.save_file(make_file_info(path, name="renamed.txt"))

    loaded = db.load_files()

    assert len(loaded) == 1
    assert loaded[0].name == "renamed.txt"
    db.close()


def test_delete_file_removes_record(tmp_path):
    """Deleting a file's record should make it disappear from load_files()."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(db_path)
    db.connect()

    path = tmp_path / "test.txt"
    db.save_file(make_file_info(path))

    db.delete_file(path)

    loaded = db.load_files()
    assert loaded == []
    db.close()


def test_delete_nonexistent_file_is_not_an_error(tmp_path):
    """Deleting a path that was never saved should not raise."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(db_path)
    db.connect()

    db.delete_file(tmp_path / "never_existed.txt")  # should not raise
    db.close()


def test_operations_before_connect_raise_clear_error(tmp_path):
    """Using the database before connect() should raise a clear,
    specific error rather than an obscure attribute error."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(db_path)

    with pytest.raises(DatabaseNotConnectedError):
        db.load_files()