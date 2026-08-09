"""
DesktopAI v2.0
Organization workspace.
"""

from __future__ import annotations

import csv
import uuid
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFileDialog,
)

from domain.organizer.planner import OrganizationPlanner
from domain.organizer.organizer import AutoOrganizer


class OrganizeView(QWidget):

    def __init__(self):
        super().__init__()

        self.scan_path: Path | None = None
        self.results: list = []
        self.actions: list = []
        self.organizer = AutoOrganizer()
        self.batch_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        layout.setSpacing(14)

        self.status_card = QFrame()
        self.status_card.setObjectName(
            "Card"
        )

        status_layout = QVBoxLayout(
            self.status_card
        )

        self.status_title = QLabel(
            "No scan loaded"
        )
        self.status_title.setObjectName(
            "Heading"
        )

        self.status_text = QLabel(
            "Scan a folder from Home first."
        )
        self.status_text.setObjectName(
            "Muted"
        )
        self.status_text.setWordWrap(True)

        status_layout.addWidget(
            self.status_title
        )

        status_layout.addWidget(
            self.status_text
        )

        layout.addWidget(
            self.status_card
        )

        self.plan_card = QFrame()
        self.plan_card.setObjectName(
            "Card"
        )

        plan_layout = QVBoxLayout(
            self.plan_card
        )

        header = QHBoxLayout()

        title = QLabel(
            "Organization Plan"
        )
        title.setObjectName(
            "Heading"
        )

        self.count_label = QLabel(
            "0 files"
        )
        self.count_label.setObjectName(
            "Muted"
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(
            self.count_label
        )

        plan_layout.addLayout(
            header
        )

        self.table = QTableWidget()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels(
            [
                "File",
                "Category",
                "Destination",
                "Confidence",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        self.table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )

        self.table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.Stretch,
        )

        self.table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents,
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        plan_layout.addWidget(
            self.table,
            1,
        )

        layout.addWidget(
            self.plan_card,
            1,
        )

        actions_card = QFrame()
        actions_card.setObjectName(
            "Card"
        )

        actions_layout = QHBoxLayout(
            actions_card
        )

        self.apply_button = QPushButton(
            "Apply Plan"
        )
        self.apply_button.setObjectName(
            "PrimaryButton"
        )

        self.undo_button = QPushButton(
            "Undo Last"
        )
        self.undo_button.setObjectName(
            "SecondaryButton"
        )

        self.export_button = QPushButton(
            "Export Report"
        )
        self.export_button.setObjectName(
            "SecondaryButton"
        )

        self.apply_button.clicked.connect(
            self._apply_plan
        )

        self.undo_button.clicked.connect(
            self._undo
        )

        self.export_button.clicked.connect(
            self._export_report
        )

        actions_layout.addWidget(
            self.apply_button
        )

        actions_layout.addWidget(
            self.undo_button
        )

        actions_layout.addWidget(
            self.export_button
        )

        actions_layout.addStretch()

        layout.addWidget(
            actions_card
        )

        self._set_enabled_state(
            False
        )

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def set_scan_context(
        self,
        scan_path: str,
        results: list,
    ):

        self.scan_path = Path(
            scan_path
        )

        self.results = results

        self.actions = []
        self.batch_id = None

        self._build_plan()

    # ==================================================================
    # PLAN
    # ==================================================================

    def _build_plan(self):

        if not self.scan_path:
            return

        if not self.results:
            self.status_title.setText(
                "Scan completed with no files"
            )

            self.status_text.setText(
                "There are no files available for organization."
            )

            self.table.setRowCount(0)

            self._set_enabled_state(
                False
            )

            return

        target = (
            self.scan_path.parent
            / f"{self.scan_path.name} - Organized"
        )

        try:
            planner = OrganizationPlanner()

            files = [
                result.file_info
                for result in self.results
                if not result.skipped
            ]

            self.actions = planner.create_plan(
                files,
                target,
            )

            self._populate_plan()

            self.status_title.setText(
                "Organization plan ready"
            )

            self.status_text.setText(
                f"{len(self.actions)} safe file operation(s) "
                f"prepared for review."
            )

            self._set_enabled_state(
                bool(self.actions)
            )

        except Exception as exc:

            self.status_title.setText(
                "Unable to build plan"
            )

            self.status_text.setText(
                str(exc)
            )

            self._set_enabled_state(
                False
            )

    def _populate_plan(self):

        self.table.setRowCount(
            len(self.actions)
        )

        for row, action in enumerate(
            self.actions
        ):

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(
                    action.source_path.name
                ),
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    action.category
                ),
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    str(
                        action.planned_target_path
                    )
                ),
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(
                    f"{int(action.confidence * 100)}%"
                ),
            )

        self.count_label.setText(
            f"{len(self.actions)} files"
        )

    # ==================================================================
    # EXECUTION
    # ==================================================================

    def _apply_plan(self):

        if not self.actions:
            return

        answer = QMessageBox.question(
            self,
            "Apply Organization Plan",
            (
                f"DesktopAI is ready to move "
                f"{len(self.actions)} file(s).\n\n"
                "The operation can be undone."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.batch_id = str(
            uuid.uuid4()
        )

        try:

            stats = self.organizer.execute_plan(
                self.actions,
                batch_id=self.batch_id,
            )

            self.status_title.setText(
                "Organization completed"
            )

            self.status_text.setText(
                f"Successful: {stats['success']}  |  "
                f"Failed: {stats['failed']}  |  "
                f"Skipped: {stats['skipped']}"
            )

            self.apply_button.setEnabled(
                False
            )

            QMessageBox.information(
                self,
                "DesktopAI",
                (
                    f"Organization complete.\n\n"
                    f"Successful: {stats['success']}\n"
                    f"Failed: {stats['failed']}\n"
                    f"Skipped: {stats['skipped']}"
                ),
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Organization Failed",
                str(exc),
            )

    # ==================================================================
    # UNDO
    # ==================================================================

    def _undo(self):

        if not self.batch_id:
            QMessageBox.information(
                self,
                "Undo",
                "There is no organization batch to undo.",
            )
            return

        try:

            count = self.organizer.undo_last_batch(
                self.batch_id
            )

            self.status_title.setText(
                "Undo completed"
            )

            self.status_text.setText(
                f"{count} operation(s) were reversed."
            )

            QMessageBox.information(
                self,
                "Undo",
                f"{count} operation(s) were reversed.",
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Undo Failed",
                str(exc),
            )

    # ==================================================================
    # EXPORT
    # ==================================================================

    def _export_report(self):

        if not self.actions:
            QMessageBox.information(
                self,
                "Export Report",
                "There is no organization plan to export.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Organization Report",
            "desktopai_organization_report.csv",
            "CSV Files (*.csv)",
        )

        if not path:
            return

        try:

            with open(
                path,
                "w",
                newline="",
                encoding="utf-8",
            ) as handle:

                writer = csv.writer(
                    handle
                )

                writer.writerow(
                    [
                        "Source",
                        "Category",
                        "Destination",
                        "Confidence",
                    ]
                )

                for action in self.actions:
                    writer.writerow(
                        [
                            str(
                                action.source_path
                            ),
                            action.category,
                            str(
                                action.planned_target_path
                            ),
                            action.confidence,
                        ]
                    )

            QMessageBox.information(
                self,
                "Export Complete",
                f"Report saved to:\n{path}",
            )

        except OSError as exc:

            QMessageBox.critical(
                self,
                "Export Failed",
                str(exc),
            )

    def _set_enabled_state(
        self,
        enabled: bool,
    ):

        self.apply_button.setEnabled(
            enabled
        )

        self.export_button.setEnabled(
            bool(self.actions)
        )

        self.undo_button.setEnabled(
            bool(self.batch_id)
        )