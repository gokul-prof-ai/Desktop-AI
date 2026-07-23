"""
DesktopAI
OCR Reader

Extracts text from image files (scanned documents, screenshots,
photos of text) using Tesseract OCR, for content that has no
selectable text layer.
"""

from pathlib import Path

import pytesseract
from PIL import Image, UnidentifiedImageError

from core.logger import get_logger

logger = get_logger("documents")


def read_image_text(path: Path) -> str | None:
    """
    Extract text from an image using OCR.

    Args:
        path (Path):
            The image file to read (e.g. .png, .jpg).

    Returns:
        str | None:
            The extracted text, or None if the file could not be
            read (missing, corrupted, not a valid image), or if
            the Tesseract OCR engine itself is not installed on
            this machine. A None result is expected behavior for
            a bad file, not a crash.
    """

    if not path.exists():
        logger.warning("Image not found: %s", path)
        return None

    try:
        image = Image.open(path)
    except UnidentifiedImageError as error:
        logger.warning("Could not open image %s: %s", path, error)
        return None

    try:
        text = pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError:
        # This means the Tesseract OCR *program* isn't installed on
        # this machine (pytesseract is just a wrapper around it).
        # This is a setup problem, not a bad file, so it gets a
        # distinct, more actionable log message.
        logger.warning(
            "Tesseract OCR engine is not installed or not found on PATH. "
            "OCR cannot run until it is installed."
        )
        return None
    finally:
        image.close()

    logger.info("OCR extracted %d character(s) from %s", len(text), path)

    return text