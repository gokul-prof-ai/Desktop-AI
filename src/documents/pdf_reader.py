"""
DesktopAI
PDF Reader Module

Extracts text from PDF files using PyMuPDF (fitz).
Includes error suppression for corrupted files.
"""
import fitz  # PyMuPDF
from pathlib import Path
from core.logger import get_logger

logger = get_logger("documents")

# Suppress ugly C-level MuPDF console errors for corrupted/empty PDFs
fitz.TOOLS.mupdf_display_errors(False)

def read_pdf_text(file_path: Path) -> str | None:
    """
    Extract text from a PDF file.
    Returns None if the file is missing, corrupted or unreadable.
    """
    if not file_path.exists():
        logger.debug(f"Skipped unreadable PDF: {file_path.name}")
        return None

    try:
        with fitz.open(file_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text.strip()
    except Exception as e:
        # We log this quietly so it doesn't clutter the terminal
        logger.debug(f"Skipped unreadable PDF: {file_path.name}")
        return None