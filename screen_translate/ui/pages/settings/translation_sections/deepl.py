"""DeepL settings section."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .shared import make_reload_line_edit


def build_deepl_section(dialog: Any) -> QWidget:
    """Build the DeepL settings section."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    grp_deepl, fl_deepl = dialog._group_form("DeepL (official library)")
    lbl_deepl = QLabel(
        "These settings only apply to the dedicated DeepL official backend, not the "
        "DeepL entry exposed by the translators library."
    )
    lbl_deepl.setWordWrap(True)
    fl_deepl.addRow(lbl_deepl)
    dialog._deepl_key = make_reload_line_edit(
        dialog,
        "deepl_api_key",
        "Enter DEEPL_API_KEY…",
        password=True,
    )
    fl_deepl.addRow("API Key:", dialog._deepl_key)
    layout.addWidget(grp_deepl)
    layout.addStretch()
    return page

