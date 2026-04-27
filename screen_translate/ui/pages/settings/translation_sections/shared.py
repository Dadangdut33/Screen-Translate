"""Shared helpers for translation settings sections."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qfluentwidgets import ComboBox, LineEdit

from screen_translate.core.translation.argos_backend import (
    argos_package_dir_from_setting,
    default_argos_package_dir,
)
from screen_translate.core.translation.libretranslate_local import (
    default_local_libretranslate_dir,
    local_libretranslate_dir_from_setting,
)
from screen_translate.core.translation.translators_backend import (
    configure_translators_region,
)


def format_bytes(size_bytes: int) -> str:
    """Format bytes in a human-readable unit."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024.0
    return f"{size_bytes} B"


def refresh_translation_runtime(dialog: Any) -> None:
    """Reload translation backends and refresh the main-window comboboxes."""
    dialog.controller.reload_translation_backends()
    main_window = getattr(dialog.controller, "main_window", None)
    if main_window is not None and hasattr(main_window, "_restore_state"):
        main_window._restore_state()


def persist_backend_setting(dialog: Any, key: str, value: Any) -> None:
    """Persist a backend-related setting and refresh runtime state."""
    dialog.s.set(key, value)
    refresh_translation_runtime(dialog)


def on_translators_region_changed(dialog: Any, region: str) -> None:
    """Persist and apply the translators region mode immediately."""
    dialog.s.set("translators_region", region)
    configure_translators_region(region)
    refresh_translation_runtime(dialog)


def libre_install_dir(dialog: Any) -> Path:
    """Return normalized managed LibreTranslate install directory."""
    raw = str(dialog.s.get("libre_local_dir", "")).strip()
    if not raw:
        raw = str(default_local_libretranslate_dir())
    return local_libretranslate_dir_from_setting(raw)


def argos_install_dir(dialog: Any) -> Path:
    """Return normalized Argos package directory."""
    raw = str(dialog.s.get("argos_package_dir", "")).strip()
    if not raw:
        raw = str(default_argos_package_dir())
    return argos_package_dir_from_setting(raw)


def libre_package_dir(dialog: Any) -> Path:
    """Return normalized local LibreTranslate model/package directory."""
    raw = str(dialog.s.get("libre_local_package_dir", "")).strip()
    if raw:
        return argos_package_dir_from_setting(raw)
    return argos_install_dir(dialog)


def update_libre_mode_visibility(dialog: Any) -> None:
    """Show either local-install controls or remote-endpoint controls."""
    use_local = bool(dialog.s.get("libre_use_local", False))
    if getattr(dialog, "_grp_libre_local", None) is not None:
        dialog._grp_libre_local.setVisible(use_local)
    if getattr(dialog, "_grp_libre_remote", None) is not None:
        dialog._grp_libre_remote.setVisible(not use_local)


def make_reload_line_edit(
    dialog: Any,
    key: str,
    placeholder: str = "",
    *,
    password: bool = False,
) -> LineEdit:
    """Create a line edit that saves on editing-finished and reloads backends."""
    line_edit = LineEdit()
    line_edit.setText(str(dialog.s.get(key, "")))
    line_edit.setPlaceholderText(placeholder)
    if password:
        line_edit.setEchoMode(LineEdit.EchoMode.Password)

    def save_and_reload() -> None:
        dialog.s.set(key, line_edit.text())
        refresh_translation_runtime(dialog)

    line_edit.editingFinished.connect(save_and_reload)
    return line_edit


def make_passthrough_line_edit(
    dialog: Any,
    key: str,
    placeholder: str = "",
) -> LineEdit:
    """Create a line edit that only persists its own setting."""
    line_edit = LineEdit()
    line_edit.setText(str(dialog.s.get(key, "")))
    line_edit.setPlaceholderText(placeholder)
    line_edit.editingFinished.connect(lambda: dialog.s.set(key, line_edit.text()))
    return line_edit


def build_translators_region_combo(dialog: Any) -> ComboBox:
    """Build the region selector for translators library."""
    combo = ComboBox()
    combo.addItems(["EN", "CN", "Auto"])
    saved_region = str(dialog.s.get("translators_region", "EN"))
    idx_region = combo.findText(saved_region)
    combo.setCurrentIndex(max(0, idx_region))
    combo.currentTextChanged.connect(lambda region: on_translators_region_changed(dialog, region))
    return combo
