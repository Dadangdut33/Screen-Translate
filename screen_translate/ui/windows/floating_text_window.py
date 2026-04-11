"""Detached floating text windows (query / result display)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import (
    QColor,
    QContextMenuEvent,
    QFont,
    QMouseEvent,
    QPalette,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel
from screen_translate.ui.theme.style_sheet import StyleSheet

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)

WindowRole = Literal["q", "res"]


class DetachedWindow(QWidget):
    """Floating, frameless overlay that displays OCR/translation text.

    Two instances are created: one for the recognised query text ("q")
    and one for the translated result ("res").  Both support opacity
    control, drag, and a right-click context menu.
    """

    def __init__(
        self,
        controller: AppController,
        role: WindowRole,
        parent: QWidget | None = None,
    ) -> None:
        """Create the detached window.

        Args:
            controller: Application controller.
            role: ``"q"`` for query/OCR text, ``"res"`` for translation result.
            parent: Optional Qt parent.
        """
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.controller = controller
        self.role = role
        self._drag_pos: QPoint | None = None
        self._opacity = 1.0
        self._text = ""
        self._pinned = True
        self._always_on_top = True
        StyleSheet.FLOATING_WINDOW.apply(self)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.resize(600, 120)
        self._build_ui()
        self._apply_settings()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self._label = BodyLabel()
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._label)

        # Drag using the label
        self._label.mousePressEvent = self._drag_press    # type: ignore[method-assign]
        self._label.mouseMoveEvent = self._drag_move      # type: ignore[method-assign]
        self._label.mouseReleaseEvent = self._drag_release  # type: ignore[method-assign]

    def _apply_settings(self) -> None:
        """Load font and colour settings from the settings store."""
        s = self.controller.settings
        key = f"tb_ex_{self.role}"
        font_family: str = s.get(f"{key}_font", "")
        font_size: int = s.get(f"{key}_font_size", 12)
        fg: str = s.get(f"{key}_font_color", "#FFFFFF")
        bg: str = s.get(f"{key}_bg_color", "#000000")

        font = QFont(font_family if font_family else QFont().family(), font_size)
        self._label.setFont(font)

        palette = self._label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(fg))
        palette.setColor(QPalette.ColorRole.Window, QColor(bg))
        self._label.setPalette(palette)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(bg))
        self.setPalette(pal)

    def refresh_from_settings(self) -> None:
        """Re-apply appearance settings from persistent storage."""
        self._apply_settings()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_text(self, text: str) -> None:
        """Update the displayed text.

        Args:
            text: New text to display.
        """
        self._text = text
        self._label.setText(text)
        # Auto-resize height
        self._label.adjustSize()
        self.adjustSize()

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        self.show()
        self.raise_()

    def overlay_opacity(self) -> float:
        """Return the current window opacity."""
        return self._opacity

    def set_overlay_opacity(self, opacity: float) -> None:
        """Set the current window opacity."""
        self._opacity = min(1.0, max(0.05, opacity))
        self.setWindowOpacity(self._opacity)

    def background_color(self) -> str:
        """Return the configured background color for this floating window."""
        return str(self.controller.settings.get(f"tb_ex_{self.role}_bg_color", "#000000"))

    def set_background_color(self, color: str) -> None:
        """Persist and apply a new background color."""
        self.controller.settings.set(f"tb_ex_{self.role}_bg_color", color)
        self._apply_settings()

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

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # type: ignore[override]
        """Show right-click menu."""
        menu = QMenu(self)
        menu.addAction("Copy", lambda: QApplication.clipboard().setText(self._text))
        menu.addSeparator()
        menu.addAction("Increase Opacity (+10%)", lambda: self._adjust_opacity(0.1))
        menu.addAction("Decrease Opacity (-10%)", lambda: self._adjust_opacity(-0.1))
        menu.addSeparator()
        menu.addAction("Settings…", self._open_settings)
        menu.addSeparator()
        menu.addAction("Close", self.hide)
        menu.exec(event.globalPos())

    def _adjust_opacity(self, delta: float) -> None:
        self.set_overlay_opacity(self._opacity + delta)

    def _open_settings(self) -> None:
        if self.controller.settings_page:
            self.controller.settings_page.show_and_raise()

    # ------------------------------------------------------------------
    # Drag support
    # ------------------------------------------------------------------

    def _drag_press(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _drag_move(self, event: QMouseEvent) -> None:
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _drag_release(self, event: QMouseEvent) -> None:
        self._drag_pos = None


FloatingTextWindow = DetachedWindow
