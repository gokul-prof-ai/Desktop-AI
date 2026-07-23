"""
DesktopAI
Watch Suggestion Engine

Turns a newly detected file (from the FolderWatcher) into a
WatchSuggestion: extracted text (if the file type supports it),
an AI-assigned category, and an AI-suggested destination folder.

This module never moves, renames, or deletes anything — it only
builds a suggestion. Turning a suggestion into an actual file move
is the Organizer module's job, and always requires an explicit
preview() + apply() call.
"""

from datetime import datetime
from pathlib import Path

from ai.classifier import classify_file
from ai.recommender import recommend_action
from core.logger import get_logger
from documents.docx_reader import read_docx_text
from documents.excel_reader import read_excel_text
from documents.ocr_reader import read_image_text
from documents.pdf_reader import read_pdf_text
from watcher.suggestion import WatchSuggestion

logger = get_logger("watcher")

# Maps a lowercase file extension to the reader function that can
# extract text from it.
_READERS = {
    ".pdf": read_pdf_text,
    ".docx": read_docx_text,
    ".xlsx": read_excel_text,
    ".png": read_image_text,
    ".jpg": read_image_text,
    ".jpeg": read_image_text,
}

# Extensions that are already plain text and don't need a special
# reader — they can be read directly.
_PLAIN_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".log"}


def extract_text(path: Path) -> str:
    """
    Extract whatever text content is available for a file, based on
    its extension.

    Args:
        path (Path):
            The file to read.

    Returns:
        str:
            The extracted text, or an empty string if the file type
            isn't supported or nothing could be read. An empty
            string (never None) keeps callers simple, since
            classify_file() and recommend_action() already treat
            empty text as "no content available".
    """
    extension = path.suffix.lower()

    reader = _READERS.get(extension)
    if reader is not None:
        text = reader(path)
        return text or ""

    if extension in _PLAIN_TEXT_EXTENSIONS:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError as error:
            logger.warning("Could not read text file %s: %s", path, error)
            return ""

    logger.info("No text reader for %s, skipping content extraction.", path)
    return ""


def build_suggestion(path: Path) -> WatchSuggestion:
    """
    Build a WatchSuggestion for a newly detected file: extract its
    text (if supported), classify it, and recommend a destination
    folder.

    Args:
        path (Path):
            The newly detected, stable file.

    Returns:
        WatchSuggestion:
            The resulting suggestion. `category` and
            `suggested_folder` may be None if the AI is unavailable
            or the file type isn't supported — that's expected, not
            an error.
    """
    text = extract_text(path)

    category = classify_file(text)
    suggested_folder = recommend_action(path.name, category=category, text=text)

    logger.info(
        "Built suggestion for %s: category=%s, folder=%s",
        path,
        category,
        suggested_folder,
    )

    return WatchSuggestion(
        path=path,
        category=category,
        suggested_folder=suggested_folder,
        detected_at=datetime.now(),
    )