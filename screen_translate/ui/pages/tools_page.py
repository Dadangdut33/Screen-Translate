"""Tools page for managing auxiliary windows and window state."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QFrame,
    QHBoxLayout,
    QStyle,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    PushButton,
    Slider,
    ToolButton,
    ToolTipFilter,
    ToolTipPosition,
    TitleLabel,
)
import qtawesome as qta

if TYPE_CHECKING:
    from screen_translate.ui.pages.main_window import MainWindow


class ToolsPage(QWidget):
    """Scrollable dashboard for managing the app's windows."""

    def __init__(self, main_window: MainWindow) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.controller = main_window.controller
        self.setObjectName("ToolsPage")

        self._tool_cards: dict[str, dict[str, object]] = {}
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(350)
        self._refresh_timer.timeout.connect(self._refresh_tools_cards)

        self._build_ui()
        self._refresh_timer.start()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = TitleLabel("Tools")
        layout.addWidget(title)

        self._build_window_card(
            layout,
            key="main",
            title="Main Window",
            window_getter=lambda: self.main_window,
            action_specs=[
                (
                    "Hide",
                    self._mdi_icon(
                        "mdi6.window-minimize",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_TitleBarShadeButton
                        ),
                    ),
                    self.main_window._hide_to_tray,
                ),
                (
                    "Close",
                    self._mdi_icon(
                        "mdi6.close",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_TitleBarCloseButton
                        ),
                    ),
                    self.main_window.close,
                ),
                (
                    "Quit",
                    self._mdi_icon(
                        "mdi6.exit-to-app",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_DialogCloseButton
                        ),
                    ),
                    self.main_window._quit_app,
                ),
            ],
            opacity_getter=lambda win: float(win.windowOpacity() or 1.0),
            opacity_setter=lambda win, value: win.setWindowOpacity(value),
            top_getter=lambda win: bool(
                win.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
            ),
            top_setter=self._set_window_always_on_top,
            color_getter=None,
            color_setter=None,
            show_pin=False,
            color_label="",
        )

        self._build_window_card(
            layout,
            key="capture",
            title="Capture Window",
            window_getter=lambda: self.controller.capture_window,
            action_specs=[
                (
                    "Show",
                    self._mdi_icon(
                        "mdi6.open-in-app",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_DialogOpenButton
                        ),
                    ),
                    self.main_window._open_capture_window,
                ),
                (
                    "Close",
                    self._mdi_icon(
                        "mdi6.close",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_TitleBarCloseButton
                        ),
                    ),
                    self.main_window._close_capture_window,
                ),
            ],
            opacity_getter=lambda win: float(win.overlay_opacity()),
            opacity_setter=lambda win, value: win.set_overlay_opacity(value),
            top_getter=lambda win: bool(win.is_always_on_top()),
            top_setter=lambda win, value: win.set_always_on_top(value),
            color_getter=lambda win: str(win.background_color()),
            color_setter=lambda win, value: win.set_background_color(value),
            pin_getter=lambda win: bool(win.is_pinned()),
            pin_setter=lambda win, value: win.set_pinned(value),
            color_label="Tint color",
        )

        self._build_window_card(
            layout,
            key="query",
            title="Query Window",
            window_getter=lambda: self.controller.query_window,
            action_specs=[
                (
                    "Show",
                    self._mdi_icon(
                        "mdi6.open-in-app",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_DialogOpenButton
                        ),
                    ),
                    self.main_window._open_query_window,
                ),
                (
                    "Close",
                    self._mdi_icon(
                        "mdi6.close",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_TitleBarCloseButton
                        ),
                    ),
                    self.main_window._close_query_window,
                ),
            ],
            opacity_getter=lambda win: float(win.overlay_opacity()),
            opacity_setter=lambda win, value: win.set_overlay_opacity(value),
            top_getter=lambda win: bool(win.is_always_on_top()),
            top_setter=lambda win, value: win.set_always_on_top(value),
            color_getter=lambda win: str(win.background_color()),
            color_setter=lambda win, value: win.set_background_color(value),
            pin_getter=lambda win: bool(win.is_pinned()),
            pin_setter=lambda win, value: win.set_pinned(value),
            color_label="Background color",
        )

        self._build_window_card(
            layout,
            key="result",
            title="Result Window",
            window_getter=lambda: self.controller.result_window,
            action_specs=[
                (
                    "Show",
                    self._mdi_icon(
                        "mdi6.open-in-app",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_DialogOpenButton
                        ),
                    ),
                    self.main_window._open_result_window,
                ),
                (
                    "Close",
                    self._mdi_icon(
                        "mdi6.close",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_TitleBarCloseButton
                        ),
                    ),
                    self.main_window._close_result_window,
                ),
            ],
            opacity_getter=lambda win: float(win.overlay_opacity()),
            opacity_setter=lambda win, value: win.set_overlay_opacity(value),
            top_getter=lambda win: bool(win.is_always_on_top()),
            top_setter=lambda win, value: win.set_always_on_top(value),
            color_getter=lambda win: str(win.background_color()),
            color_setter=lambda win, value: win.set_background_color(value),
            pin_getter=lambda win: bool(win.is_pinned()),
            pin_setter=lambda win, value: win.set_pinned(value),
            color_label="Background color",
        )

        self._build_window_card(
            layout,
            key="mask",
            title="Mask Window",
            window_getter=lambda: self.controller.mask_window,
            action_specs=[
                (
                    "Show",
                    self._mdi_icon(
                        "mdi6.open-in-app",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_DialogOpenButton
                        ),
                    ),
                    self.main_window._open_mask_window,
                ),
                (
                    "Close",
                    self._mdi_icon(
                        "mdi6.close",
                        self.style().standardIcon(
                            QStyle.StandardPixmap.SP_TitleBarCloseButton
                        ),
                    ),
                    self.main_window._close_mask_window,
                ),
            ],
            opacity_getter=lambda win: float(win.overlay_opacity()),
            opacity_setter=lambda win, value: win.set_overlay_opacity(value),
            top_getter=lambda win: bool(win.is_always_on_top()),
            top_setter=lambda win, value: win.set_always_on_top(value),
            color_getter=lambda win: str(win.background_color()),
            color_setter=lambda win, value: win.set_background_color(value),
            pin_getter=lambda win: bool(win.is_pinned()),
            pin_setter=lambda win, value: win.set_pinned(value),
            color_label="Background color",
        )

        utility_card = QFrame(self)
        utility_card.setObjectName("AboutInfoCard")
        utility_layout = QVBoxLayout(utility_card)
        utility_layout.setContentsMargins(16, 16, 16, 16)
        utility_layout.setSpacing(10)
        utility_layout.addWidget(BodyLabel("Utilities"))

        captured_btn = PushButton("Open Captured Images")
        captured_btn.clicked.connect(self.main_window._open_captured_dir)
        utility_layout.addWidget(captured_btn)

        test_dialog_btn = PushButton("Test Controller Dialog")
        test_dialog_btn.clicked.connect(self.controller.show_test_dialog)
        utility_layout.addWidget(test_dialog_btn)

        layout.addWidget(utility_card)
        layout.addStretch(1)

    def _build_window_card(
        self,
        parent_layout: QVBoxLayout,
        *,
        key: str,
        title: str,
        window_getter: Callable[[], QWidget | None],
        action_specs: list[tuple[str, QIcon, Callable[[], None]]],
        opacity_getter: Callable[[QWidget], float],
        opacity_setter: Callable[[QWidget, float], None],
        top_getter: Callable[[QWidget], bool],
        top_setter: Callable[[QWidget, bool], None],
        color_getter: Callable[[QWidget], str] | None,
        color_setter: Callable[[QWidget, str], None] | None,
        pin_getter: Callable[[QWidget], bool] | None = None,
        pin_setter: Callable[[QWidget, bool], None] | None = None,
        show_pin: bool = True,
        color_label: str = "Color",
    ) -> None:
        """Create a card for controlling one window."""
        card = QFrame(self)
        card.setObjectName("ToolWindowCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        header = QHBoxLayout()
        title_label = BodyLabel(title)
        state_label = BodyLabel("Unknown")
        state_label.setObjectName("ToolWindowState")
        header.addWidget(title_label)
        header.addStretch(1)
        header.addWidget(state_label)
        card_layout.addLayout(header)

        action_row = QHBoxLayout()
        action_row.setSpacing(6)
        action_buttons: list[PushButton] = []
        for tooltip, icon, slot in action_specs:
            button = PushButton(card)
            button.setIcon(icon)
            button.setText(tooltip)
            button.setToolTip(tooltip)
            button.clicked.connect(slot)
            action_row.addWidget(button)
            action_buttons.append(button)
        action_row.addStretch(1)
        card_layout.addLayout(action_row)

        info_label = BodyLabel("")
        info_label.setObjectName("ToolWindowInfo")
        info_label.setWordWrap(True)
        card_layout.addWidget(info_label)

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(BodyLabel("Opacity"))
        opacity_slider = Slider(Qt.Orientation.Horizontal, card)
        opacity_slider.setRange(10, 100)
        opacity_value = BodyLabel("100%")
        opacity_row.addWidget(opacity_slider, 1)
        opacity_row.addWidget(opacity_value)
        card_layout.addLayout(opacity_row)

        toggles_row = QHBoxLayout()
        pin_toggle: CheckBox | None = None
        if show_pin and pin_getter is not None and pin_setter is not None:
            pin_toggle = CheckBox("Pinned")
            pin_toggle.setToolTip("Pinned uses the Qt tool-window flag.")
            toggles_row.addWidget(pin_toggle)
        top_toggle = CheckBox("Always on top")
        toggles_row.addWidget(top_toggle)
        toggles_row.addStretch(1)
        card_layout.addLayout(toggles_row)

        color_preview: BodyLabel | None = None
        color_button: ToolButton | None = None
        if color_getter is not None and color_setter is not None:
            color_row = QHBoxLayout()
            color_preview = BodyLabel("")
            color_button = ToolButton(
                self._mdi_icon("mdi6.palette-outline", self._color_icon("#000000")),
                card,
            )
            color_button.setFixedSize(32, 32)
            color_button.setToolTip("Choose color")
            color_row.addWidget(BodyLabel(color_label))
            color_row.addWidget(color_preview)
            color_row.addWidget(color_button)
            color_row.addStretch(1)
            card_layout.addLayout(color_row)

        parent_layout.addWidget(card)

        self._tool_cards[key] = {
            "getter": window_getter,
            "state_label": state_label,
            "info_label": info_label,
            "opacity_slider": opacity_slider,
            "opacity_value": opacity_value,
            "opacity_getter": opacity_getter,
            "opacity_setter": opacity_setter,
            "top_toggle": top_toggle,
            "top_getter": top_getter,
            "top_setter": top_setter,
            "pin_toggle": pin_toggle,
            "pin_getter": pin_getter,
            "pin_setter": pin_setter,
            "color_preview": color_preview,
            "color_button": color_button,
            "color_getter": color_getter,
            "color_setter": color_setter,
            "action_buttons": action_buttons,
        }

        opacity_slider.valueChanged.connect(
            lambda value, card_key=key: self._set_card_opacity(card_key, value)
        )
        top_toggle.stateChanged.connect(
            lambda _state, card_key=key: self._set_card_topmost(card_key)
        )
        if pin_toggle is not None:
            pin_toggle.stateChanged.connect(
                lambda _state, card_key=key: self._set_card_pinned(card_key)
            )
        if color_button is not None:
            color_button.clicked.connect(
                lambda _checked=False, card_key=key: self._choose_card_color(card_key)
            )

    def _window_geometry_text(self, window: QWidget) -> str:
        """Return readable position/size text for a window."""
        geo = window.geometry()
        return (
            f"State: {'Visible' if window.isVisible() else 'Hidden'}\n"
            f"Position: {geo.x()}, {geo.y()}\n"
            f"Size: {geo.width()} × {geo.height()}"
        )

    def _color_icon(self, color: str) -> QIcon:
        """Build a square color icon preview."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(0, 0, 0, 90))
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(1, 1, 14, 14, 3, 3)
        painter.end()
        return QIcon(pixmap)

    def _mdi_icon(self, name: str, fallback: QIcon) -> QIcon:
        """Return a qtawesome mdi6 icon with a Qt fallback."""
        if qta is None:
            return fallback
        try:
            color = self.palette().color(self.foregroundRole())
            return qta.icon(name, color=QColor(color))
        except Exception:
            return fallback

    def _resolve_tool_window(self, key: str) -> QWidget | None:
        """Resolve the window object for a card key."""
        card = self._tool_cards.get(key)
        getter = None if card is None else card.get("getter")
        if callable(getter):
            window = getter()
            return window if isinstance(window, QWidget) else None
        return None

    def _refresh_tools_cards(self) -> None:
        """Refresh card labels and control values."""
        for key, refs in self._tool_cards.items():
            window = self._resolve_tool_window(key)
            enabled = window is not None
            supports_opacity = enabled and self._supports_opacity_control(key, window)
            state_label = refs["state_label"]
            info_label = refs["info_label"]
            opacity_slider = refs["opacity_slider"]
            opacity_value = refs["opacity_value"]
            top_toggle = refs["top_toggle"]
            pin_toggle = refs["pin_toggle"]
            color_preview = refs["color_preview"]
            color_button = refs["color_button"]
            action_buttons = refs["action_buttons"]

            state_label.setText(
                "Visible" if enabled and window.isVisible() else "Hidden"
            )
            info_text = (
                self._window_geometry_text(window) if enabled else "Window unavailable"
            )
            if enabled and not supports_opacity:
                info_text += (
                    "\nOpacity control is not supported by this Qt platform plugin."
                )
            info_label.setText(info_text)

            for button in action_buttons:
                button.setEnabled(enabled)

            opacity_slider.blockSignals(True)
            opacity_slider.setEnabled(supports_opacity)
            opacity = 1.0
            if enabled and callable(refs["opacity_getter"]):
                opacity = float(refs["opacity_getter"](window))
            opacity_slider.setValue(int(opacity * 100))
            opacity_slider.blockSignals(False)
            opacity_value.setText(
                f"{int(opacity * 100)}%" if supports_opacity else "Unsupported"
            )

            top_toggle.blockSignals(True)
            top_toggle.setEnabled(enabled)
            top_toggle.setChecked(
                bool(
                    enabled
                    and callable(refs["top_getter"])
                    and refs["top_getter"](window)
                )
            )
            top_toggle.blockSignals(False)

            if pin_toggle is not None:
                pin_toggle.blockSignals(True)
                pin_toggle.setEnabled(enabled)
                pin_toggle.setChecked(
                    bool(
                        enabled
                        and callable(refs["pin_getter"])
                        and refs["pin_getter"](window)
                    )
                )
                pin_toggle.blockSignals(False)

            if color_preview is not None and color_button is not None:
                color_button.setEnabled(enabled)
                color = "#000000"
                if enabled and callable(refs["color_getter"]):
                    color = str(refs["color_getter"](window))
                color_preview.setText(color)
                color_button.setIcon(self._color_icon(color))

    def _set_card_opacity(self, key: str, value: int) -> None:
        """Apply the opacity slider value for one card."""
        window = self._resolve_tool_window(key)
        refs = self._tool_cards.get(key)
        if window is None or refs is None:
            return
        if not self._supports_opacity_control(key, window):
            self._refresh_tools_cards()
            return
        setter = refs.get("opacity_setter")
        if callable(setter):
            setter(window, value / 100.0)
        self._refresh_tools_cards()

    def _supports_opacity_control(self, key: str, window: QWidget) -> bool:
        """Return whether opacity control is safe for the given managed window."""
        if key != "main":
            return True
        app = QApplication.instance()
        platform_name = ""
        if app is not None:
            platform_name = app.platformName().lower()
        unsupported_platforms = ("wayland", "offscreen", "minimal")
        if any(name in platform_name for name in unsupported_platforms):
            return False
        return True

    def _set_card_topmost(self, key: str) -> None:
        """Apply the always-on-top toggle for one card."""
        window = self._resolve_tool_window(key)
        refs = self._tool_cards.get(key)
        if window is None or refs is None:
            return
        toggle = refs.get("top_toggle")
        setter = refs.get("top_setter")
        if toggle is not None and callable(setter):
            setter(window, bool(toggle.isChecked()))
        self._refresh_tools_cards()

    def _set_card_pinned(self, key: str) -> None:
        """Apply the pinned toggle for one card."""
        window = self._resolve_tool_window(key)
        refs = self._tool_cards.get(key)
        if window is None or refs is None:
            return
        toggle = refs.get("pin_toggle")
        setter = refs.get("pin_setter")
        if toggle is not None and callable(setter):
            setter(window, bool(toggle.isChecked()))
        self._refresh_tools_cards()

    def _choose_card_color(self, key: str) -> None:
        """Open a color picker for a managed window card."""
        window = self._resolve_tool_window(key)
        refs = self._tool_cards.get(key)
        if window is None or refs is None:
            return
        getter = refs.get("color_getter")
        setter = refs.get("color_setter")
        if not callable(getter) or not callable(setter):
            return
        current = QColor(str(getter(window)))
        color = QColorDialog.getColor(current, self, "Choose Window Color")
        if color.isValid():
            setter(window, color.name())
            refresh = getattr(window, "refresh_from_settings", None)
            if callable(refresh):
                refresh()
            self._refresh_tools_cards()

    def _set_window_always_on_top(self, window: QWidget, enabled: bool) -> None:
        """Toggle the always-on-top flag for a generic top-level window."""
        was_visible = window.isVisible()
        geometry = window.geometry()
        flags = window.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        window.setWindowFlags(flags)
        window.setGeometry(geometry)
        if was_visible:
            window.show()
