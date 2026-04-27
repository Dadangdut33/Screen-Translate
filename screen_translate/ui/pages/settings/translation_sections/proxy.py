"""Translation proxy settings section."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from qfluentwidgets import CheckBox

from .shared import make_reload_line_edit, persist_backend_setting


def build_proxy_section(dialog: Any) -> QWidget:
    """Build the translation proxy settings section."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    grp_proxy, fl_proxy = dialog._group_form("Translation Proxy")
    lbl_proxy = QLabel(
        "Proxy settings here apply to network-backed translation backends such as "
        "translators, LibreTranslate, and DeepL (official)."
    )
    lbl_proxy.setWordWrap(True)
    fl_proxy.addRow(lbl_proxy)
    dialog._chk_translation_proxy = CheckBox("Enable translation proxy")
    dialog._chk_translation_proxy.setChecked(
        bool(dialog.s.get("translation_proxy_enabled", False))
    )
    dialog._chk_translation_proxy.toggled.connect(
        lambda checked: persist_backend_setting(dialog, "translation_proxy_enabled", checked)
    )
    fl_proxy.addRow(dialog._chk_translation_proxy)
    dialog._proxy_http = make_reload_line_edit(
        dialog,
        "translation_proxy_http",
        "http://127.0.0.1:8080",
    )
    dialog._proxy_https = make_reload_line_edit(
        dialog,
        "translation_proxy_https",
        "http://127.0.0.1:8080",
    )
    dialog._proxy_no_proxy = make_reload_line_edit(
        dialog,
        "translation_proxy_no_proxy",
        "localhost,127.0.0.1",
    )
    fl_proxy.addRow("HTTP proxy:", dialog._proxy_http)
    fl_proxy.addRow("HTTPS proxy:", dialog._proxy_https)
    fl_proxy.addRow("NO_PROXY:", dialog._proxy_no_proxy)
    layout.addWidget(grp_proxy)
    layout.addStretch()
    return page
