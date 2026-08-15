"""
DesktopAI v2.0 — Application Shell
File: src/gui/windows/main_window.py

Navigation shell only. Uses the premium theme engine and exposes
a ToastManager for non-blocking feedback across all views.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QFrame, QPushButton,
)

from core.constants import APP_NAME, WINDOW_DEFAULT_HEIGHT, WINDOW_DEFAULT_WIDTH
from gui.components.animated_stack import AnimatedStackedWidget
from gui.components.toast import ToastManager
from gui.theme.premium_theme import apply_premium_theme
from gui.views.home_view import HomeView
from gui.views.organize_view import OrganizeView
from gui.views.search_view import SearchView
from gui.views.chat_view import ChatView
from gui.views.history_view import HistoryView
from gui.views.settings_view import SettingsView
from infrastructure.config.settings import Settings
from core.logger import get_logger
from services import ApplicationServices
from domain.organizer.organizer import Organizer

logger = get_logger(__name__)

_MENU = [
    ("⌂", "Home", "Your library at a glance — drop a folder to begin."),
    ("▦", "Organize", "Review how DesktopAI proposes to organize your library."),
    ("⌕", "Search", "Find files by name, type, content, or meaning."),
    ("✦", "Chat", "Ask DesktopAI about your files, folders, or organization."),
    ("≡", "History", "Everything DesktopAI has done, with undo."),
]
_SYSTEM = [
    ("⚙", "Settings", "Appearance, AI engine, scanning and privacy."),
]


class MainWindow(QMainWindow):
    def __init__(self, services: ApplicationServices) -> None:
        super().__init__()
        self.services = services
        self.current_theme = (
            Settings.app.theme if Settings.app.theme in {"light", "dark"} else "dark"
        )
        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(1100, 680)

        self._service = self.services.file_service
        self._service.open()
        db_manager = getattr(self.services, "db_manager", None)
        self._organizer = Organizer(db_manager=db_manager)

        self._build_ui()
        self.toasts = ToastManager(self)

        apply_premium_theme(self.application(), self.current_theme)
        self._update_theme_button()

        self._connect_events()
        self._setup_shortcuts()
        logger.info("MainWindow ready")

    def closeEvent(self, event) -> None:
        try:
            self.services.close()
        except Exception:
            logger.exception("Failed to close application services cleanly.")
        super().closeEvent(event)

    # ── Build UI ────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_content(), 1)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        brand = QWidget()
        brand.setFixedHeight(64)
        b_lay = QHBoxLayout(brand)
        b_lay.setContentsMargins(16, 0, 16, 0)
        b_lay.setSpacing(10)
        logo = QLabel("D")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(30, 30)
        logo.setStyleSheet("background:#7C3AED; color:white; font-size:14px; font-weight:700; border-radius:7px;")
        b_lay.addWidget(logo)
        col = QVBoxLayout()
        col.setSpacing(1)
        name = QLabel(APP_NAME)
        name.setObjectName("BrandName")
        sub = QLabel("AI File Organizer")
        sub.setObjectName("BrandSub")
        col.addWidget(name)
        col.addWidget(sub)
        b_lay.addLayout(col)
        b_lay.addStretch()
        layout.addWidget(brand)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(div)
        layout.addSpacing(8)

        menu_group = QLabel("MENU")
        menu_group.setObjectName("NavGroup")
        menu_group.setContentsMargins(18, 4, 0, 4)
        layout.addWidget(menu_group)

        self.nav = QListWidget()
        self.nav.setObjectName("NavList")
        self.nav.setFocusPolicy(Qt.NoFocus)
        self.nav.setSpacing(1)
        self.sections = [label for _, label, _ in _MENU]
        for icon, label, _ in _MENU:
            item = QListWidgetItem(f" {icon}  {label}")
            item.setSizeHint(QSize(220, 36))
            self.nav.addItem(item)
        layout.addWidget(self.nav, 1)

        sys_group = QLabel("SYSTEM")
        sys_group.setObjectName("NavGroup")
        sys_group.setContentsMargins(18, 8, 0, 4)
        layout.addWidget(sys_group)

        self.sys_nav = QListWidget()
        self.sys_nav.setObjectName("NavList")
        self.sys_nav.setFocusPolicy(Qt.NoFocus)
        self.sys_nav.setFixedHeight(44)
        self.sys_nav.setSpacing(1)
        for icon, label, _ in _SYSTEM:
            item = QListWidgetItem(f" {icon}  {label}")
            item.setSizeHint(QSize(220, 36))
            self.sys_nav.addItem(item)
        layout.addWidget(self.sys_nav)
        layout.addSpacing(8)

        ver = QLabel("v2.0.0")
        ver.setObjectName("Caption")
        ver.setAlignment(Qt.AlignCenter)
        ver.setContentsMargins(0, 0, 0, 12)
        layout.addWidget(ver)
        return sidebar

    def _build_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("Content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header_bar = self._build_header_bar()
        layout.addWidget(self.header_bar)

        wrapper = QWidget()
        wrapper.setObjectName("Content")
        w_layout = QVBoxLayout(wrapper)
        w_layout.setContentsMargins(28, 20, 28, 20)
        w_layout.setSpacing(0)

        self.stack = AnimatedStackedWidget()
        self.home_view = HomeView(self._service)
        self.organize_view = OrganizeView(self._service)
        self.search_view = SearchView(self._service)
        self.chat_view = ChatView()
        self.history_view = HistoryView()
        self.settings_view = SettingsView()
        for view in [
            self.home_view, self.organize_view, self.search_view,
            self.chat_view, self.history_view, self.settings_view,
        ]:
            self.stack.addWidget(view)
        w_layout.addWidget(self.stack)
        layout.addWidget(wrapper, 1)

        self.nav.setCurrentRow(0)
        return content

    def _build_header_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopHeader")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(28, 0, 20, 0)

        col = QVBoxLayout()
        col.setSpacing(1)
        self.page_title = QLabel("Home")
        self.page_title.setObjectName("PageTitle")
        self.page_context = QLabel(_MENU[0][2])
        self.page_context.setObjectName("PageContext")
        col.addWidget(self.page_title)
        col.addWidget(self.page_context)
        layout.addLayout(col)
        layout.addStretch()

        self.theme_button = QPushButton()
        self.theme_button.setObjectName("ThemeButton")
        layout.addWidget(self.theme_button)
        return bar

    # ── Events ──────────────────────────────────────────────────
    def _connect_events(self) -> None:
        self.nav.currentRowChanged.connect(self._on_menu_changed)
        self.sys_nav.currentRowChanged.connect(self._on_system_changed)
        self.theme_button.clicked.connect(self._toggle_theme)
        self.home_view.scan_ready.connect(self._on_scan_ready)
        if hasattr(self.organize_view, "history_changed"):
            self.organize_view.history_changed.connect(self.history_view.refresh)

    def _on_menu_changed(self, index: int) -> None:
        if not (0 <= index < len(self.sections)):
            return
        if self.sys_nav.currentRow() != -1:
            self.sys_nav.blockSignals(True)
            self.sys_nav.clearSelection()
            self.sys_nav.setCurrentRow(-1)
            self.sys_nav.blockSignals(False)
        self._show_page(index)

    def _on_system_changed(self, index: int) -> None:
        if not (0 <= index < len(_SYSTEM)):
            return
        if self.nav.currentRow() != -1:
            self.nav.blockSignals(True)
            self.nav.clearSelection()
            self.nav.setCurrentRow(-1)
            self.nav.blockSignals(False)
        self._show_page(len(_MENU) + index)

    def _show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if index < len(_MENU):
            self.page_title.setText(_MENU[index][1])
            self.page_context.setText(_MENU[index][2])
        else:
            s = index - len(_MENU)
            self.page_title.setText(_SYSTEM[s][1])
            self.page_context.setText(_SYSTEM[s][2])

    def _on_scan_ready(self, scan_path: str, results: list) -> None:
        self._broadcast_scan_context(scan_path, results)

    def _broadcast_scan_context(self, scan_path: str, results: list) -> None:
        for view, name in [
            (self.organize_view, "OrganizeView"),
            (self.search_view, "SearchView"),
            (self.chat_view, "ChatView"),
        ]:
            fn = getattr(view, "set_scan_context", None)
            if callable(fn):
                try:
                    fn(scan_path, results)
                except Exception as exc:
                    logger.warning("%s.set_scan_context() raised %s: %s",
                                   name, type(exc).__name__, exc)
        try:
            self.history_view.refresh()
        except Exception as exc:
            logger.debug("HistoryView.refresh() raised %s: %s", type(exc).__name__, exc)
        count = len(results or [])
        self.toasts.show_success("Scan complete", f"{count} files analyzed.")
        logger.info("Scan context broadcast complete (path=%s, %d results).", scan_path, count)

    # ── Shortcuts ───────────────────────────────────────────────
    def _setup_shortcuts(self) -> None:
        for key, idx in [
            ("Ctrl+1", 0), ("Ctrl+2", 1), ("Ctrl+3", 2),
            ("Ctrl+4", 3), ("Ctrl+5", 4), ("Ctrl+6", 5),
        ]:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda i=idx: self._jump_to(i))

    def _jump_to(self, index: int) -> None:
        if index < len(_MENU):
            self.nav.setCurrentRow(index)
        else:
            self.sys_nav.setCurrentRow(index - len(_MENU))

    # ── Theme ───────────────────────────────────────────────────
    def _toggle_theme(self) -> None:
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        apply_premium_theme(self.application(), self.current_theme)
        Settings.app.theme = self.current_theme
        try:
            Settings.save()
        except Exception:
            logger.exception("Failed to persist theme setting.")
        self._update_theme_button()
        # Let self-themed views (e.g. Home) re-skin instantly.
        for view in [self.home_view]:
            fn = getattr(view, "_apply_theme", None)
            if callable(fn):
                fn()

    def _update_theme_button(self) -> None:
        self.theme_button.setText("☀" if self.current_theme == "dark" else "☾")
        self.theme_button.setToolTip(
            "Switch to light mode" if self.current_theme == "dark"
            else "Switch to dark mode"
        )

    def application(self):
        from PySide6.QtWidgets import QApplication
        return QApplication.instance()