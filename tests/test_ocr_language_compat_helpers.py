"""Shared helpers for OCR compatibility integration-style tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from screen_translate.core.ocr.base import OCRError
from screen_translate.core.ocr.language_compat import resolve_tesseract_language_code
from screen_translate.core.ocr.tesseract import TesseractOCRBackend


def get_real_tesseract_languages() -> list[str]:
    """Return the real installed Tesseract language codes or skip the test."""
    try:
        backend = TesseractOCRBackend()
    except OCRError as exc:
        pytest.skip(f"Tesseract is not available in this environment: {exc}")
    return backend.detect_languages()


def expected_compatibility(
    languages: list[str],
    installed_languages: list[str],
) -> tuple[dict[str, str], list[str]]:
    """Return expected compatible and incompatible language partitions."""
    compatible = {
        lang: resolved
        for lang in languages
        if (resolved := resolve_tesseract_language_code(lang, installed_languages))
        is not None
    }
    incompatible = [lang for lang in languages if lang not in compatible]
    return compatible, incompatible


def write_compatibility_report(
    backend_name: str,
    installed_languages: list[str],
    report: dict[str, dict[str, str] | list[str]],
) -> Path:
    """Write a JSON compatibility report for a backend and return the output path."""
    report_dir = Path("tests") / "compat_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-z0-9]+", "_", backend_name.lower()).strip("_")
    output_path = report_dir / f"{safe_name}.json"
    payload = {
        "backend": backend_name,
        "installed_tesseract_languages": installed_languages,
        "compatible": report["compatible"],
        "incompatible": report["incompatible"],
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
