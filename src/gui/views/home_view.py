"""
DesktopAI v2.0 — Home View (Command Center)
File: src/gui/views/home_view.py

Theme-aware dashboard: greeting, live stats, hero drop zone,
quick actions, recent folders, activity feed, scan progress
and results. All data comes from FileService (no fake values).
No emoji — only guaranteed glyphs.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.logger import get_logger
from gui.utils.file_icons import icon_for
from gui.viewmodels.home_vm import HomeViewModel
from services import FileService

logger = get_logger(__name__)


# ── Theme tokens (explicit hex — never palette()) ────────────────────────────
_DARK = dict(
    text="#E8E8F0", muted="#8B8BA8", card="#15151D", sub="#1B1B26",
    border="#26263A", accent="#8B5CF6", accent_hover="#7C3AED",
    hero_bg="rgba(139,92,246,0.06)", hero_hover="rgba(139,92,246,0.12)",
    hero_border="#3A3A55", ok="#34D399", warn="#FBBF24", bad="#F87171",
)
_LIGHT = dict(
    text="#17171F", muted="#6B6B80", card="#FFFFFF", sub="#F4F4FA",
    border="#E2E2EC", accent="#7C3AED", accent_hover="#6D28D9",
    hero_bg="rgba(124,58,237,0.05)", hero_hover="rgba(124,58,237,0.10)",
    hero_border="#C9C9DC", ok="#059669", warn="#B45309", bad="#B91C1C",
)


def _build_qss(t: dict) -> str:
    """View-scoped stylesheet from explicit tokens (both themes)."""
    return f"""
    #hvGreet {{ color: {t['text']}; font-size: 26px; font-weight: 700; }}
    #hvSub {{ color: {t['muted']}; font-size: 13px; }}
    #hvDateChip {{ color: {t['muted']}; background: {t['card']}; border: 1px solid {t['border']};
                   border-radius: 10px; padding: 6px 12px; font-size: 12px; }}
    #hvStatCard {{ background: {t['card']}; border: 1px solid {t['border']}; border-radius: 14px; }}
    #hvStatValue {{ color: {t['text']}; font-size: 22px; font-weight: 700; }}
    #hvStatLabel {{ color: {t['muted']}; font-size: 12px; }}
    #hvHero {{ background: {t['hero_bg']}; border: 2px dashed {t['hero_border']}; border-radius: 20px; }}
    #hvHero:hover {{ border-color: {t['accent']}; background: {t['hero_hover']}; }}
    #hvHeroIcon {{ color: {t['accent']}; font-size: 30px; font-weight: 700; }}
    #hvHeroTitle {{ color: {t['text']}; font-size: 16px; font-weight: 600; }}
    #hvHeroSub {{ color: {t['muted']}; font-size: 12px; }}
    #hvBrowse {{ background: {t['accent']}; color: #FFFFFF; border: none; border-radius: 10px;
                 padding: 9px 18px; font-weight: 600; }}
    #hvBrowse:hover {{ background: {t['accent_hover']}; }}
    #hvQuick {{ background: {t['card']}; color: {t['text']}; border: 1px solid {t['border']};
                border-radius: 10px; padding: 8px 14px; }}
    #hvQuick:hover {{ border-color: {t['accent']}; color: {t['accent']}; }}
    #hvQuick:disabled {{ color: {t['muted']}; border-color: {t['border']}; }}
    #hvStatus {{ color: {t['muted']}; font-size: 12px; }}
    #hvSection {{ color: {t['text']}; font-size: 15px; font-weight: 600; }}
    #hvCard {{ background: {t['card']}; border: 1px solid {t['border']}; border-radius: 14px; }}
    #hvFolderCard {{ background: {t['sub']}; border: 1px solid {t['border']}; border-radius: 12px; }}
    #hvFolderCard:hover {{ border-color: {t['accent']}; }}
    #hvFolderName {{ color: {t['text']}; font-size: 13px; font-weight: 600; }}
    #hvFolderMeta {{ color: {t['muted']}; font-size: 11px; }}
    #hvActText {{ color: {t['text']}; font-size: 12px; }}
    #hvActTime {{ color: {t['muted']}; font-size: 11px; }}
    #hvEmpty {{ color: {t['muted']}; font-size: 12px; }}
    #hvProgressLabel {{ color: {t['text']}; font-size: 13px; }}
    #hvBar {{ border: none; border-radius: 5px; background: {t['sub']}; }}
    #hvBar::chunk {{ background: {t['accent']}; border-radius: 5px; }}
    #hvTable {{ background: {t['card']}; border: 1px solid {t['border']}; border-radius: 12px;
                gridline-color: {t['border']}; color: {t['text']}; }}
    #hvTable::item {{ padding: 8px; }}
    QHeaderView::section {{ background: {t['sub']}; color: {t['muted']}; border: none;
                            padding: 8px; font-weight: 600; }}
    #hvGhost {{ background: transparent; color: {t['muted']}; border: 1px solid {t['border']};
                border-radius: 10px; padding: 8px 14px; }}
    #hvGhost:hover {{ color: {t['text']}; }}
    """


class _DropHero(QFrame):
    """Large themed drop zone (hero element)."""
    folder_dropped = Signal(str)
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("hvHero")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(170)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        icon = QLabel("↑")
        icon.setObjectName("hvHeroIcon")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        title = QLabel("Drop a folder to analyze")
        title.setObjectName("hvHeroTitle")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("or click anywhere in this area to browse")
        sub.setObjectName("hvHeroSub")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                event.acceptProposedAction()
                self.folder_dropped.emit(url.toLocalFile())
                return


class _FolderCard(QFrame):
    """Clickable recent-folder card."""
    opened = Signal(str)

    def __init__(self, folder: str, meta: str, parent=None):
        super().__init__(parent)
        self._folder = folder
        self.setObjectName("hvFolderCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(64)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(3)

        name = QLabel(Path(folder).name or folder)
        name.setObjectName("hvFolderName")
        lay.addWidget(name)

        m = QLabel(meta)
        m.setObjectName("hvFolderMeta")
        lay.addWidget(m)

    def mousePressEvent(self, event):
        self.opened.emit(self._folder)
        super().mousePressEvent(event)


class _IndexWorker(QThread):
    """Builds the search index off the GUI thread."""
    finished_index = Signal(dict)

    def __init__(self, service: FileService, parent=None):
        super().__init__(parent)
        self._service = service

    def run(self):
        self.finished_index.emit(self._service.build_index())


class HomeView(QWidget):
    """Home command center."""

    scan_ready = Signal(str, list)   # (scan_path, results) — consumed by MainWindow

    def __init__(self, file_service: FileService, parent=None):
        super().__init__(parent)
        self.file_service = file_service
        self.vm = HomeViewModel(file_service)
        self._theme = ""
        self._last_folder = ""
        self._index_worker = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.layout_main = QVBoxLayout(self.content)
        self.layout_main.setContentsMargins(28, 24, 28, 24)
        self.layout_main.setSpacing(18)

        self._build_header()
        self._build_stats()
        self._build_hero()
        self._build_quick_actions()
        self._build_bottom_stack()
        self.layout_main.addStretch()

        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll)

        self._connect_signals()
        self._refresh_stats()

    # ── Sections ──────────────────────────────────────────────────
    def _build_header(self):
        row = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(4)

        hour = datetime.now().hour
        greet_word = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
        self.greet = QLabel(greet_word)
        self.greet.setObjectName("hvGreet")
        col.addWidget(self.greet)

        self.sub = QLabel("Your library at a glance — drop a folder to begin.")
        self.sub.setObjectName("hvSub")
        col.addWidget(self.sub)
        row.addLayout(col)
        row.addStretch()

        self.date_chip = QLabel(datetime.now().strftime("%a, %d %b %Y"))
        self.date_chip.setObjectName("hvDateChip")
        row.addWidget(self.date_chip)
        self.layout_main.addLayout(row)

    def _build_stats(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        self.stat_values = {}
        for key, label in (("files", "Files analyzed"), ("ops", "Operations"),
                           ("cats", "Categories"), ("sessions", "Scan sessions")):
            card = QFrame()
            card.setObjectName("hvStatCard")
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            card.setMinimumHeight(78)
            lay = QVBoxLayout(card)
            lay.setContentsMargins(16, 12, 16, 12)
            lay.setSpacing(2)
            value = QLabel("—")
            value.setObjectName("hvStatValue")
            lay.addWidget(value)
            lab = QLabel(label)
            lab.setObjectName("hvStatLabel")
            lay.addWidget(lab)
            self.stat_values[key] = value
            row.addWidget(card)
        self.layout_main.addLayout(row)

    def _build_hero(self):
        self.hero = _DropHero()
        self.layout_main.addWidget(self.hero)

    def _build_quick_actions(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        self.btn_scan = QPushButton("Scan Folder")
        self.btn_scan.setObjectName("hvBrowse")
        row.addWidget(self.btn_scan)

        self.btn_rescan = QPushButton("Rescan Last Folder")
        self.btn_rescan.setObjectName("hvQuick")
        self.btn_rescan.setEnabled(False)
        row.addWidget(self.btn_rescan)

        self.btn_index = QPushButton("Build Search Index")
        self.btn_index.setObjectName("hvQuick")
        row.addWidget(self.btn_index)

        self.status = QLabel("")
        self.status.setObjectName("hvStatus")
        row.addWidget(self.status, 1)
        self.layout_main.addLayout(row)

    def _build_bottom_stack(self):
        self.bottom = QStackedWidget()

        # Page 0 — idle: recent folders + activity
        idle = QWidget()
        idle.setStyleSheet("background: transparent;")
        idle_lay = QHBoxLayout(idle)
        idle_lay.setContentsMargins(0, 0, 0, 0)
        idle_lay.setSpacing(14)

        self.folders_card = QFrame()
        self.folders_card.setObjectName("hvCard")
        f_lay = QVBoxLayout(self.folders_card)
        f_lay.setContentsMargins(16, 14, 16, 14)
        f_lay.setSpacing(10)
        f_title = QLabel("Recent folders")
        f_title.setObjectName("hvSection")
        f_lay.addWidget(f_title)
        self.folders_box = QVBoxLayout()
        self.folders_box.setSpacing(8)
        f_lay.addLayout(self.folders_box)
        f_lay.addStretch()
        idle_lay.addWidget(self.folders_card, 3)

        self.activity_card = QFrame()
        self.activity_card.setObjectName("hvCard")
        a_lay = QVBoxLayout(self.activity_card)
        a_lay.setContentsMargins(16, 14, 16, 14)
        a_lay.setSpacing(10)
        a_title = QLabel("Recent activity")
        a_title.setObjectName("hvSection")
        a_lay.addWidget(a_title)
        self.activity_box = QVBoxLayout()
        self.activity_box.setSpacing(8)
        a_lay.addLayout(self.activity_box)
        a_lay.addStretch()
        idle_lay.addWidget(self.activity_card, 2)

        self.bottom.addWidget(idle)

        # Page 1 — progress
        prog = QWidget()
        prog.setStyleSheet("background: transparent;")
        p_lay = QVBoxLayout(prog)
        p_lay.setContentsMargins(0, 8, 0, 8)
        p_lay.setSpacing(12)
        self.progress_label = QLabel("Starting scan...")
        self.progress_label.setObjectName("hvProgressLabel")
        p_lay.addWidget(self.progress_label)
        self.bar = QProgressBar()
        self.bar.setObjectName("hvBar")
        self.bar.setFixedHeight(10)
        self.bar.setTextVisible(False)
        p_lay.addWidget(self.bar)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("hvGhost")
        cancel.setFixedWidth(110)
        cancel.clicked.connect(self.vm.cancel_scan)
        p_lay.addWidget(cancel, 0, Qt.AlignLeft)
        self.bottom.addWidget(prog)

        # Page 2 — results
        res = QWidget()
        res.setStyleSheet("background: transparent;")
        r_lay = QVBoxLayout(res)
        r_lay.setContentsMargins(0, 0, 0, 0)
        r_lay.setSpacing(10)

        head = QHBoxLayout()
        self.results_header = QLabel("Scan results")
        self.results_header.setObjectName("hvSection")
        head.addWidget(self.results_header)
        head.addStretch()
        back = QPushButton("Back to overview")
        back.setObjectName("hvGhost")
        back.clicked.connect(lambda: self.bottom.setCurrentIndex(0))
        head.addWidget(back)
        r_lay.addLayout(head)

        self.table = QTableWidget()
        self.table.setObjectName("hvTable")
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Confidence", "Size"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in (1, 2, 3):
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        r_lay.addWidget(self.table)
        self.bottom.addWidget(res)

        self.layout_main.addWidget(self.bottom, 1)

    # ── Signals / actions ─────────────────────────────────────────
    def _connect_signals(self):
        self.hero.clicked.connect(self._browse_folder)
        self.hero.folder_dropped.connect(self._start_scan)
        self.btn_scan.clicked.connect(self._browse_folder)
        self.btn_rescan.clicked.connect(lambda: self._start_scan(self._last_folder))
        self.btn_index.clicked.connect(self._build_index)

        self.vm.scan_started.connect(self._on_scan_started)
        self.vm.scan_progress.connect(self._on_scan_progress)
        self.vm.scan_completed.connect(self._on_scan_completed)
        self.vm.scan_failed.connect(self._on_scan_failed)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self._start_scan(folder)

    def _start_scan(self, folder: str):
        if not folder:
            return
        self._last_folder = folder
        self.btn_rescan.setEnabled(True)
        self.vm.start_scan(folder)

    def _build_index(self):
        if self._index_worker and self._index_worker.isRunning():
            return
        self.btn_index.setEnabled(False)
        self.status.setText("Building search index...")
        self._index_worker = _IndexWorker(self.file_service)
        self._index_worker.finished_index.connect(self._on_index_done)
        self._index_worker.start()

    def _on_index_done(self, result: dict):
        self.btn_index.setEnabled(True)
        if result.get("error"):
            self.status.setText(f"Index failed: {result['error']}")
        else:
            self.status.setText(f"Search index ready — {result.get('indexed', 0)} file(s).")

    # ── Scan lifecycle ────────────────────────────────────────────
    def _on_scan_started(self):
        self.bottom.setCurrentIndex(1)
        self.bar.setValue(0)
        self.progress_label.setText("Starting scan...")

    def _on_scan_progress(self, current: int, total: int):
        self.progress_label.setText(f"Analyzing {current} / {total} files...")
        if total > 0:
            self.bar.setValue(int((current / total) * 100))

    def _on_scan_completed(self, results: list):
        self.bottom.setCurrentIndex(2)
        self.results_header.setText(f"Scan results ({len(results)} files)")
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            filename = r.get("filename", "unknown")
            self.table.setItem(row, 0, QTableWidgetItem(f"{icon_for(filename)}  {filename}"))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("category", "Unknown")))
            conf = r.get("confidence", 0.0)
            conf_item = QTableWidgetItem(f"{int(conf * 100)}%")
            self.table.setItem(row, 2, conf_item)
            self.table.setItem(row, 3, QTableWidgetItem(self._format_size(r.get("size_bytes", 0))))
        folder = str(Path(results[0]["path"]).parent) if results else self._last_folder
        self.scan_ready.emit(folder, results)
        self._refresh_stats()

    def _on_scan_failed(self, error: str):
        self.bottom.setCurrentIndex(0)
        self.status.setText(f"Scan failed: {error}")
        logger.error("Scan failed: %s", error)

    # ── Data (real values from FileService) ───────────────────────
    def _refresh_stats(self):
        try:
            stats = self.file_service.get_memory_stats()
        except Exception as exc:
            logger.warning("get_memory_stats failed: %s", exc)
            stats = {}

        self.stat_values["files"].setText(str(stats.get("total_files", 0)))
        self.stat_values["ops"].setText(str(stats.get("total_operations", 0)))
        self.stat_values["cats"].setText(str(len(stats.get("categories", {}) or {})))
        self.stat_values["sessions"].setText(str(len(stats.get("recent_sessions", []) or [])))

        self._rebuild_folders(stats.get("recent_sessions", []) or [])
        self._rebuild_activity(stats.get("recent_sessions", []) or [])

    def _rebuild_folders(self, sessions: list):
        while self.folders_box.count():
            item = self.folders_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        seen, cards = set(), 0
        for s in sessions:
            folder = s.get("folder_path") or s.get("path") or s.get("folder") or ""
            if not folder or folder in seen:
                continue
            seen.add(folder)
            meta = s.get("created_at") or s.get("started_at") or "previous session"
            card = _FolderCard(folder, str(meta)[:19])
            card.opened.connect(self._start_scan)
            self.folders_box.addWidget(card)
            cards += 1
            if cards >= 3:
                break
        if not cards:
            empty = QLabel("No recent scans yet — drop a folder above to get started.")
            empty.setObjectName("hvEmpty")
            self.folders_box.addWidget(empty)

    def _rebuild_activity(self, sessions: list):
        while self.activity_box.count():
            item = self.activity_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not sessions:
            empty = QLabel("Activity from your scans will appear here.")
            empty.setObjectName("hvEmpty")
            self.activity_box.addWidget(empty)
            return

        for s in sessions[:5]:
            folder = s.get("folder_path") or s.get("path") or "session"
            row = QHBoxLayout()
            txt = QLabel(f"Scanned {Path(str(folder)).name}")
            txt.setObjectName("hvActText")
            row.addWidget(txt)
            row.addStretch()
            when = QLabel(str(s.get("created_at") or s.get("started_at") or "")[:16])
            when.setObjectName("hvActTime")
            row.addWidget(when)
            wrap = QWidget()
            wrap.setStyleSheet("background: transparent;")
            wrap.setLayout(row)
            self.activity_box.addWidget(wrap)

    # ── Theme handling ────────────────────────────────────────────
    def _current_theme(self) -> str:
        try:
            from infrastructure.config.settings import Settings
            return Settings.app.theme if Settings.app.theme in ("light", "dark") else "dark"
        except Exception:
            return "dark"

    def _apply_theme(self):
        self._theme = self._current_theme()
        tokens = _LIGHT if self._theme == "light" else _DARK
        self.content.setStyleSheet(_build_qss(tokens) + " background: transparent;")

    def showEvent(self, event):
        if self._current_theme() != self._theme:
            self._apply_theme()
        super().showEvent(event)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"