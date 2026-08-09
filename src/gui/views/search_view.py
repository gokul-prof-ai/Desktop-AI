"""
DesktopAI v2.0 — Search View
File: src/gui/views/search_view.py
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

class SearchView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        title = QLabel("Semantic Search")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        subtitle = QLabel("Find anything in your files using natural language")
        subtitle.setStyleSheet("color: #A1A1AA; font-size: 14px;")
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search your files... (e.g., 'invoices from 2023')")
        self.search_input.setFixedHeight(56)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #0A0A0F; border: 1px solid #2A2A35;
                border-radius: 12px; color: #FFFFFF; font-size: 16px; padding: 0 20px;
            }
            QLineEdit:focus { border: 1px solid #8B5CF6; background-color: #101018; }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)
        
        self.results_label = QLabel("Type to search...")
        self.results_label.setStyleSheet("color: #71717A; font-size: 14px;")
        layout.addWidget(self.results_label)
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #0A0A0F; border: 1px solid #1A1A24;
                border-radius: 12px; color: #E4E4E7; font-size: 13px;
            }
            QListWidget::item { padding: 12px 16px; border-bottom: 1px solid #1A1A24; }
            QListWidget::item:hover { background-color: rgba(139, 92, 246, 0.1); }
        """)
        self.results_list.setVisible(False)
        layout.addWidget(self.results_list, 1)
        layout.addStretch()
        
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
    
    def _on_search_changed(self, text: str):
        if text.strip():
            self._search_timer.start(300)
        else:
            self.results_list.clear()
            self.results_list.setVisible(False)
            self.results_label.setText("Type to search...")
    
    def _perform_search(self):
        query = self.search_input.text().strip()
        if not query: return
        
        self.results_label.setText(f"Searching for '{query}'...")
        self.results_list.clear()
        
        # Mock search results
        mock_results = [
            ("invoice_2023.pdf", "Finance", "0.94", "Total due: ₹24,500"),
            ("budget_report.xlsx", "Finance", "0.87", "Q3 expenses summary"),
            ("meeting_notes.docx", "Documents", "0.82", "Project discussion"),
        ]
        
        self.results_list.setVisible(True)
        for filename, category, score, snippet in mock_results:
            item = QListWidgetItem(f"📄 {filename}")
            item.setToolTip(f"{snippet}\nCategory: {category}\nRelevance: {score}")
            self.results_list.addItem(item)
        
        self.results_label.setText(f"Found {len(mock_results)} results for '{query}'")