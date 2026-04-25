"""Appearance settings page."""

from __future__ import annotations

import logging
import sys
from typing import Any

from PyQt6.QtCore import QMetaObject, QProcess, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CheckBox,
    ComboBox,
    InfoBar,
    InfoBarIcon,
    InfoBarPosition,
    PushButton,
    Theme,
    qconfig,
)

from .common import bind_spin

_THEME_OPTIONS: list[str] = ["Dark", "Light"]
logger = logging.getLogger(__name__)


def _is_theme_current(theme: str) -> bool:
    """Return whether the selected theme already matches the live app theme."""
    target_theme = Theme.DARK if theme == "Dark" else Theme.LIGHT
    return qconfig.theme == target_theme


def _is_fusion_style_current(dialog: Any) -> bool:
    """Return whether the selected Fusion base-style preference matches the live app."""
    app = QApplication.instance()
    if app is None:
        return True
    expected = bool(dialog.s.get("use_fusion_base_style", False))
    current = app.property("useFusionBaseStyle")
    if current is None:
        return True
    return bool(current) == expected


def _needs_restart(dialog: Any, theme: str) -> bool:
    """Return whether the current appearance settings differ from the live app state."""
    return (not _is_theme_current(theme)) or (not _is_fusion_style_current(dialog))


def _update_theme_restart_notice(dialog: Any, theme: str) -> None:
    """Show or hide the restart notice for appearance changes."""
    notice = getattr(dialog, "_theme_restart_notice", None)
    if notice is None:
        return
    notice.setVisible(_needs_restart(dialog, theme))


def _restart_application(dialog: Any) -> None:
    """Restart the current application process."""
    app = QApplication.instance()
    program = sys.executable
    arguments = sys.argv[:]

    if getattr(sys, "frozen", False):
        arguments = sys.argv[1:]
    else:
        arguments = ["-m", "screen_translate", *sys.argv[1:]]

    started = QProcess.startDetached(program, arguments)
    if started:
        main_window = getattr(getattr(dialog, "controller", None), "main_window", None)
        if main_window is not None and hasattr(main_window, "_quit_app"):
            QMetaObject.invokeMethod(
                main_window,
                "_quit_app",
                Qt.ConnectionType.QueuedConnection,
            )
        elif app is not None:
            app.quit()
        return

    logger.warning(
        "Could not restart application automatically with program=%s args=%s",
        program,
        arguments,
    )


def on_theme_changed(dialog: Any, theme: str) -> None:
    """Persist the selected theme.

    Live theme switching is intentionally disabled because it can crash the
    current Qt/QFluentWidgets widget tree on some systems.
    """
    dialog.s.set("theme", theme)
    _update_theme_restart_notice(dialog, theme)


def on_fusion_base_style_changed(dialog: Any, enabled: bool) -> None:
    """Persist the Fusion base-style preference."""
    dialog.s.set("use_fusion_base_style", enabled)
    theme_combo = getattr(dialog, "_cb_theme", None)
    theme = theme_combo.currentText() if theme_combo is not None else "Dark"
    _update_theme_restart_notice(dialog, theme)


def color_picker_row(dialog: Any, key: str) -> PushButton:
    """Create a colour-picker button tied to a settings key."""
    btn = PushButton()
    btn.setFixedWidth(60)

    def apply_button_color(color: QColor) -> None:
        btn.setProperty("selectedColor", color)
        btn.setStyleSheet(f"background-color: {color.name()};")

    stored = QColor(str(dialog.s.get(key, "#000000")))
    apply_button_color(stored if stored.isValid() else QColor("#000000"))

    def pick() -> None:
        current = btn.property("selectedColor")
        initial = (
            current
            if isinstance(current, QColor) and current.isValid()
            else QColor("#000000")
        )
        col = QColorDialog.getColor(initial, dialog, "Select Colour")
        if col.isValid():
            dialog.s.set(key, col.name())
            apply_button_color(col)

    btn.clicked.connect(pick)
    return btn


def build_appearance_page(dialog: Any) -> QWidget:
    """Build the Appearance settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)

    grp_theme, fl_theme = dialog._group_form("Theme")
    dialog._cb_theme = ComboBox()
    dialog._cb_theme.addItems(_THEME_OPTIONS)
    saved_theme = str(dialog.s.get("theme", "Dark"))
    idx_theme = dialog._cb_theme.findText(saved_theme)
    dialog._cb_theme.setCurrentIndex(max(0, idx_theme))
    dialog._cb_theme.currentTextChanged.connect(
        lambda theme: on_theme_changed(dialog, theme)
    )
    fl_theme.addRow("Theme:", dialog._cb_theme)
    dialog._chk_use_fusion_base_style = CheckBox("Set base style to Fusion")
    dialog._chk_use_fusion_base_style.setChecked(
        bool(dialog.s.get("use_fusion_base_style", False))
    )
    dialog._chk_use_fusion_base_style.toggled.connect(
        lambda checked: on_fusion_base_style_changed(dialog, checked)
    )
    fl_theme.addRow("", dialog._chk_use_fusion_base_style)
    dialog._theme_restart_notice = InfoBar(
        InfoBarIcon.WARNING,
        "Restart Required",
        "Restart the app to apply the selected appearance settings.",
        duration=-1,
        position=InfoBarPosition.NONE,
        parent=w,
        isClosable=False,
    )
    restart_button = PushButton("Restart Now", dialog._theme_restart_notice)
    restart_button.clicked.connect(lambda: _restart_application(dialog))
    dialog._theme_restart_notice.addWidget(restart_button)
    fl_theme.addRow(dialog._theme_restart_notice)
    _update_theme_restart_notice(dialog, dialog._cb_theme.currentText())
    vl.addWidget(grp_theme)

    grp_query, fl_query = dialog._group_form("Query Window")
    fl_query.addRow("Font size:", bind_spin("tb_ex_q_font_size", dialog.s, 6, 72))
    fl_query.addRow("Font color:", color_picker_row(dialog, "tb_ex_q_font_color"))
    fl_query.addRow("Background:", color_picker_row(dialog, "tb_ex_q_bg_color"))
    vl.addWidget(grp_query)

    grp_result, fl_result = dialog._group_form("Result Window")
    fl_result.addRow("Font size:", bind_spin("tb_ex_res_font_size", dialog.s, 6, 72))
    fl_result.addRow("Font color:", color_picker_row(dialog, "tb_ex_res_font_color"))
    fl_result.addRow("Background:", color_picker_row(dialog, "tb_ex_res_bg_color"))
    vl.addWidget(grp_result)

    grp_mask, fl_mask = dialog._group_form("Mask Window")
    fl_mask.addRow(
        "Background color:", color_picker_row(dialog, "mask_window_bg_color")
    )
    vl.addWidget(grp_mask)
    vl.addStretch()
    return w
