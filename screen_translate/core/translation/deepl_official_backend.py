"""Official DeepL translation backend (requires DEEPL_API_KEY)."""

from __future__ import annotations

import logging
import os

from .base import TranslationBackend, TranslationError

logger = logging.getLogger(__name__)

_SOURCE_LANGS: list[str] = [
    "Auto", "Bulgarian", "Chinese Simplified", "Czech", "Danish", "Dutch",
    "English", "Estonian", "Finnish", "French", "German", "Greek",
    "Hungarian", "Indonesian", "Italian", "Japanese", "Korean", "Latvian",
    "Lithuanian", "Norwegian", "Polish", "Portuguese", "Romanian", "Russian",
    "Slovak", "Slovenian", "Spanish", "Swedish", "Turkish", "Ukrainian",
]

_TARGET_LANGS: list[str] = [lang for lang in _SOURCE_LANGS if lang != "Auto"]

# deepl code → display name
_CODE_TO_NAME: dict[str, str] = {
    "BG": "Bulgarian", "ZH": "Chinese Simplified", "CS": "Czech", "DA": "Danish",
    "NL": "Dutch", "EN-GB": "English (British)", "EN-US": "English (US)",
    "EN": "English", "ET": "Estonian", "FI": "Finnish", "FR": "French",
    "DE": "German", "EL": "Greek", "HU": "Hungarian", "ID": "Indonesian",
    "IT": "Italian", "JA": "Japanese", "KO": "Korean", "LV": "Latvian",
    "LT": "Lithuanian", "NB": "Norwegian", "PL": "Polish", "PT": "Portuguese",
    "PT-BR": "Portuguese (Brazilian)", "RO": "Romanian", "RU": "Russian",
    "SK": "Slovak", "SL": "Slovenian", "ES": "Spanish", "SV": "Swedish",
    "TR": "Turkish", "UK": "Ukrainian",
}

_NAME_TO_CODE: dict[str, str] = {
    "Bulgarian": "BG", "Chinese Simplified": "ZH", "Czech": "CS", "Danish": "DA",
    "Dutch": "NL", "English": "EN", "Estonian": "ET", "Finnish": "FI",
    "French": "FR", "German": "DE", "Greek": "EL", "Hungarian": "HU",
    "Indonesian": "ID", "Italian": "IT", "Japanese": "JA", "Korean": "KO",
    "Latvian": "LV", "Lithuanian": "LT", "Norwegian": "NB", "Polish": "PL",
    "Portuguese": "PT", "Romanian": "RO", "Russian": "RU", "Slovak": "SK",
    "Slovenian": "SL", "Spanish": "ES", "Swedish": "SV", "Turkish": "TR",
    "Ukrainian": "UK",
}


class DeepLOfficialBackend(TranslationBackend):
    """Official DeepL API backend via the ``deepl-python`` package.

    Requires the ``DEEPL_API_KEY`` environment variable **or** an API key
    supplied at initialisation.  When neither is set, this backend will not
    be added to the available backend list.

    This backend is only available when the *deepl* optional dependency
    group is installed::

        pip install "screen-translate[deepl]"
    """

    @property
    def requires_api_key(self) -> bool:
        """Return True - DeepL official always needs an API key."""
        return True

    def __init__(self, api_key: str = "") -> None:
        """Initialise the backend with an API key.

        Args:
            api_key: DeepL API authentication key.  Falls back to the
                ``DEEPL_API_KEY`` environment variable if empty.

        Raises:
            TranslationError: If the *deepl* package is not installed or
                the API key is missing.
        """
        try:
            import deepl  # noqa: F401
        except ImportError as exc:
            raise TranslationError(
                "deepl package is not installed. Run: pip install 'screen-translate[deepl]'"
            ) from exc

        resolved_key = api_key or os.environ.get("DEEPL_API_KEY", "")
        if not resolved_key:
            raise TranslationError(
                "DeepL API key is required.\n"
                "Set the DEEPL_API_KEY environment variable or enter your key in Settings."
            )
        self._api_key = resolved_key
        logger.debug("DeepLOfficialBackend initialised")

    @property
    def name(self) -> str:
        """Return backend name."""
        return "DeepL (official)"

    def available_languages(self) -> list[str]:
        """Return display names of languages supported by the official DeepL API.

        Returns:
            Sorted list of language display names.
        """
        return sorted(_TARGET_LANGS)

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using the official DeepL API.

        Args:
            text: Text to translate.
            source_lang: Source language display name (or 'Auto').
            target_lang: Target language display name.

        Returns:
            Translated text.

        Raises:
            TranslationError: On API error or unsupported language pair.
        """
        try:
            import deepl

            translator = deepl.Translator(self._api_key)
            src_code: str | None = None if source_lang == "Auto" else _NAME_TO_CODE.get(source_lang)
            tgt_code = _NAME_TO_CODE.get(target_lang)
            if tgt_code is None:
                raise TranslationError(f"Unsupported target language: {target_lang!r}")

            result = translator.translate_text(text.strip(), source_lang=src_code, target_lang=tgt_code)
            return str(result)
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


def load_deepl_official_backend(api_key: str = "") -> DeepLOfficialBackend | None:
    """Return a DeepL official backend if the package is installed and an API key is set.

    Args:
        api_key: DeepL API key (also checked via environment variable).

    Returns:
        Backend instance, or *None* if unavailable.
    """
    try:
        return DeepLOfficialBackend(api_key=api_key)
    except TranslationError as exc:
        logger.debug("DeepL official backend not loaded: %s", exc)
        return None
