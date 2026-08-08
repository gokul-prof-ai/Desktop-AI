"""
DesktopAI v2.0 — Main Window Shell
File: src/gui/windows/main_window.py

The primary application window. Acts ONLY as a navigation shell.
Contains no business logic. Business logic belongs in ViewModels.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame, QPushButton
)
from PySide6.QtCore import Qt, QSize, QTimer
from core.constants import WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT, APP_NAME
from gui.animations import PageTransition, AIPulseWidget, ToastNotification


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(1024, 680)
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Build the main window layout: Sidebar + Content Area."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ── Sidebar ────────────────────────────────────────────────
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        nav_items = [
            ("🏠", "Home"),
            ("📂", "Organize"),
            ("🔍", "Search"),
            ("💬", "Chat"),
            ("⚙️", "Settings"),
        ]
        
        for icon, text in nav_items:
            item = QListWidgetItem(f"  {icon}  {text}")
            item.setSizeHint(QSize(220, 48))
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.sidebar.addItem(item)
            
        self.sidebar.currentRowChanged.connect(self._on_nav_changed)
        
        # ── Content Area ───────────────────────────────────────────
        self.content_area = QStackedWidget()
        self.content_area.setObjectName("ContentArea")
        
        # Placeholder views (will be replaced by actual views in M9-M13)
        for name in ["Home", "Organize", "Search", "Chat", "Settings"]:
            view = self._create_placeholder_view(name)
            self.content_area.addWidget(view)
            
        # Add widgets to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area, 1)  # Content takes remaining space
        
        # Select "Home" by default
        self.sidebar.setCurrentRow(0)
        
        # ── AI Pulse Button (signature animation) ──────────────────
        self._setup_ai_pulse_button()
        
        # Show a welcome toast after 1 second
        QTimer.singleShot(1000, self._show_welcome_toast)

    def _create_placeholder_view(self, name: str) -> QWidget:
        """Create a temporary placeholder view for navigation testing."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel(f"{name} View")
        title.setObjectName("Title")
        
        subtitle = QLabel(f"This is the placeholder for the {name} screen. Will be built in upcoming milestones.")
        subtitle.setObjectName("Subtitle")
        
        # Neomorphic card example
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("Future UI components will live inside cards like this."))
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        layout.addWidget(card)
        layout.addStretch()
        
        return container

    def _on_nav_changed(self, index: int) -> None:
        """Switch the stacked widget to the selected view with animation."""
        self.content_area.setCurrentIndex(index)
        
        # Apply page transition to the new view
        current_widget = self.content_area.currentWidget()
        if current_widget:
            PageTransition.transition(current_widget, duration=400)

    def _setup_ai_pulse_button(self) -> None:
        """Add the signature AI Pulse button to the bottom-right corner."""
        # Create a container for the button + pulse
        button_container = QWidget(self)
        button_container.setGeometry(self.width() - 100, self.height() - 100, 80, 80)
        
        # The pulse effect (behind the button)
        self.ai_pulse = AIPulseWidget(button_container)
        self.ai_pulse.setGeometry(0, 0, 80, 80)
        
        # The actual button
        self.ai_button = QPushButton("🤖", button_container)
        self.ai_button.setGeometry(15, 15, 50, 50)
        self.ai_button.setObjectName("PrimaryButton")
        self.ai_button.setStyleSheet("""
            QPushButton {
                background-color: #4F8EF7;
                border-radius: 25px;
                font-size: 24px;
                border: none;
            }
            QPushButton:hover {
                background-color: #6AA1F9;
            }
        """)
        
        # Demo: cycle through states every 5 seconds
        self._pulse_states = ["idle", "thinking", "done"]
        self._pulse_index = 0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._cycle_pulse_state)
        self._pulse_timer.start(5000)

    def _cycle_pulse_state(self) -> None:
        """Cycle through pulse states for demo purposes."""
        self._pulse_index = (self._pulse_index + 1) % len(self._pulse_states)
        state = self._pulse_states[self._pulse_index]
        self.ai_pulse.set_state(state)

    def _show_welcome_toast(self) -> None:
        """Show a welcome notification."""
        toast = ToastNotification("Welcome to DesktopAI v2.0!", level="success", parent=self)
        toast.show_at(self.width() - 320, self.height() - 120)

    def resizeEvent(self, event) -> None:
        """Reposition the AI button when window resizes."""
        super().resizeEvent(event)
        if hasattr(self, 'ai_button'):
            # This is a simplified version - in production you'd use a layout
            pass