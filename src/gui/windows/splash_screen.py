"""
DesktopAI v2.0 — Boot Splash Screen
File: src/gui/windows/splash_screen.py

Plays boot_up.mp4 with audio during application startup.
Shows animated DesktopAI branding overlay with Inter font.
Fades out and calls the ready callback when video ends.

Requires: PySide6.QtMultimedia, PySide6.QtMultimediaWidgets
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QFontDatabase, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect,
)

_ASSETS = Path(__file__).resolve().parent.parent.parent.parent / "assets"
_BOOT_VIDEO = _ASSETS / "boot_up.mp4"
_FONT_PATH  = _ASSETS / "fonts" / "InterVariable.ttf"


class SplashScreen(QWidget):
    """
    Full-screen boot splash.

    Usage:
        splash = SplashScreen(theme="dark", on_finished=lambda: window.show())
        splash.show()
        splash.play()
    """

    def __init__(
        self,
        theme: str = "dark",
        on_finished=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._on_finished = on_finished
        self._finished = False

        # Window setup — frameless, always on top
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.SplashScreen
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(1100, 680)
        self._center_on_screen()

        # Build layers
        self._build_ui()
        self._setup_player()

    # ── UI ─────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Background fill
        bg_color = "#0A0A0B" if self._theme == "dark" else "#F0F0F2"
        self.setStyleSheet(f"background: {bg_color};")

        # Video widget (fills the whole window)
        self.video_widget = QVideoWidget(self)
        self.video_widget.setGeometry(0, 0, 1100, 680)

        # Overlay — sits on top of video
        self.overlay = QWidget(self)
        self.overlay.setGeometry(0, 0, 1100, 680)
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.overlay.setStyleSheet("background: transparent;")

        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 48)
        overlay_layout.setSpacing(0)
        overlay_layout.addStretch()

        # Logo dot + brand name row
        brand_row = QWidget()
        brand_row.setStyleSheet("background: transparent;")
        brand_row_layout = QVBoxLayout(brand_row)
        brand_row_layout.setContentsMargins(0, 0, 0, 0)
        brand_row_layout.setSpacing(8)
        brand_row_layout.setAlignment(Qt.AlignCenter)

        # Inter font registration
        font_id = QFontDatabase.addApplicationFont(str(_FONT_PATH))
        inter_families = QFontDatabase.applicationFontFamilies(font_id)
        font_family = inter_families[0] if inter_families else "Segoe UI"

        # App name
        text_color, shadow_css = self._text_styles()

        self.name_label = QLabel("DesktopAI")
        name_font = QFont(font_family)
        name_font.setPointSize(42)
        name_font.setWeight(QFont.Weight.Bold)
        self.name_label.setFont(name_font)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(
            f"color: {text_color}; background: transparent; {shadow_css}"
        )

        # Tagline
        self.tag_label = QLabel("Your local AI file organizer")
        tag_font = QFont(font_family)
        tag_font.setPointSize(14)
        tag_font.setWeight(QFont.Weight.Normal)
        self.tag_label.setFont(tag_font)
        self.tag_label.setAlignment(Qt.AlignCenter)
        tag_color = "rgba(255,255,255,0.72)" if self._theme == "dark" else "rgba(0,0,0,0.55)"
        self.tag_label.setStyleSheet(
            f"color: {tag_color}; background: transparent; letter-spacing: 0.5px;"
        )

        # Loading indicator
        self.status_label = QLabel("Starting…")
        status_font = QFont(font_family)
        status_font.setPointSize(11)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignCenter)
        status_color = "rgba(255,255,255,0.45)" if self._theme == "dark" else "rgba(0,0,0,0.38)"
        self.status_label.setStyleSheet(
            f"color: {status_color}; background: transparent;"
        )

        brand_row_layout.addWidget(self.name_label)
        brand_row_layout.addWidget(self.tag_label)
        brand_row_layout.addSpacing(16)
        brand_row_layout.addWidget(self.status_label)

        overlay_layout.addWidget(brand_row)

        # Opacity effect for fade animations
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)

        # Text fade-in animation
        self._text_effect = QGraphicsOpacityEffect(brand_row)
        brand_row.setGraphicsEffect(self._text_effect)
        self._text_effect.setOpacity(0.0)

        # Animate text in after 400ms
        QTimer.singleShot(400, self._animate_text_in)

        # Cycle status messages
        self._status_messages = [
            "Starting…",
            "Loading AI engine…",
            "Initializing database…",
            "Preparing workspace…",
            "Ready.",
        ]
        self._status_idx = 0
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._cycle_status)
        self._status_timer.start(900)

    def _text_styles(self) -> tuple[str, str]:
        """Return (text_color, shadow_css) for current theme."""
        if self._theme == "dark":
            color = "#FFFFFF"
            shadow = (
                "text-shadow: "
                "0 0 40px rgba(10,132,255,0.6), "
                "0 2px 8px rgba(0,0,0,0.9);"
            )
        else:
            color = "#0A0A0B"
            shadow = (
                "text-shadow: "
                "0 1px 3px rgba(0,0,0,0.18), "
                "0 0 20px rgba(255,255,255,0.8);"
            )
        return color, shadow

    # ── Media player ───────────────────────────────────────────────

    def _setup_player(self) -> None:
        self.player = QMediaPlayer(self)
        self.audio  = QAudioOutput(self)

        self.audio.setVolume(0.85)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)

        if _BOOT_VIDEO.exists():
            self.player.setSource(QUrl.fromLocalFile(str(_BOOT_VIDEO)))
        else:
            # No video — just show branding, finish after 3s
            QTimer.singleShot(3000, self._finish)
            return

        self.player.playbackStateChanged.connect(self._on_playback_changed)
        self.player.errorOccurred.connect(self._on_error)

    def play(self) -> None:
        """Start video playback. Call after show()."""
        if _BOOT_VIDEO.exists():
            self.player.play()
        else:
            QTimer.singleShot(3000, self._finish)

    # ── Animations ─────────────────────────────────────────────────

    def _animate_text_in(self) -> None:
        """Fade in the brand text overlay."""
        anim = QPropertyAnimation(self._text_effect, b"opacity", self)
        anim.setDuration(800)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._text_anim = anim  # keep reference

    def _animate_fade_out(self) -> None:
        """Fade the entire splash to transparent, then call on_finished."""
        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(600)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.finished.connect(self._call_finished)
        anim.start()
        self._fade_anim = anim

    def _cycle_status(self) -> None:
        if self._status_idx < len(self._status_messages) - 1:
            self._status_idx += 1
            self.status_label.setText(self._status_messages[self._status_idx])

    # ── Playback events ────────────────────────────────────────────

    def _on_playback_changed(self, state) -> None:
        from PySide6.QtMultimedia import QMediaPlayer as MP
        if state == MP.PlaybackState.StoppedState and not self._finished:
            self._finish()

    def _on_error(self, error, error_string: str) -> None:
        from core.logger import get_logger
        get_logger(__name__).warning("Splash video error: %s", error_string)
        self._finish()

    def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        self._status_timer.stop()
        self.status_label.setText("Ready.")
        QTimer.singleShot(300, self._animate_fade_out)

    def _call_finished(self) -> None:
        self.player.stop()
        self.hide()
        if callable(self._on_finished):
            self._on_finished()

    # ── Helpers ────────────────────────────────────────────────────

    def _center_on_screen(self) -> None:
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )