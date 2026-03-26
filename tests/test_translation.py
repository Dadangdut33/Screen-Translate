"""Tests for translation backends."""

from __future__ import annotations

import pytest

from screen_translate.core.translation.base import TranslationError
from screen_translate.core.translation.deep_translator_backend import GoogleTranslateBackend


def test_google_translate_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Google backend translates using the mocked deep_translator."""
    backend = GoogleTranslateBackend()
    assert "Google" in backend.name
    assert "English" in backend.available_languages()

    class MockGoogleTranslator:
        def __init__(self, source: str, target: str) -> None:
            self.source = source
            self.target = target

        def translate(self, text: str) -> str:
            return f"MOCK[{self.source}->{self.target}]: {text}"

    # We mock deep_translator module via sys.modules so the inner import succeeds
    import sys
    import types
    mock_module = types.ModuleType("deep_translator")
    mock_module.GoogleTranslator = MockGoogleTranslator  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "deep_translator", mock_module)

    result = backend.translate("hello", "English", "Japanese")
    assert result == "MOCK[en->ja]: hello"


def test_invalid_language_raises_error() -> None:
    """Passing an invalid language display name raises TranslationError."""
    backend = GoogleTranslateBackend()
    with pytest.raises(TranslationError, match="Unsupported language"):
        backend.translate("hello", "NotARealLanguage", "English")
