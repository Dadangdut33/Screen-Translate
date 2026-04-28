"""Shared helpers for translation settings sections."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from qfluentwidgets import ComboBox, LineEdit, MessageBox

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

if TYPE_CHECKING:
    from screen_translate.ui.pages.settings_page import SettingsPage


class WindowLike(Protocol):
    """Minimal parent interface needed for confirmation dialogs."""

    def window(self) -> object: ...


def format_bytes(size_bytes: int) -> str:
    """Format bytes in a human-readable unit."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024.0
    return f"{size_bytes} B"


def normalize_path(path: str | Path) -> Path:
    """Return a normalized absolute path."""
    return Path(path).expanduser().resolve()


def paths_equivalent(left: str | Path, right: str | Path) -> bool:
    """Return True when two paths refer to the same normalized location."""
    return normalize_path(left) == normalize_path(right)


def directory_has_content(path: str | Path) -> bool:
    """Return True when a directory exists and contains at least one entry."""
    target = Path(path).expanduser()
    if not target.exists() or not target.is_dir():
        return False
    try:
        next(target.iterdir())
    except StopIteration:
        return False
    except OSError:
        return False
    return True


def confirm_directory_move(
    parent: WindowLike | object,
    *,
    title: str,
    subject: str,
    source: str | Path,
    destination: str | Path,
) -> bool:
    """Ask the user to confirm a directory migration."""
    source_path = normalize_path(source)
    destination_path = normalize_path(destination)
    box = MessageBox(
        title,
        (
            f"{subject} will be moved to the new directory.\n\n"
            f"From:\n{source_path}\n\n"
            f"To:\n{destination_path}\n\n"
            "If the destination already contains same-named files or folders, "
            "they will be replaced."
        ),
        parent.window() if hasattr(parent, "window") else parent,
    )
    box.yesButton.setText("Move")
    box.cancelButton.setText("Cancel")
    return bool(box.exec())


def move_directory_contents(source: str | Path, destination: str | Path) -> int:
    """Move all content from one directory to another, merging folders."""
    source_path = normalize_path(source)
    destination_path = normalize_path(destination)

    if source_path == destination_path:
        return 0
    if source_path in destination_path.parents:
        raise ValueError("Destination directory cannot be inside the source directory.")
    if destination_path in source_path.parents:
        raise ValueError("Source directory cannot be inside the destination directory.")

    if not source_path.exists():
        destination_path.mkdir(parents=True, exist_ok=True)
        return 0

    destination_path.mkdir(parents=True, exist_ok=True)
    moved = 0
    for child in list(source_path.iterdir()):
        target = destination_path / child.name
        if target.exists():
            if child.is_dir() and target.is_dir():
                moved += move_directory_contents(child, target)
                try:
                    child.rmdir()
                except OSError:
                    pass
                continue
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(child), str(target))
        moved += 1

    try:
        source_path.rmdir()
    except OSError:
        pass
    return moved


def refresh_translation_runtime(dialog: "SettingsPage") -> None:
    """Reload translation backends and refresh the main-window comboboxes."""
    dialog.controller.reload_translation_backends()
    main_window = getattr(dialog.controller, "main_window", None)
    if main_window is not None and hasattr(main_window, "_restore_state"):
        main_window._restore_state()


def persist_backend_setting(
    dialog: "SettingsPage", key: str, value: object
) -> None:
    """Persist a backend-related setting and refresh runtime state."""
    dialog.s.set(key, value)
    refresh_translation_runtime(dialog)


def on_translators_region_changed(dialog: "SettingsPage", region: str) -> None:
    """Persist and apply the translators region mode immediately."""
    dialog.s.set("translators_region", region)
    configure_translators_region(region)
    refresh_translation_runtime(dialog)


def libre_install_dir(dialog: "SettingsPage") -> Path:
    """Return normalized managed LibreTranslate install directory."""
    raw = str(dialog.s.get("libre_local_dir", "")).strip()
    if not raw:
        raw = str(default_local_libretranslate_dir())
    return local_libretranslate_dir_from_setting(raw)


def argos_install_dir(dialog: "SettingsPage") -> Path:
    """Return normalized Argos package directory."""
    raw = str(dialog.s.get("argos_package_dir", "")).strip()
    if not raw:
        raw = str(default_argos_package_dir())
    return argos_package_dir_from_setting(raw)


def libre_package_dir(dialog: "SettingsPage") -> Path:
    """Return normalized local LibreTranslate model/package directory."""
    raw = str(dialog.s.get("libre_local_package_dir", "")).strip()
    if raw:
        return argos_package_dir_from_setting(raw)
    return argos_install_dir(dialog)


def update_libre_mode_visibility(dialog: "SettingsPage") -> None:
    """Show either local-install controls or remote-endpoint controls."""
    use_local = bool(dialog.s.get("libre_use_local", False))
    if getattr(dialog, "_grp_libre_local", None) is not None:
        dialog._grp_libre_local.setVisible(use_local)
    if getattr(dialog, "_grp_libre_remote", None) is not None:
        dialog._grp_libre_remote.setVisible(not use_local)


def make_reload_line_edit(
    dialog: "SettingsPage",
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
    dialog: "SettingsPage",
    key: str,
    placeholder: str = "",
) -> LineEdit:
    """Create a line edit that only persists its own setting."""
    line_edit = LineEdit()
    line_edit.setText(str(dialog.s.get(key, "")))
    line_edit.setPlaceholderText(placeholder)
    line_edit.editingFinished.connect(lambda: dialog.s.set(key, line_edit.text()))
    return line_edit


def build_translators_region_combo(dialog: "SettingsPage") -> ComboBox:
    """Build the region selector for translators library."""
    combo = ComboBox()
    combo.addItems(["EN", "CN", "Auto"])
    saved_region = str(dialog.s.get("translators_region", "EN"))
    idx_region = combo.findText(saved_region)
    combo.setCurrentIndex(max(0, idx_region))
    combo.currentTextChanged.connect(lambda region: on_translators_region_changed(dialog, region))
    return combo
