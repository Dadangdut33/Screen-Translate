"""OCR compatibility tests for the Argos Translate backend."""

from __future__ import annotations

import pytest

from screen_translate.core.ocr.language_compat import (
    build_backend_ocr_compatibility_report,
)
from screen_translate.core.translation.argos_backend import ArgosTranslateBackend
from tests.test_ocr_language_compat_helpers import (
    expected_compatibility,
    get_real_tesseract_languages,
    write_compatibility_report,
)


def test_argos_backend_languages_are_partitioned_against_real_tesseract_languages() -> None:
    """Argos language keys should be compared against installed Tesseract languages."""

    installed_languages = get_real_tesseract_languages()
    backend = ArgosTranslateBackend()
    langs = backend.available_languages()
    if not langs:
        pytest.skip("Argos Translate has no installed language packs in this environment.")

    report = build_backend_ocr_compatibility_report(langs, installed_languages)
    expected_compatible, expected_incompatible = expected_compatibility(
        langs,
        installed_languages,
    )
    write_compatibility_report(backend.name, installed_languages, report)

    assert report["compatible"] == expected_compatible
    assert report["incompatible"] == expected_incompatible
