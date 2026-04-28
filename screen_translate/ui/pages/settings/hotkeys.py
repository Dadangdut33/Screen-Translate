"""Hotkeys settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from screen_translate.ui.widgets import (
    InfoBannerCard,
    SettingsCardGroup,
    WidgetSettingCard,
    load_qta_icon,
)

from .common import bind_line, bind_spin


def build_hotkeys_page(dialog: Any) -> QWidget:
    """Build the Hotkeys settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)
    vl.setContentsMargins(0, 0, 0, 0)
    vl.setSpacing(20)

    vl.addWidget(
        InfoBannerCard(
            "Global Hotkeys",
            "Global hotkeys depend on the 'keyboard' package and may require extra permissions on Linux. "
            "Leave a shortcut empty to disable it.",
            w,
            icon_name="mdi6.keyboard-outline",
        )
    )

    grp = SettingsCardGroup("Hotkey Bindings", w)
    grp.addSettingCards(
        [
            WidgetSettingCard(
                load_qta_icon("mdi6.content-cut"),
                "Snip & Translate shortcut",
                "Global shortcut used to start snip capture and translation.",
                bind_line("hk_snip_cap", dialog.s, "ctrl+alt+t"),
                grp,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.timer-outline"),
                "Snip delay (ms)",
                "Delay before the snip workflow begins after pressing the shortcut.",
                bind_spin("hk_snip_cap_delay", dialog.s, 0, 5000),
                grp,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.camera-outline"),
                "Capture Window shortcut",
                "Global shortcut used to trigger the capture window workflow.",
                bind_line("hk_cap_window", dialog.s, "e.g. ctrl+alt+c"),
                grp,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.timer-sand"),
                "Capture delay (ms)",
                "Delay before the capture window action runs after the hotkey.",
                bind_spin("hk_cap_window_delay", dialog.s, 0, 5000),
                grp,
            ),
        ]
    )
    vl.addWidget(grp)
    vl.addStretch()
    return w
