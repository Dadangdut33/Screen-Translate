"""Tests for translation backends."""

from __future__ import annotations

import os

import pytest

from screen_translate.core.translation.argos_backend import ArgosTranslateBackend
from screen_translate.core.translation.base import TranslationError
from screen_translate.core.translation.libretranslate_backend import (
    LibreTranslateBackend,
    LibreTranslateConfig,
)
from screen_translate.core.translation.translators_backend import TranslatorsBackend


def test_translators_backend_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test translators backend translates using the mocked library."""

    # Mock translators logic
    monkeypatch.setitem(os.environ, "translators_default_region", "EN")
    import translators as ts
    monkeypatch.setattr(ts, "get_languages", lambda translator: {"auto": "auto", "en": "en", "es": "es"})

    def mock_translate_text(
        query_text: str,
        translator: str,
        from_language: str,
        to_language: str,
        proxies: dict[str, str] | None = None,
    ) -> str:
        assert proxies is None
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

    mock_root = types.ModuleType("argostranslate")
    mock_translate = types.ModuleType("argostranslate.translate")
    mock_package = types.ModuleType("argostranslate.package")
    mock_translate.get_installed_languages = MockTranslateModule.get_installed_languages  # type: ignore[attr-defined]
    mock_package.get_available_packages = lambda: []  # type: ignore[attr-defined]
    mock_root.translate = mock_translate  # type: ignore[attr-defined]
    mock_root.package = mock_package  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "argostranslate", mock_root)
    monkeypatch.setitem(sys.modules, "argostranslate.translate", mock_translate)
    monkeypatch.setitem(sys.modules, "argostranslate.package", mock_package)

    backend = ArgosTranslateBackend()
    assert "Argos" in backend.name
    langs = backend.available_languages()
    assert "en" in langs
    assert "es" in langs

    result = backend.translate("hello", "en", "es")
    assert result == "ARGOSMOCK[en->es]: hello"

    with pytest.raises(TranslationError, match="No direct translation pack"):
        backend.translate("hello", "es", "en")


def test_libretranslate_backend_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test LibreTranslate backend language loading and translation."""

    class MockResponse:
        def __init__(self, payload: object) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> object:
            return self._payload

    def mock_get(url: str, timeout: float, proxies: dict[str, str] | None = None) -> MockResponse:
        assert url.endswith("/languages")
        assert proxies == {"http": "http://proxy.local:8080"}
        return MockResponse(
            [
                {"code": "en", "targets": ["id"]},
                {"code": "id", "targets": ["en"]},
            ]
        )

    def mock_post(
        url: str,
        data: dict[str, object],
        timeout: float,
        proxies: dict[str, str] | None = None,
    ) -> MockResponse:
        assert url.endswith("/translate")
        assert data["source"] == "en"
        assert data["target"] == "id"
        assert data["api_key"] == "secret"
        assert proxies == {"http": "http://proxy.local:8080"}
        return MockResponse({"translatedText": "halo"})

    import requests

    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(requests, "post", mock_post)

    backend = LibreTranslateBackend(
        LibreTranslateConfig(
            host="example.test",
            use_https=True,
            api_key="secret",
            proxies={"http": "http://proxy.local:8080"},
        )
    )

    assert backend.available_languages() == ["auto", "en", "id"]
    assert backend.available_target_languages("en") == ["id"]
    assert backend.translate("hello", "en", "id") == "halo"
