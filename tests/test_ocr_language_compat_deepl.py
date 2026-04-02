"""OCR compatibility tests for the DeepL official backend."""

from __future__ import annotations

import os

import pytest

from screen_translate.core.ocr.language_compat import (
    build_backend_ocr_compatibility_report,
)
from screen_translate.core.translation.deepl_official_backend import (
    DeepLOfficialBackend,
)
from tests.test_ocr_language_compat_helpers import (
    expected_compatibility,
    get_real_tesseract_languages,
    write_compatibility_report,
)


def test_deepl_backend_languages_are_partitioned_against_real_tesseract_languages() -> None:
    """DeepL language keys should be compared against installed Tesseract languages."""
    api_key = os.environ.get("DEEPL_API_KEY", "")
    if not api_key:
        pytest.skip("DEEPL_API_KEY is not set for DeepL official integration testing.")

    installed_languages = get_real_tesseract_languages()
    backend = DeepLOfficialBackend(api_key=api_key)
    langs = backend.available_languages()
    if langs == ["auto"] or not langs:
        pytest.skip("DeepL official backend did not return a usable language list.")

    report = build_backend_ocr_compatibility_report(langs, installed_languages)
    expected_compatible, expected_incompatible = expected_compatibility(
        langs,
        installed_languages,
    )
    write_compatibility_report(backend.name, installed_languages, report)

    assert report["compatible"] == expected_compatible
    assert report["incompatible"] == expected_incompatible
