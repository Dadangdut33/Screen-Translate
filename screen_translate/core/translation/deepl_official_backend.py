"""Official DeepL translation backend (requires DEEPL_API_KEY)."""

from __future__ import annotations

import logging
import os

from .base import TranslationBackend, TranslationError

logger = logging.getLogger(__name__)


class DeepLOfficialBackend(TranslationBackend):
    """Official DeepL API backend via the ``deepl-python`` package."""

    @property
    def requires_api_key(self) -> bool:
        """Return True - DeepL official always needs an API key."""
        return True

    def __init__(self, api_key: str = "") -> None:
        """Initialise the backend. Doesn't fetch languages until needed using the key."""
        try:
            import deepl  # noqa: F401
        except ImportError as exc:
            raise TranslationError("deepl package is not installed.") from exc

        self._api_key = api_key or os.environ.get("DEEPL_API_KEY", "")
        self._langs: list[str] = []

    def _fetch_langs(self) -> None:
        if self._langs or not self._api_key:
            return
        try:
            import deepl

            translator = deepl.Translator(self._api_key)
            # Combine source and target languages for a unified list of codes
            sources = translator.get_source_languages()
            targets = translator.get_target_languages()
            codes = {lang.code for lang in sources}
            codes.update({lang.code for lang in targets})
            self._langs = sorted(codes)
            self._langs.insert(0, "auto")
        except Exception as e:
            logger.debug("DeepL API key error or network error: %s", e)
            self._langs = ["auto"]

    @property
    def name(self) -> str:
        """Return backend name."""
        return "DeepL (official)"

    def available_languages(self) -> list[str]:
        """Return language codes provided by the DeepL API."""
        self._fetch_langs()
        return self._langs or ["auto"]

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using the official DeepL API."""
        try:
            import deepl

            if not self._api_key:
                raise TranslationError("DeepL API key is required but missing.")

            translator = deepl.Translator(self._api_key)
            src_code = None if source_lang.lower() == "auto" else source_lang.upper()
            tgt_code = target_lang.upper()

            # DeepL API requires EN-US or EN-GB for targets if EN is chosen
            if tgt_code == "EN":
                tgt_code = "EN-US"
            elif tgt_code == "PT":
                tgt_code = "PT-BR"

            result = translator.translate_text(
                text.strip(), source_lang=src_code, target_lang=tgt_code
            )
            return str(result.text)
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


def load_deepl_official_backend(api_key: str = "") -> DeepLOfficialBackend | None:
    """Return a DeepL official backend if the package is installed."""
    try:
        return DeepLOfficialBackend(api_key=api_key)
    except TranslationError as exc:
        logger.debug("DeepL official backend not loaded: %s", exc)
        return None
