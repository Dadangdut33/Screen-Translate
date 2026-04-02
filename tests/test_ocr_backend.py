"""Tests for OCR backend."""

from __future__ import annotations

import pytest

from screen_translate.core.ocr.tesseract import TesseractOCRBackend


def test_tesseract_languages_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """detect_languages() should query tesseract and cache the result."""
    import screen_translate.core.ocr.tesseract as tess_mod
    monkeypatch.setattr(tess_mod, "check_tesseract", lambda path: None)

    backend = TesseractOCRBackend()

    # Mock pytesseract.get_languages directly
    import pytesseract
    monkeypatch.setattr(pytesseract, "get_languages", lambda config: ["eng", "jpn", "osd"])

    # We clear the cache to ensure the mock is hit
    from screen_translate.core.ocr.tesseract import _get_installed_languages
    _get_installed_languages.cache_clear()

    langs = backend.detect_languages()
    assert "eng" in langs
    assert "jpn" in langs
    assert "osd" not in langs  # osd should be filtered out
