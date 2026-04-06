"""Custom QFluentWidgets style sheets for application windows."""

from __future__ import annotations

import importlib.resources
import sys
from enum import Enum
from pathlib import Path

from qfluentwidgets import StyleSheetBase, Theme, qconfig


def _candidate_qss_roots() -> list[Path]:
    """Return possible QSS roots for source, installed, and frozen runs."""
    roots: list[Path] = []

    # Normal source tree / installed package on disk.
    roots.append(Path(__file__).resolve().parent.parent / "qss")
    roots.append(Path(__file__).resolve().parent / "qss")

    # Package resource path when available as real files on disk.
    try:
        package_root = importlib.resources.files("screen_translate.ui")
        package_qss = package_root.joinpath("qss")
        if isinstance(package_qss, Path):
            roots.append(package_qss)
        else:
            candidate = Path(str(package_qss))
            roots.append(candidate)
    except Exception:
        pass

    # PyInstaller-style frozen app extraction directory.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass) / "screen_translate" / "ui" / "qss")
        roots.append(Path(meipass) / "ui" / "qss")

    # Preserve order while dropping duplicates.
    unique_roots: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root not in seen:
            seen.add(root)
            unique_roots.append(root)
    return unique_roots


def _resolve_qss_path(theme_name: str, sheet_name: str) -> Path:
    """Resolve a style sheet file path across source and bundled layouts."""
    relative = Path(theme_name) / f"{sheet_name}.qss"
    for root in _candidate_qss_roots():
        candidate = root / relative
        if candidate.exists():
            return candidate
    return _candidate_qss_roots()[0] / relative


class StyleSheet(StyleSheetBase, Enum):
    """Application-specific style sheet files."""

    MAIN_WINDOW = "main_window"
    SETTINGS_DIALOG = "settings_dialog"
    FLOATING_WINDOW = "floating_window"
    AUXILIARY_WINDOW = "auxiliary_window"

    def path(self, theme: Theme = Theme.AUTO) -> str:
        current_theme = qconfig.theme if theme == Theme.AUTO else theme
        qss_path = _resolve_qss_path(current_theme.value.lower(), self.value)
        return str(qss_path)
