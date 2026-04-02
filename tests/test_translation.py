"""Tests for translation backends."""

from __future__ import annotations

import pytest

from screen_translate.core.translation.argos_backend import ArgosTranslateBackend
from screen_translate.core.translation.base import TranslationError
from screen_translate.core.translation.translators_backend import TranslatorsBackend


def test_translators_backend_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test translators backend translates using the mocked library."""

    # Mock translators logic
    import translators as ts
    monkeypatch.setattr(ts, "get_languages", lambda translator: {"auto": "auto", "en": "en", "es": "es"})

    def mock_translate_text(query_text: str, translator: str, from_language: str, to_language: str) -> str:
        return f"MOCK[{from_language}->{to_language}]: {query_text}"

    monkeypatch.setattr(ts, "translate_text", mock_translate_text)

    backend = TranslatorsBackend("google")
    assert "google" in backend.name
    assert "en" in backend.available_languages()

    result = backend.translate("hello", "en", "es")
    assert result == "MOCK[en->es]: hello"


def test_argos_backend_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Offline argos translates via argostranslate."""

    # Ensure backend can load
    class MockLang:
        def __init__(self, code: str):
            self.code = code
        def get_translation(self, tgt):
            if tgt.code == "es":
                # Capture variables for the closure
                src_code = self.code
                tgt_code = tgt.code
                class MockTranslation:
                    def translate(self, text: str) -> str:
                        return f"ARGOSMOCK[{src_code}->{tgt_code}]: {text}"
                return MockTranslation()
            return None

    class MockTranslateModule:
        @staticmethod
        def get_installed_languages():
            return [MockLang("en"), MockLang("es")]

    import sys
    import types
    mock_module = types.ModuleType("argostranslate")
    mock_module.translate = MockTranslateModule  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "argostranslate", mock_module)

    backend = ArgosTranslateBackend()
    assert "Argos" in backend.name
    langs = backend.available_languages()
    assert "en" in langs
    assert "es" in langs

    result = backend.translate("hello", "en", "es")
    assert result == "ARGOSMOCK[en->es]: hello"

    with pytest.raises(TranslationError, match="No direct translation pack"):
        backend.translate("hello", "es", "en")
