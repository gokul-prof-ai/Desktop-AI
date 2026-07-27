"""Test fixtures and dependency fallbacks."""

from __future__ import annotations

import sys
import types
from typing import Any, Callable


def pytest_configure() -> None:
    """Provide a tiny PySide6 fallback when native Qt libraries are missing."""
    try:
        import PySide6.QtWidgets  # noqa: F401
    except ImportError:
        _install_pyside6_fallback()


def _install_pyside6_fallback() -> None:
    pyside6 = types.ModuleType("PySide6")
    qtcore = types.ModuleType("PySide6.QtCore")
    qtwidgets = types.ModuleType("PySide6.QtWidgets")

    class _BoundSignal:
        def __init__(self) -> None:
            self._callbacks: list[Callable[..., Any]] = []

        def connect(self, callback: Callable[..., Any]) -> None:
            self._callbacks.append(callback)

        def emit(self, *args: Any, **kwargs: Any) -> None:
            for callback in list(self._callbacks):
                callback(*args, **kwargs)

    class Signal:
        def __init__(self, *_types: Any) -> None:
            self._name: str | None = None

        def __set_name__(self, owner: type[Any], name: str) -> None:
            self._name = f"__qt_signal_{name}"

        def __get__(self, instance: Any, owner: type[Any] | None = None) -> Any:
            if instance is None:
                return self
            signal = instance.__dict__.get(self._name)
            if signal is None:
                signal = _BoundSignal()
                instance.__dict__[self._name] = signal
            return signal

    class QThread:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self._running = False

        def start(self) -> None:
            self._running = True
            try:
                self.run()
            finally:
                self._running = False

        def run(self) -> None:
            pass

        def isRunning(self) -> bool:
            return self._running

        def quit(self) -> None:
            self._running = False

        def wait(self, _msecs: int | None = None) -> bool:
            self._running = False
            return True

        def terminate(self) -> None:
            self._running = False

    class _Widget:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self._enabled = True
            self._text = ""

        def setEnabled(self, enabled: bool) -> None:
            self._enabled = enabled

        def resize(self, *_args: Any) -> None:
            pass

        def setWindowTitle(self, title: str) -> None:
            self._title = title

    class QApplication:
        _instance: QApplication | None = None

        def __init__(self, _args: list[str] | None = None) -> None:
            QApplication._instance = self

        @classmethod
        def instance(cls) -> QApplication | None:
            return cls._instance

        def exec(self) -> int:
            return 0

    class QWidget(_Widget):
        pass

    class QMainWindow(QWidget):
        def setCentralWidget(self, widget: QWidget) -> None:
            self._central_widget = widget

    class _Layout:
        def __init__(self, *_args: Any) -> None:
            self.items: list[Any] = []

        def addWidget(self, widget: Any) -> None:
            self.items.append(widget)

        def addLayout(self, layout: Any) -> None:
            self.items.append(layout)

    class QVBoxLayout(_Layout):
        pass

    class QHBoxLayout(_Layout):
        pass

    class QLabel(QWidget):
        def __init__(self, text: str = "") -> None:
            super().__init__()
            self._text = text

        def setText(self, text: str) -> None:
            self._text = text

        def text(self) -> str:
            return self._text

    class QLineEdit(QLabel):
        def __init__(self) -> None:
            super().__init__("")
            self.returnPressed = _BoundSignal()

        def setPlaceholderText(self, text: str) -> None:
            self._placeholder = text

        def clear(self) -> None:
            self._text = ""

    class QPushButton(QLabel):
        def __init__(self, text: str = "") -> None:
            super().__init__(text)
            self.clicked = _BoundSignal()

    class QPlainTextEdit(QLabel):
        def setReadOnly(self, read_only: bool) -> None:
            self._read_only = read_only

        def appendPlainText(self, text: str) -> None:
            self._text = f"{self._text}\n{text}" if self._text else text

    class QListWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.items: list[str] = []

        def addItem(self, text: str) -> None:
            self.items.append(text)

        def clear(self) -> None:
            self.items.clear()

    class QTableWidget(QWidget):
        def __init__(self, rows: int, columns: int) -> None:
            super().__init__()
            self.rows = rows
            self.columns = columns
            self.items: dict[tuple[int, int], Any] = {}

        def setHorizontalHeaderLabels(self, labels: list[str]) -> None:
            self.labels = labels

        def setRowCount(self, rows: int) -> None:
            self.rows = rows

        def setItem(self, row: int, column: int, item: Any) -> None:
            self.items[(row, column)] = item

    class QTableWidgetItem(QLabel):
        pass

    class QTabWidget(QWidget):
        def addTab(self, widget: QWidget, title: str) -> None:
            pass

    class QFileDialog:
        @staticmethod
        def getExistingDirectory(*_args: Any, **_kwargs: Any) -> str:
            return ""

    class QMessageBox:
        @staticmethod
        def warning(*_args: Any, **_kwargs: Any) -> None:
            pass

    qtcore.QThread = QThread
    qtcore.Signal = Signal
    for widget_cls in (
        QApplication,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    ):
        setattr(qtwidgets, widget_cls.__name__, widget_cls)

    pyside6.QtCore = qtcore
    pyside6.QtWidgets = qtwidgets
    sys.modules.update(
        {
            "PySide6": pyside6,
            "PySide6.QtCore": qtcore,
            "PySide6.QtWidgets": qtwidgets,
        }
    )