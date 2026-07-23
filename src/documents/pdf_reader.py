"""
DesktopAI
PDF Reader

Extracts text content from PDF files, so later phases (AI, search)
have actual content to work with, not just file metadata.
"""

from pathlib import Path

import fitz

from core.logger import get_logger

logger = get_logger("documents")


def read_pdf_text(path: Path) -> str | None:
    """
    Extract all text from a PDF file.

    Args:
        path (Path):
            The PDF file to read.

    Returns:
        str | None:
            The extracted text, or None if the file could not be
            read (missing, corrupted, password-protected, or not
            a valid PDF). A None result is expected behavior for a
            bad file, not a crash.
    """

    if not path.exists():
        logger.warning("PDF not found: %s", path)
        return None

    try:
        document = fitz.open(path)
    except RuntimeError as error:
        # PyMuPDF raises RuntimeError (or a subclass of it) for
        # corrupted, password-protected, or invalid PDF files.
        logger.warning("Could not open PDF %s: %s", path, error)
        return None

    try:
        text_parts = [page.get_text() for page in document]
    finally:
        document.close()

    text = "".join(text_parts)

    logger.info("Read %d character(s) from %s", len(text), path)

    return text