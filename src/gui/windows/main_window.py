"""
DesktopAI v2.0
Application Shell.

The shell owns:
    - navigation
    - theme
    - cross-page scan state
    - page lifecycle
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QFrame,
    QPushButton,
)

from core.constants import (
    APP_NAME,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
)

from gui.theme.app_shell import apply_theme
from gui.views.home_view import HomeView
from gui.views.organize_view import OrganizeView
from gui.views.search_view import SearchView
from gui.views.chat_view import ChatView
from gui.views.settings_view import SettingsView
from gui.components.animated_stack import AnimatedStackedWidget

from infrastructure.config.settings import Settings


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.current_theme = (
            Settings.app.theme
            if Settings.app.theme
            in {"light", "dark"}
            else "dark"
        )

        self.setWindowTitle(
            APP_NAME
        )

        self.resize(
            WINDOW_DEFAULT_WIDTH,
            WINDOW_DEFAULT_HEIGHT,
        )

        self.setMinimumSize(
            1100,
            700,
        )

        self._build_ui()
        self._connect_events()

    # ==================================================================
    # UI
    # ==================================================================

    def _build_ui(self):

        root = QWidget()

        root.setObjectName(
            "Root"
        )

        self.setCentralWidget(
            root
        )

        root_layout = QHBoxLayout(
            root
        )

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(0)

        # --------------------------------------------------------------
        # SIDEBAR
        # --------------------------------------------------------------

        sidebar = QFrame()

        sidebar.setObjectName(
            "Sidebar"
        )

        sidebar.setFixedWidth(
            240
        )

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            12,
            20,
            12,
            16,
        )

        brand = QLabel(
            "DesktopAI"
        )

        brand.setObjectName(
            "Brand"
        )

        brand_subtitle = QLabel(
            "Local AI File Organizer"
        )

        brand_subtitle.setObjectName(
            "BrandSubtitle"
        )

        sidebar_layout.addWidget(
            brand
        )

        sidebar_layout.addWidget(
            brand_subtitle
        )

        sidebar_layout.addSpacing(
            24
        )

        main_label = QLabel(
            "MAIN"
        )

        main_label.setObjectName(
            "Muted"
        )

        sidebar_layout.addWidget(
            main_label
        )

        self.nav = QListWidget()

        self.nav.setObjectName(
            "NavList"
        )

        self.sections = [
            "Home",
            "Organize",
            "Search",
            "Chat",
            "Settings",
        ]

        for section in self.sections:

            item = QListWidgetItem(
                section
            )

            self.nav.addItem(
                item
            )

        sidebar_layout.addWidget(
            self.nav,
            1,
        )

        sidebar_layout.addSpacing(
            10
        )

        version = QLabel(
            "v2.0.0"
        )

        version.setObjectName(
            "Muted"
        )

        version.setAlignment(
            Qt.AlignCenter
        )

        sidebar_layout.addWidget(
            version
        )

        root_layout.addWidget(
            sidebar
        )

        # --------------------------------------------------------------
        # CONTENT
        # --------------------------------------------------------------

        content = QWidget()

        content.setObjectName(
            "Content"
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            24,
            18,
            24,
            18,
        )

        content_layout.setSpacing(
            12
        )

        # Header
        header = QHBoxLayout()

        title_container = QVBoxLayout()

        self.page_title = QLabel(
            "Home"
        )

        self.page_title.setObjectName(
            "PageTitle"
        )

        self.page_subtitle = QLabel(
            "Scan, understand and organize your files."
        )

        self.page_subtitle.setObjectName(
            "PageSubtitle"
        )

        title_container.addWidget(
            self.page_title
        )

        title_container.addWidget(
            self.page_subtitle
        )

        header.addLayout(
            title_container
        )

        header.addStretch()

        self.theme_button = QPushButton()

        self.theme_button.setObjectName(
            "ThemeButton"
        )

        header.addWidget(
            self.theme_button
        )

        content_layout.addLayout(
            header
        )

        # Pages
        self.stack = AnimatedStackedWidget()

        self.home_view = HomeView()
        self.organize_view = OrganizeView()
        self.search_view = SearchView()
        self.chat_view = ChatView()
        self.settings_view = SettingsView()

        self.stack.addWidget(
            self.home_view
        )

        self.stack.addWidget(
            self.organize_view
        )

        self.stack.addWidget(
            self.search_view
        )

        self.stack.addWidget(
            self.chat_view
        )

        self.stack.addWidget(
            self.settings_view
        )

        content_layout.addWidget(
            self.stack,
            1,
        )

        root_layout.addWidget(
            content,
            1,
        )

        self.nav.setCurrentRow(
            0
        )

        self._update_theme_button()

    # ==================================================================
    # EVENTS
    # ==================================================================

    def _connect_events(self):

        self.nav.currentRowChanged.connect(
            self._on_navigation_changed
        )

        self.theme_button.clicked.connect(
            self._toggle_theme
        )

        self.home_view.scan_ready.connect(
            self._on_scan_ready
        )

    def _on_navigation_changed(
        self,
        index: int,
    ):

        if not (
            0 <= index < len(self.sections)
        ):
            return

        self.stack.setCurrentIndex(
            index
        )

        self.page_title.setText(
            self.sections[index]
        )

        subtitles = {
            0: "Scan and understand your files.",
            1: "Review and safely apply organization plans.",
            2: "Find files using fast local search.",
            3: "Ask DesktopAI about your files.",
            4: "Configure AI, scanner, OCR and search.",
        }

        self.page_subtitle.setText(
            subtitles.get(
                index,
                "",
            )
        )

    # ==================================================================
    # CROSS-PAGE STATE
    # ==================================================================

    def _on_scan_ready(
        self,
        scan_path: str,
        results: list,
    ):

        self.organize_view.set_scan_context(
            scan_path,
            results,
        )

        self.search_view.set_scan_context(
            scan_path,
            results,
        )

        self.chat_view.set_scan_context(
            scan_path,
            results,
        )

    # ==================================================================
    # THEME
    # ==================================================================

    def _toggle_theme(self):

        self.current_theme = (
            "light"
            if self.current_theme == "dark"
            else "dark"
        )

        apply_theme(
            self.application(),
            self.current_theme,
        )

        Settings.app.theme = (
            self.current_theme
        )

        try:
            Settings.save()
        except Exception:
            pass

        self._update_theme_button()

    def _update_theme_button(self):

        if self.current_theme == "dark":
            self.theme_button.setText(
                "☀"
            )

            self.theme_button.setToolTip(
                "Switch to light mode"
            )

        else:
            self.theme_button.setText(
                "☾"
            )

            self.theme_button.setToolTip(
                "Switch to dark mode"
            )

    def application(self):
        from PySide6.QtWidgets import QApplication

        return QApplication.instance()