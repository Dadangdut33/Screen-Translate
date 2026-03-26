"""Translation backends using deep_translator (multi-provider wrapper)."""

from __future__ import annotations

import logging
from typing import Any

from .base import TranslationBackend, TranslationError

logger = logging.getLogger(__name__)

# Language display name → language code maps (from original LangCode.py)
_GOOGLE_LANG: dict[str, str] = {
    "Auto": "auto", "Afrikaans": "af", "Amharic": "am", "Arabic": "ar",
    "Armenian": "hy", "Azerbaijani": "az", "Belarusian": "be", "Bengali": "bn",
    "Bosnian": "bs", "Bulgarian": "bg", "Catalan": "ca", "Cebuano": "ceb",
    "Czech": "cs", "Chinese Simplified": "zh-CN", "Chinese Traditional": "zh-TW",
    "Corsican": "co", "Welsh": "cy", "Danish": "da", "German": "de",
    "Greek": "el", "English": "en", "Esperanto": "eo", "Estonian": "et",
    "Basque": "eu", "Persian": "fa", "Filipino": "tl", "Finnish": "fi",
    "French": "fr", "Irish": "ga", "Galician": "gl", "Gujarati": "gu",
    "Haitian": "ht", "Hebrew": "iw", "Hindi": "hi", "Hungarian": "hu",
    "Indonesian": "id", "Icelandic": "is", "Italian": "it", "Javanese": "jw",
    "Japanese": "ja", "Kannada": "kn", "Georgian": "ka", "Kazakh": "kk",
    "Khmer": "km", "Korean": "ko", "Kurdish": "ku", "Lao": "lo",
    "Latin": "la", "Latvian": "lv", "Lithuanian": "lt", "Luxembourgish": "lb",
    "Malayalam": "ml", "Marathi": "mr", "Macedonian": "mk", "Maltese": "mt",
    "Mongolian": "mn", "Maori": "mi", "Malay": "ms", "Burmese": "my",
    "Nepali": "ne", "Dutch": "nl", "Norwegian": "no", "Punjabi": "pa",
    "Polish": "pl", "Portuguese": "pt", "Romanian": "ro", "Russian": "ru",
    "Spanish": "es", "Albanian": "sq", "Serbian": "sr", "Sundanese": "su",
    "Swahili": "sw", "Swedish": "sv", "Tamil": "ta", "Tatar": "tt",
    "Telugu": "te", "Tajik": "tg", "Thai": "th", "Turkish": "tr",
    "Ukrainian": "uk", "Urdu": "ur", "Uzbek": "uz", "Vietnamese": "vi",
    "Yiddish": "yi", "Yoruba": "yo",
}

_MY_MEMORY_LANG: dict[str, str] = {
    "Auto": "auto", "Afrikaans": "af", "Albanian": "sq", "Amharic": "am",
    "Arabic": "ar", "Armenian": "hy", "Azerbaijani": "az", "Basque": "eu",
    "Belarusian": "be", "Bengali": "bn", "Bosnian": "bs", "Bulgarian": "bg",
    "Catalan": "ca", "Chinese Simplified": "zh-CN", "Chinese Traditional": "zh-TW",
    "Corsican": "co", "Czech": "cs", "Danish": "da", "Dutch": "nl",
    "English": "en", "Esperanto": "eo", "Estonian": "et", "Filipino": "fil",
    "Finnish": "fi", "French": "fr", "Galician": "gl", "Georgian": "ka",
    "German": "de", "Greek": "el", "Gujarati": "gu", "Hebrew": "he",
    "Hindi": "hi", "Hungarian": "hu", "Icelandic": "is", "Indonesian": "id",
    "Irish": "ga", "Italian": "it", "Japanese": "ja", "Javanese": "jw",
    "Kannada": "kn", "Kazakh": "kk", "Khmer": "km", "Korean": "ko",
    "Kurdish": "ku", "Lao": "lo", "Latin": "la", "Latvian": "lv",
    "Lithuanian": "lt", "Luxembourgish": "lb", "Macedonian": "mk", "Malay": "ms",
    "Malayalam": "ml", "Maltese": "mt", "Maori": "mi", "Marathi": "mr",
    "Mongolian": "mn", "Burmese": "my", "Nepali": "ne", "Norwegian": "no",
    "Persian": "fa", "Polish": "pl", "Portuguese": "pt", "Punjabi": "pa",
    "Romanian": "ro", "Russian": "ru", "Samoan": "sm", "Serbian": "sr",
    "Spanish": "es", "Sundanese": "su", "Swahili": "sw", "Swedish": "sv",
    "Tagalog": "tl", "Tajik": "tg", "Tamil": "ta", "Telugu": "te",
    "Thai": "th", "Turkish": "tr", "Ukrainian": "uk", "Urdu": "ur",
    "Uzbek": "uz", "Vietnamese": "vi", "Welsh": "cy", "Yiddish": "yi",
    "Yoruba": "yo",
}

_PONS_LANG: dict[str, str] = {
    "Arabic": "ar", "Bulgarian": "bg", "Chinese Simplified": "zh-cn",
    "Czech": "cs", "Danish": "da", "Dutch": "nl", "English": "en",
    "French": "fr", "German": "de", "Greek": "el", "Hungarian": "hu",
    "Italian": "it", "Latin": "la", "Norwegian": "no", "Polish": "pl",
    "Portuguese": "pt", "Russian": "ru", "Spanish": "es", "Swedish": "sv",
    "Turkish": "tr",
}

_LIBRE_LANG: dict[str, str] = {
    "Auto": "auto", "English": "en", "Arabic": "ar",
    "Chinese Simplified": "zh", "Dutch": "nl", "Finnish": "fi", "French": "fr",
    "German": "de", "Hindi": "hi", "Hungarian": "hu", "Indonesian": "id",
    "Irish": "ga", "Italian": "it", "Japanese": "ja", "Korean": "ko",
    "Polish": "pl", "Portuguese": "pt", "Russian": "ru", "Spanish": "es",
    "Swedish": "sv", "Turkish": "tr", "Ukrainian": "uk", "Vietnamese": "vi",
}


def _sorted_display_names(lang_map: dict[str, str], include_auto: bool = False) -> list[str]:
    """Return sorted display names, optionally including 'Auto'.

    Args:
        lang_map: Mapping of display name to language code.
        include_auto: Whether to prepend 'Auto' to the result.

    Returns:
        List of display names.
    """
    names = sorted(k for k in lang_map if k != "Auto")
    if include_auto:
        names.insert(0, "Auto")
    return names


def _to_code(lang_map: dict[str, str], display_name: str) -> str:
    """Look up a language code, case-insensitively falling back to the raw name.

    Args:
        lang_map: Map of display name → language code.
        display_name: User-facing language name.

    Returns:
        Language code string.

    Raises:
        TranslationError: If the display name is not in the map.
    """
    code = lang_map.get(display_name)
    if code is None:
        raise TranslationError(f"Unsupported language: {display_name!r}")
    return code


# ---------------------------------------------------------------------------
# Individual backend classes
# ---------------------------------------------------------------------------


class GoogleTranslateBackend(TranslationBackend):
    """Google Translate via deep_translator (no API key required)."""

    @property
    def name(self) -> str:
        """Return backend name."""
        return "Google Translate"

    def available_languages(self) -> list[str]:
        """Return list of supported language display names."""
        return _sorted_display_names(_GOOGLE_LANG, include_auto=True)

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Google Translate.

        Args:
            text: Text to translate.
            source_lang: Source language display name (or 'Auto').
            target_lang: Target language display name.

        Returns:
            Translated text.

        Raises:
            TranslationError: On any translation failure.
        """
        try:
            from deep_translator import GoogleTranslator

            src = _to_code(_GOOGLE_LANG, source_lang)
            tgt = _to_code(_GOOGLE_LANG, target_lang)
            result: str = GoogleTranslator(source=src, target=tgt).translate(text.strip()) or ""
            logger.debug("Google TL: %d chars → %d chars", len(text), len(result))
            return result
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


class MyMemoryBackend(TranslationBackend):
    """MyMemory translator via deep_translator (free, no API key)."""

    @property
    def name(self) -> str:
        """Return backend name."""
        return "MyMemory"

    def available_languages(self) -> list[str]:
        """Return list of supported language display names."""
        return _sorted_display_names(_MY_MEMORY_LANG, include_auto=True)

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using MyMemory.

        Args:
            text: Text to translate.
            source_lang: Source language display name (or 'Auto').
            target_lang: Target language display name.

        Returns:
            Translated text.

        Raises:
            TranslationError: On any translation failure.
        """
        try:
            from deep_translator import MyMemoryTranslator

            src = _to_code(_MY_MEMORY_LANG, source_lang)
            tgt = _to_code(_MY_MEMORY_LANG, target_lang)
            result: str = MyMemoryTranslator(source=src, target=tgt).translate(text.strip()) or ""
            return result
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


class PonsBackend(TranslationBackend):
    """PONS dictionary translator via deep_translator."""

    @property
    def name(self) -> str:
        """Return backend name."""
        return "PONS"

    def available_languages(self) -> list[str]:
        """Return list of supported language display names."""
        return _sorted_display_names(_PONS_LANG)

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using PONS.

        Args:
            text: Text to translate.
            source_lang: Source language display name.
            target_lang: Target language display name.

        Returns:
            Translated text.

        Raises:
            TranslationError: On any translation failure.
        """
        try:
            from deep_translator import PonsTranslator

            src = _to_code(_PONS_LANG, source_lang)
            tgt = _to_code(_PONS_LANG, target_lang)
            result: Any = PonsTranslator(source=src, target=tgt).translate(text.strip())
            return str(result) if result else ""
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


class LibreTranslateBackend(TranslationBackend):
    """LibreTranslate backend via deep_translator.

    Can target a self-hosted instance or the public API.
    """

    def __init__(
        self,
        host: str = "translate.argosopentech.com",
        port: str = "",
        use_https: bool = True,
        api_key: str = "",
    ) -> None:
        """Initialise LibreTranslate connection parameters.

        Args:
            host: LibreTranslate server hostname.
            port: Port number (empty = use default for scheme).
            use_https: Use HTTPS when True.
            api_key: Optional API key.
        """
        self._host = host
        self._port = port
        self._use_https = use_https
        self._api_key = api_key

    @property
    def name(self) -> str:
        """Return backend name."""
        return "LibreTranslate"

    def available_languages(self) -> list[str]:
        """Return list of supported language display names."""
        return _sorted_display_names(_LIBRE_LANG, include_auto=True)

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using LibreTranslate.

        Args:
            text: Text to translate.
            source_lang: Source language display name (or 'Auto').
            target_lang: Target language display name.

        Returns:
            Translated text.

        Raises:
            TranslationError: On connection or translation failure.
        """
        try:
            from deep_translator import LibreTranslator

            src = _to_code(_LIBRE_LANG, source_lang)
            tgt = _to_code(_LIBRE_LANG, target_lang)
            scheme = "https" if self._use_https else "http"
            base_url = f"{scheme}://{self._host}"
            if self._port:
                base_url += f":{self._port}"

            kwargs: dict[str, Any] = {"source": src, "target": tgt, "base_url": base_url + "/translate"}
            if self._api_key:
                kwargs["api_key"] = self._api_key

            result: str = LibreTranslator(**kwargs).translate(text.strip()) or ""
            return result
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


class DeepLFreeBackend(TranslationBackend):
    """DeepL free-tier translation via deep_translator (no API key needed)."""

    from typing import ClassVar
    _LANGS: ClassVar[dict[str, str]] = {
        "Bulgarian": "bg", "Chinese Simplified": "zh", "Czech": "cs",
        "Danish": "da", "Dutch": "nl", "English": "en", "Estonian": "et",
        "Finnish": "fi", "French": "fr", "German": "de", "Greek": "el",
        "Hungarian": "hu", "Indonesian": "id", "Italian": "it", "Japanese": "ja",
        "Korean": "ko", "Latvian": "lv", "Lithuanian": "lt", "Norwegian": "nb",
        "Polish": "pl", "Portuguese": "pt", "Romanian": "ro", "Russian": "ru",
        "Slovak": "sk", "Slovenian": "sl", "Spanish": "es", "Swedish": "sv",
        "Turkish": "tr", "Ukrainian": "uk",
    }

    @property
    def name(self) -> str:
        """Return backend name."""
        return "DeepL (free)"

    def available_languages(self) -> list[str]:
        """Return list of supported language display names."""
        return sorted(self._LANGS)

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using DeepL free tier.

        Args:
            text: Text to translate.
            source_lang: Source language display name.
            target_lang: Target language display name.

        Returns:
            Translated text.

        Raises:
            TranslationError: On any translation failure.
        """
        try:
            from deep_translator import DeepLTranslator

            src = self._LANGS.get(source_lang, "auto")
            tgt = _to_code(self._LANGS, target_lang)
            result: str = DeepLTranslator(source=src, target=tgt).translate(text.strip()) or ""
            return result
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


def load_deep_translator_backends(
    libre_host: str = "translate.argosopentech.com",
    libre_port: str = "",
    libre_https: bool = True,
    libre_api_key: str = "",
) -> list[TranslationBackend]:
    """Instantiate all deep_translator backends that can be imported.

    Args:
        libre_host: LibreTranslate server host.
        libre_port: LibreTranslate server port.
        libre_https: Use HTTPS for LibreTranslate.
        libre_api_key: LibreTranslate API key.

    Returns:
        List of instantiated backends.
    """
    backends: list[TranslationBackend] = []
    try:
        import deep_translator as _  # noqa: F401

        backends.extend(
            [
                GoogleTranslateBackend(),
                MyMemoryBackend(),
                DeepLFreeBackend(),
                LibreTranslateBackend(
                    host=libre_host,
                    port=libre_port,
                    use_https=libre_https,
                    api_key=libre_api_key,
                ),
                PonsBackend(),
            ]
        )
    except ImportError:
        logger.warning("deep_translator not installed - Google/MyMemory/PONS/LibreTranslate unavailable")
    return backends
