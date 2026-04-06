"""Shared UI utility helpers."""

from __future__ import annotations

import importlib.resources
import logging
import sys
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
        asset = importlib.resources.files("screen_translate.assets").joinpath("logo.ico")
        with importlib.resources.as_file(asset) as path:
            if path.exists():
                return QIcon(str(path))
    except Exception:
        pass

    candidates = [
        Path(__file__).resolve().parents[2] / "assets" / "logo.ico",
        Path(__file__).resolve().parents[3] / "assets" / "logo.ico",
    ]

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.extend(
            [
                Path(meipass) / "screen_translate" / "assets" / "logo.ico",
                Path(meipass) / "assets" / "logo.ico",
            ]
        )

    for fallback in candidates:
        if fallback.exists():
            return QIcon(str(fallback))
    return QIcon()
