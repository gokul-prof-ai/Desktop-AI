"""
DesktopAI
OCR Reader

Extracts text from image files using Tesseract OCR. OCR is an optional
runtime capability: the rest of DesktopAI must still import and run when
pytesseract/Tesseract is not installed.
"""

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from core.logger import get_logger

logger = get_logger("documents")


def read_image_text(path: Path) -> str | None:
    """
    Extract text from an image using OCR.

    Returns None when the file is missing/corrupt or the optional OCR
    dependency/engine is unavailable. Importing this module never requires
    pytesseract to be installed, which keeps unrelated tests and features
    usable on minimal installations.
    """
    if not path.exists():
        logger.warning("Image not found: %s", path)
        return None

    try:
        image = Image.open(path)
    except (UnidentifiedImageError, OSError) as error:
        logger.warning("Could not open image %s: %s", path, error)
        return None

    try:
        # Import lazily so OCR remains an optional feature instead of an
        # import-time requirement for the entire application.
        try:
            import pytesseract
        except ImportError:
            logger.warning(
                "pytesseract is not installed. OCR skipped for %s.", path
            )
            return None

        try:
            text = pytesseract.image_to_string(image)
        except (
            pytesseract.TesseractNotFoundError,
            pytesseract.TesseractError,
        ) as error:
            logger.warning(
                "Tesseract OCR engine error or not installed on PATH (%s). OCR skipped.",
                error,
            )
            return None

        logger.info("OCR extracted %d character(s) from %s", len(text), path)
        return text
    finally:
        image.close()
