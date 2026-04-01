"""Translation backend using the translators library."""

from __future__ import annotations

import logging
import os
from types import ModuleType

from screen_translate.core.translation.base import TranslationBackend, TranslationError

logger = logging.getLogger(__name__)


def configure_translators_region(region: str) -> None:
    """Apply the user-selected translators region mode to the environment."""
    normalized = region.strip().upper()
    if normalized == "AUTO":
        os.environ.pop("translators_default_region", None)
        return
    if normalized in {"EN", "CN"}:
        os.environ["translators_default_region"] = normalized


def _import_translators() -> ModuleType:
    """Import translators using the region mode already applied to the environment."""
    import translators as ts

    return ts


class TranslatorsBackend(TranslationBackend):
    """A generic backend wrapping a specific provider from the translators library."""

    def __init__(self, provider: str) -> None:
        """Create a new backend for the given provider.

        Args:
            provider: The name of the provider (e.g. 'google', 'bing', 'deepl').
        """
        self._provider = provider
        self._name = f"translators-{provider}"
        self._langs: list[str] = []
        self._langs_loaded = False

    @property
    def name(self) -> str:
        return self._name

    def available_languages(self) -> list[str]:
        if not self._langs_loaded:
            self._load_languages()
        return self._langs

    def _load_languages(self) -> None:
        """Load the provider's language identifiers lazily."""
        self._langs_loaded = True
        try:
            ts = _import_translators()
            langs = ts.get_languages(translator=self._provider)
            loaded: list[str] = []
            if isinstance(langs, dict):
                loaded = [str(key) for key in langs.keys()]
            elif isinstance(langs, list):
                loaded = [str(item) for item in langs]
            self._langs = sorted(dict.fromkeys(loaded))
        except Exception as exc:
            logger.warning("Failed to load languages for %s: %s", self._provider, exc)
            self._langs = []

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        try:
            ts = _import_translators()
            # The library might expect "auto" to be "auto"
            return ts.translate_text(
                query_text=text,
                translator=self._provider,
                from_language=source_lang,
                to_language=target_lang,
            )
        except Exception as e:
            raise TranslationError(f"{self.name} error: {e}") from e


def get_all_translators_backends() -> list[TranslationBackend]:
    """Return an instantiated backend for every provider in translators_pool."""
    backends: list[TranslationBackend] = []
    try:
        ts = _import_translators()
        for provider in ts.translators_pool:
            try:
                backends.append(TranslatorsBackend(provider))
            except Exception as e:
                logger.debug("Failed to init translator %s: %s", provider, e)
    except ImportError:
        logger.warning("translators not installed.")
    except Exception as exc:
        logger.warning("translators backend unavailable: %s", exc)

    return backends
