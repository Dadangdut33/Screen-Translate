"""Abstract base class for translation backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TranslationBackend(ABC):
    """Pluggable translation backend interface.

    All concrete backends must implement :meth:`translate`,
    :meth:`available_languages`, and the :attr:`name` property.
    They must **not** import Qt - this module is pure Python.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name shown in the Settings UI."""

    @property
    def requires_api_key(self) -> bool:
        """Return True if this backend needs an API key to function.

        Backends that return True should handle a missing key gracefully
        (raise :class:`TranslationError` with a clear message).
        """
        return False

    @abstractmethod
    def available_languages(self) -> list[str]:
        """Return display names of all languages this backend supports.

        Returns:
            Sorted list of language display names.
        """

    def available_target_languages(self, source_lang: str) -> list[str]:
        """Return target languages available from *source_lang*.

        Backends that do not have pair-specific metadata can simply fall back
        to the generic language list.
        """
        return [
            lang
            for lang in self.available_languages()
            if lang not in {"auto", "Auto"}
        ]

    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate *text* from *source_lang* to *target_lang*.

        Args:
            text: Text to translate.
            source_lang: Display name of the source language, or ``"Auto"`` if
                auto-detection is supported.
            target_lang: Display name of the target language.

        Returns:
            Translated text.

        Raises:
            TranslationError: If translation fails for any reason.
        """


class TranslationError(RuntimeError):
    """Raised when a translation backend encounters an error."""
