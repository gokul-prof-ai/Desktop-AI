"""
DesktopAI
Excel Reader

Extracts cell content from Excel (.xlsx) files, across all sheets
in the workbook.
"""

import zipfile
from pathlib import Path

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

from core.logger import get_logger

logger = get_logger("documents")


def read_excel_text(path: Path) -> str | None:
    """
    Extract all cell values from an Excel file, across every sheet.

    Args:
        path (Path):
            The Excel (.xlsx) file to read.

    Returns:
        str | None:
            The extracted text (one value per line), or None if the
            file could not be read (missing, corrupted, or not a
            valid Excel file). A None result is expected behavior
            for a bad file, not a crash.
    """

    if not path.exists():
        logger.warning("Excel file not found: %s", path)
        return None

    try:
        # data_only=True reads the last calculated value of formulas,
        # rather than the formula text itself (e.g. 95 instead of "=B2+5").
        workbook = openpyxl.load_workbook(path, data_only=True)
    except (zipfile.BadZipFile, InvalidFileException) as error:
        logger.warning("Could not open Excel file %s: %s", path, error)
        return None

    text_parts: list[str] = []

    for sheet in workbook.worksheets:
        for row in sheet.iter_rows(values_only=True):
            for cell_value in row:
                if cell_value is not None:
                    text_parts.append(str(cell_value))

    workbook.close()

    text = "\n".join(text_parts)

    logger.info("Read %d value(s) from %s", len(text_parts), path)

    return text