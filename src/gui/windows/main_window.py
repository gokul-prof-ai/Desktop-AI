"""
DesktopAI v2.0 — Main Window
File: src/gui/windows/main_window.py
Shell with top bar: theme toggle + sound toggle. Routes scan results.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QFrame,
)
from PySide6.QtGui import QFont

from core.constants import APP_NAME, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT
from gui.components.animated_stack import AnimatedStackedWidget
from gui.components.sound_button import SoundButton
from gui.theme import theme_manager
from gui.utils.sounds import SOUNDS
from gui.views.home_view import HomeView
from gui.views.organize_view import OrganizeView
from gui.views.search_view import SearchView
from gui.views.chat_view import ChatView
from gui.views.settings_view import SettingsView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(1000, 700)
        self._latest_results: list = []

        theme_manager.apply_saved_theme()
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._create_top_bar())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._create_sidebar())
        body_layout.addWidget(self._create_main_content(), 1)
        root.addWidget(body, 1)

    def _create_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 8, 20, 8)

        logo = QLabel("DesktopAI")
        logo.setObjectName("Logo")
        layout.addWidget(logo)
        layout.addStretch()

        self.sound_btn = SoundButton("🔊")
        self.sound_btn.setObjectName("IconButton")
        self.sound_btn.setFixedSize(40, 40)
        self.sound_btn.clicked.connect(self._toggle_sound)
        layout.addWidget(self.sound_btn)

        self.theme_btn = SoundButton("🌙" if theme_manager.current_theme() == "dark" else "☀️")
        self.theme_btn.setObjectName("IconButton")
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)
        return bar

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)

        self.nav = QListWidget()
        self.nav.setObjectName("Sidebar")
        self.nav.setFixedWidth(240)
        self.sections = ["Home", "Organize", "Search", "Chat", "Settings"]
        for item in self.sections:
            QListWidgetItem(item, self.nav)
        self.nav.currentRowChanged.connect(self._on_nav_changed)
        layout.addWidget(self.nav)
        layout.addStretch()
        return sidebar

    def _create_main_content(self) -> QWidget:
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 30, 40, 30)

        self.page_title = QLabel("Home")
        self.page_title.setObjectName("PageTitle")
        layout.addWidget(self.page_title)
        layout.addSpacing(20)

        self.stack = AnimatedStackedWidget()
        self.home_view = HomeView()
        self.organize_view = OrganizeView()
        self.stack.addWidget(self.home_view)
        self.stack.addWidget(self.organize_view)
        self.stack.addWidget(SearchView())
        self.stack.addWidget(ChatView())
        self.stack.addWidget(SettingsView())
        layout.addWidget(self.stack, 1)

        self.home_view.vm.scan_completed.connect(self._on_scan_completed)
        return content

    def _toggle_theme(self):
        new = theme_manager.toggle_theme()
        self.theme_btn.setText("🌙" if new == "dark" else "☀️")

    def _toggle_sound(self):
        SOUNDS.set_enabled(not SOUNDS.enabled)
        self.sound_btn.setText("🔊" if SOUNDS.enabled else "🔇")
        SOUNDS.play_click()

    def _on_scan_completed(self, results: list) -> None:
        self._latest_results = results

    def _on_nav_changed(self, index: int) -> None:
        if 0 <= index < len(self.sections):
            SOUNDS.play_click()
            self.page_title.setText(self.sections[index])
            self.stack.setCurrentIndex(index)
            if index == 1 and self._latest_results:
                self.organize_view.load_results(self._latest_results)