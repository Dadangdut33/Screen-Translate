"""Helpers for mapping translation language codes to OCR compatibility."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from screen_translate.core.ocr.base import OCRBackend
    from screen_translate.core.translation.base import TranslationBackend

_TESSERACT_LANGUAGE_ALIASES: dict[str, str] = {
    "ar": "ara",
    "de": "deu",
    "en": "eng",
    "es": "spa",
    "fr": "fra",
    "hi": "hin",
    "id": "ind",
    "it": "ita",
    "ja": "jpn",
    "ko": "kor",
    "pt": "por",
    "ru": "rus",
    "zh": "chi_sim",
    "zh-CN": "chi_sim",
    "zh-TW": "chi_tra",
}


def tesseract_language_aliases() -> dict[str, str]:
    """Return the supported translation-code to Tesseract-code aliases."""
    return dict(_TESSERACT_LANGUAGE_ALIASES)


def resolve_tesseract_language_code(
    selected_lang: str,
    installed_languages: list[str],
    overrides: dict[str, str] | None = None,
) -> str | None:
    """Resolve a selected translation language to an installed Tesseract code."""
    if not installed_languages:
        return None

    normalized = selected_lang.strip()
    normalized_overrides = {
        key.strip(): value.strip()
        for key, value in (overrides or {}).items()
        if key and value
    }

    if normalized in installed_languages:
        return normalized

    lowered_installed = {lang.lower(): lang for lang in installed_languages}
    direct_match = lowered_installed.get(normalized.lower())
    if direct_match is not None:
        return direct_match

    override_match = normalized_overrides.get(normalized) or normalized_overrides.get(
        normalized.lower()
    )
    if override_match:
        override_direct = lowered_installed.get(override_match.lower())
        if override_direct is not None:
            return override_direct

    alias_keys = [normalized, normalized.lower()]
    if "-" in normalized or "_" in normalized:
        base_part = normalized.replace("_", "-").split("-", 1)[0]
        alias_keys.extend([base_part, base_part.lower()])

    for key in alias_keys:
        mapped = _TESSERACT_LANGUAGE_ALIASES.get(key)
        if mapped and mapped in installed_languages:
            return mapped

    if normalized.lower() == "auto":
        if "eng" in installed_languages:
            return "eng"
        return installed_languages[0] if installed_languages else None

    return None


def is_tesseract_language_compatible(
    selected_lang: str,
    installed_languages: list[str],
    overrides: dict[str, str] | None = None,
) -> bool:
    """Return True when the selected translation language can be OCRed by Tesseract."""
    return (
        resolve_tesseract_language_code(
            selected_lang,
            installed_languages,
            overrides=overrides,
        )
        is not None
    )


def partition_languages_by_tesseract_compatibility(
    translator_languages: list[str],
    installed_languages: list[str],
    overrides: dict[str, str] | None = None,
) -> tuple[list[str], list[str]]:
    """Split translation language codes into Tesseract-compatible and incompatible lists."""
    compatible: list[str] = []
    incompatible: list[str] = []
    for lang in translator_languages:
        if is_tesseract_language_compatible(
            lang,
            installed_languages,
            overrides=overrides,
        ):
            compatible.append(lang)
        else:
            incompatible.append(lang)
    return compatible, incompatible


def build_backend_ocr_compatibility_report(
    translation_languages: list[str],
    installed_languages: list[str],
    overrides: dict[str, str] | None = None,
) -> dict[str, dict[str, str] | list[str]]:
    """Build a compatibility report for translation language keys against Tesseract."""
    compatible: dict[str, str] = {}
    incompatible: list[str] = []

    for lang in translation_languages:
        resolved = resolve_tesseract_language_code(
            lang,
            installed_languages,
            overrides=overrides,
        )
        if resolved is None:
            incompatible.append(lang)
        else:
            compatible[lang] = resolved

    return {
        "compatible": compatible,
        "incompatible": incompatible,
    }


def build_translation_backends_ocr_compatibility_report(
    backends: list["TranslationBackend"],
    ocr_backend: "OCRBackend",
    backend_overrides: dict[str, dict[str, str]] | None = None,
) -> dict[str, dict[str, dict[str, str] | list[str]]]:
    """Build a compatibility report for every translation backend against an OCR backend."""
    installed_languages = ocr_backend.detect_languages()
    report: dict[str, dict[str, dict[str, str] | list[str]]] = {}

    for backend in backends:
        report[backend.name] = build_backend_ocr_compatibility_report(
            backend.available_languages(),
            installed_languages,
            overrides=(backend_overrides or {}).get(backend.name, {}),
        )

    return report
