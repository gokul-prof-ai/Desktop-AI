"""
DesktopAI v2.0 — Organize View (Review Workspace)
File: src/gui/views/organize_view.py
"""
from __future__ import annotations
import csv
import uuid
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QSplitter,
    QSizePolicy,
)

from domain.organizer.planner import OrganizationPlanner
from domain.organizer.organizer import AutoOrganizer
from core.logger import get_logger

logger = get_logger(__name__)


class OrganizeView(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.scan_path: Path | None = None
        self.results: list = []
        self.actions: list = []
        self.organizer = AutoOrganizer()
        self.batch_id: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Sub-header
        sub = QLabel(
            "Review the AI's organization plan before applying any changes. "
            "All operations can be undone."
        )
        sub.setObjectName("Muted")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # Status banner
        self.banner = self._build_banner()
        layout.addWidget(self.banner)

        # Category summary chips row
        self.chips_row = QHBoxLayout()
        self.chips_row.setSpacing(6)
        self.chips_widget = QWidget()
        self.chips_widget.setLayout(self.chips_row)
        self.chips_widget.setVisible(False)
        layout.addWidget(self.chips_widget)

        # Plan table card
        table_card = QFrame()
        table_card.setObjectName("Card")
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)

        # Table toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(16, 12, 16, 8)

        plan_title = QLabel("Organization Plan")
        plan_title.setObjectName("SubHeading")
        toolbar.addWidget(plan_title)
        toolbar.addStretch()

        self.count_label = QLabel("0 files")
        self.count_label.setObjectName("Muted")
        toolbar.addWidget(self.count_label)

        tc_layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Destination", "Confidence"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        tc_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)

        # Action bar
        layout.addWidget(self._build_action_bar())

        self._set_enabled(False)

    def _build_banner(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedHeight(60)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        self.banner_icon = QLabel("○")
        self.banner_icon.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.banner_icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        self.banner_title = QLabel("No scan loaded")
        self.banner_title.setObjectName("SubHeading")

        self.banner_sub = QLabel(
            "Scan a folder from Home to generate an organization plan."
        )
        self.banner_sub.setObjectName("Caption")

        text_col.addWidget(self.banner_title)
        text_col.addWidget(self.banner_sub)

        layout.addLayout(text_col)
        layout.addStretch()

        return card

    def _build_action_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("Card")
        bar.setFixedHeight(56)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        self.apply_btn = QPushButton("Apply Plan")
        self.apply_btn.setObjectName("PrimaryButton")
        self.apply_btn.clicked.connect(self._apply_plan)

        self.undo_btn = QPushButton("Undo Last")
        self.undo_btn.setObjectName("SecondaryButton")
        self.undo_btn.clicked.connect(self._undo)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setObjectName("GhostButton")
        self.export_btn.clicked.connect(self._export)

        layout.addWidget(self.apply_btn)
        layout.addWidget(self.undo_btn)
        layout.addWidget(self.export_btn)
        layout.addStretch()

        # Safety note
        note = QLabel("ⓘ  All operations are reversible via Undo Last")
        note.setObjectName("Caption")
        layout.addWidget(note)

        return bar

    # ── Public API ─────────────────────────────────────────────────

    def set_scan_context(self, scan_path: str, results: list) -> None:
        self.scan_path = Path(scan_path)
        self.results = results
        self.actions = []
        self.batch_id = None
        self._build_plan()

    # ── Plan ───────────────────────────────────────────────────────

    def _build_plan(self) -> None:
        if not self.scan_path or not self.results:
            self.banner_title.setText("No files to organize")
            self.banner_sub.setText("The scan returned no results.")
            self._set_enabled(False)
            return

        target = self.scan_path.parent / f"{self.scan_path.name} - Organized"

        try:
            planner = OrganizationPlanner()
            files = [r.file_info for r in self.results if not r.skipped]
            self.actions = planner.create_plan(files, target)
            self._populate_table()
            self._populate_chips()

            self.banner_icon.setText("✓")
            self.banner_icon.setStyleSheet("color: #30D158; font-size: 18px;")
            self.banner_title.setText(f"Plan ready — {len(self.actions)} file operations")
            self.banner_sub.setText(
                f"Review the plan below, then click Apply. Target: {target}"
            )
            self._set_enabled(bool(self.actions))

        except Exception as exc:
            self.banner_icon.setText("⚠")
            self.banner_icon.setStyleSheet("color: #FFD60A; font-size: 18px;")
            self.banner_title.setText("Unable to build plan")
            self.banner_sub.setText(str(exc))
            self._set_enabled(False)

    def _populate_table(self) -> None:
        self.table.setRowCount(len(self.actions))
        for row, action in enumerate(self.actions):
            self.table.setItem(row, 0, QTableWidgetItem(action.source_path.name))
            self.table.setItem(row, 1, QTableWidgetItem(action.category))
            self.table.setItem(row, 2, QTableWidgetItem(str(action.planned_target_path)))
            pct = int(action.confidence * 100)
            conf_item = QTableWidgetItem(f"{pct}%")
            if pct >= 80:
                conf_item.setForeground(Qt.green)
            elif pct >= 50:
                conf_item.setForeground(Qt.yellow)
            else:
                conf_item.setForeground(Qt.red)
            self.table.setItem(row, 3, conf_item)
            self.table.setRowHeight(row, 36)
        self.count_label.setText(f"{len(self.actions)} files")

    def _populate_chips(self) -> None:
        """Build category summary chips above the table."""
        # Clear old chips
        while self.chips_row.count():
            item = self.chips_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cats: dict[str, int] = {}
        for a in self.actions:
            cats[a.category] = cats.get(a.category, 0) + 1

        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            chip = QLabel(f"  {cat}  {count}  ")
            chip.setObjectName("TagNeutral")
            chip.setToolTip(f"{count} files → {cat}")
            self.chips_row.addWidget(chip)

        self.chips_row.addStretch()
        self.chips_widget.setVisible(bool(cats))

    # ── Actions ────────────────────────────────────────────────────

    def _apply_plan(self) -> None:
        if not self.actions:
            return

        # Group by category for confirmation dialog
        cats: dict[str, int] = {}
        for a in self.actions:
            cats[a.category] = cats.get(a.category, 0) + 1

        cat_lines = "\n".join(f"  {cat}: {n} files" for cat, n in sorted(cats.items()))

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Confirm Organization")
        dlg.setText(
            f"DesktopAI will move {len(self.actions)} files.\n\n"
            f"{cat_lines}\n\n"
            "This operation can be undone using  Undo Last."
        )
        dlg.setIcon(QMessageBox.Question)
        apply_btn = dlg.addButton("Apply Safely", QMessageBox.AcceptRole)
        dlg.addButton("Cancel", QMessageBox.RejectRole)
        dlg.setDefaultButton(apply_btn)
        dlg.exec()

        if dlg.clickedButton() is not apply_btn:
            return

        self.batch_id = str(uuid.uuid4())
        try:
            stats = self.organizer.execute_plan(self.actions, batch_id=self.batch_id)
            self.banner_icon.setText("✓")
            self.banner_icon.setStyleSheet("color: #30D158; font-size: 18px;")
            self.banner_title.setText("Organization complete")
            self.banner_sub.setText(
                f"Moved {stats['success']}  ·  Failed {stats['failed']}  ·  Skipped {stats['skipped']}"
            )
            self.apply_btn.setEnabled(False)
            self.undo_btn.setEnabled(True)
        except Exception as exc:
            QMessageBox.critical(self, "Failed", str(exc))

    def _undo(self) -> None:
        if not self.batch_id:
            QMessageBox.information(self, "Nothing to undo", "No batch to reverse.")
            return
        try:
            count = self.organizer.undo_last_batch(self.batch_id)
            self.banner_title.setText("Undo complete")
            self.banner_sub.setText(f"{count} operation(s) reversed.")
            self.batch_id = None
            self._set_enabled(True)
        except Exception as exc:
            QMessageBox.critical(self, "Undo Failed", str(exc))

    def _export(self) -> None:
        if not self.actions:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Report", "desktopai_report.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Source", "Category", "Destination", "Confidence"])
                for a in self.actions:
                    w.writerow([str(a.source_path), a.category,
                                 str(a.planned_target_path), a.confidence])
            QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
        except OSError as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _set_enabled(self, enabled: bool) -> None:
        self.apply_btn.setEnabled(enabled)
        self.export_btn.setEnabled(bool(self.actions))
        self.undo_btn.setEnabled(bool(self.batch_id))