"""Live log viewer window."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)

_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class _QtLogHandler(logging.Handler):
    """Logging handler that appends records to a QPlainTextEdit."""

    def __init__(self, widget: QPlainTextEdit) -> None:
        super().__init__()
        self._widget = widget

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._widget.appendPlainText(msg)
        except Exception:
            self.handleError(record)


class LogWindow(QMainWindow):
    """Live scrolling log viewer backed by Python's logging system."""

    def __init__(self, controller: AppController) -> None:
        """Create the log window.

        Args:
            controller: Application controller.
        """
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Log Viewer")
        self.resize(800, 450)
        self._handler: _QtLogHandler | None = None
        self._build_ui()
        self._install_handler()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        vl = QVBoxLayout(central)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("Log Level:"))
        self._cb_level = QComboBox()
        self._cb_level.addItems(_LOG_LEVELS)
        current_level = logging.getLogger().level
        level_name = logging.getLevelName(current_level)
        idx = self._cb_level.findText(level_name)
        self._cb_level.setCurrentIndex(max(0, idx))
        self._cb_level.currentTextChanged.connect(self._on_level_changed)
        hl.addWidget(self._cb_level)

        self._chk_scroll = QCheckBox("Auto-scroll")
        self._chk_scroll.setChecked(True)
        hl.addWidget(self._chk_scroll)

        self._btn_clear = QPushButton("Clear")
        self._btn_clear.clicked.connect(self._log_view.clear if hasattr(self, "_log_view") else lambda: None)
        hl.addWidget(self._btn_clear)
        hl.addStretch()
        vl.addLayout(hl)

        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(5000)
        font = self._log_view.font()
        font.setFamily("Courier New")
        font.setPointSize(9)
        self._log_view.setFont(font)
        vl.addWidget(self._log_view)

        # Now bind clear button correctly
        self._btn_clear.clicked.disconnect()
        self._btn_clear.clicked.connect(self._log_view.clear)

    def _install_handler(self) -> None:
        """Attach the Qt logging handler to the root logger."""
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
        self._handler = _QtLogHandler(self._log_view)
        self._handler.setFormatter(fmt)
        logging.getLogger().addHandler(self._handler)

    @pyqtSlot(str)
    def _on_level_changed(self, level_name: str) -> None:
        """Update the root logger level."""
        level = logging.getLevelName(level_name)
        logging.getLogger().setLevel(level)
        self.controller.settings.set("log_level", level_name)

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: object) -> None:  # type: ignore[override]
        """Detach the logging handler when hidden."""
        self.hide()

    def __del__(self) -> None:
        """Remove handler on garbage collection."""
        if self._handler:
            logging.getLogger().removeHandler(self._handler)
