"""Translation settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import SegmentedWidget

from .translation_sections.argos import build_argos_section, refresh_argos_info, refresh_argos_package_index
from .translation_sections.deepl import build_deepl_section
from .translation_sections.libre import build_libre_section, refresh_libre_local_info
from .translation_sections.proxy import build_proxy_section
from .translation_sections.shared import update_libre_mode_visibility
from .translation_sections.translators import build_translators_section


def build_translation_page(dialog: Any) -> QWidget:
    """Build the Translation settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)
    dialog._translation_sections = SegmentedWidget()
    dialog._translation_stack = QStackedWidget()

    pages = [
        ("translators", "translators", build_translators_section(dialog)),
        ("argos", "Argos", build_argos_section(dialog)),
        ("libre", "LibreTranslate", build_libre_section(dialog)),
        ("deepl", "DeepL", build_deepl_section(dialog)),
        ("proxy", "Proxy", build_proxy_section(dialog)),
    ]

    for route_key, label, page in pages:
        page_layout = page.layout()
        if page_layout is not None:
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(12)
        dialog._translation_stack.addWidget(page)
        dialog._translation_sections.addItem(
            routeKey=route_key,
            text=label,
            onClick=lambda _checked=False, idx=dialog._translation_stack.count() - 1: dialog._translation_stack.setCurrentIndex(idx),
        )

    dialog._translation_sections.setCurrentItem("translators")
    dialog._translation_stack.setCurrentIndex(0)
    vl.addWidget(dialog._translation_sections)
    vl.addWidget(dialog._translation_stack, 1)

    refresh_argos_info(dialog)
    refresh_argos_package_index(dialog)
    refresh_libre_local_info(dialog)
    update_libre_mode_visibility(dialog)

    return w
