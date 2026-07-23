"""
DesktopAI
Tests for the PDF Reader module.
"""

import fitz

from documents.pdf_reader import read_pdf_text


def make_test_pdf(path, text: str) -> None:
    """Helper: create a real, minimal PDF file containing given text."""
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_read_pdf_text_extracts_content(tmp_path):
    """A valid PDF's text should be extracted correctly."""
    pdf_path = tmp_path / "sample.pdf"
    make_test_pdf(pdf_path, "Hello DesktopAI")

    result = read_pdf_text(pdf_path)

    assert result is not None
    assert "Hello DesktopAI" in result


def test_read_pdf_text_returns_none_for_missing_file(tmp_path):
    """A path that doesn't exist should return None, not raise."""
    missing_path = tmp_path / "does_not_exist.pdf"

    result = read_pdf_text(missing_path)

    assert result is None


def test_read_pdf_text_returns_none_for_corrupt_file(tmp_path):
    """A file that isn't actually a valid PDF should return None,
    not crash the caller."""
    fake_pdf_path = tmp_path / "corrupt.pdf"
    fake_pdf_path.write_bytes(b"this is not a real pdf")

    result = read_pdf_text(fake_pdf_path)

    assert result is None