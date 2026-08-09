"""
DesktopAI v2.0 — Application Shell
File: src/gui/windows/main_window.py
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QKeySequence, QShortcut, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QFrame,
    QPushButton, QSizePolicy,
)

from core.constants import APP_NAME, WINDOW_DEFAULT_HEIGHT, WINDOW_DEFAULT_WIDTH
from gui.theme.app_shell import apply_theme
from gui.views.home_view import HomeView
from gui.views.organize_view import OrganizeView
from gui.views.search_view import SearchView
from gui.views.chat_view import ChatView
from gui.views.history_view import HistoryView
from gui.views.settings_view import SettingsView
from gui.components.animated_stack import AnimatedStackedWidget
from infrastructure.config.settings import Settings
from core.logger import get_logger
from services import FileService

logger = get_logger(__name__)

# Nav: (icon, label, subtitle)
_NAV = [
    ("⌂", "Home",     "Scan and understand your files."),
    ("⊞", "Organize", "Review and safely apply organization plans."),
    ("⊕", "Search",   "Find files using natural language."),
    ("◎", "Chat",     "Ask DesktopAI about your files."),
    ("≡", "History",  "Browse your organization activity."),
    ("⚙", "Settings", "Configure AI, scanner, and preferences."),
]


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.current_theme = (
            Settings.app.theme if Settings.app.theme in {"light", "dark"} else "dark"
        )
        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(1100, 680)

        # Single FileService instance shared across all views
        self._service = FileService()
        self._service.open()

        self._build_ui()
        self._connect_events()
        self._setup_shortcuts()
        logger.info("MainWindow ready")

    def closeEvent(self, event) -> None:
        """Close DB cleanly on window close."""
        try:
            self._service.close()
        except Exception:
            pass
        super().closeEvent(event)

    # ── Build UI ───────────────────────────────────────────────────

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

        # Brand
        brand_widget = QWidget()
        brand_widget.setFixedHeight(64)
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(16, 0, 16, 0)
        brand_layout.setSpacing(10)

        logo = QLabel("D")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(30, 30)
        logo.setStyleSheet(
            "background:#0A84FF; color:white; font-size:14px;"
            "font-weight:700; border-radius:7px;"
        )
        brand_layout.addWidget(logo)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        brand_name = QLabel(APP_NAME)
        brand_name.setObjectName("Brand")
        brand_sub = QLabel("AI File Organizer")
        brand_sub.setObjectName("BrandSubtitle")
        text_col.addWidget(brand_name)
        text_col.addWidget(brand_sub)
        brand_layout.addLayout(text_col)
        brand_layout.addStretch()

        layout.addWidget(brand_widget)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background: #3A3A3C; border: none;")
        layout.addWidget(div)

        layout.addSpacing(8)

        # Nav group label
        nav_group = QLabel("MENU")
        nav_group.setObjectName("NavGroup")
        nav_group.setContentsMargins(18, 4, 0, 4)
        layout.addWidget(nav_group)

        # Nav list
        self.nav = QListWidget()
        self.nav.setObjectName("NavList")
        self.nav.setFocusPolicy(Qt.NoFocus)
        self.nav.setSpacing(1)

        self.sections = [label for _, label, _ in _NAV]

        for icon, label, _ in _NAV:
            item = QListWidgetItem(f"  {icon}  {label}")
            item.setSizeHint(QSize(220, 36))
            self.nav.addItem(item)

        layout.addWidget(self.nav, 1)
        layout.addSpacing(8)

        # Version
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

        # Header bar
        self.header_bar = self._build_header_bar()
        layout.addWidget(self.header_bar)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background: #3A3A3C; border: none;")
        layout.addWidget(div)

        # Page content (with padding)
        wrapper = QWidget()
        wrapper.setObjectName("Content")
        w_layout = QVBoxLayout(wrapper)
        w_layout.setContentsMargins(28, 20, 28, 20)
        w_layout.setSpacing(0)

        # Views
        self.stack = AnimatedStackedWidget()
        self.home_view     = HomeView(self._service)
        self.organize_view = OrganizeView(self._service)
        self.search_view   = SearchView(self._service)
        self.chat_view     = ChatView()
        self.history_view  = HistoryView()
        self.settings_view = SettingsView()

        for view in [
            self.home_view, self.organize_view,
            self.search_view, self.chat_view,
            self.history_view, self.settings_view,
        ]:
            self.stack.addWidget(view)

        w_layout.addWidget(self.stack)
        layout.addWidget(wrapper, 1)

        self.nav.setCurrentRow(0)
        self._update_theme_button()

        return content

    def _build_header_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("Content")
        bar.setFixedHeight(52)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(28, 0, 20, 0)

        self.page_title = QLabel("Home")
        self.page_title.setObjectName("PageTitle")
        layout.addWidget(self.page_title)

        layout.addStretch()

        # Theme toggle
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("ThemeButton")
        layout.addWidget(self.theme_button)

        return bar

    # ── Events ─────────────────────────────────────────────────────

    def _connect_events(self) -> None:
        self.nav.currentRowChanged.connect(self._on_nav_changed)
        self.theme_button.clicked.connect(self._toggle_theme)
        self.home_view.scan_ready.connect(self._on_scan_ready)

    def _on_nav_changed(self, index: int) -> None:
        if not (0 <= index < len(self.sections)):
            return
        self.stack.setCurrentIndex(index)
        self.page_title.setText(self.sections[index])

    def _on_scan_ready(self, scan_path: str, results: list) -> None:
        self.organize_view.set_scan_context(scan_path, results)
        self.search_view.set_scan_context(scan_path, results)
        self.chat_view.set_scan_context(scan_path, results)
        self.history_view.refresh()

    # ── Shortcuts ──────────────────────────────────────────────────

    def _setup_shortcuts(self) -> None:
        shortcuts = [
            ("Ctrl+1", 0), ("Ctrl+2", 1), ("Ctrl+3", 2),
            ("Ctrl+4", 3), ("Ctrl+5", 4), ("Ctrl+6", 5),
        ]
        for key, idx in shortcuts:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda i=idx: self._jump_to(i))

    def _jump_to(self, index: int) -> None:
        self.nav.setCurrentRow(index)

    # ── Theme ──────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        apply_theme(self.application(), self.current_theme)
        Settings.app.theme = self.current_theme
        try:
            Settings.save()
        except Exception:
            pass
        self._update_theme_button()

    def _update_theme_button(self) -> None:
        self.theme_button.setText("☀" if self.current_theme == "dark" else "☾")
        self.theme_button.setToolTip(
            "Switch to light mode" if self.current_theme == "dark"
            else "Switch to dark mode"
        )

    def application(self):
        from PySide6.QtWidgets import QApplication
        return QApplication.instance()