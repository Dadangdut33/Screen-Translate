"""ABCfor OCR backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image


class OCRBackend(ABC):
    """Abstract base class for OCR backends.

    All backends must accept a Pillow *Image* and return plain text.
    The image is kept as Pillow rather than QImage so that the core
    layer stays free of Qt imports.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name."""

    @abstractmethod
    def detect_languages(self) -> list[str]:
        """Return a list of language codes (or display names) available to this backend.

        Returns:
            List of available language identifiers.
        """

    @abstractmethod
    def extract_text(self, image: Image) -> str:
        """Extract text from *image* and return it as a plain string.

        Args:
            image: A Pillow Image (RGB or L mode).

        Returns:
            Recognised text, possibly empty.

        Raises:
            RuntimeError: If the backend is unavailable or extraction fails.
        """


class OCRError(RuntimeError):
    """Raised when OCR extraction fails."""
