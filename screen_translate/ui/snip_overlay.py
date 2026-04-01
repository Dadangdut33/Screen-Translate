"""Per-monitor full-screen snip overlay."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)


class SnipOverlay(QWidget):
    """Full-screen, semi-transparent overlay on a single monitor.

    The user draws a rubber-band rectangle; on mouse release the
    enclosed region is captured and submitted to the OCR pipeline.
    Multiple instances are created (one per monitor) and coordinated
    by :class:`~screen_translate.ui.controller.AppController`.
    """

    def __init__(self, controller: AppController, screen_index: int = 0) -> None:
        """Create an overlay for the given screen.

        Args:
            controller: Application controller.
            screen_index: Index into ``QApplication.screens()``.
        """
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.controller = controller
        self.screen_index = screen_index
        self._screen_pixmap: QPixmap | None = None
        self._start: QPoint | None = None
        self._current: QPoint | None = None
        self._active = False

        self.setWindowTitle(f"Snip Overlay (Screen {screen_index + 1})")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowOpacity(1.0)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # Apply geometry of target screen
        screens = QApplication.screens()
        if screen_index < len(screens):
            self.setGeometry(screens[screen_index].geometry())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_snip(self) -> None:
        """Capture the full screen image and display this overlay."""
        screens = QApplication.screens()
        if self.screen_index >= len(screens):
            return

        screen = screens[self.screen_index]
        self._screen_pixmap = screen.grabWindow(0)
        self._start = None
        self._current = None
        self._active = True

        self.setWindowTitle("Snip Overlay (Screen {})".format(self.screen_index + 1))
        self.setGeometry(screen.geometry())
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def cancel(self) -> None:
        """Hide the overlay without capturing."""
        self._active = False
        self.hide()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        """Cancel snip on Escape."""
        if event.key() == Qt.Key.Key_Escape:
            self._cancel_all()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        """Record selection start on left button press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._current = event.pos()
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        """Update selection rectangle during drag."""
        if self._start:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        """Capture the selected region on left button release."""
        if event.button() == Qt.MouseButton.LeftButton and self._start:
            self._current = event.pos()
            self._capture_selection()

    def paintEvent(self, event: object) -> None:  # type: ignore[override]
        """Draw screenshot background + semi-transparent mask + selection rect."""
        painter = QPainter(self)

        # Draw screenshot
        if self._screen_pixmap:
            painter.drawPixmap(self.rect(), self._screen_pixmap)

        # Dark semi-transparent overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        # Selection rectangle
        if self._start and self._current:
            sel = self._selection_rect()
            # Clear the selection area (show original screenshot)
            if self._screen_pixmap:
                painter.drawPixmap(sel, self._screen_pixmap, sel)
            pen = QPen(QColor(255, 80, 80), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(sel)

        painter.end()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _selection_rect(self) -> QRect:
        """Return a normalised selection rectangle.

        Returns:
            QRect in widget-local coordinates.
        """
        if not self._start or not self._current:
            return QRect()
        return QRect(self._start, self._current).normalized()

    def _capture_selection(self) -> None:
        """Crop the screen pixmap to the selection and run OCR."""
        sel = self._selection_rect()
        if sel.width() < 4 or sel.height() < 4:
            self._cancel_all()
            return

        self._cancel_all()

        if not self._screen_pixmap:
            return

        cropped = self._screen_pixmap.copy(sel)
        pil_image = _pixmap_to_pil(cropped)
        if pil_image:
            self.controller.run_ocr(pil_image)

    def _cancel_all(self) -> None:
        """Hide all overlays managed by the controller."""
        for overlay in self.controller.snip_overlays:
            overlay.cancel()


def _pixmap_to_pil(pixmap: QPixmap) -> object | None:
    """Convert a QPixmap to a Pillow Image.

    Args:
        pixmap: Source QPixmap.

    Returns:
        PIL.Image.Image or None on failure.
    """
    try:
        from PIL import Image

        img = pixmap.toImage()
        img = img.convertToFormat(img.Format.Format_RGB32)
        bits = img.bits()
        if bits is None:
            return None
        bits.setsize(img.sizeInBytes())
        pil = Image.frombytes(
            "RGB",
            (img.width(), img.height()),
            bytes(bits),
            "raw",
            "BGRX",
        )
        return pil
    except Exception as exc:
        logger.exception("pixmap_to_pil failed: %s", exc)
        return None
