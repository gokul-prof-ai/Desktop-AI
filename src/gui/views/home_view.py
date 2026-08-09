"""
DesktopAI v2.0
Home page.

Responsibilities:
    - Folder scanning
    - Scan progress
    - Real statistics
    - Classification results
    - File opening
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QFrame,
    QProgressBar,
)

from core.logger import get_logger
from domain.scanner.file_info import AnalysisResult
from gui.components.trendy_drop_zone import MagneticDropZone
from gui.viewmodels.home_vm import HomeViewModel
from infrastructure.storage.database import DB


logger = get_logger(__name__)


class HomeView(QWidget):
    """
    Main application dashboard.
    """

    scan_ready = Signal(str, list)

    def __init__(self):
        super().__init__()

        self.vm = HomeViewModel()
        self.current_scan_path: str | None = None
        self.results: list[AnalysisResult] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self._create_empty_page()
        self._create_results_page()

        self.vm.scan_progress.connect(
            self._on_scan_progress
        )

        self.vm.scan_completed.connect(
            self._on_scan_completed
        )

        self.vm.scan_failed.connect(
            self._on_scan_failed
        )

    # ==================================================================
    # EMPTY STATE
    # ==================================================================

    def _create_empty_page(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        title = QLabel(
            "Organize your files with DesktopAI"
        )
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            "Scan a folder to classify files, build an organization plan, "
            "and make them searchable."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)

        self.drop_zone = MagneticDropZone()

        self.drop_zone.folder_selected.connect(
            self._on_folder_selected
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(
            self.drop_zone,
            alignment=Qt.AlignCenter,
        )

        self.stack.addWidget(page)

    # ==================================================================
    # RESULTS PAGE
    # ==================================================================

    def _create_results_page(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(12)

        self.files_stat = self._create_stat_card(
            "Files Tracked",
            "0",
        )

        self.categories_stat = self._create_stat_card(
            "Categories",
            "0",
        )

        self.operations_stat = self._create_stat_card(
            "Operations",
            "0",
        )

        self.stats_layout.addWidget(
            self.files_stat,
            1,
        )

        self.stats_layout.addWidget(
            self.categories_stat,
            1,
        )

        self.stats_layout.addWidget(
            self.operations_stat,
            1,
        )

        layout.addLayout(
            self.stats_layout
        )

        self.scan_status = QLabel(
            "No scan loaded."
        )
        self.scan_status.setObjectName("PageSubtitle")

        layout.addWidget(
            self.scan_status
        )

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)

        layout.addWidget(
            self.progress
        )

        self.table = QTableWidget()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels(
            [
                "File Name",
                "Category",
                "Confidence",
                "Size",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )

        self.table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )

        self.table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
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

        self.table.setAlternatingRowColors(True)

        self.table.cellDoubleClicked.connect(
            self._open_file
        )

        layout.addWidget(
            self.table,
            1,
        )

        footer = QHBoxLayout()

        self.scan_again_button = QPushButton(
            "Scan Another Folder"
        )

        self.scan_again_button.setObjectName(
            "SecondaryButton"
        )

        self.scan_again_button.clicked.connect(
            self._show_empty
        )

        footer.addStretch()
        footer.addWidget(
            self.scan_again_button
        )

        layout.addLayout(
            footer
        )

        self.stack.addWidget(page)

    # ==================================================================
    # STAT CARD
    # ==================================================================

    def _create_stat_card(
        self,
        label: str,
        value: str,
    ) -> QFrame:

        card = QFrame()
        card.setObjectName("StatCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        value_label = QLabel(value)
        value_label.setObjectName(
            "StatValue"
        )

        label_widget = QLabel(label)
        label_widget.setObjectName(
            "StatLabel"
        )

        layout.addWidget(
            value_label
        )

        layout.addWidget(
            label_widget
        )

        card.value_label = value_label

        return card

    # ==================================================================
    # SCAN
    # ==================================================================

    def _on_folder_selected(
        self,
        path: str,
    ):

        if not Path(path).is_dir():
            self._on_scan_failed(
                "The selected path is not a folder."
            )
            return

        self.current_scan_path = path
        self.results = []

        self.table.setRowCount(0)

        self.progress.setVisible(True)
        self.progress.setValue(0)

        self.scan_status.setText(
            f"Scanning: {path}"
        )

        self.stack.setCurrentIndex(1)

        self.vm.start_scan(path)

    def _on_scan_progress(
        self,
        done: int,
        total: int,
    ):

        if total > 0:
            percentage = int(
                (done / total) * 100
            )

            self.progress.setValue(
                percentage
            )

        self.scan_status.setText(
            f"Analyzing files — {done}/{total}"
        )

    def _on_scan_completed(
        self,
        results: list,
    ):

        self.results = results

        self.progress.setVisible(False)

        self._populate_results(
            results
        )

        count = len(results)

        categories = {
            result.category
            for result in results
            if result.category
        }

        operations = 0

        try:
            history = DB.get_history(
                limit=10000
            )

            operations = len(
                [
                    item
                    for item in history
                    if item.get("status")
                    in {
                        "completed",
                        "undone",
                    }
                ]
            )

        except Exception as exc:
            logger.debug(
                "Unable to read operation history: %s",
                exc,
            )

        self.files_stat.value_label.setText(
            str(count)
        )

        self.categories_stat.value_label.setText(
            str(len(categories))
        )

        self.operations_stat.value_label.setText(
            str(operations)
        )

        self.scan_status.setText(
            f"Scan complete — {count} files analyzed"
        )

        if self.current_scan_path:
            self.scan_ready.emit(
                self.current_scan_path,
                results,
            )

    def _populate_results(
        self,
        results: list,
    ):

        self.table.setRowCount(
            len(results)
        )

        for row, result in enumerate(results):

            file_info = result.file_info

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(
                    file_info.filename
                ),
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    result.category
                ),
            )

            confidence = int(
                result.confidence * 100
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    f"{confidence}%"
                ),
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(
                    file_info.display_size
                ),
            )

    def _on_scan_failed(
        self,
        error: str,
    ):

        self.progress.setVisible(False)

        self.scan_status.setText(
            f"Scan failed — {error}"
        )

        logger.error(
            "HomeView scan failed: %s",
            error,
        )

    def _show_empty(self):

        self.stack.setCurrentIndex(0)

    def _open_file(
        self,
        row: int,
        _column: int,
    ):

        if row < 0 or row >= len(self.results):
            return

        path = self.results[row].file_info.path

        if path.exists():
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(
                    str(path)
                )
            )