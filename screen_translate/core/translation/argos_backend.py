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

    .. note::
        This backend is only available when the *argos* optional dependency
        group is installed::

            pip install "screen-translate[argos]"
    """

    @property
    def name(self) -> str:
        """Return backend name."""
        return "Argos Translate (offline)"

    def available_languages(self) -> list[str]:
        """Return display names of installed language pairs.

        Returns:
            Sorted list of ``"Source → Target"`` pair strings, or an empty
            list when no packs are installed.
        """
        try:
            from argostranslate import package

            langs: list[str] = []
            for pkg in package.get_installed_packages():
                langs.append(f"{pkg.from_name} → {pkg.to_name}")
            return sorted(langs)
        except Exception as exc:
            logger.debug("argostranslate unavailable: %s", exc)
            return []

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Argos Translate (offline).

        Args:
            text: Text to translate.
            source_lang: Source language name (e.g. ``"English"``).
            target_lang: Target language name (e.g. ``"Japanese"``).

        Returns:
            Translated text.

        Raises:
            TranslationError: If translation fails or no matching pack is
                installed.
        """
        try:
            from argostranslate import translate

            installed = translate.get_installed_languages()
            src_obj = next((lang for lang in installed if lang.name == source_lang), None)
            tgt_obj = next((lang for lang in installed if lang.name == target_lang), None)

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
    def install_language_pack(from_lang: str, to_lang: str) -> None:
        """Download and install an Argos language pack.

        Args:
            from_lang: Source language name (e.g. ``"English"``).
            to_lang: Target language name (e.g. ``"Japanese"``).

        Raises:
            TranslationError: If the pack cannot be found or installed.
        """
        try:
            from argostranslate import package

            package.update_package_index()
            available = package.get_available_packages()
            pkg = next(
                (p for p in available if p.from_name == from_lang and p.to_name == to_lang),
                None,
            )
            if pkg is None:
                raise TranslationError(
                    f"No Argos pack found for {from_lang!r} → {to_lang!r}."
                )
            package.install_from_path(pkg.download())
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


def load_argos_backend() -> ArgosTranslateBackend | None:
    """Return an ArgosTranslateBackend if the package is installed.

    Returns:
        Backend instance, or *None* if argostranslate is not installed.
    """
    try:
        import argostranslate  # noqa: F401

        return ArgosTranslateBackend()
    except ImportError:
        logger.debug("argostranslate not installed - offline backend unavailable")
        return None
