"""Custom QFluentWidgets style sheets for application windows."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from qfluentwidgets import StyleSheetBase, Theme, qconfig

_QSS_ROOT = Path(__file__).resolve().parent / "qss"


class StyleSheet(StyleSheetBase, Enum):
    """Application-specific style sheet files."""

    MAIN_WINDOW = "main_window"
    SETTINGS_DIALOG = "settings_dialog"
    FLOATING_WINDOW = "floating_window"
    AUXILIARY_WINDOW = "auxiliary_window"

    def path(self, theme: Theme = Theme.AUTO) -> str:
        current_theme = qconfig.theme if theme == Theme.AUTO else theme
        return str(_QSS_ROOT / current_theme.value.lower() / f"{self.value}.qss")
