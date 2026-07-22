"""
DesktopAI
Tests for the Scanner module.
"""

import hashlib

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


def test_scan_computes_correct_sha256_hash(tmp_path):
    """The computed hash should match Python's own hashlib result."""
    content = b"hello world"
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    assert len(results) == 1
    assert results[0].file_hash == expected_hash


def test_scan_gives_identical_files_the_same_hash(tmp_path):
    """Two files with identical content should have identical hashes."""
    (tmp_path / "original.txt").write_bytes(b"duplicate content")
    (tmp_path / "copy.txt").write_bytes(b"duplicate content")

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    hashes = {f.name: f.file_hash for f in results}
    assert hashes["original.txt"] == hashes["copy.txt"]


def test_scan_gives_different_files_different_hashes(tmp_path):
    """Two files with different content should have different hashes."""
    (tmp_path / "file_a.txt").write_bytes(b"content A")
    (tmp_path / "file_b.txt").write_bytes(b"content B")

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    hashes = {f.name: f.file_hash for f in results}
    assert hashes["file_a.txt"] != hashes["file_b.txt"]


def test_scan_detects_real_type_from_content(tmp_path):
    """A file's real type should be detected from its content, not its name."""
    jpeg_header = bytes.fromhex("FFD8FFE0") + b"0" * 20
    file_path = tmp_path / "photo.jpg"
    file_path.write_bytes(jpeg_header)

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    assert results[0].detected_type == "image/jpeg"


def test_scan_detects_mismatched_extension(tmp_path):
    """A file with JPEG content but a .txt name should still be
    detected as image/jpeg — proving detection uses content, not name."""
    jpeg_header = bytes.fromhex("FFD8FFE0") + b"0" * 20
    file_path = tmp_path / "disguised.txt"
    file_path.write_bytes(jpeg_header)

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    assert results[0].detected_type == "image/jpeg"


def test_scan_plain_text_has_no_detected_type(tmp_path):
    """Plain text files have no magic number, so detected_type
    should be None. This is expected, normal behavior."""
    file_path = tmp_path / "notes.txt"
    file_path.write_text("just some plain text")

    scanner = FileScanner()
    results = scanner.scan(tmp_path)

    assert results[0].detected_type is None