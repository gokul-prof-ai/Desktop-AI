"""
DesktopAI v2.0 — Application Shell
File: src/gui/windows/main_window.py
Navigation shell only. Premium theme, icon system, brand, palette,
boot overlay, sound prefs.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QFrame, QPushButton,
)

from core.constants import APP_NAME, WINDOW_DEFAULT_HEIGHT, WINDOW_DEFAULT_WIDTH
from core.logger import get_logger
from domain.organizer.organizer import Organizer
from infrastructure.config.settings import Settings
from services import ApplicationServices

from gui.components import icons as I
from gui.components.animated_stack import AnimatedStackedWidget
from gui.components.boot_overlay import BootOverlay
from gui.components.brand import LogoMark, app_icon, ensure_brand_assets
from gui.components.command_palette import CommandPalette
from gui.components.toast import ToastManager
from gui.components.widgets import StatusIndicator
from gui.theme.premium_theme import apply_premium_theme
from gui.theme.typography import apply_typography
from gui.theme.design_tokens import tokens_for
from gui.utils import sound_prefs

from gui.views.home_view import HomeView
from gui.views.organize_view import OrganizeView
from gui.views.search_view import SearchView
from gui.views.chat_view import ChatView
from gui.views.history_view import HistoryView
from gui.views.settings_view import SettingsView

try:
    from gui.utils.sounds import SOUNDS
except Exception:  # sounds optional
    SOUNDS = None

logger = get_logger(__name__)

_MENU = [
    ("home", "Home", "Your library at a glance — drop a folder to begin."),
    ("organize", "Organize", "Review how DesktopAI proposes to organize your library."),
    ("search", "Search", "Find files by name, type, content, or meaning."),
    ("chat", "Chat", "Ask DesktopAI about your files, folders, or organization."),
    ("history", "History", "Everything DesktopAI has done, with undo."),
]
_SYSTEM = [
    ("watcher", "Watcher", "Automatic monitoring of your folders."),
    ("settings", "Settings", "Appearance, AI engine, scanning and privacy."),
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
        self._boot_overlay = None

        self._service = self.services.file_service
        self._service.open()
        db_manager = getattr(self.services, "db_manager", None)
        self._organizer = Organizer(db_manager=db_manager)

        sound_prefs.apply_to(SOUNDS)
        apply_typography(self.application())
        ensure_brand_assets()
        self.setWindowIcon(app_icon())

        self._build_ui()
        self.toasts = ToastManager(self)
        apply_premium_theme(self.application(), self.current_theme)
        self._refresh_nav_icons()
        self._update_theme_button()

        self._connect_events()
        self._setup_shortcuts()
        self._show_boot()
        logger.info("MainWindow ready")

    def closeEvent(self, event) -> None:
        try:
            self.services.close()
        except Exception:
            logger.exception("Failed to close application services cleanly.")
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._boot_overlay is not None:
            try:
                self._boot_overlay.setGeometry(self.centralWidget().rect())
            except RuntimeError:
                self._boot_overlay = None

    # ── Build ────────────────────────────────────────────────────
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
        sidebar.setFixedWidth(224)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        brand = QWidget()
        brand.setFixedHeight(72)
        b_lay = QHBoxLayout(brand)
        b_lay.setContentsMargins(16, 0, 16, 0)
        b_lay.setSpacing(10)
        b_lay.addWidget(LogoMark(32))
        col = QVBoxLayout()
        col.setSpacing(1)
        name = QLabel(APP_NAME)
        name.setObjectName("BrandName")
        sub = QLabel("Your files. Understood.")
        sub.setObjectName("BrandSub")
        col.addWidget(name)
        col.addWidget(sub)
        b_lay.addLayout(col)
        b_lay.addStretch()
        layout.addWidget(brand)

        menu_group = QLabel("WORKSPACE")
        menu_group.setObjectName("NavGroup")
        menu_group.setContentsMargins(18, 4, 0, 4)
        layout.addWidget(menu_group)

        self.nav = QListWidget()
        self.nav.setObjectName("NavList")
        self.nav.setFocusPolicy(Qt.NoFocus)
        self.nav.setSpacing(1)
        self.sections = [label for _, label, _ in _MENU]
        for icon, label, _ in _MENU:
            item = QListWidgetItem(f"  {label}")
            item.setSizeHint(QSize(224, 38))
            item.setData(Qt.UserRole, icon)
            self.nav.addItem(item)
        layout.addWidget(self.nav, 1)

        sys_group = QLabel("SYSTEM")
        sys_group.setObjectName("NavGroup")
        sys_group.setContentsMargins(18, 8, 0, 4)
        layout.addWidget(sys_group)

        self.sys_nav = QListWidget()
        self.sys_nav.setObjectName("NavList")
        self.sys_nav.setFocusPolicy(Qt.NoFocus)
        self.sys_nav.setFixedHeight(84)
        self.sys_nav.setSpacing(1)
        for icon, label, _ in _SYSTEM:
            item = QListWidgetItem(f"  {label}")
            item.setSizeHint(QSize(224, 38))
            item.setData(Qt.UserRole, icon)
            self.sys_nav.addItem(item)
        layout.addWidget(self.sys_nav)
        layout.addSpacing(8)

        ver = QLabel("DesktopAI V2\nLocal • Private")
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
        layout.addWidget(self._build_header_bar())

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
        self.watcher_view = self._make_watcher_view()
        self.settings_view = SettingsView()

        self._pages = [
            self.home_view, self.organize_view, self.search_view,
            self.chat_view, self.history_view, self.watcher_view,
            self.settings_view,
        ]
        for view in self._pages:
            self.stack.addWidget(view)
        w_layout.addWidget(self.stack)
        layout.addWidget(wrapper, 1)
        self.nav.setCurrentRow(0)
        return content

    def _make_watcher_view(self) -> QWidget:
        try:
            from gui.views.watcher_view import WatcherView
            try:
                return WatcherView(self.services.watcher_service)
            except TypeError:
                return WatcherView()
        except Exception as exc:
            logger.warning("WatcherView unavailable: %s", exc)
            from gui.components.widgets import EmptyState
            return EmptyState("Watcher unavailable", "This build could not load the watcher module.")

    def _build_header_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopHeader")
        bar.setFixedHeight(60)
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

        self.status = StatusIndicator("Local • Private", "ok")
        layout.addWidget(self.status)

        self.theme_button = QPushButton()
        self.theme_button.setObjectName("ThemeButton")
        self.theme_button.setFixedSize(36, 36)
        layout.addWidget(self.theme_button)
        return bar

    # ── Boot overlay ──────────────────────────────────────────────
    def _show_boot(self) -> None:
        overlay = BootOverlay(self.centralWidget())
        overlay.setGeometry(self.centralWidget().rect())
        overlay.show()
        overlay.raise_()
        self._boot_overlay = overlay

    # ── Nav icons ─────────────────────────────────────────────────
    def _refresh_nav_icons(self) -> None:
        t = tokens_for(self.current_theme)
        active = QColor(t["nav_active_text"])
        idle = QColor(t["text_2"])

        def paint(list_widget: QListWidget):
            for row in range(list_widget.count()):
                item = list_widget.item(row)
                icon_name = item.data(Qt.UserRole)
                is_active = (list_widget.currentRow() == row)
                item.setIcon(I.qicon(icon_name, 18, active if is_active else idle))

        paint(self.nav)
        paint(self.sys_nav)

    # ── Events ────────────────────────────────────────────────────
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
        self._clear_other(self.nav)
        self._show_page(index)
        self._refresh_nav_icons()

    def _on_system_changed(self, index: int) -> None:
        if not (0 <= index < len(_SYSTEM)):
            return
        self._clear_other(self.sys_nav)
        self._show_page(len(_MENU) + index)
        self._refresh_nav_icons()

    def _clear_other(self, active_list: QListWidget) -> None:
        other = self.sys_nav if active_list is self.nav else self.nav
        if other.currentRow() != -1:
            other.blockSignals(True)
            other.clearSelection()
            other.setCurrentRow(-1)
            other.blockSignals(False)

    def _show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        all_pages = _MENU + _SYSTEM
        self.page_title.setText(all_pages[index][1])
        self.page_context.setText(all_pages[index][2])

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
                    logger.warning("%s.set_scan_context() raised %s: %s", name, type(exc).__name__, exc)
        try:
            self.history_view.refresh()
        except Exception as exc:
            logger.debug("HistoryView.refresh() raised %s: %s", type(exc).__name__, exc)
        count = len(results or [])
        self.toasts.show_success("Scan complete", f"{count} files analyzed.")
        if SOUNDS:
            SOUNDS.play_success()
        logger.info("Scan context broadcast complete (path=%s, %d results).", scan_path, count)

    # ── Shortcuts & palette ───────────────────────────────────────
    def _setup_shortcuts(self) -> None:
        for key, idx in [("Ctrl+1", 0), ("Ctrl+2", 1), ("Ctrl+3", 2),
                         ("Ctrl+4", 3), ("Ctrl+5", 4), ("Ctrl+6", 5), ("Ctrl+7", 6)]:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda i=idx: self._jump_to(i))

        QShortcut(QKeySequence("Ctrl+K"), self).activated.connect(self._open_palette)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.home_view._browse_folder)
        QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(lambda: self._jump_to(6))

    def _jump_to(self, index: int) -> None:
        if index < len(_MENU):
            self.nav.setCurrentRow(index)
        else:
            self.sys_nav.setCurrentRow(index - len(_MENU))

    def _open_palette(self) -> None:
        actions = [
            ("scan", "Scan Folder", "Ctrl+O"),
            ("search", "Search Files", "Ctrl+3"),
            ("organize", "Organize Files", "Ctrl+2"),
            ("index", "Build Search Index", ""),
            ("theme", "Toggle Theme", ""),
            ("history", "View History", "Ctrl+5"),
            ("settings", "Open Settings", "Ctrl+,"),
        ]
        palette = CommandPalette(actions, self.current_theme, self)
        chosen = palette.exec()
        if not chosen:
            return
        if chosen == "scan":
            self.home_view._browse_folder()
        elif chosen == "search":
            self._jump_to(2)
        elif chosen == "organize":
            self._jump_to(1)
        elif chosen == "index":
            self.home_view._build_index()
        elif chosen == "theme":
            self._toggle_theme()
        elif chosen == "history":
            self._jump_to(4)
        elif chosen == "settings":
            self._jump_to(6)

    # ── Theme ─────────────────────────────────────────────────────
    def _toggle_theme(self) -> None:
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        apply_premium_theme(self.application(), self.current_theme)
        Settings.app.theme = self.current_theme
        try:
            Settings.save()
        except Exception:
            logger.exception("Failed to persist theme setting.")
        self._update_theme_button()
        self._refresh_nav_icons()
        fn = getattr(self.home_view, "_apply_theme", None)
        if callable(fn):
            fn()

    def _update_theme_button(self) -> None:
        t = tokens_for(self.current_theme)
        name = "sun" if self.current_theme == "dark" else "moon"
        self.theme_button.setIcon(I.qicon(name, 18, QColor(t["text_2"])))
        self.theme_button.setToolTip(
            "Switch to light mode" if self.current_theme == "dark" else "Switch to dark mode"
        )

    def application(self):
        from PySide6.QtWidgets import QApplication
        return QApplication.instance()