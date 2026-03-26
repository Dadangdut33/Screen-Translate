"""Shared UI utility helpers."""

from __future__ import annotations

import importlib.resources
import logging
from pathlib import Path

from PyQt6.QtGui import QIcon

logger = logging.getLogger(__name__)


def load_icon() -> QIcon:
    """Load the application icon from bundled assets.

    Falls back to a null icon if the asset is not found.

    Returns:
        QIcon (may be null if asset unavailable).
    """
    try:
        with importlib.resources.path("screen_translate.assets", "logo.ico") as p:
            return QIcon(str(p))
    except Exception:
        pass
    # Fallback: look relative to __file__
    fallback = Path(__file__).parent.parent / "assets" / "logo.ico"
    if fallback.exists():
        return QIcon(str(fallback))
    return QIcon()
