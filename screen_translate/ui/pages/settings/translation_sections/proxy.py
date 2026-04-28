"""Translation proxy settings section."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtGui import QFocusEvent
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import CheckBox, PlainTextEdit

if TYPE_CHECKING:
    from screen_translate.ui.pages.settings_page import SettingsPage

from .shared import persist_backend_setting


class _ProxyListEdit(PlainTextEdit):
    """Multi-line proxy editor that persists when editing focus is lost."""

    def __init__(self, dialog: "SettingsPage", key: str, placeholder: str) -> None:
        super().__init__()
        self._dialog = dialog
        self._key = key
        raw = dialog.s.get(key, "")
        if isinstance(raw, list):
            self.setPlainText("\n".join(str(item) for item in raw if str(item).strip()))
        else:
            self.setPlainText(str(raw))
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(72)
        # Fix the vertical size policy — Expanding causes QFormLayout rows to bloat
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def focusOutEvent(self, event: QFocusEvent) -> None:  # type: ignore[override]
        super().focusOutEvent(event)
        persist_backend_setting(self._dialog, self._key, self.toPlainText())


def _make_proxy_editor(
    dialog: "SettingsPage", key: str, placeholder: str
) -> PlainTextEdit:
    editor = _ProxyListEdit(dialog, key, placeholder)
    # PlainTextEdit has Expanding vertical policy by default — override it
    # so QFormLayout rows don't balloon with extra space
    editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return editor


def build_proxy_section(dialog: "SettingsPage") -> QWidget:
    """Build the translation proxy settings section."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    intro = QLabel(
        "Enter one proxy per line. The app will randomly chooses one HTTP and one "
        "HTTPS proxy from the configured lists when proxy settings are built. "
        "NO_PROXY is a bypass list of domains or IPs that should connect directly "
        "without using the proxy."
    )
    intro.setWordWrap(True)
    layout.addWidget(intro)

    grp_proxy, fl_proxy = dialog._group_form("Translation Proxy")

    # Checkbox row — same as fl_libre.addRow(dialog._chk_libre_use_local)
    dialog._chk_translation_proxy = CheckBox("Enable translation proxy")
    dialog._chk_translation_proxy.setChecked(
        bool(dialog.s.get("translation_proxy_enabled", False))
    )
    dialog._chk_translation_proxy.toggled.connect(
        lambda checked: persist_backend_setting(
            dialog, "translation_proxy_enabled", checked
        )
    )
    fl_proxy.addRow(dialog._chk_translation_proxy)

    # All editors in one inner widget — same pattern as dialog._grp_libre_local
    _grp_proxy_fields = QWidget()
    proxy_fields_layout = QVBoxLayout(_grp_proxy_fields)
    proxy_fields_layout.setContentsMargins(0, 0, 0, 0)
    proxy_fields_layout.setSpacing(8)

    proxy_fields_layout.addWidget(QLabel("HTTP proxy:"))
    dialog._proxy_http = _make_proxy_editor(
        dialog,
        "translation_proxy_http",
        "http://127.0.0.1:8080\nhttp://10.0.0.2:8080",
    )
    proxy_fields_layout.addWidget(dialog._proxy_http)

    proxy_fields_layout.addWidget(QLabel("HTTPS proxy:"))
    dialog._proxy_https = _make_proxy_editor(
        dialog,
        "translation_proxy_https",
        "http://127.0.0.1:8080\nhttp://10.0.0.2:8080",
    )
    proxy_fields_layout.addWidget(dialog._proxy_https)

    proxy_fields_layout.addWidget(QLabel("NO_PROXY:"))
    dialog._proxy_no_proxy = _make_proxy_editor(
        dialog,
        "translation_proxy_no_proxy",
        "localhost\n127.0.0.1",
    )
    proxy_fields_layout.addWidget(dialog._proxy_no_proxy)

    fl_proxy.addRow(_grp_proxy_fields)
    layout.addWidget(grp_proxy)
    layout.addStretch()
    return page
