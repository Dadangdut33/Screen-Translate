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
from screen_translate.ui.style_sheet import StyleSheet

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
        self._opacity = min(1.0, max(0.05, self._opacity + delta))
        self.setWindowOpacity(self._opacity)

    def _open_settings(self) -> None:
        if self.controller.settings_dialog:
            self.controller.settings_dialog.show_and_raise()

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
