"""
DesktopAI
Tests for the Scanner module.
"""

import pytest

from scanner.scanner import FileScanner


def test_scan_finds_regular_files(tmp_path):
    """A folder with normal files should return one FileInfo per file."""
    (tmp_path / "notes.txt").write_text("hello")
    (tmp_path / "image.jpg").write_bytes(b"")

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    names = {f.name for f in results}
    assert names == {"notes.txt", "image.jpg"}


def test_scan_skips_hidden_files(tmp_path):
    """Files starting with a dot (like .gitkeep) should be ignored."""
    (tmp_path / ".gitkeep").write_text("")
    (tmp_path / "real_file.txt").write_text("hello")

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    names = {f.name for f in results}
    assert names == {"real_file.txt"}


def test_scan_ignores_subfolders(tmp_path):
    """Subdirectories should not appear as scanned files."""
    (tmp_path / "subfolder").mkdir()
    (tmp_path / "file.txt").write_text("hello")

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    names = {f.name for f in results}
    assert names == {"file.txt"}


def test_scan_raises_on_missing_folder(tmp_path):
    """Scanning a folder that doesn't exist should raise FileNotFoundError."""
    missing = tmp_path / "does_not_exist"

    scanner = FileScanner()
    with pytest.raises(FileNotFoundError):
        scanner.scan(missing)


def test_scan_raises_on_non_directory(tmp_path):
    """Scanning a file (not a folder) should raise NotADirectoryError."""
    a_file = tmp_path / "not_a_folder.txt"
    a_file.write_text("hello")

    scanner = FileScanner()
    with pytest.raises(NotADirectoryError):
        scanner.scan(a_file)