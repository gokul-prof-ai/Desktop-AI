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


def test_scan_recurses_into_subfolders(tmp_path):
    """Files inside subfolders should be found, not just top-level files."""
    (tmp_path / "top_level.txt").write_text("hello")

    subfolder = tmp_path / "subfolder"
    subfolder.mkdir()
    (subfolder / "nested.txt").write_text("hello")

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    names = {f.name for f in results}
    assert names == {"top_level.txt", "nested.txt"}


def test_scan_respects_max_depth(tmp_path):
    """Files deeper than max_depth should not be found."""
    level_1 = tmp_path / "level_1"
    level_2 = level_1 / "level_2"
    level_2.mkdir(parents=True)

    (level_1 / "shallow.txt").write_text("hello")
    (level_2 / "deep.txt").write_text("hello")

    scanner = FileScanner()

    # max_depth=1 means: top folder (depth 0) + one level of
    # subfolders (depth 1). level_2 is depth 2, so it should
    # be excluded.
    results = scanner.scan(tmp_path, max_depth=1)

    names = {f.name for f in results}
    assert names == {"shallow.txt"}
    assert "deep.txt" not in names


def test_scan_max_depth_zero_is_non_recursive(tmp_path):
    """max_depth=0 should behave like the old non-recursive scan."""
    (tmp_path / "top_level.txt").write_text("hello")

    subfolder = tmp_path / "subfolder"
    subfolder.mkdir()
    (subfolder / "nested.txt").write_text("hello")

    scanner = FileScanner()
    results = scanner.scan(tmp_path, max_depth=0)

    names = {f.name for f in results}
    assert names == {"top_level.txt"}


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