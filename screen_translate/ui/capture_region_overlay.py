"""Per-screen overlay used to define a persistent capture rectangle."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)


class CaptureRegionOverlay(QWidget):
    """Fullscreen overlay that lets the user define a persistent capture region."""

    def __init__(self, controller: AppController, screen_index: int = 0) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.controller = controller
        self.screen_index = screen_index
        self._start: QPoint | None = None
        self._current: QPoint | None = None
        self._active = False

        self.setWindowTitle(f"Capture Region Overlay (Screen {screen_index + 1})")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screens = QApplication.screens()
        if screen_index < len(screens):
            self.setGeometry(screens[screen_index].geometry())

    def start_selection(self) -> None:
        """Show the overlay and let the user draw a capture region."""
        screens = QApplication.screens()
        if self.screen_index >= len(screens):
            return
        screen = screens[self.screen_index]
        self._start = None
        self._current = None
        self._active = True
        self.setGeometry(screen.geometry())
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def cancel(self) -> None:
        """Hide the overlay without changing the stored region."""
        self._active = False
        self.hide()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Escape:
            self._cancel_all()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._current = event.pos()
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if self._start:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton and self._start:
            self._current = event.pos()
            self._store_selection()

    def paintEvent(self, event: object) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))

        existing = self._existing_local_rect()
        if existing is not None:
            painter.setPen(QPen(QColor(0, 200, 255), 2, Qt.PenStyle.DashLine))
            painter.drawRect(existing)

        if self._start and self._current:
            sel = self._selection_rect()
            painter.fillRect(sel, QColor(255, 255, 255, 20))
            painter.setPen(QPen(QColor(255, 120, 60), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(sel)

    def _selection_rect(self) -> QRect:
        if not self._start or not self._current:
            return QRect()
        return QRect(self._start, self._current).normalized()

    def _existing_local_rect(self) -> QRect | None:
        rect = self.controller.get_capture_region()
        if rect is None:
            return None
        overlay_geo = self.geometry()
        if not overlay_geo.intersects(rect):
            return None
        local_top_left = rect.topLeft() - overlay_geo.topLeft()
        return QRect(local_top_left, rect.size())

    def _store_selection(self) -> None:
        sel = self._selection_rect()
        if sel.width() < 4 or sel.height() < 4:
            self._cancel_all()
            return

        screen_geo = self.geometry()
        global_rect = QRect(
            screen_geo.x() + sel.x(),
            screen_geo.y() + sel.y(),
            sel.width(),
            sel.height(),
        )
        logger.debug(
            "Capture region selected on screen %d: local=%s global=%s screen_geo=%s",
            self.screen_index,
            sel.getRect(),
            global_rect.getRect(),
            screen_geo.getRect(),
        )
        self.controller.set_capture_region(global_rect)
        self._cancel_all()

    def _cancel_all(self) -> None:
        for overlay in self.controller.capture_region_overlays:
            overlay.cancel()
