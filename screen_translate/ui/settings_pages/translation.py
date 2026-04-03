"""Translation settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QFormLayout, QGroupBox, QVBoxLayout, QWidget
from qfluentwidgets import ComboBox, LineEdit

from .common import bind_check, bind_line
from screen_translate.core.translation.translators_backend import (
    configure_translators_region,
)


def update_deepl_visibility(dialog: Any, name: str) -> None:
    """Show DeepL key field only when the official backend is selected."""
    dialog._grp_deepl.setVisible(
        "deepl" in name.lower() and "official" in name.lower()
    )


@pyqtSlot(str)
def on_backend_changed(dialog: Any, name: str) -> None:
    """Switch active backend and update API key visibility."""
    dialog.controller.set_active_backend(name)
    update_deepl_visibility(dialog, name)
    if dialog.controller.main_window:
        dialog.controller.main_window._refresh_lang_combos()


@pyqtSlot(str)
def on_translators_region_changed(dialog: Any, region: str) -> None:
    """Persist and apply the translators region mode immediately."""
    dialog.s.set("translators_region", region)
    configure_translators_region(region)


def build_translation_page(dialog: Any) -> QWidget:
    """Build the Translation settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)

    grp = QGroupBox("Active Backend")
    gfl = QFormLayout(grp)
    dialog._cb_backend = ComboBox()
    for name in dialog.controller.available_backend_names():
        dialog._cb_backend.addItem(name)
    saved = dialog.s.get("engine", "translators-google")
    idx = dialog._cb_backend.findText(saved)
    if idx < 0:
        idx = 0
    dialog._cb_backend.setCurrentIndex(max(0, idx))
    dialog._cb_backend.currentTextChanged.connect(
        lambda name: on_backend_changed(dialog, name)
    )
    gfl.addRow("Backend:", dialog._cb_backend)
    vl.addWidget(grp)

    dialog._grp_deepl = QGroupBox("DeepL Official API Key")
    deepl_fl = QFormLayout(dialog._grp_deepl)
    dialog._deepl_key = LineEdit()
    dialog._deepl_key.setText(str(dialog.s.get("deepl_api_key", "")))
    dialog._deepl_key.setEchoMode(LineEdit.EchoMode.Password)
    dialog._deepl_key.setPlaceholderText("Enter DEEPL_API_KEY…")
    dialog._deepl_key.textChanged.connect(lambda v: dialog.s.set("deepl_api_key", v))
    deepl_fl.addRow("API Key:", dialog._deepl_key)
    vl.addWidget(dialog._grp_deepl)

    grp_libre = QGroupBox("LibreTranslate Server")
    libre_fl = QFormLayout(grp_libre)
    libre_fl.addRow(
        "Host:", bind_line("libre_host", dialog.s, "translate.argosopentech.com")
    )
    libre_fl.addRow("Port:", bind_line("libre_port", dialog.s, "5000 or blank"))
    libre_fl.addRow(bind_check("libre_https", "Use HTTPS", dialog.s))
    libre_fl.addRow("API Key:", bind_line("libre_api_key", dialog.s, "optional"))
    vl.addWidget(grp_libre)

    dialog._cb_translators_region = ComboBox()
    dialog._cb_translators_region.addItems(["EN", "CN", "Auto"])
    saved_region = str(dialog.s.get("translators_region", "EN"))
    idx_region = dialog._cb_translators_region.findText(saved_region)
    dialog._cb_translators_region.setCurrentIndex(max(0, idx_region))
    dialog._cb_translators_region.currentTextChanged.connect(
        lambda region: on_translators_region_changed(dialog, region)
    )
    gfl.addRow("translators region:", dialog._cb_translators_region)

    update_deepl_visibility(dialog, dialog._cb_backend.currentText())
    vl.addStretch()
    return w
