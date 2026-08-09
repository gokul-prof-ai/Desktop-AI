"""
DesktopAI
Optional OCR reader.

OCR dependencies are intentionally imported lazily.

Reason:
A missing OCR package must never prevent unrelated modules
or tests from being imported.
"""

from __future__ import annotations

from pathlib import Path

from core.logger import get_logger


logger = get_logger("documents")


def read_image_text(path: Path) -> str | None:
    """
    Extract text from an image using Tesseract.

    OCR is optional. If pytesseract or the Tesseract executable
    is unavailable, None is returned instead of crashing the app.
    """

    if not path.exists():
        logger.warning("Image not found: %s", path)
        return None

    try:
        from PIL import Image, UnidentifiedImageError
    except ModuleNotFoundError:
        logger.warning(
            "Pillow is not installed. OCR skipped."
        )
        return None

    try:
        import pytesseract
    except ModuleNotFoundError:
        logger.warning(
            "pytesseract is not installed. OCR skipped."
        )
        return None

    try:
        image = Image.open(path)
    except UnidentifiedImageError as exc:
        logger.warning(
            "Invalid image %s: %s",
            path,
            exc,
        )
        return None
    except OSError as exc:
        logger.warning(
            "Could not open image %s: %s",
            path,
            exc,
        )
        return None

    try:
        text = pytesseract.image_to_string(image)

    except pytesseract.TesseractNotFoundError as exc:
        logger.warning(
            "Tesseract executable not found. "
            "Install Tesseract OCR to enable image OCR: %s",
            exc,
        )
        return None

    except pytesseract.TesseractError as exc:
        logger.warning(
            "Tesseract OCR failed for %s: %s",
            path,
            exc,
        )
        return None

    except Exception as exc:
        logger.exception(
            "Unexpected OCR error for %s: %s",
            path,
            exc,
        )
        return None

    finally:
        image.close()

    cleaned = text.strip()

    logger.info(
        "OCR extracted %d character(s) from %s",
        len(cleaned),
        path,
    )

    return cleaned or None