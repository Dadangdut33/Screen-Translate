"""Transparent, draggable/resizable capture overlay window."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, Qt, pyqtSlot
from PyQt6.QtGui import QAction, QColor, QContextMenuEvent, QMouseEvent, QPainter
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

from screen_translate.ui.utils import load_icon

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)


class CaptureWindow(QWidget):
    """Floating semi-transparent overlay used for continuous OCR capture.

    The user positions and resizes this window over the region of interest.
    Clicking *Capture & Translate* grabs pixels exactly under the window
    and submits them to the OCR pipeline.
    """

    def __init__(self, controller: AppController) -> None:
        """Create the capture window.

        Args:
            controller: Application controller.
        """
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.controller = controller
        self._drag_pos: QPoint | None = None
        self._is_hidden_titlebar = False

        icon = load_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)

        self.setWindowOpacity(0.8)
        self.setMinimumSize(200, 80)
        self.resize(600, 150)

        self._build_ui()
        self._build_context_menu()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        top_row = QHBoxLayout()

        self._drag_label = QLabel("▶ Drag")
        self._drag_label.setToolTip("Drag here to move the window")
        self._drag_label.setCursor(Qt.CursorShape.OpenHandCursor)
        top_row.addWidget(self._drag_label)

        self._btn_capture = QPushButton("Capture & Translate")
        self._btn_capture.clicked.connect(self.trigger_capture)
        top_row.addWidget(self._btn_capture)

        top_row.addStretch()

        self._lbl_opacity = QLabel("Opacity 80%")
        top_row.addWidget(self._lbl_opacity)

        layout.addLayout(top_row)
        layout.addStretch()

        # Size grip in bottom-right corner
        grip_row = QHBoxLayout()
        grip_row.addStretch()
        grip_row.addWidget(QSizeGrip(self))
        layout.addLayout(grip_row)

        # Drag interactions
        self._drag_label.mousePressEvent = self._drag_press  # type: ignore[method-assign]
        self._drag_label.mouseMoveEvent = self._drag_move    # type: ignore[method-assign]
        self._drag_label.mouseReleaseEvent = self._drag_release  # type: ignore[method-assign]

    def _build_context_menu(self) -> None:
        self._ctx_menu = QMenu(self)
        self._act_topmost = QAction("Always on Top", self, checkable=True, checked=True)
        self._act_topmost.triggered.connect(self._toggle_topmost)
        self._ctx_menu.addAction(self._act_topmost)
        self._ctx_menu.addSeparator()
        self._ctx_menu.addAction("Increase Opacity (+10%)", lambda: self._adjust_opacity(0.1))
        self._ctx_menu.addAction("Decrease Opacity (-10%)", lambda: self._adjust_opacity(-0.1))
        self._ctx_menu.addSeparator()
        self._ctx_menu.addAction("Close", self.hide)

    # ------------------------------------------------------------------
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # type: ignore[override]
        """Show the context menu on right-click."""
        self._ctx_menu.exec(event.globalPos())

    def paintEvent(self, event: object) -> None:  # type: ignore[override]
        """Draw a semi-transparent tinted background."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))

    def _drag_press(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._drag_label.setCursor(Qt.CursorShape.ClosedHandCursor)

    def _drag_move(self, event: QMouseEvent) -> None:
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _drag_release(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        self._drag_label.setCursor(Qt.CursorShape.OpenHandCursor)

    @pyqtSlot()
    def trigger_capture(self) -> None:
        """Grab the screen region beneath this window and start OCR."""

        from PIL import Image
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtWidgets import QApplication

        # Hide self so we don't capture our own UI
        prev_opacity = self.windowOpacity()
        self.setWindowOpacity(0.0)
        QApplication.processEvents()

        geo = self.geometry()
        # Apply user offset from settings
        sx: int = int(self.controller.settings.get("offSetX", 0))
        sy: int = int(self.controller.settings.get("offSetY", 0))
        sw: int = int(self.controller.settings.get("offSetW", 0))
        sh: int = int(self.controller.settings.get("offSetH", 0))

        screen = QApplication.primaryScreen()
        if screen:
            pixmap: QPixmap = screen.grabWindow(
                0,
                geo.x() + sx,
                geo.y() + sy,
                geo.width() + sw,
                geo.height() + sh,
            )
            # Convert QPixmap → PIL Image
            buf = pixmap.toImage()
            buf_bytes = buf.bits()  # type: ignore[attr-defined]
            if buf_bytes:
                pil_img = Image.frombytes(
                    "RGB",
                    (buf.width(), buf.height()),
                    bytes(buf_bytes),
                    "raw",
                    "BGRA",
                )
                self.controller.run_ocr(pil_img)
            else:
                logger.error("Could not read pixmap bytes")

        self.setWindowOpacity(prev_opacity)

    @pyqtSlot(bool)
    def _toggle_topmost(self, checked: bool) -> None:
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _adjust_opacity(self, delta: float) -> None:
        cur = self.windowOpacity()
        new = min(1.0, max(0.1, cur + delta))
        self.setWindowOpacity(new)
        pct = int(new * 100)
        self._lbl_opacity.setText(f"Opacity {pct}%")

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        self.show()
        self.raise_()
        self.activateWindow()
