"""Solid-colour mask window (overlay background)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QContextMenuEvent, QMouseEvent, QPalette
from PyQt6.QtWidgets import QColorDialog, QMenu, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel
from screen_translate.ui.theme.style_sheet import StyleSheet

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)


class MaskWindow(QWidget):
    """Solid-colour frameless overlay used as a visual mask.

    The user can pick any background colour.  Useful for hiding
    background distractions while reading the translation result.
    """

    def __init__(self, controller: AppController) -> None:
        """Create the mask window.

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
        self._opacity = 1.0
        self._pinned = True
        self._always_on_top = True
        StyleSheet.FLOATING_WINDOW.apply(self)

        self.setWindowTitle("Mask Window")
        self.resize(400, 300)
        self._apply_color()
        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self._hint = BodyLabel("Right-click for options")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setStyleSheet("color: rgba(200,200,200,80); font-size: 10px;")
        layout.addWidget(self._hint)

    def _apply_color(self) -> None:
        color_str: str = self.controller.settings.get("mask_window_bg_color", "#555555")
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(color_str))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

    def refresh_from_settings(self) -> None:
        """Re-apply appearance settings from persistent storage."""
        self._apply_color()

    # ------------------------------------------------------------------

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # type: ignore[override]
        menu = QMenu(self)
        color_str: str = self.controller.settings.get("mask_window_bg_color", "#555555")
        menu.addAction(f"Color: {color_str}").setEnabled(False)
        menu.addSeparator()
        menu.addAction("Change Color…", self._pick_color)
        menu.addSeparator()
        menu.addAction("Close", self.hide)
        menu.exec(event.globalPos())

    def _pick_color(self) -> None:
        current: str = self.controller.settings.get("mask_window_bg_color", "#555555")
        color = QColorDialog.getColor(QColor(current), self, "Choose Mask Color")
        if color.isValid():
            self.set_background_color(color.name())

    def overlay_opacity(self) -> float:
        """Return the current window opacity."""
        return self._opacity

    def set_overlay_opacity(self, opacity: float) -> None:
        """Set the current window opacity."""
        self._opacity = min(1.0, max(0.05, opacity))
        self.setWindowOpacity(self._opacity)

    def background_color(self) -> str:
        """Return the configured mask color."""
        return str(self.controller.settings.get("mask_window_bg_color", "#555555"))

    def set_background_color(self, color: str) -> None:
        """Persist and apply a new mask color."""
        self.controller.settings.set("mask_window_bg_color", color)
        self._apply_color()

    def is_pinned(self) -> bool:
        """Return whether the window is using the Tool flag."""
        return self._pinned

    def set_pinned(self, pinned: bool) -> None:
        """Toggle the Tool window flag."""
        self._pinned = pinned
        self._apply_window_flags()

    def is_always_on_top(self) -> bool:
        """Return whether the window stays on top."""
        return self._always_on_top

    def set_always_on_top(self, enabled: bool) -> None:
        """Toggle the always-on-top flag."""
        self._always_on_top = enabled
        self._apply_window_flags()

    def _apply_window_flags(self) -> None:
        """Rebuild window flags from pinned/on-top state while preserving geometry."""
        was_visible = self.isVisible()
        geometry = self.geometry()
        flags = Qt.WindowType.Tool if self._pinned else Qt.WindowType.Window
        if self._pinned:
            flags |= Qt.WindowType.FramelessWindowHint
        if self._always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setGeometry(geometry)
        if was_visible:
            self.show()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        self._drag_pos = None

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        self.show()
        self.raise_()
