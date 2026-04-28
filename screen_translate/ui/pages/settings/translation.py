"""Translation settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import SegmentedWidget

from .translation_sections.argos import (
    apply_argos_info,
    apply_argos_package_index,
    build_argos_section,
    collect_argos_info,
    collect_argos_package_index,
    refresh_argos_info,
    refresh_argos_package_index,
)
from .translation_sections.deepl import build_deepl_section
from .translation_sections.libre import (
    apply_libre_local_info,
    build_libre_section,
    collect_libre_local_info,
    refresh_libre_local_info,
)
from .translation_sections.openrouter import build_openrouter_section
from .translation_sections.proxy import build_proxy_section
from .translation_sections.shared import update_libre_mode_visibility
from .translation_sections.translators import build_translators_section


class _TranslationSectionSignals(QObject):
    """Signals emitted by background translation-settings loaders."""

    finished = pyqtSignal(str, object)
    error = pyqtSignal(str, str)


class _TranslationSectionWorker(QRunnable):
    """Run a translation-settings data collection task off the UI thread."""

    def __init__(self, key: str, fn) -> None:
        super().__init__()
        self.key = key
        self.fn = fn
        self.signals = _TranslationSectionSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:
        try:
            self.signals.finished.emit(self.key, self.fn())
        except Exception as exc:
            self.signals.error.emit(self.key, str(exc))


def _start_translation_section_load(dialog: Any, key: str, fn) -> None:
    """Start a background loader for a heavy translation settings subsection."""
    in_progress = getattr(dialog, "_translation_section_loading", set())
    if key in in_progress:
        return
    in_progress.add(key)
    dialog._translation_section_loading = in_progress
    worker = _TranslationSectionWorker(key, fn)
    worker.signals.finished.connect(lambda section, payload: _on_section_loaded(dialog, section, payload))
    worker.signals.error.connect(lambda section, error: _on_section_error(dialog, section, error))
    dialog.controller._pool.start(worker)


def _on_section_loaded(dialog: Any, key: str, payload: object) -> None:
    """Apply a completed background subsection refresh."""
    getattr(dialog, "_translation_section_loading", set()).discard(key)
    loaded = getattr(dialog, "_translation_section_loaded", set())
    loaded.add(key)
    dialog._translation_section_loaded = loaded
    if key == "argos_info" and isinstance(payload, dict):
        apply_argos_info(dialog, payload)
    elif key == "argos_index" and isinstance(payload, dict):
        apply_argos_package_index(dialog, payload)
    elif key == "libre_info" and isinstance(payload, dict):
        apply_libre_local_info(dialog, payload)


def _on_section_error(dialog: Any, key: str, error: str) -> None:
    """Handle a failed background subsection refresh."""
    getattr(dialog, "_translation_section_loading", set()).discard(key)
    if key == "argos_info":
        dialog._lbl_argos_status.setText("Argos Translate status unavailable")
        dialog._lbl_argos_dir.setText(f"Unavailable: {error}")
        if getattr(dialog, "_lbl_argos_installed_codes", None) is not None:
            dialog._lbl_argos_installed_codes.setText("Unavailable")
    elif key == "argos_index":
        dialog._lbl_argos_index_status.setText(f"Argos package index unavailable: {error}")
    elif key == "libre_info":
        dialog._lbl_libre_local_status.setText("LibreTranslate status unavailable")
        dialog._lbl_libre_local_running.setText(error)


def _ensure_translation_section_loaded(dialog: Any, route_key: str) -> None:
    """Kick off background loads for expensive translation subsections."""
    loaded = getattr(dialog, "_translation_section_loaded", set())
    if route_key == "argos":
        if "argos_info" not in loaded:
            _start_translation_section_load(dialog, "argos_info", lambda: collect_argos_info(dialog))
        if "argos_index" not in loaded:
            _start_translation_section_load(
                dialog,
                "argos_index",
                lambda: collect_argos_package_index(dialog),
            )
    elif route_key == "libre" and "libre_info" not in loaded:
        _start_translation_section_load(dialog, "libre_info", lambda: collect_libre_local_info(dialog))


def _on_translation_section_changed(dialog: Any, route_key: str, index: int) -> None:
    """Switch the stacked page and trigger any needed lazy background loads."""
    dialog._translation_stack.setCurrentIndex(index)
    _ensure_translation_section_loaded(dialog, route_key)


def build_translation_page(dialog: Any) -> QWidget:
    """Build the Translation settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)
    dialog._translation_sections = SegmentedWidget()
    dialog._translation_stack = QStackedWidget()
    dialog._translation_section_loaded = set()
    dialog._translation_section_loading = set()

    pages = [
        ("translators", "translators", build_translators_section(dialog)),
        ("argos", "Argos", build_argos_section(dialog)),
        ("libre", "LibreTranslate", build_libre_section(dialog)),
        ("openrouter", "OpenRouter", build_openrouter_section(dialog)),
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
            onClick=lambda _checked=False, rk=route_key, idx=dialog._translation_stack.count() - 1: _on_translation_section_changed(dialog, rk, idx),
        )

    dialog._translation_sections.setCurrentItem("translators")
    dialog._translation_stack.setCurrentIndex(0)
    vl.addWidget(dialog._translation_sections)
    vl.addWidget(dialog._translation_stack, 1)

    update_libre_mode_visibility(dialog)

    return w
