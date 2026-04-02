"""Hotkeys settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .common import bind_line, bind_spin


def build_hotkeys_page(dialog: Any) -> QWidget:
    """Build the Hotkeys settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)
    grp, fl = dialog._group_form("Global Hotkeys")
    fl.addRow(
        QLabel(
            "Hotkeys require the 'keyboard' package and may need root on Linux.\n"
            "Leave blank to disable."
        )
    )
    fl.addRow("Snip & Translate:", bind_line("hk_snip_cap", dialog.s, "ctrl+alt+t"))
    fl.addRow("Snip delay (ms):", bind_spin("hk_snip_cap_delay", dialog.s, 0, 5000))
    fl.addRow("Capture Window:", bind_line("hk_cap_window", dialog.s, "e.g. ctrl+alt+c"))
    fl.addRow(
        "Capture delay (ms):", bind_spin("hk_cap_window_delay", dialog.s, 0, 5000)
    )
    vl.addWidget(grp)
    vl.addStretch()
    return w
