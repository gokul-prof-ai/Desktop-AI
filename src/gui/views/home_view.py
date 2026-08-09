"""
DesktopAI v2.0 — Home View (Premium Dashboard)
File: src/gui/views/home_view.py
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QFrame, QProgressBar,
    QSizePolicy,
)

from core.logger import get_logger
from gui.components.trendy_drop_zone import MagneticDropZone
from gui.viewmodels.home_vm import HomeViewModel
from services import FileService

logger = get_logger(__name__)

_EXT_ICONS = {
    ".pdf": "📄", ".docx": "📝", ".doc": "📝", ".xlsx": "📊",
    ".xls": "📊", ".csv": "📊", ".py": "🐍", ".js": "⚡",
    ".ts": "⚡", ".html": "🌐", ".json": "{ }", ".txt": "📃",
    ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼", ".gif": "🖼",
    ".mp4": "🎬", ".mp3": "🎵", ".zip": "📦", ".rar": "📦",
}


def _file_icon(ext: str) -> str:
    return _EXT_ICONS.get(ext.lower(), "📄")


def _conf_tag(confidence: float) -> tuple[str, str]:
    """Return (object_name, text) for a confidence badge."""
    pct = int(confidence * 100)
    if pct >= 80:
        return "TagSuccess", f"{pct}%"
    elif pct >= 50:
        return "TagWarning", f"{pct}%"
    return "TagDanger", f"{pct}%"


class HomeView(QWidget):
    scan_ready = Signal(str, list)

    def __init__(self, service: FileService) -> None:
        super().__init__()
        self._service = service
        self.vm = HomeViewModel()
        self.current_scan_path: str | None = None
        self.results: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self._build_empty_page()
        self._build_results_page()

        self.vm.scan_progress.connect(self._on_progress)
        self.vm.scan_completed.connect(self._on_completed)
        self.vm.scan_failed.connect(self._on_failed)

    # ── Empty page ─────────────────────────────────────────────────

    def _build_empty_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Stat row (always visible)
        layout.addWidget(self._build_stat_row())

        # Drop zone card (center hero)
        hero = QFrame()
        hero.setObjectName("Card")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setAlignment(Qt.AlignCenter)
        hero_layout.setSpacing(12)

        hero_title = QLabel("Scan a folder to get started")
        hero_title.setObjectName("Heading")
        hero_title.setAlignment(Qt.AlignCenter)

        hero_sub = QLabel(
            "Drop a folder below or click to browse.\n"
            "DesktopAI will classify your files and build\n"
            "an organization plan for your review."
        )
        hero_sub.setObjectName("Muted")
        hero_sub.setAlignment(Qt.AlignCenter)
        hero_sub.setWordWrap(True)

        self.drop_zone = MagneticDropZone()
        self.drop_zone.folder_selected.connect(self._on_folder_selected)

        hero_layout.addSpacing(16)
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_sub)
        hero_layout.addSpacing(8)
        hero_layout.addWidget(self.drop_zone, alignment=Qt.AlignCenter)
        hero_layout.addSpacing(16)

        layout.addWidget(hero, 1)

        # Quick actions row
        layout.addWidget(self._build_quick_actions())

        self.stack.addWidget(page)

    def _build_stat_row(self) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        self.stat_files = self._stat_card("Files Tracked", "0", "Total files DesktopAI has seen")
        self.stat_cats  = self._stat_card("Categories", "11", "Active category rules")
        self.stat_ops   = self._stat_card("Operations", "0", "File operations performed")

        try:
            stats = self._service.get_memory_stats()
            self.stat_files.value_label.setText(str(stats["total_files"]))
            self.stat_ops.value_label.setText(str(stats["total_operations"]))
        except Exception:
            pass

        h.addWidget(self.stat_files, 1)
        h.addWidget(self.stat_cats, 1)
        h.addWidget(self.stat_ops, 1)
        return row

    def _stat_card(self, label: str, value: str, tooltip: str = "") -> QFrame:
        card = QFrame()
        card.setObjectName("StatCard")
        if tooltip:
            card.setToolTip(tooltip)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(2)

        val = QLabel(value)
        val.setObjectName("StatValue")
        lbl = QLabel(label)
        lbl.setObjectName("StatLabel")

        layout.addWidget(val)
        layout.addWidget(lbl)

        card.value_label = val
        return card

    def _build_quick_actions(self) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        actions = [
            ("Scan Folder",    self._trigger_scan),
            ("View History",   self._noop),
            ("Search Files",   self._noop),
        ]

        for label, slot in actions:
            btn = QPushButton(label)
            btn.setObjectName("SecondaryButton")
            btn.clicked.connect(slot)
            h.addWidget(btn)

        h.addStretch()
        return row

    def _trigger_scan(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if path:
            self._on_folder_selected(path)

    def _noop(self) -> None:
        pass

    # ── Results page ───────────────────────────────────────────────

    def _build_results_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Stat row (updated after scan)
        self.results_stat_row = QHBoxLayout()
        self.results_stat_row.setSpacing(12)

        self.res_files_stat = self._stat_card("Files Found", "0")
        self.res_cats_stat  = self._stat_card("Categories", "0")
        self.res_ops_stat   = self._stat_card("Operations", "0")

        self.results_stat_row.addWidget(self.res_files_stat, 1)
        self.results_stat_row.addWidget(self.res_cats_stat, 1)
        self.results_stat_row.addWidget(self.res_ops_stat, 1)

        layout.addLayout(self.results_stat_row)

        # Progress (hidden after scan)
        prog_card = QFrame()
        prog_card.setObjectName("Card")
        prog_layout = QVBoxLayout(prog_card)
        prog_layout.setContentsMargins(18, 12, 18, 12)
        prog_layout.setSpacing(6)

        self.scan_status = QLabel("Scanning…")
        self.scan_status.setObjectName("SubHeading")

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFixedHeight(6)

        self.progress_detail = QLabel("")
        self.progress_detail.setObjectName("Caption")

        prog_layout.addWidget(self.scan_status)
        prog_layout.addWidget(self.progress)
        prog_layout.addWidget(self.progress_detail)

        self.progress_card = prog_card
        layout.addWidget(self.progress_card)

        # Results table card
        table_card = QFrame()
        table_card.setObjectName("Card")
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)

        # Table toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(16, 12, 16, 8)

        results_title = QLabel("Scan Results")
        results_title.setObjectName("SubHeading")
        toolbar.addWidget(results_title)
        toolbar.addStretch()

        self.results_count_lbl = QLabel("0 files")
        self.results_count_lbl.setObjectName("Muted")
        toolbar.addWidget(self.results_count_lbl)

        tc_layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Confidence", "Size"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._open_file)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        tc_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()

        organize_btn = QPushButton("Review & Organize →")
        organize_btn.setObjectName("PrimaryButton")
        organize_btn.clicked.connect(self._go_to_organize)

        scan_again = QPushButton("Scan Another Folder")
        scan_again.setObjectName("SecondaryButton")
        scan_again.clicked.connect(self._show_empty)

        footer.addWidget(scan_again)
        footer.addWidget(organize_btn)
        layout.addLayout(footer)

        self.stack.addWidget(page)

    # ── Scan logic ─────────────────────────────────────────────────

    def _on_folder_selected(self, path: str) -> None:
        if not Path(path).is_dir():
            return
        self.current_scan_path = path
        self.results = []
        self.table.setRowCount(0)
        self.progress.setValue(0)
        self.progress_card.setVisible(True)
        folder_name = Path(path).name
        self.scan_status.setText(f"Scanning  {folder_name}…")
        self.progress_detail.setText("")
        self.stack.setCurrentIndex(1)
        self.vm.start_scan(path)

    def _on_progress(self, done: int, total: int) -> None:
        if total > 0:
            self.progress.setValue(int(done / total * 100))
        self.progress_detail.setText(f"{done} of {total} files classified")

    def _on_completed(self, results: list) -> None:
        """results is list[AnalysisResult] from ScannerWorker; convert to dicts."""
        # ScannerWorker emits domain AnalysisResult objects — convert to plain dicts
        # so the rest of the app only passes dicts through FileService.
        if results and hasattr(results[0], "file_info"):
            dicts = [
                {
                    "path":       str(r.file_info.path),
                    "filename":   r.file_info.filename,
                    "extension":  r.file_info.extension,
                    "size_bytes": r.file_info.size_bytes,
                    "category":   r.category,
                    "confidence": r.confidence,
                    "method":     r.method,
                    "skipped":    r.skipped,
                    "skip_reason": r.skip_reason,
                }
                for r in results
            ]
        else:
            dicts = results  # already plain dicts

        self.results = dicts
        self.progress_card.setVisible(False)
        count = len(dicts)
        cats = {r["category"] for r in dicts if r.get("category")}

        ops = 0
        try:
            stats = self._service.get_memory_stats()
            ops = stats["total_operations"]
        except Exception:
            pass

        self.res_files_stat.value_label.setText(str(count))
        self.res_cats_stat.value_label.setText(str(len(cats)))
        self.res_ops_stat.value_label.setText(str(ops))
        self.results_count_lbl.setText(f"{count} files")
        self._populate_table(dicts)

        if self.current_scan_path:
            self.scan_ready.emit(self.current_scan_path, dicts)

    def _on_failed(self, error: str) -> None:
        self.progress_card.setVisible(False)
        self.scan_status.setText(f"Scan failed — {error}")
        logger.error("Scan failed: %s", error)

    def _populate_table(self, results: list[dict]) -> None:
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            icon = _file_icon(r.get("extension", ""))
            self.table.setItem(row, 0, QTableWidgetItem(f"{icon}  {r['filename']}"))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("category") or "—"))

            pct = int((r.get("confidence") or 0) * 100)
            conf_item = QTableWidgetItem(f"{pct}%")
            if pct >= 80:
                conf_item.setForeground(Qt.green)
            elif pct >= 50:
                conf_item.setForeground(Qt.yellow)
            else:
                conf_item.setForeground(Qt.red)
            self.table.setItem(row, 2, conf_item)

            size = r.get("size_bytes", 0)
            size_str = f"{size / 1024:.1f} KB" if size < 1_048_576 else f"{size / 1_048_576:.1f} MB"
            self.table.setItem(row, 3, QTableWidgetItem(size_str))
            self.table.setRowHeight(row, 36)

    def _open_file(self, row: int, _col: int) -> None:
        if 0 <= row < len(self.results):
            p = Path(self.results[row]["path"])
            if p.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    def _show_empty(self) -> None:
        self.stack.setCurrentIndex(0)

    def _go_to_organize(self) -> None:
        # Signal to main window — jump to Organize tab
        try:
            parent = self.window()
            if hasattr(parent, "nav"):
                parent.nav.setCurrentRow(1)
        except Exception:
            pass