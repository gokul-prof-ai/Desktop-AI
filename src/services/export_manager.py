"""
DesktopAI V2 - Export Manager
==============================

M11: Export history and organization plans to CSV and PDF.

Responsibilities:
    - Export history records to CSV
    - Export organization plans to CSV
    - Export history records to PDF
    - Export organization plans to PDF

This service is intentionally independent from the GUI. GUI views should
call this service rather than accessing the database or ReportLab directly.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.logger import get_logger

logger = get_logger(__name__)


class ExportError(RuntimeError):
    """Raised when an export operation cannot be completed."""


class ExportManager:
    """
    Service responsible for exporting DesktopAI data.

    The manager accepts plain dictionaries/lists so that GUI code does not
    need to know about database row objects or domain dataclasses.
    """

    HISTORY_COLUMNS = (
        "id",
        "batch_id",
        "action_type",
        "source_path",
        "target_path",
        "category",
        "confidence",
        "status",
        "error_message",
        "performed_at",
    )

    PLAN_COLUMNS = (
        "action",
        "source_path",
        "target_path",
        "category",
        "confidence",
        "reason",
    )

    def __init__(self) -> None:
        self._generated_at = datetime.now

    # ------------------------------------------------------------------
    # Public CSV API
    # ------------------------------------------------------------------

    def export_history_csv(
        self,
        records: Iterable[Mapping[str, Any]],
        output_path: str | Path,
    ) -> Path:
        """
        Export history records to a CSV file.

        Parameters
        ----------
        records:
            Iterable of dictionaries containing history information.

        output_path:
            Destination CSV path.

        Returns
        -------
        Path
            The resolved output path.
        """
        rows = self._normalise_records(records)
        destination = self._prepare_output_path(output_path, ".csv")

        try:
            with destination.open(
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=self.HISTORY_COLUMNS,
                    extrasaction="ignore",
                )
                writer.writeheader()

                for row in rows:
                    writer.writerow(
                        {
                            column: self._csv_value(row.get(column))
                            for column in self.HISTORY_COLUMNS
                        }
                    )

        except OSError as exc:
            logger.exception("Failed to export history CSV: %s", exc)
            raise ExportError(
                f"Unable to write history CSV: {destination}"
            ) from exc

        logger.info(
            "History CSV exported: %s (%d records)",
            destination,
            len(rows),
        )

        return destination

    def export_plan_csv(
        self,
        plan: Any,
        output_path: str | Path,
    ) -> Path:
        """
        Export an organization plan to CSV.

        The method accepts common DesktopAI plan representations:

            - list[dict]
            - tuple/list containing action dictionaries
            - dict with ``actions``
            - dict with ``plan`` containing actions

        Unknown fields are ignored.
        """
        rows = self._extract_plan_rows(plan)
        destination = self._prepare_output_path(output_path, ".csv")

        try:
            with destination.open(
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=self.PLAN_COLUMNS,
                    extrasaction="ignore",
                )
                writer.writeheader()

                for row in rows:
                    writer.writerow(
                        {
                            column: self._csv_value(row.get(column))
                            for column in self.PLAN_COLUMNS
                        }
                    )

        except OSError as exc:
            logger.exception("Failed to export plan CSV: %s", exc)
            raise ExportError(
                f"Unable to write plan CSV: {destination}"
            ) from exc

        logger.info(
            "Organization plan CSV exported: %s (%d actions)",
            destination,
            len(rows),
        )

        return destination

    # ------------------------------------------------------------------
    # Public PDF API
    # ------------------------------------------------------------------

    def export_history_pdf(
        self,
        records: Iterable[Mapping[str, Any]],
        output_path: str | Path,
        title: str = "DesktopAI History Report",
    ) -> Path:
        """
        Export history records as a formatted PDF report.
        """
        rows = self._normalise_records(records)
        destination = self._prepare_output_path(output_path, ".pdf")

        summary = self._history_summary(rows)

        story = self._build_pdf_header(title)
        story.extend(
            self._build_summary_table(
                summary,
                "History Summary",
            )
        )
        story.append(Spacer(1, 8 * mm))

        story.append(
            Paragraph(
                "File Operations",
                self._styles()["section"],
            )
        )
        story.append(Spacer(1, 2 * mm))

        story.append(
            self._history_pdf_table(rows)
        )

        self._write_pdf(destination, story)

        logger.info(
            "History PDF exported: %s (%d records)",
            destination,
            len(rows),
        )

        return destination

    def export_plan_pdf(
        self,
        plan: Any,
        output_path: str | Path,
        title: str = "DesktopAI Organization Plan",
    ) -> Path:
        """
        Export an organization plan as a formatted PDF report.
        """
        rows = self._extract_plan_rows(plan)
        destination = self._prepare_output_path(output_path, ".pdf")

        summary = self._plan_summary(rows)

        story = self._build_pdf_header(title)
        story.extend(
            self._build_summary_table(
                summary,
                "Plan Summary",
            )
        )
        story.append(Spacer(1, 8 * mm))

        story.append(
            Paragraph(
                "Planned File Operations",
                self._styles()["section"],
            )
        )
        story.append(Spacer(1, 2 * mm))

        story.append(
            self._plan_pdf_table(rows)
        )

        self._write_pdf(destination, story)

        logger.info(
            "Organization plan PDF exported: %s (%d actions)",
            destination,
            len(rows),
        )

        return destination

    # ------------------------------------------------------------------
    # PDF helpers
    # ------------------------------------------------------------------

    def _build_pdf_header(self, title: str) -> list[Any]:
        """
        Build the common PDF header.
        """
        styles = self._styles()

        generated = self._generated_at().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return [
            Paragraph(
                "DESKTOPAI",
                styles["brand"],
            ),
            Spacer(1, 2 * mm),
            Paragraph(
                self._escape_text(title),
                styles["title"],
            ),
            Spacer(1, 2 * mm),
            Paragraph(
                f"Generated: {generated}",
                styles["metadata"],
            ),
            Spacer(1, 6 * mm),
        ]

    def _build_summary_table(
        self,
        values: Mapping[str, Any],
        heading: str,
    ) -> list[Any]:
        styles = self._styles()

        data: list[list[Any]] = [
            [
                Paragraph(
                    self._escape_text(heading),
                    styles["summary_heading"],
                ),
                "",
            ]
        ]

        for key, value in values.items():
            data.append(
                [
                    Paragraph(
                        self._escape_text(str(key)),
                        styles["summary_key"],
                    ),
                    Paragraph(
                        self._escape_text(str(value)),
                        styles["summary_value"],
                    ),
                ]
            )

        table = Table(
            data,
            colWidths=[55 * mm, 115 * mm],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "SPAN",
                        (0, 0),
                        (1, 0),
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (1, 0),
                        colors.HexColor("#20242A"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (1, 0),
                        colors.white,
                    ),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (0, -1),
                        colors.HexColor("#F1F3F5"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#D0D4D8"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        return [table]

    def _history_pdf_table(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> Table:
        styles = self._styles()

        header = [
            "Action",
            "Source",
            "Target",
            "Category",
            "Status",
            "Confidence",
        ]

        data: list[list[Any]] = [header]

        for row in rows:
            data.append(
                [
                    self._paragraph(
                        row.get("action_type", ""),
                        styles["table"],
                    ),
                    self._paragraph(
                        row.get("source_path", ""),
                        styles["table"],
                    ),
                    self._paragraph(
                        row.get("target_path", ""),
                        styles["table"],
                    ),
                    self._paragraph(
                        row.get("category", ""),
                        styles["table"],
                    ),
                    self._paragraph(
                        row.get("status", ""),
                        styles["table"],
                    ),
                    self._paragraph(
                        self._format_confidence(
                            row.get("confidence")
                        ),
                        styles["table"],
                    ),
                ]
            )

        if not rows:
            data.append(
                [
                    Paragraph(
                        "No history records available.",
                        styles["empty"],
                    ),
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )

        table = Table(
            data,
            colWidths=[
                22 * mm,
                48 * mm,
                48 * mm,
                25 * mm,
                20 * mm,
                22 * mm,
            ],
            repeatRows=1,
        )

        self._apply_table_style(table)

        return table

    def _plan_pdf_table(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> Table:
        styles = self._styles()

        header = [
            "Action",
            "Source",
            "Target",
            "Category",
            "Confidence",
            "Reason",
        ]

        data: list[list[Any]] = [header]

        for row in rows:
            data.append(
                [
                    self._paragraph(
                        row.get("action", ""),
                        styles["table"],
                    ),
                    self._paragraph(
                        row.get("source_path", ""),
                        styles["table"],
                    ),
                    self._paragraph(
                        row.get("target_path", ""),
                        styles["table"],
                    ),
                    self._paragraph(
                        row.get("category", ""),
                        styles["table"],
                    ),
                    self._paragraph(
                        self._format_confidence(
                            row.get("confidence")
                        ),
                        styles["table"],
                    ),
                    self._paragraph(
                        row.get("reason", ""),
                        styles["table"],
                    ),
                ]
            )

        if not rows:
            data.append(
                [
                    Paragraph(
                        "No planned actions available.",
                        styles["empty"],
                    ),
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )

        table = Table(
            data,
            colWidths=[
                22 * mm,
                45 * mm,
                45 * mm,
                24 * mm,
                22 * mm,
                42 * mm,
            ],
            repeatRows=1,
        )

        self._apply_table_style(table)

        return table

    @staticmethod
    def _apply_table_style(table: Table) -> None:
        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#20242A"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, 0),
                        7,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.3,
                        colors.HexColor("#D0D4D8"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor("#F8F9FA"),
                        ],
                    ),
                ]
            )
        )

    def _write_pdf(
        self,
        destination: Path,
        story: Sequence[Any],
    ) -> None:
        try:
            document = SimpleDocTemplate(
                str(destination),
                pagesize=landscape(A4),
                rightMargin=10 * mm,
                leftMargin=10 * mm,
                topMargin=10 * mm,
                bottomMargin=10 * mm,
                title="DesktopAI Export",
                author="DesktopAI",
            )

            document.build(
                list(story),
                onFirstPage=self._draw_footer,
                onLaterPages=self._draw_footer,
            )

        except (OSError, IOError, ValueError) as exc:
            logger.exception("Failed to create PDF: %s", exc)
            raise ExportError(
                f"Unable to write PDF: {destination}"
            ) from exc

    @staticmethod
    def _draw_footer(
        canvas: Any,
        document: Any,
    ) -> None:
        canvas.saveState()

        width, _ = document.pagesize

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(
            colors.HexColor("#6C757D")
        )

        canvas.drawString(
            10 * mm,
            6 * mm,
            "DesktopAI — Local-first file intelligence",
        )

        canvas.drawRightString(
            width - 10 * mm,
            6 * mm,
            f"Page {document.page}",
        )

        canvas.restoreState()

    # ------------------------------------------------------------------
    # Data normalisation
    # ------------------------------------------------------------------

    @classmethod
    def _normalise_records(
        cls,
        records: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        if records is None:
            return []

        result: list[dict[str, Any]] = []

        for record in records:
            if isinstance(record, Mapping):
                result.append(dict(record))
                continue

            if hasattr(record, "keys"):
                try:
                    result.append(
                        {
                            key: record[key]
                            for key in record.keys()
                        }
                    )
                    continue
                except Exception:
                    pass

            if hasattr(record, "__dict__"):
                result.append(
                    {
                        key: value
                        for key, value in vars(record).items()
                        if not key.startswith("_")
                    }
                )

        return result

    @classmethod
    def _extract_plan_rows(
        cls,
        plan: Any,
    ) -> list[dict[str, Any]]:
        if plan is None:
            return []

        if isinstance(plan, Mapping):
            for key in (
                "actions",
                "plan",
                "items",
                "operations",
                "action_items",
            ):
                if key in plan:
                    return cls._extract_plan_rows(plan[key])

            return [dict(plan)]

        if isinstance(plan, (list, tuple)):
            rows: list[dict[str, Any]] = []

            for item in plan:
                if isinstance(item, Mapping):
                    rows.append(dict(item))
                elif hasattr(item, "__dict__"):
                    rows.append(
                        {
                            key: value
                            for key, value in vars(item).items()
                            if not key.startswith("_")
                        }
                    )

            return rows

        if hasattr(plan, "__dict__"):
            return [
                {
                    key: value
                    for key, value in vars(plan).items()
                    if not key.startswith("_")
                }
            ]

        return []

    @staticmethod
    def _history_summary(
        rows: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        total = len(rows)

        completed = sum(
            1
            for row in rows
            if str(row.get("status", "")).lower()
            in {"completed", "success", "successful", "done"}
        )

        failed = sum(
            1
            for row in rows
            if str(row.get("status", "")).lower()
            in {"failed", "error"}
        )

        undone = sum(
            1
            for row in rows
            if str(row.get("status", "")).lower()
            in {"undone", "undo"}
        )

        categories = {
            str(row.get("category"))
            for row in rows
            if row.get("category")
        }

        return {
            "Total records": total,
            "Completed": completed,
            "Failed": failed,
            "Undone": undone,
            "Categories": len(categories),
        }

    @staticmethod
    def _plan_summary(
        rows: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        categories = {
            str(row.get("category"))
            for row in rows
            if row.get("category")
        }

        return {
            "Total planned actions": len(rows),
            "Categories": len(categories),
        }

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _prepare_output_path(
        output_path: str | Path,
        extension: str,
    ) -> Path:
        if not output_path:
            raise ExportError("An output path is required.")

        path = Path(output_path).expanduser()

        if path.suffix.lower() != extension:
            path = path.with_suffix(extension)

        try:
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as exc:
            raise ExportError(
                f"Unable to create output directory: {path.parent}"
            ) from exc

        return path.resolve()

    @staticmethod
    def _csv_value(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, float):
            return f"{value:.4f}"

        return str(value)

    @staticmethod
    def _format_confidence(value: Any) -> str:
        if value is None or value == "":
            return ""

        try:
            number = float(value)

            if number <= 1:
                return f"{number * 100:.1f}%"

            return f"{number:.1f}%"

        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _escape_text(value: Any) -> str:
        text = "" if value is None else str(value)

        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @classmethod
    def _paragraph(
        cls,
        value: Any,
        style: ParagraphStyle,
    ) -> Paragraph:
        return Paragraph(
            cls._escape_text(value),
            style,
        )

    @staticmethod
    def _styles() -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()

        return {
            "brand": ParagraphStyle(
                "DesktopAIBrand",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=18,
                alignment=TA_LEFT,
            ),
            "title": ParagraphStyle(
                "DesktopAITitle",
                parent=base["Title"],
                fontName="Helvetica-Bold",
                fontSize=20,
                leading=23,
                alignment=TA_LEFT,
            ),
            "metadata": ParagraphStyle(
                "DesktopAIMetadata",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
            ),
            "section": ParagraphStyle(
                "DesktopAISection",
                parent=base["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=14,
            ),
            "summary_heading": ParagraphStyle(
                "DesktopAISummaryHeading",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=11,
                alignment=TA_LEFT,
            ),
            "summary_key": ParagraphStyle(
                "DesktopAISummaryKey",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
            ),
            "summary_value": ParagraphStyle(
                "DesktopAISummaryValue",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
            ),
            "table": ParagraphStyle(
                "DesktopAITable",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=6.5,
                leading=8,
                alignment=TA_LEFT,
            ),
            "empty": ParagraphStyle(
                "DesktopAIEmpty",
                parent=base["Normal"],
                fontName="Helvetica-Oblique",
                fontSize=8,
                leading=10,
            ),
        }


__all__ = [
    "ExportError",
    "ExportManager",
]