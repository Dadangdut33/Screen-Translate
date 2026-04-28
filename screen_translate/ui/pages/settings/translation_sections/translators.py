"""translators library settings section."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .shared import build_translators_region_combo

if TYPE_CHECKING:
    from screen_translate.ui.pages.settings_page import SettingsPage


def build_translators_section(dialog: "SettingsPage") -> QWidget:
    """Build the translators-library settings section."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    grp_translators, fl_translators = dialog._group_form("translators Library")
    lbl_translators = QLabel(
        "Settings in this section apply to the web-backed providers exposed by the "
        "third-party translators library."
    )
    lbl_translators.setWordWrap(True)
    fl_translators.addRow(lbl_translators)
    dialog._cb_translators_region = build_translators_region_combo(dialog)
    fl_translators.addRow("Region mode:", dialog._cb_translators_region)
    layout.addWidget(grp_translators)
    layout.addStretch()
    return page
