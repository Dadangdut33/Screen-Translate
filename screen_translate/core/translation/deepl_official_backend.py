"""Official DeepL translation backend (requires DEEPL_API_KEY)."""

from __future__ import annotations

import logging
import os

from .base import TranslationBackend, TranslationError
from .proxy import temporary_proxy_env

logger = logging.getLogger(__name__)


class DeepLOfficialBackend(TranslationBackend):
    """Official DeepL API backend via the ``deepl-python`` package."""

    @property
    def requires_api_key(self) -> bool:
        """Return True - DeepL official always needs an API key."""
        return True

    def __init__(
        self,
        api_key: str = "",
        proxies: dict[str, str] | None = None,
        no_proxy: str = "",
    ) -> None:
        """Initialise the backend. Doesn't fetch languages until needed using the key."""
        try:
            import deepl  # noqa: F401
        except ImportError as exc:
            raise TranslationError("deepl package is not installed.") from exc

        self._api_key = api_key or os.environ.get("DEEPL_API_KEY", "")
        self._langs: list[str] = []
        self._proxies = proxies or {}
        self._no_proxy = no_proxy

    def _fetch_langs(self) -> None:
        if self._langs:
            return
        try:
            import deepl

            with temporary_proxy_env(self._proxies, self._no_proxy):
                if self._api_key:
                    translator = deepl.Translator(self._api_key)
                    sources = translator.get_source_languages()
                    targets = translator.get_target_languages()
                    codes = {lang.code for lang in sources}
                    codes.update({lang.code for lang in targets})
                else:
                    codes = self._static_language_codes(deepl)

            normalized_codes = {
                str(code).strip()
                for code in codes
                if isinstance(code, str) and str(code).strip()
            }
            self._langs = ["auto", *sorted(normalized_codes)]
        except Exception as e:
            logger.debug("DeepL API key error or network error: %s", e)
            self._langs = ["auto"]

    def _static_language_codes(self, deepl_module: object) -> set[str]:
        """Return best-effort DeepL language codes from the library itself."""
        language_enum = getattr(deepl_module, "Language", None)
        if language_enum is None:
            return set()

        codes: set[str] = set()
        for attr_name in dir(language_enum):
            if attr_name.startswith("_"):
                continue
            value = getattr(language_enum, attr_name, None)
            if isinstance(value, str) and value.strip():
                codes.add(value.strip())
        return codes

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

            with temporary_proxy_env(self._proxies, self._no_proxy):
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


def load_deepl_official_backend(
    api_key: str = "",
    proxies: dict[str, str] | None = None,
    no_proxy: str = "",
) -> DeepLOfficialBackend | None:
    """Return a DeepL official backend if the package is installed."""
    try:
        return DeepLOfficialBackend(
            api_key=api_key,
            proxies=proxies,
            no_proxy=no_proxy,
        )
    except TranslationError as exc:
        logger.debug("DeepL official backend not loaded: %s", exc)
        return None
