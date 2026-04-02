"""OCR compatibility tests for translators-library backends."""

from __future__ import annotations
import os

from screen_translate.core.ocr.language_compat import (
    build_backend_ocr_compatibility_report,
)
from screen_translate.core.translation.translators_backend import (
    get_all_translators_backends,
)
from tests.test_ocr_language_compat_helpers import (
    expected_compatibility,
    get_real_tesseract_languages,
    write_compatibility_report,
)


def test_all_translators_backends_are_partitioned_against_real_tesseract_languages() -> (
    None
):
    """Every translators provider returned by the loader should be checked."""

    os.environ["translators_default_region"] = "EN"
    installed_languages = get_real_tesseract_languages()
    backends = get_all_translators_backends()
    if not backends:
        raise AssertionError(
            "No translators backends were loaded from the translators library."
        )

    total = len(backends)
    print(
        f"[compat] detected {len(installed_languages)} Tesseract language(s): "
        f"{', '.join(installed_languages)}",
        flush=True,
    )
    print(f"[compat] checking {total} translators backend(s)", flush=True)

    for index, backend in enumerate(backends, start=1):
        print(f"[compat] ({index}/{total}) loading {backend.name}", flush=True)
        langs = backend.available_languages()
        if not langs:
            print(
                f"[compat] ({index}/{total}) {backend.name}: no languages returned, skipping",
                flush=True,
            )
            continue
        print(
            f"[compat] ({index}/{total}) {backend.name}: {len(langs)} language key(s)",
            flush=True,
        )
        report = build_backend_ocr_compatibility_report(langs, installed_languages)
        expected_compatible, expected_incompatible = expected_compatibility(
            langs,
            installed_languages,
        )
        output_path = write_compatibility_report(
            backend.name,
            installed_languages,
            report,
        )

        print(
            f"[compat] ({index}/{total}) {backend.name}: "
            f"{len(expected_compatible)} compatible, {len(expected_incompatible)} incompatible "
            f"-> {output_path}",
            flush=True,
        )

        assert report["compatible"] == expected_compatible
        assert report["incompatible"] == expected_incompatible
