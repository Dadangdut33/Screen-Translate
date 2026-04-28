"""Capture settings page."""

from __future__ import annotations

import sys
from typing import Any

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from screen_translate.ui.widgets import (
    SettingsCardGroup,
    WidgetSettingCard,
    load_qta_icon,
    make_switch_setting_card,
)

from .common import bind_combo, bind_combo_with_callback


def refresh_capture_window_ui(dialog: Any) -> None:
    """Apply capture-mode UI changes immediately to the capture window."""
    if dialog.controller.capture_window:
        dialog.controller.capture_window._sync_mode_ui()


def build_capture_page(dialog: Any) -> QWidget:
    """Build the Capture settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)
    vl.setContentsMargins(0, 0, 0, 0)
    vl.setSpacing(20)

    grp_mode = SettingsCardGroup("Capture Backend", w)
    grp_mode.addSettingCard(
        WidgetSettingCard(
            load_qta_icon("mdi6.monitor-screenshot"),
            "Capture mode for capture window",
            "Choose whether the capture window uses a floating tool or a virtual overlay.",
            bind_combo_with_callback(
                "capture_mode",
                ["Floating Window", "Virtual Overlay"],
                dialog.s,
                lambda: refresh_capture_window_ui(dialog),
            ),
            grp_mode,
        )
    )
    if sys.platform.startswith("linux"):
        grp_mode.addSettingCard(
            WidgetSettingCard(
                load_qta_icon("mdi6.linux"),
                "Capture backend",
                "Select which Linux capture tool integration should be used.",
                bind_combo(
                    "capture_backend",
                    ["Auto", "Spectacle", "GNOME Shell", "grim"],
                    dialog.s,
                ),
                grp_mode,
            )
        )
    grp_mode.addSettingCards(
        [
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.content-save-outline"),
                title="Save captured images to disk",
                content="Keep raw capture images in the saved capture directory.",
                checked=bool(dialog.s.get("keep_image", False)),
                on_changed=lambda value: dialog.s.set("keep_image", value),
                parent=grp_mode,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.crop"),
                title="Also save the final cropped capture",
                content="Store the image after crop/selection as an additional file.",
                checked=bool(dialog.s.get("save_cropped_image", False)),
                on_changed=lambda value: dialog.s.set("save_cropped_image", value),
                parent=grp_mode,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.alert-circle-outline"),
                title="Suppress missing-file errors",
                content="Hide errors from external capture tools when no image file is returned.",
                checked=bool(
                    dialog.s.get("suppress_missing_capture_file_errors", False)
                ),
                on_changed=lambda value: dialog.s.set(
                    "suppress_missing_capture_file_errors", value
                ),
                parent=grp_mode,
            ),
        ]
    )
    vl.addWidget(grp_mode)

    grp_visibility = SettingsCardGroup("Window Visibility", w)
    grp_visibility.addSettingCards(
        [
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.monitor-off"),
                title="Hide main window during capture",
                content="Temporarily hide the main window while capturing.",
                checked=bool(dialog.s.get("hide_mw_on_cap", False)),
                on_changed=lambda value: dialog.s.set("hide_mw_on_cap", value),
                parent=grp_visibility,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.form-textbox-password"),
                title="Hide query window during capture",
                content="Hide the OCR query floating window while capturing.",
                checked=bool(dialog.s.get("hide_ex_qw_on_cap", False)),
                on_changed=lambda value: dialog.s.set("hide_ex_qw_on_cap", value),
                parent=grp_visibility,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.message-text-outline"),
                title="Hide result window during capture",
                content="Hide the translation result floating window while capturing.",
                checked=bool(dialog.s.get("hide_ex_resw_on_cap", False)),
                on_changed=lambda value: dialog.s.set("hide_ex_resw_on_cap", value),
                parent=grp_visibility,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.eye-outline"),
                title="Show query window after capture",
                content="Reopen the query floating window after a capture completes.",
                checked=bool(dialog.s.get("show_query_window_after_capture", False)),
                on_changed=lambda value: dialog.s.set(
                    "show_query_window_after_capture", value
                ),
                parent=grp_visibility,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.eye-plus-outline"),
                title="Show result window after capture",
                content="Reopen the result floating window after a capture completes.",
                checked=bool(dialog.s.get("show_result_window_after_capture", False)),
                on_changed=lambda value: dialog.s.set(
                    "show_result_window_after_capture", value
                ),
                parent=grp_visibility,
            ),
        ]
    )
    vl.addWidget(grp_visibility)
    vl.addStretch()
    return w
