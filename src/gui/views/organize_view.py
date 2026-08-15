"""
DesktopAI v2.0 — Organize View (Review Workspace)
File: src/gui/views/organize_view.py

Flow: empty → review (category cards + file table) → progress →
success (undo available) / error (retry + details).
All operations go through FileService on background threads.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.logger import get_logger
from gui.components import icons as I
from gui.components.widgets import (
    CategoryBadge, ConfidenceBadge, EmptyState, ErrorState, GhostButton,
    PrimaryButton, ProgressCard, SecondaryButton, SectionHeader, SuccessState,
)
from services import FileService

logger = get_logger(__name__)


class _ApplyWorker(QThread):
    progress = Signal(int, str)
    finished_apply = Signal(dict, list)
    failed = Signal(str)

    def __init__(self, service: FileService, target: str, parent=None):
        super().__init__(parent)
        self._service = service
        self._target = target

    def run(self):
        try:
            plan = self._service.plan_organisation(self._target)
            result = self._service.apply_plan(
                plan,
                progress_callback=lambda p, m: self.progress.emit(p, m),
            )
            self.finished_apply.emit(result, plan)
        except Exception as exc:
            logger.exception("Apply failed")
            self.failed.emit(str(exc))


class _UndoWorker(QThread):
    finished_undo = Signal(dict)
    failed = Signal(str)

    def __init__(self, service: FileService, parent=None):
        super().__init__(parent)
        self._service = service

    def run(self):
        try:
            self.finished_undo.emit(self._service.undo_last())
        except Exception as exc:
            self.failed.emit(str(exc))


class OrganizeView(QWidget):
    """Review and apply organization proposals."""

    history_changed = Signal()

    def __init__(self, file_service: FileService, parent=None):
        super().__init__(parent)
        self.service = file_service
        self._results: list = []
        self._target = ""
        self._ignore_apply = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.header = SectionHeader(
            "Organize your files",
            "Review DesktopAI's suggestions before anything is moved.",
        )
        layout.addWidget(self.header)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_empty())    # 0
        self.stack.addWidget(self._build_review())   # 1
        self.stack.addWidget(self._build_progress()) # 2
        self.stack.addWidget(self._build_success())  # 3
        self.stack.addWidget(self._build_error())    # 4
        layout.addWidget(self.stack, 1)

        self.stack.setCurrentIndex(0)

    # ── Pages ─────────────────────────────────────────────────────
    def _build_empty(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignCenter)
        state = EmptyState(
            "No scan to review",
            "Analyze a folder from Home and DesktopAI will propose an organization here.",
        )
        lay.addWidget(state)
        return page

    def _build_review(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(14)

        self.cats_row = QHBoxLayout()
        self.cats_row.setSpacing(10)
        lay.addLayout(self.cats_row)

        self.summary = QLabel("")
        self.summary.setObjectName("daSectionSub")
        lay.addWidget(self.summary)

        self.table = QTableWidget()
        self.table.setObjectName("daTable")
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Confidence", "Size"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in (1, 2, 3):
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        lay.addWidget(self.table, 1)

        foot = QHBoxLayout()
        foot.setSpacing(10)
        self.target_label = QLabel("Destination: —")
        self.target_label.setObjectName("daProgressText")
        foot.addWidget(self.target_label, 1)
        self.btn_dest = SecondaryButton("Choose Destination")
        self.btn_dest.clicked.connect(self._choose_destination)
        foot.addWidget(self.btn_dest)
        self.btn_apply = PrimaryButton("Organize Files")
        self.btn_apply.clicked.connect(self._start_apply)
        foot.addWidget(self.btn_apply)
        lay.addLayout(foot)
        return page

    def _build_progress(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignCenter)
        self.progress_card = ProgressCard("Organizing your library")
        self.progress_card.setMaximumWidth(560)
        self.progress_card.cancel.clicked.connect(self._cancel_apply)
        lay.addWidget(self.progress_card)
        return page

    def _build_success(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignCenter)
        self.success_state = SuccessState("Organization complete", "")
        self.btn_undo = SecondaryButton("Undo Last Batch")
        self.btn_undo.clicked.connect(self._start_undo)
        self.success_state.add_action(self.btn_undo)
        self.btn_back_review = GhostButton("Back to Review")
        self.btn_back_review.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.success_state.add_action(self.btn_back_review)
        lay.addWidget(self.success_state)
        return page

    def _build_error(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignCenter)
        self.error_state = ErrorState(
            "We couldn't complete the organization.",
            "Your files were not modified.",
        )
        self.btn_retry = PrimaryButton("Try Again")
        self.btn_retry.clicked.connect(self._start_apply)
        self.error_state.add_action(self.btn_retry)
        self.btn_details = GhostButton("View Details")
        self.btn_details.clicked.connect(self._toggle_details)
        self.error_state.add_action(self.btn_details)
        lay.addWidget(self.error_state)
        self.error_details = QLabel("")
        self.error_details.setObjectName("daProgressText")
        self.error_details.setWordWrap(True)
        self.error_details.hide()
        lay.addWidget(self.error_details)
        return page

    # ── Context (called by MainWindow after scans) ────────────────
    def set_scan_context(self, path: str, results: list) -> None:
        self._results = results or []
        self._target = path or ""
        if not self._results:
            self.stack.setCurrentIndex(0)
            return
        self._populate()
        self.stack.setCurrentIndex(1)

    def _populate(self) -> None:
        while self.cats_row.count():
            item = self.cats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        counts: dict = {}
        for r in self._results:
            cat = r.get("category", "Unknown")
            counts[cat] = counts.get(cat, 0) + 1
        for cat, n in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:6]:
            card = QFrame()
            card.setObjectName("daStatCard")
            card.setMinimumHeight(70)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.setSpacing(2)
            v = QLabel(str(n))
            v.setObjectName("daStatValue")
            cl.addWidget(v)
            l = QLabel(cat.title())
            l.setObjectName("daStatLabel")
            cl.addWidget(l)
            self.cats_row.addWidget(card)
        self.cats_row.addStretch()

        low = sum(1 for r in self._results if r.get("confidence", 0) < 0.5)
        self.summary.setText(
            f"{len(self._results)} files • {len(counts)} categories"
            + (f" • {low} need review" if low else "")
        )

        self.table.setRowCount(len(self._results))
        for row, r in enumerate(self._results):
            self.table.setItem(row, 0, QTableWidgetItem(f"  {r.get('filename', 'unknown')}"))
            self.table.setCellWidget(row, 1, CategoryBadge(r.get("category", "Unknown")))
            self.table.setCellWidget(row, 2, ConfidenceBadge(r.get("confidence", 0.0)))
            self.table.setItem(row, 3, QTableWidgetItem(self._format_size(r.get("size_bytes", 0))))

        self.target_label.setText(f"Destination: {self._target or '—'}")

    # ── Actions ─────────────────────────────────────────────────
    def _choose_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Destination")
        if folder:
            self._target = folder
            self.target_label.setText(f"Destination: {folder}")

    def _start_apply(self):
        if not self._results or not self._target:
            return
        self._ignore_apply = False
        self.stack.setCurrentIndex(2)
        self.progress_card.bar.setValue(0)
        self.progress_card.set_detail("Preparing…")
        self._apply_worker = _ApplyWorker(self.service, self._target)
        self._apply_worker.progress.connect(
            lambda p, m: (self.progress_card.bar.setValue(p), self.progress_card.set_detail(m))
        )
        self._apply_worker.finished_apply.connect(self._on_applied)
        self._apply_worker.failed.connect(self._on_apply_failed)
        self._apply_worker.start()

    def _cancel_apply(self):
        self._ignore_apply = True
        self.stack.setCurrentIndex(1)

    def _on_applied(self, result: dict, plan: list):
        if self._ignore_apply:
            return
        ok = result.get("success", 0)
        self.success_state.title.setText("Organization complete")
        self.success_state.desc.setText(
            f"{ok} files organized • {result.get('failed', 0)} errors"
        )
        self.stack.setCurrentIndex(3)
        self.history_changed.emit()
        self._toast("success", "Organization complete", f"{ok} files organized.")

    def _on_apply_failed(self, message: str):
        if self._ignore_apply:
            return
        self.error_details.setText(message)
        self.stack.setCurrentIndex(4)
        self._toast("error", "Organization failed", "Your files were not modified.")

    def _toggle_details(self):
        self.error_details.setVisible(not self.error_details.isVisible())

    def _start_undo(self):
        self._undo_worker = _UndoWorker(self.service)
        self._undo_worker.finished_undo.connect(self._on_undone)
        self._undo_worker.failed.connect(
            lambda m: self._toast("error", "Undo failed", m)
        )
        self._undo_worker.start()

    def _on_undone(self, result: dict):
        self.history_changed.emit()
        self._toast("success", "Undo complete", f"{result.get('reversed', 0)} files restored.")
        self.stack.setCurrentIndex(1)

    # ── Helpers ───────────────────────────────────────────────────
    def _toast(self, kind: str, title: str, msg: str):
        toasts = getattr(self.window(), "toasts", None)
        if toasts:
            getattr(toasts, f"show_{kind}")(title, msg)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"