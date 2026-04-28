"""Appearance settings page."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from PyQt6.QtCore import QMetaObject, QProcess, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QColorDialog, QVBoxLayout, QWidget
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

from screen_translate.ui.widgets import (
    SettingsCardGroup,
    WidgetSettingCard,
    load_qta_icon,
    make_switch_setting_card,
)

from .common import bind_spin

if TYPE_CHECKING:
    from screen_translate.ui.pages.settings_page import SettingsPage

_THEME_OPTIONS: list[str] = ["Dark", "Light"]
logger = logging.getLogger(__name__)


def _is_theme_current(theme: str) -> bool:
    """Return whether the selected theme already matches the live app theme."""
    target_theme = Theme.DARK if theme == "Dark" else Theme.LIGHT
    return qconfig.theme == target_theme


def _is_fusion_style_current(dialog: "SettingsPage") -> bool:
    """Return whether the selected Fusion base-style preference matches the live app."""
    app = QApplication.instance()
    if app is None:
        return True
    expected = bool(dialog.s.get("use_fusion_base_style", False))
    current = app.property("useFusionBaseStyle")
    if current is None:
        return True
    return bool(current) == expected


def _needs_restart(dialog: "SettingsPage", theme: str) -> bool:
    """Return whether the current appearance settings differ from the live app state."""
    return (not _is_theme_current(theme)) or (not _is_fusion_style_current(dialog))


def _update_theme_restart_notice(dialog: "SettingsPage", theme: str) -> None:
    """Show or hide the restart notice for appearance changes."""
    notice = getattr(dialog, "_theme_restart_notice", None)
    if notice is None:
        return
    notice.setVisible(_needs_restart(dialog, theme))


def _restart_application(dialog: "SettingsPage") -> None:
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


def on_theme_changed(dialog: "SettingsPage", theme: str) -> None:
    """Persist the selected theme."""
    dialog.s.set("theme", theme)
    _update_theme_restart_notice(dialog, theme)


def on_fusion_base_style_changed(dialog: "SettingsPage", enabled: bool) -> None:
    """Persist the Fusion base-style preference."""
    dialog.s.set("use_fusion_base_style", enabled)
    theme_combo = getattr(dialog, "_cb_theme", None)
    theme = theme_combo.currentText() if theme_combo is not None else "Dark"
    _update_theme_restart_notice(dialog, theme)


def color_picker_row(dialog: "SettingsPage", key: str) -> PushButton:
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


def build_appearance_page(dialog: "SettingsPage") -> QWidget:
    """Build the Appearance settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)
    vl.setContentsMargins(0, 0, 0, 0)
    vl.setSpacing(20)

    grp_theme = SettingsCardGroup("Theme", w)
    dialog._cb_theme = ComboBox()
    dialog._cb_theme.addItems(_THEME_OPTIONS)
    saved_theme = str(dialog.s.get("theme", "Dark"))
    idx_theme = dialog._cb_theme.findText(saved_theme)
    dialog._cb_theme.setCurrentIndex(max(0, idx_theme))
    dialog._cb_theme.currentTextChanged.connect(
        lambda theme: on_theme_changed(dialog, theme)
    )
    grp_theme.addSettingCards(
        [
            WidgetSettingCard(
                load_qta_icon("mdi6.theme-light-dark"),
                "Theme",
                "Choose between the app's Fluent dark and light themes.",
                dialog._cb_theme,
                grp_theme,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.palette-swatch-outline"),
                title="Set base style to Fusion",
                content="Use Qt's cross-platform Fusion base style under the Fluent theme. Restart required.",
                checked=bool(dialog.s.get("use_fusion_base_style", False)),
                on_changed=lambda checked: on_fusion_base_style_changed(dialog, checked),
                parent=grp_theme,
            ),
        ]
    )
    vl.addWidget(grp_theme)

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
    _update_theme_restart_notice(dialog, dialog._cb_theme.currentText())
    vl.addWidget(dialog._theme_restart_notice)

    grp_query = SettingsCardGroup("Query Window", w)
    grp_query.addSettingCards(
        [
            WidgetSettingCard(
                load_qta_icon("mdi6.format-size"),
                "Font size",
                "Adjust the text size used in the query floating window.",
                bind_spin("tb_ex_q_font_size", dialog.s, 6, 72),
                grp_query,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.format-color-text"),
                "Font color",
                "Choose the query window text color.",
                color_picker_row(dialog, "tb_ex_q_font_color"),
                grp_query,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.palette-outline"),
                "Background color",
                "Choose the query window background color.",
                color_picker_row(dialog, "tb_ex_q_bg_color"),
                grp_query,
            ),
        ]
    )
    vl.addWidget(grp_query)

    grp_result = SettingsCardGroup("Result Window", w)
    grp_result.addSettingCards(
        [
            WidgetSettingCard(
                load_qta_icon("mdi6.format-size"),
                "Font size",
                "Adjust the text size used in the result floating window.",
                bind_spin("tb_ex_res_font_size", dialog.s, 6, 72),
                grp_result,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.format-color-text"),
                "Font color",
                "Choose the result window text color.",
                color_picker_row(dialog, "tb_ex_res_font_color"),
                grp_result,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.palette-outline"),
                "Background color",
                "Choose the result window background color.",
                color_picker_row(dialog, "tb_ex_res_bg_color"),
                grp_result,
            ),
        ]
    )
    vl.addWidget(grp_result)

    grp_mask = SettingsCardGroup("Mask Window", w)
    grp_mask.addSettingCard(
        WidgetSettingCard(
            load_qta_icon("mdi6.blur"),
            "Background color",
            "Choose the overlay color used by the mask window.",
            color_picker_row(dialog, "mask_window_bg_color"),
            grp_mask,
        )
    )
    vl.addWidget(grp_mask)
    vl.addStretch()
    return w
