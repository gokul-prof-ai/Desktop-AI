"""
DesktopAI v2.0 — Main Window (App Shell UI)
File: src/gui/windows/main_window.py

Implements the App Shell UI shell:
  L0  TitleBar (theme toggle + app title)
  L1  Sidebar (brand + nav groups)
  L2  Content canvas (soft charcoal)
  L3  View surfaces (raised cards)

This file is the navigation shell only.
No business logic lives here.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QFrame,
    QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from core.constants import (
    APP_NAME, APP_VERSION,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    SIDEBAR_WIDTH,
)
from gui.components.animated_stack import AnimatedStackedWidget
from gui.views.home_view import HomeView
from gui.views.organize_view import OrganizeView
from gui.views.search_view import SearchView
from gui.views.chat_view import ChatView
from gui.views.settings_view import SettingsView
from core.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    Application shell. Navigation only — no business logic.

    Structure:
        QMainWindow
        └── AppCanvas (QWidget, horizontal)
            ├── Sidebar (QFrame, 240px fixed)
            │   ├── Brand block
            │   ├── Nav groups
            │   └── Version label
            └── RightPane (QWidget, flex)
                ├── TitleBar (QFrame, 48px fixed)
                └── ContentArea (QWidget, flex)
                    └── AnimatedStackedWidget
    """

    # Nav items: (label, section_group)
    _NAV_ITEMS = [
        ("Home",     "MAIN"),
        ("Organize", "MAIN"),
        ("Search",   "MAIN"),
        ("Chat",     "MAIN"),
        ("Settings", "SYSTEM"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._current_index = 0
        self._setup_ui()
        self._set_initial_nav()

        logger.info("MainWindow initialized")

    # ── UI Construction ────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """Build the full shell layout."""
        # Root canvas
        canvas = QWidget()
        canvas.setObjectName("AppCanvas")
        self.setCentralWidget(canvas)

        root = QHBoxLayout(canvas)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # Right pane (titlebar + content)
        right = self._build_right_pane()
        root.addWidget(right, 1)

    def _build_sidebar(self) -> QFrame:
        """Build the left sidebar with brand + nav."""
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand block
        brand = self._build_brand_block()
        layout.addWidget(brand)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.08); border: none;")
        layout.addWidget(sep)

        layout.addSpacing(8)

        # Nav list
        self.nav = QListWidget()
        self.nav.setObjectName("NavList")
        self.nav.setFocusPolicy(Qt.NoFocus)

        prev_group = None
        for label, group in self._NAV_ITEMS:
            # Insert group header when group changes
            if group != prev_group:
                header = QListWidgetItem(group)
                header.setFlags(Qt.NoItemFlags)
                font = QFont()
                font.setPointSize(9)
                font.setWeight(QFont.Weight.Medium)
                header.setFont(font)
                header.setForeground(Qt.darkGray)
                header.setSizeHint(QSize(SIDEBAR_WIDTH, 28))
                self.nav.addItem(header)
                prev_group = group

            item = QListWidgetItem(f"  {label}")
            item.setSizeHint(QSize(SIDEBAR_WIDTH, 38))
            self.nav.addItem(item)

        self.nav.currentRowChanged.connect(self._on_nav_changed)
        layout.addWidget(self.nav, 1)

        layout.addSpacing(8)

        # Version label at bottom
        ver = QLabel(f"v{APP_VERSION}")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #6C6C70; font-size: 11px; padding: 12px;")
        layout.addWidget(ver)

        return sidebar

    def _build_brand_block(self) -> QWidget:
        """Build the app logo + name block at the top of sidebar."""
        brand = QWidget()
        brand.setFixedHeight(72)
        layout = QHBoxLayout(brand)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Logo tile — rounded square with 'D' monogram
        logo_tile = QLabel("D")
        logo_tile.setAlignment(Qt.AlignCenter)
        logo_tile.setFixedSize(36, 36)
        logo_tile.setStyleSheet("""
            QLabel {
                background-color: #0A84FF;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 700;
                border-radius: 8px;
            }
        """)
        layout.addWidget(logo_tile)

        # App name + subtitle
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        text_col.setContentsMargins(0, 0, 0, 0)

        title = QLabel(APP_NAME)
        title.setObjectName("BrandTitle")
        text_col.addWidget(title)

        subtitle = QLabel("AI File Organizer")
        subtitle.setObjectName("BrandSubtitle")
        text_col.addWidget(subtitle)

        layout.addLayout(text_col)
        layout.addStretch()

        return brand

    def _build_right_pane(self) -> QWidget:
        """Build the right pane: titlebar on top, content below."""
        pane = QWidget()
        pane.setObjectName("ContentArea")

        layout = QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # TitleBar
        titlebar = self._build_titlebar()
        layout.addWidget(titlebar)

        # Content: stacked views
        self.stack = AnimatedStackedWidget()
        self.stack.setObjectName("ViewStack")

        self.stack.addWidget(HomeView())
        self.stack.addWidget(OrganizeView())
        self.stack.addWidget(SearchView())
        self.stack.addWidget(ChatView())
        self.stack.addWidget(SettingsView())

        layout.addWidget(self.stack, 1)

        return pane

    def _build_titlebar(self) -> QFrame:
        """Build the top titlebar with page title and theme toggle."""
        bar = QFrame()
        bar.setObjectName("TitleBar")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(CONTENT_PADDING, 0, CONTENT_PADDING, 0)

        # Page title (updates on nav change)
        self.title_label = QLabel("Home")
        self.title_label.setObjectName("PageTitle")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Theme toggle button (moon/sun)
        self.theme_btn = QPushButton("☀")
        self.theme_btn.setObjectName("IconButton")
        self.theme_btn.setToolTip("Toggle light/dark theme")
        self.theme_btn.setFixedSize(28, 28)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        return bar

    # ── Navigation ─────────────────────────────────────────────────

    def _set_initial_nav(self) -> None:
        """Select the first real nav item (skip group headers)."""
        # Row 0 = group header "MAIN", row 1 = "Home"
        self.nav.setCurrentRow(1)
        self.stack.setCurrentIndex(0)

    def _on_nav_changed(self, row: int) -> None:
        """Handle navigation list row change."""
        # Skip group header rows (non-selectable items)
        item = self.nav.item(row)
        if item is None or not (item.flags() & Qt.ItemIsEnabled):
            return

        # Map nav row to view index (skip group headers)
        view_index = self._row_to_view_index(row)
        if view_index < 0:
            return

        # Update titlebar
        label = item.text().strip()
        self.title_label.setText(label)

        # Switch view
        self.stack.setCurrentIndex(view_index)
        self._current_index = view_index

        logger.debug("Nav → %s (view %d)", label, view_index)

    def _row_to_view_index(self, row: int) -> int:
        """
        Convert a nav list row number to a stack index.
        Group header rows are skipped (they return -1).
        """
        view_idx = -1
        for r in range(self.nav.count()):
            item = self.nav.item(r)
            if item and (item.flags() & Qt.ItemIsEnabled):
                view_idx += 1
                if r == row:
                    return view_idx
        return -1

    # ── Theme Toggle ───────────────────────────────────────────────

    _dark_mode: bool = True

    def _toggle_theme(self) -> None:
        """Toggle between dark and light App Shell themes."""
        self._dark_mode = not self._dark_mode

        if self._dark_mode:
            self.theme_btn.setText("☀")
            self._apply_dark()
        else:
            self.theme_btn.setText("☾")
            self._apply_light()

    def _apply_dark(self) -> None:
        """Apply dark theme overrides."""
        app = self.window()
        qss_override = """
            QWidget#AppCanvas { background-color: #1C1C1E; }
            QFrame#Sidebar { background-color: #161617; border-right: 1px solid rgba(255,255,255,0.08); }
            QFrame#TitleBar { background-color: #2C2C2E; border-bottom: 1px solid rgba(255,255,255,0.08); }
            QFrame#Card { background-color: #2C2C2E; border: 1px solid rgba(255,255,255,0.08); }
            QListWidget#NavList::item { color: #A1A1A6; }
            QListWidget#NavList::item:selected { background-color: rgba(10,132,255,0.22); color: #0A84FF; }
            QLabel#PageTitle { color: #F5F5F7; }
            QLabel#BrandTitle { color: #F5F5F7; }
            QLabel#StatValue { color: #F5F5F7; }
        """
        self.setStyleSheet(qss_override)

    def _apply_light(self) -> None:
        """Apply light theme overrides."""
        qss_override = """
            QWidget#AppCanvas { background-color: #F4F5F7; }
            QFrame#Sidebar { background-color: #EEF0F3; border-right: 1px solid rgba(0,0,0,0.08); }
            QFrame#TitleBar { background-color: #FAFBFC; border-bottom: 1px solid rgba(0,0,0,0.08); }
            QFrame#Card { background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.08); }
            QListWidget#NavList::item { color: #636366; }
            QListWidget#NavList::item:selected { background-color: rgba(0,122,255,0.12); color: #007AFF; }
            QLabel#PageTitle { color: #1C1C1E; }
            QLabel#BrandTitle { color: #1C1C1E; }
            QLabel#StatValue { color: #1C1C1E; }
        """
        self.setStyleSheet(qss_override)


# Import at module level to avoid circular reference in _build_titlebar
CONTENT_PADDING = 24