"""Builders for individual settings dialog pages."""

from .appearance import build_appearance_page
from .capture import build_capture_page
from .general import build_general_page
from .hotkeys import build_hotkeys_page
from .ocr import build_ocr_page
from .ocr_overrides import build_ocr_overrides_page
from .translation import build_translation_page

__all__ = [
    "build_appearance_page",
    "build_capture_page",
    "build_general_page",
    "build_hotkeys_page",
    "build_ocr_page",
    "build_ocr_overrides_page",
    "build_translation_page",
]
