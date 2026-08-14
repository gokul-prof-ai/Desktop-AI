"""
DesktopAI v2.0 — Video Drop Zone
File: src/gui/components/video_drop_zone.py

Continuously loops Files_dropping.mp4 with its audio.
Overlays "Drop folder here" text in theme-aware Inter font.
Emits folder_selected when user drops or clicks.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal, QTimer
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFileDialog, QFrame,
)

_ASSETS       = Path(__file__).resolve().parent.parent.parent.parent / "assets"
_DROP_VIDEO   = _ASSETS / "files_dropping.mp4"
_FONT_PATH    = _ASSETS / "fonts" / "InterVariable.ttf"


def _inter(size: int, weight=QFont.Weight.Normal) -> QFont:
    fid = QFontDatabase.addApplicationFont(str(_FONT_PATH))
    families = QFontDatabase.applicationFontFamilies(fid)
    family = families[0] if families else "Segoe UI"
    f = QFont(family)
    f.setPointSize(size)
    f.setWeight(weight)
    return f


class VideoDropZone(QWidget):
    """
    Drop zone that loops Files_dropping.mp4 as background.

    Signals:
        folder_selected(str)  — absolute path of chosen folder
        files_dropped(list)   — list of dropped folder paths
    """

    folder_selected = Signal(str)
    files_dropped   = Signal(list)

    def __init__(self, theme: str = "dark", parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._drag_active = False

        self.setMinimumSize(520, 280)
        self.setMaximumSize(720, 320)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)

        self._build_ui()
        self._setup_player()

    # ── UI ─────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video widget fills the drop zone
        self.video_widget = QVideoWidget(self)
        self.video_widget.setGeometry(0, 0, 720, 320)

        # Overlay on top
        self.overlay = QWidget(self)
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.overlay.setStyleSheet("background: transparent;")

        o_layout = QVBoxLayout(self.overlay)
        o_layout.setAlignment(Qt.AlignCenter)
        o_layout.setSpacing(6)
        o_layout.setContentsMargins(32, 24, 32, 24)

        # Theme-dependent text colors
        if self._theme == "dark":
            title_color  = "#FFFFFF"
            sub_color    = "rgba(255,255,255,0.65)"
            title_shadow = (
                "text-shadow: 0 2px 8px rgba(0,0,0,0.9), "
                "0 0 24px rgba(10,132,255,0.4);"
            )
        else:
            title_color  = "#0A0A0B"
            sub_color    = "rgba(0,0,0,0.55)"
            title_shadow = (
                "text-shadow: 0 1px 4px rgba(255,255,255,0.9), "
                "0 2px 8px rgba(0,0,0,0.12);"
            )

        self.title_label = QLabel("Drop folder here")
        self.title_label.setFont(_inter(18, QFont.Weight.DemiBold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            f"color: {title_color}; background: transparent; {title_shadow}"
        )

        self.sub_label = QLabel("or click to browse your computer")
        self.sub_label.setFont(_inter(12))
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet(
            f"color: {sub_color}; background: transparent;"
        )

        self.hint_label = QLabel("")
        self.hint_label.setFont(_inter(11))
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet(
            "color: rgba(10,132,255,0.9); background: transparent;"
        )

        o_layout.addStretch()
        o_layout.addWidget(self.title_label)
        o_layout.addWidget(self.sub_label)
        o_layout.addWidget(self.hint_label)
        o_layout.addStretch()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self.video_widget.setGeometry(0, 0, w, h)
        self.overlay.setGeometry(0, 0, w, h)

    # ── Media ──────────────────────────────────────────────────────

    def _setup_player(self) -> None:
        self.player = QMediaPlayer(self)
        self.audio  = QAudioOutput(self)

        self.audio.setVolume(0.55)   # moderate volume for background loop
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)

        if _DROP_VIDEO.exists():
            self.player.setSource(QUrl.fromLocalFile(str(_DROP_VIDEO)))
            # Loop: when playback stops, restart
            self.player.playbackStateChanged.connect(self._on_state_changed)
            self.player.play()
        # If no video, zone still works — just shows text on transparent bg

    def _on_state_changed(self, state) -> None:
        from PySide6.QtMultimedia import QMediaPlayer as MP
        if state == MP.PlaybackState.StoppedState:
            # Seamless loop: seek to start and play again
            self.player.setPosition(0)
            self.player.play()

    def set_volume(self, volume: float) -> None:
        """Set loop video volume 0.0–1.0."""
        self.audio.setVolume(max(0.0, min(1.0, volume)))

    def set_theme(self, theme: str) -> None:
        """Hot-swap theme without recreating the widget."""
        self._theme = theme
        if theme == "dark":
            self.title_label.setStyleSheet(
                "color: #FFFFFF; background: transparent; "
                "text-shadow: 0 2px 8px rgba(0,0,0,0.9), 0 0 24px rgba(10,132,255,0.4);"
            )
            self.sub_label.setStyleSheet(
                "color: rgba(255,255,255,0.65); background: transparent;"
            )
        else:
            self.title_label.setStyleSheet(
                "color: #0A0A0B; background: transparent; "
                "text-shadow: 0 1px 4px rgba(255,255,255,0.9), 0 2px 8px rgba(0,0,0,0.12);"
            )
            self.sub_label.setStyleSheet(
                "color: rgba(0,0,0,0.55); background: transparent;"
            )

    # ── Drag and drop ──────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self._drag_active = True
            self.hint_label.setText("Release to scan this folder")
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._drag_active = False
        self.hint_label.setText("")

    def dropEvent(self, event) -> None:
        self._drag_active = False
        self.hint_label.setText("")
        paths  = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        folders = [p for p in paths if Path(p).is_dir()]
        if folders:
            self.files_dropped.emit(folders)
            self.folder_selected.emit(folders[0])
        event.acceptProposedAction()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.folder_selected.emit(folder)
