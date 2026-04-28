"""Live log viewer window."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFontComboBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QPlainTextEdit,
    QWidget,
)
from qfluentwidgets import CheckBox, ComboBox, PushButton

from screen_translate.logging_setup import set_log_level
from screen_translate.ui.theme.style_sheet import StyleSheet

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class _LogEmitter(QObject):
    """Qt bridge for log lines coming from loguru sinks."""

    line_ready = pyqtSignal(str)


class _QtLogSink:
    """Loguru sink that forwards formatted lines into the UI thread."""

    def __init__(self, emitter: _LogEmitter) -> None:
        self._emitter = emitter

    def write(self, message: str) -> None:
        text = message.rstrip()
        if text:
            self._emitter.line_ready.emit(text)


class LogPage(QWidget):
    """Embedded live log viewer backed by loguru."""

    def __init__(self, controller: AppController) -> None:
        """Create the log page.

        Args:
            controller: Application controller.
        """
        super().__init__()
        self.controller = controller
        self.setObjectName("LogPage")
        StyleSheet.AUXILIARY_WINDOW.apply(self)
        self._sink_id: int | None = None
        self._emitter = _LogEmitter()
        self._build_ui()
        self._install_handler()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        vl = QVBoxLayout(self)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("Log Level:"))
        self._cb_level = ComboBox()
        self._cb_level.addItems(_LOG_LEVELS)
        level_name = str(self.controller.settings.get("log_level", "DEBUG")).upper()
        idx = self._cb_level.findText(level_name)
        self._cb_level.setCurrentIndex(max(0, idx))
        self._cb_level.currentTextChanged.connect(self._on_level_changed)
        hl.addWidget(self._cb_level)

        hl.addWidget(QLabel("Font:"))
        self._cb_font = QFontComboBox(self)
        self._cb_font.setObjectName("LogFontCombo")
        saved_font = (
            str(self.controller.settings.get("log_font_family", "Courier New")).strip()
            or "Courier New"
        )
        self._cb_font.setCurrentFont(QFont(saved_font))
        self._cb_font.currentFontChanged.connect(self._on_font_changed)
        hl.addWidget(self._cb_font)

        self._chk_scroll = CheckBox("Auto-scroll")
        self._chk_scroll.setChecked(True)
        hl.addWidget(self._chk_scroll)

        self._btn_clear = PushButton("Clear")
        self._btn_clear.clicked.connect(
            self._log_view.clear if hasattr(self, "_log_view") else lambda: None
        )
        hl.addWidget(self._btn_clear)
        hl.addStretch()
        vl.addLayout(hl)

        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(5000)
        font = self._log_view.font()
        font.setFamily(saved_font)
        font.setPointSize(9)
        self._log_view.setFont(font)
        vl.addWidget(self._log_view)

        # Now bind clear button correctly
        self._btn_clear.clicked.disconnect()
        self._btn_clear.clicked.connect(self._log_view.clear)

    def _install_handler(self) -> None:
        """Attach a loguru sink that appends lines into the view."""
        self._emitter.line_ready.connect(self._append_log_line)
        self._sink_id = logger.add(
            _QtLogSink(self._emitter),
            format="{time:HH:mm:ss} [{level}] {extra[logger_name]}: {message}",
            level="DEBUG",
            enqueue=True,
            backtrace=False,
            diagnose=False,
        )

    @pyqtSlot(str)
    def _append_log_line(self, line: str) -> None:
        """Append a log line and keep the view scrolled when requested."""
        self._log_view.appendPlainText(line)
        if self._chk_scroll.isChecked():
            scrollbar = self._log_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    @pyqtSlot(str)
    def _on_level_changed(self, level_name: str) -> None:
        """Update the effective application log level."""
        set_log_level(level_name)
        self.controller.settings.set("log_level", level_name)

    @pyqtSlot(QFont)
    def _on_font_changed(self, font: QFont) -> None:
        """Update the log viewer font family and persist it."""
        current = self._log_view.font()
        current.setFamily(font.family())
        self._log_view.setFont(current)
        self.controller.settings.set("log_font_family", font.family())

    def __del__(self) -> None:
        """Remove handler on garbage collection."""
        if self._sink_id is not None:
            logger.remove(self._sink_id)


LogWindow = LogPage
