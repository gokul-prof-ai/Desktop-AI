"""
DesktopAI
Tests for the OCR Reader module.
"""

from PIL import Image, ImageDraw

from documents.ocr_reader import read_image_text


def make_test_image(path, text: str) -> None:
    """Helper: create a real image file containing given text."""
    image = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((10, 30), text, fill="black")
    image.save(path)


def test_read_image_text_extracts_text(tmp_path):
    """A valid image with clear text should have that text extracted."""
    image_path = tmp_path / "sample.png"
    make_test_image(image_path, "Hello DesktopAI")

    result = read_image_text(image_path)

    assert result is not None
    # OCR isn't always perfect character-for-character, so we check
    # for the recognizable core of the text rather than an exact match.
    assert "DesktopAI" in result or "Desktop" in result


def test_read_image_text_returns_none_for_missing_file(tmp_path):
    """A path that doesn't exist should return None, not raise."""
    missing_path = tmp_path / "does_not_exist.png"

    result = read_image_text(missing_path)

    assert result is None


def test_read_image_text_returns_none_for_corrupt_file(tmp_path):
    """A file that isn't actually a valid image should return None,
    not crash the caller."""
    fake_image_path = tmp_path / "corrupt.png"
    fake_image_path.write_bytes(b"this is not a real image")

    result = read_image_text(fake_image_path)

    assert result is None