"""
DesktopAI v2.0 — Organize View
File: src/gui/views/organize_view.py

Displays the organization plan built from scan results.
Lets the user review, apply, and undo file moves.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QProgressBar,
)

from core.logger import get_logger
from services import FileService

logger = get_logger(__name__)


class OrganizeView(QWidget):
    """
    Organize screen — review plan and apply / undo file moves.

    Receives scan results via set_scan_context() from MainWindow.
    Emits history_changed() after a successful apply or undo so the
    HistoryView can refresh.
    """

    history_changed = Signal()

    # Column indices for the plan table
    _COL_FILE     = 0
    _COL_CATEGORY = 1
    _COL_DEST     = 2
    _COL_STATUS   = 3

    def __init__(self, service: FileService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service      = service
        self._scan_path    : str  = ""
        self._scan_results : list = []
        self._plan         : list = []   # list[dict] from FileService.plan_organisation()
        self._target_folder: Path | None = None

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # ── Status banner ──────────────────────────────────────────
        self._banner = QLabel("No scan results yet — go to Home and scan a folder first.")
        self._banner.setObjectName("StatusBanner")
        self._banner.setAlignment(Qt.AlignCenter)
        self._banner.setStyleSheet(
            "background:#2C2C2E; color:#8E8E93; padding:10px 16px;"
            "border-radius:8px; font-size:13px;"
        )
        layout.addWidget(self._banner)

        # ── Summary chips row ──────────────────────────────────────
        self._chips_row = QHBoxLayout()
        self._chips_row.setSpacing(8)
        chips_widget = QWidget()
        chips_widget.setLayout(self._chips_row)
        layout.addWidget(chips_widget)

        # ── Plan table ────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["File", "Category", "Destination", "Status"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

        # ── Progress bar (hidden until apply is running) ───────────
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        layout.addWidget(self._progress)

        # ── Action bar ────────────────────────────────────────────
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self._btn_choose = QPushButton("Choose Target Folder…")
        self._btn_choose.setObjectName("SecondaryButton")
        self._btn_choose.clicked.connect(self._choose_folder)
        action_bar.addWidget(self._btn_choose)

        self._btn_plan = QPushButton("Build Plan")
        self._btn_plan.setObjectName("SecondaryButton")
        self._btn_plan.setEnabled(False)
        self._btn_plan.clicked.connect(self._build_plan)
        action_bar.addWidget(self._btn_plan)

        action_bar.addStretch()

        self._btn_apply = QPushButton("Apply Plan")
        self._btn_apply.setObjectName("PrimaryButton")
        self._btn_apply.setEnabled(False)
        self._btn_apply.clicked.connect(self._apply_plan)
        action_bar.addWidget(self._btn_apply)

        self._btn_undo = QPushButton("Undo Last")
        self._btn_undo.setObjectName("SecondaryButton")
        self._btn_undo.setEnabled(False)
        self._btn_undo.clicked.connect(self._undo_last)
        action_bar.addWidget(self._btn_undo)

        layout.addLayout(action_bar)

    # ── Public API called by MainWindow ───────────────────────────

    def set_scan_context(self, scan_path: str, results: list) -> None:
        """Receive a completed scan from HomeView (via MainWindow broadcast)."""
        self._scan_path    = str(scan_path)
        self._scan_results = results or []
        self._plan         = []
        self._target_folder = Path(self._scan_path) if self._scan_path else None

        count = len(self._scan_results)
        self._banner.setText(
            f"✓  {count} file{'s' if count != 1 else ''} scanned from "
            f"{Path(self._scan_path).name!r} — choose a target folder and build a plan."
        )
        self._banner.setStyleSheet(
            "background:#1C3A2A; color:#30D158; padding:10px 16px;"
            "border-radius:8px; font-size:13px;"
        )
        self._update_chips()
        self._clear_table()
        self._btn_plan.setEnabled(bool(self._scan_results))
        self._btn_apply.setEnabled(False)

    # ── Internal helpers ──────────────────────────────────────────

    def _update_chips(self) -> None:
        """Rebuild category summary chips."""
        # Remove old chips
        while self._chips_row.count():
            item = self._chips_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Count by category
        cats: dict[str, int] = {}
        for r in self._scan_results:
            cat = r.get("category", "Unknown") if isinstance(r, dict) else getattr(r, "category", "Unknown")
            cats[cat] = cats.get(cat, 0) + 1

        for cat, count in sorted(cats.items(), key=lambda x: -x[1])[:8]:
            chip = QLabel(f"  {cat}  {count}  ")
            chip.setStyleSheet(
                "background:#2C2C2E; color:#E5E5EA; border-radius:10px;"
                "font-size:11px; padding:3px 8px;"
            )
            self._chips_row.addWidget(chip)
        self._chips_row.addStretch()

    def _clear_table(self) -> None:
        self._table.setRowCount(0)

    def _populate_table(self, plan: list) -> None:
        self._table.setRowCount(0)
        for item in plan:
            row = self._table.rowCount()
            self._table.insertRow(row)
            filename = Path(item.get("source", "")).name
            self._table.setItem(row, self._COL_FILE,     QTableWidgetItem(filename))
            self._table.setItem(row, self._COL_CATEGORY, QTableWidgetItem(item.get("category", "")))
            dest = item.get("destination", "")
            self._table.setItem(row, self._COL_DEST,     QTableWidgetItem(str(dest)))
            self._table.setItem(row, self._COL_STATUS,   QTableWidgetItem(item.get("status", "pending")))

    # ── Button handlers ───────────────────────────────────────────

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choose target folder",
            self._scan_path or str(Path.home()),
        )
        if folder:
            self._target_folder = Path(folder)
            self._btn_plan.setEnabled(bool(self._scan_results))
            self._banner.setText(
                self._banner.text().split("—")[0].strip()
                + f" — target: {self._target_folder.name!r}"
            )

    def _build_plan(self) -> None:
        if not self._scan_results:
            return
        target = self._target_folder or Path(self._scan_path)
        try:
            self._plan = self._service.plan_organisation(
                target_folder=target,
                scan_results=self._scan_results if isinstance(self._scan_results[0], dict) else None,
            )
        except Exception as exc:
            logger.error("plan_organisation failed: %s", exc)
            QMessageBox.warning(self, "Plan Error", str(exc))
            return

        self._populate_table(self._plan)
        count = len(self._plan)
        self._banner.setText(
            f"Plan ready — {count} action{'s' if count != 1 else ''} to apply."
        )
        self._btn_apply.setEnabled(bool(self._plan))

    def _apply_plan(self) -> None:
        if not self._plan:
            return
        confirm = QMessageBox.question(
            self, "Apply Plan",
            f"Move {len(self._plan)} file(s)?\nThis can be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        self._btn_apply.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)  # indeterminate

        try:
            result = self._service.apply_plan(self._plan)
        except Exception as exc:
            logger.error("apply_plan failed: %s", exc)
            QMessageBox.critical(self, "Apply Failed", str(exc))
            self._progress.setVisible(False)
            self._btn_apply.setEnabled(True)
            return

        self._progress.setVisible(False)
        success  = result.get("success", 0)
        failed   = result.get("failed", 0)
        self._banner.setText(
            f"✓  Done — {success} moved, {failed} failed."
        )
        self._btn_undo.setEnabled(True)
        self.history_changed.emit()

    def _undo_last(self) -> None:
        confirm = QMessageBox.question(
            self, "Undo", "Reverse the last applied batch?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            result = self._service.undo_last()
        except Exception as exc:
            logger.error("undo_last failed: %s", exc)
            QMessageBox.critical(self, "Undo Failed", str(exc))
            return

        reversed_count = result.get("reversed", 0)
        self._banner.setText(f"↶  Undone — {reversed_count} file(s) restored.")
        self._btn_undo.setEnabled(False)
        self.history_changed.emit()