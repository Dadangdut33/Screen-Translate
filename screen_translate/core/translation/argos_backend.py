"""Argos Translate backend - fully offline neural translation."""

from __future__ import annotations

import logging

from .base import TranslationBackend, TranslationError

logger = logging.getLogger(__name__)


class ArgosTranslateBackend(TranslationBackend):
    """Offline neural translation via argostranslate.

    Language packs must be downloaded separately.  If none are installed
    the backend will still load but ``available_languages()`` returns an
    empty list and ``translate()`` raises :class:`TranslationError`.
    """

    @property
    def name(self) -> str:
        """Return backend name."""
        return "Argos Translate (offline)"

    def available_languages(self) -> list[str]:
        """Return unique language codes of installed language packs."""
        try:
            from argostranslate import translate

            installed = translate.get_installed_languages()
            codes = {lang.code for lang in installed}
            return sorted(codes)
        except Exception as exc:
            logger.debug("argostranslate unavailable: %s", exc)
            return []

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Argos Translate (offline).

        Args:
            text: Text to translate.
            source_lang: Source language code.
            target_lang: Target language code.
        """
        try:
            from argostranslate import translate

            installed = translate.get_installed_languages()
            src_obj = next((lang for lang in installed if lang.code == source_lang), None)
            tgt_obj = next((lang for lang in installed if lang.code == target_lang), None)

            if src_obj is None or tgt_obj is None:
                raise TranslationError(
                    f"No installed Argos pack for {source_lang!r} → {target_lang!r}. "
                    "Use the Settings dialog to install language packs."
                )

            translation = src_obj.get_translation(tgt_obj)
            if translation is None:
                raise TranslationError(
                    f"No direct translation pack for {source_lang!r} → {target_lang!r}."
                )
            return str(translation.translate(text))
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc

    @staticmethod
    def install_language_pack(from_lang_code: str, to_lang_code: str) -> None:
        """Download and install an Argos language pack."""
        try:
            from argostranslate import package

            package.update_package_index()
            available = package.get_available_packages()
            pkg = next(
                (p for p in available if p.from_code == from_lang_code and p.to_code == to_lang_code),
                None,
            )
            if pkg is None:
                raise TranslationError(
                    f"No Argos pack found for {from_lang_code!r} → {to_lang_code!r}."
                )
            package.install_from_path(pkg.download())
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


def load_argos_backend() -> ArgosTranslateBackend | None:
    """Return an ArgosTranslateBackend if the package is installed."""
    try:
        import argostranslate  # noqa: F401
        return ArgosTranslateBackend()
    except ImportError:
        logger.debug("argostranslate not installed - offline backend unavailable")
        return None
