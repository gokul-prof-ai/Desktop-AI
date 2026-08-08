"""
DesktopAI v2.0 — Modern Dashboard Main Window
File: src/gui/windows/main_window.py

Modern investment-dashboard inspired interface with:
- Sleek sidebar navigation
- Glassmorphism cards
- Purple/pink gradient accents
- Professional, clean layout
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
    QFrame, QPushButton, QSizePolicy, QScrollArea, QSpacerItem
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QFont, QIcon, QPalette, QColor
from core.constants import WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT, APP_NAME


class ModernMainWindow(QMainWindow):
    """Modern dashboard-style main window."""
    
    # Signals for navigation
    navigate_home = Signal()
    navigate_organize = Signal()
    navigate_search = Signal()
    navigate_chat = Signal()
    navigate_settings = Signal()
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Dashboard")
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(1200, 800)
        
        # Apply modern styling
        self._apply_modern_style()
        
        self._setup_ui()
        self._connect_signals()
    
    def _apply_modern_style(self) -> None:
        """Apply modern dashboard styling to the window."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#0D0D0F"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#FFFFFF"))
        self.setPalette(palette)
    
    def _setup_ui(self) -> None:
        """Build the modern dashboard layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ── Sidebar ───────────────────────────────────────────────
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # ── Main Content Area ──────────────────────────────────────
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top bar
        top_bar = self._create_top_bar()
        content_layout.addWidget(top_bar)
        
        # Content area with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        
        # Dashboard content
        dashboard_content = self._create_dashboard_content()
        scroll.setWidget(dashboard_content)
        
        content_layout.addWidget(scroll, 1)
        main_layout.addWidget(content_widget, 1)
    
    def _create_sidebar(self) -> QWidget:
        """Create the modern sidebar navigation."""
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("background-color: #151518;")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo/Brand section
        brand_widget = QWidget()
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(24, 24, 24, 24)
        
        logo_label = QLabel("H")
        logo_label.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: #8B5CF6;")
        brand_layout.addWidget(logo_label)
        
        brand_text = QLabel("DesktopAI")
        brand_text.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        brand_text.setStyleSheet("color: #FFFFFF;")
        brand_layout.addWidget(brand_text)
        brand_layout.addStretch()
        
        layout.addWidget(brand_widget)
        
        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("Sidebar")
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        nav_items = [
            ("🏠", "Dashboard", "home"),
            ("📁", "Organize", "organize"),
            ("🔍", "Search", "search"),
            ("💬", "Chat", "chat"),
            ("⚙️", "Settings", "settings"),
        ]
        
        for icon, text, nav_id in nav_items:
            item = QListWidgetItem(f"  {icon}  {text}")
            item.setData(Qt.ItemDataRole.UserRole, nav_id)
            item.setSizeHint(QSize(280, 52))
            item.setFont(QFont("Inter", 14, QFont.Weight.Medium))
            self.nav_list.addItem(item)
        
        layout.addWidget(self.nav_list)
        layout.addStretch()
        
        # User profile section at bottom
        user_widget = self._create_user_profile()
        layout.addWidget(user_widget)
        
        return sidebar
    
    def _create_user_profile(self) -> QWidget:
        """Create user profile widget at bottom of sidebar."""
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(24, 16, 24, 24)
        
        # Avatar placeholder
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8B5CF6, stop:1 #D946EF);
                border-radius: 20px;
            }
        """)
        layout.addWidget(avatar)
        
        # User info
        user_info = QWidget()
        user_layout = QVBoxLayout(user_info)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(0)
        
        name_label = QLabel("User Name")
        name_label.setFont(QFont("Inter", 13, QFont.Weight.SemiBold))
        name_label.setStyleSheet("color: #FFFFFF;")
        user_layout.addWidget(name_label)
        
        email_label = QLabel("user@example.com")
        email_label.setFont(QFont("Inter", 12))
        email_label.setStyleSheet("color: #71717A;")
        user_layout.addWidget(email_label)
        
        layout.addWidget(user_info)
        layout.addStretch()
        
        return widget
    
    def _create_top_bar(self) -> QWidget:
        """Create the top navigation bar."""
        top_bar = QWidget()
        top_bar.setFixedHeight(80)
        top_bar.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-bottom: 1px solid #27272A;
            }
        """)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(32, 16, 32, 16)
        
        # Welcome section
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(4)
        
        welcome_label = QLabel("Welcome back")
        welcome_label.setFont(QFont("Inter", 14))
        welcome_label.setStyleSheet("color: #A1A1AA;")
        welcome_layout.addWidget(welcome_label)
        
        greeting_label = QLabel("Good morning, User")
        greeting_label.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        greeting_label.setStyleSheet("color: #FFFFFF;")
        welcome_layout.addWidget(greeting_label)
        
        layout.addWidget(welcome_widget)
        layout.addStretch()
        
        # Top bar actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(12)
        
        # Search button
        search_btn = QPushButton("🔍")
        search_btn.setFixedSize(44, 44)
        search_btn.setObjectName("IconButton")
        actions_layout.addWidget(search_btn)
        
        # Notifications button
        notify_btn = QPushButton("🔔")
        notify_btn.setFixedSize(44, 44)
        notify_btn.setObjectName("IconButton")
        actions_layout.addWidget(notify_btn)
        
        # Settings button
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(44, 44)
        settings_btn.setObjectName("IconButton")
        actions_layout.addWidget(settings_btn)
        
        layout.addWidget(actions_widget)
        
        return top_bar
    
    def _create_dashboard_content(self) -> QWidget:
        """Create the main dashboard content with cards."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(24)
        
        # Total Files Card
        total_files_card = self._create_stat_card(
            "Total Files",
            "12,304",
            "+2.5%",
            ""
        )
        stats_layout.addWidget(total_files_card, 1)
        
        # Organized Card
        organized_card = self._create_stat_card(
            "Organized",
            "8,456",
            "+12.3%",
            "✅"
        )
        stats_layout.addWidget(organized_card, 1)
        
        # Pending Card
        pending_card = self._create_stat_card(
            "Pending Review",
            "127",
            "-5.2%",
            "⏳"
        )
        stats_layout.addWidget(pending_card, 1)
        
        # AI Confidence Card
        confidence_card = self._create_stat_card(
            "AI Confidence",
            "94.2%",
            "+1.8%",
            ""
        )
        stats_layout.addWidget(confidence_card, 1)
        
        layout.addLayout(stats_layout)
        
        # Main content grid
        main_grid = QHBoxLayout()
        main_grid.setSpacing(24)
        
        # Left column - Activity/Recent
        left_column = QVBoxLayout()
        left_column.setSpacing(24)
        
        # Recent Activity Card
        activity_card = self._create_activity_card()
        left_column.addWidget(activity_card)
        
        # Quick Actions Card
        actions_card = self._create_quick_actions_card()
        left_column.addWidget(actions_card)
        
        left_widget = QWidget()
        left_widget.setLayout(left_column)
        main_grid.addWidget(left_widget, 2)
        
        # Right column - Categories/Stats
        right_column = QVBoxLayout()
        right_column.setSpacing(24)
        
        # Categories Card
        categories_card = self._create_categories_card()
        right_column.addWidget(categories_card)
        
        # Storage Card
        storage_card = self._create_storage_card()
        right_column.addWidget(storage_card)
        
        right_widget = QWidget()
        right_widget.setLayout(right_column)
        main_grid.addWidget(right_widget, 1)
        
        layout.addLayout(main_grid)
        layout.addStretch()
        
        return content
    
    def _create_stat_card(self, title: str, value: str, change: str, icon: str) -> QFrame:
        """Create a statistics card."""
        card = QFrame()
        card.setObjectName("ModernCard")
        card.setMinimumHeight(140)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Icon and title row
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        # Change indicator
        change_label = QLabel(change)
        is_positive = change.startswith("+")
        change_color = "#10B981" if is_positive else "#EF4444"
        change_label.setStyleSheet(f"""
            color: {change_color};
            font-size: 13px;
            font-weight: 600;
        """)
        header_layout.addWidget(change_label)
        
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont("Inter", 32, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #FFFFFF; letter-spacing: -1px;")
        layout.addWidget(value_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Inter", 14))
        title_label.setStyleSheet("color: #A1A1AA;")
        layout.addWidget(title_label)
        
        return card
    
    def _create_activity_card(self) -> QFrame:
        """Create recent activity card."""
        card = QFrame()
        card.setObjectName("ModernCard")
        card.setMinimumHeight(300)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Recent Activity")
        title.setFont(QFont("Inter", 18, QFont.Weight.SemiBold))
        title.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        see_all = QPushButton("See All")
        see_all.setObjectName("SecondaryButton")
        see_all.setFixedSize(80, 32)
        header_layout.addWidget(see_all)
        
        layout.addLayout(header_layout)
        
        # Activity list (placeholder)
        activities = [
            ("invoice_2024.pdf", "Categorized as Finance", "2 min ago"),
            ("project_docs.zip", "Moved to Archives", "15 min ago"),
            ("meeting_notes.docx", "Categorized as Work", "1 hour ago"),
            ("photo_001.jpg", "Categorized as Images", "3 hours ago"),
        ]
        
        for filename, action, time in activities:
            activity_item = self._create_activity_item(filename, action, time)
            layout.addWidget(activity_item)
        
        layout.addStretch()
        return card
    
    def _create_activity_item(self, filename: str, action: str, time: str) -> QWidget:
        """Create a single activity item."""
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(16)
        
        # Icon
        icon = QLabel("📄")
        icon.setFont(QFont("Segoe UI Emoji", 16))
        layout.addWidget(icon)
        
        # Text
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        filename_label = QLabel(filename)
        filename_label.setFont(QFont("Inter", 14, QFont.Weight.Medium))
        filename_label.setStyleSheet("color: #FFFFFF;")
        text_layout.addWidget(filename_label)
        
        action_label = QLabel(action)
        action_label.setFont(QFont("Inter", 13))
        action_label.setStyleSheet("color: #71717A;")
        text_layout.addWidget(action_label)
        
        layout.addWidget(text_widget)
        layout.addStretch()
        
        # Time
        time_label = QLabel(time)
        time_label.setFont(QFont("Inter", 12))
        time_label.setStyleSheet("color: #71717A;")
        layout.addWidget(time_label)
        
        return widget
    
    def _create_quick_actions_card(self) -> QFrame:
        """Create quick actions card."""
        card = QFrame()
        card.setObjectName("AccentCard")
        card.setMinimumHeight(180)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Quick Actions")
        title.setFont(QFont("Inter", 18, QFont.Weight.SemiBold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        actions = [
            ("📁", "Scan Folder"),
            ("", "AI Organize"),
            ("", "Search"),
            ("📊", "Reports"),
        ]
        
        for icon, label in actions:
            btn = QPushButton(f"{icon} {label}")
            btn.setMinimumHeight(48)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(139, 92, 246, 0.3);
                    border-radius: 12px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 12px 16px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
            """)
            buttons_layout.addWidget(btn, 1)
        
        layout.addLayout(buttons_layout)
        return card
    
    def _create_categories_card(self) -> QFrame:
        """Create categories breakdown card."""
        card = QFrame()
        card.setObjectName("ModernCard")
        card.setMinimumHeight(300)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        title = QLabel("Categories")
        title.setFont(QFont("Inter", 18, QFont.Weight.SemiBold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # Category items
        categories = [
            ("Documents", 2456, "#8B5CF6"),
            ("Images", 1823, "#D946EF"),
            ("Finance", 892, "#10B981"),
            ("Code", 654, "#3B82F6"),
            ("Archives", 432, "#F59E0B"),
        ]
        
        for name, count, color in categories:
            cat_widget = self._create_category_item(name, count, color)
            layout.addWidget(cat_widget)
        
        layout.addStretch()
        return card
    
    def _create_category_item(self, name: str, count: int, color: str) -> QWidget:
        """Create a category item with progress bar."""
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        
        # Name and count
        header_layout = QHBoxLayout()
        name_label = QLabel(name)
        name_label.setFont(QFont("Inter", 14, QFont.Weight.Medium))
        name_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(name_label)
        
        count_label = QLabel(str(count))
        count_label.setFont(QFont("Inter", 14, QFont.Weight.SemiBold))
        count_label.setStyleSheet(f"color: {color};")
        header_layout.addWidget(count_label)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        progress = QFrame()
        progress.setFixedHeight(6)
        progress.setStyleSheet(f"""
            QFrame {{
                background-color: #27272A;
                border-radius: 3px;
            }}
        """)
        layout.addWidget(progress)
        
        return widget
    
    def _create_storage_card(self) -> QFrame:
        """Create storage usage card."""
        card = QFrame()
        card.setObjectName("ModernCard")
        card.setMinimumHeight(180)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Storage")
        title.setFont(QFont("Inter", 18, QFont.Weight.SemiBold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # Storage info
        storage_layout = QHBoxLayout()
        
        used_label = QLabel("245.6 GB")
        used_label.setFont(QFont("Inter", 28, QFont.Weight.Bold))
        used_label.setStyleSheet("color: #FFFFFF;")
        storage_layout.addWidget(used_label)
        
        total_label = QLabel("/ 500 GB")
        total_label.setFont(QFont("Inter", 18))
        total_label.setStyleSheet("color: #71717A;")
        storage_layout.addWidget(total_label)
        
        storage_layout.addStretch()
        layout.addLayout(storage_layout)
        
        # Progress
        progress_label = QLabel("49.1% used")
        progress_label.setFont(QFont("Inter", 13))
        progress_label.setStyleSheet("color: #A1A1AA;")
        layout.addWidget(progress_label)
        
        # Visual progress bar
        progress_bar = QFrame()
        progress_bar.setFixedHeight(8)
        progress_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B5CF6, stop:1 #D946EF);
                border-radius: 4px;
                min-width: 200px;
            }
        """)
        layout.addWidget(progress_bar)
        
        layout.addStretch()
        return card
    
    def _connect_signals(self) -> None:
        """Connect navigation signals."""
        self.nav_list.currentRowChanged.connect(self._on_navigation_changed)
    
    def _on_navigation_changed(self, index: int) -> None:
        """Handle navigation item selection."""
        item = self.nav_list.item(index)
        if item:
            nav_id = item.data(Qt.ItemDataRole.UserRole)
            # Emit appropriate signal based on navigation
            if nav_id == "home":
                self.navigate_home.emit()
            elif nav_id == "organize":
                self.navigate_organize.emit()
            elif nav_id == "search":
                self.navigate_search.emit()
            elif nav_id == "chat":
                self.navigate_chat.emit()
            elif nav_id == "settings":
                self.navigate_settings.emit()