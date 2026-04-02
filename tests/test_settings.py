"""Tests for SettingsManager - get/set/restore and type coercion."""

from __future__ import annotations

import os
import tempfile

import pytest

from screen_translate.config.settings import SettingsManager


@pytest.fixture()
def tmp_settings(monkeypatch: pytest.MonkeyPatch) -> SettingsManager:
    """Return a SettingsManager pointing at a temporary INI file."""
    from screen_translate.config import settings as _settings_mod

    with tempfile.NamedTemporaryFile(suffix=".ini", delete=False) as f:
        tmp_path = f.name

    monkeypatch.setattr(_settings_mod, "SETTINGS_PATH", tmp_path)

    from screen_translate.config.settings import SettingsManager

    mgr = SettingsManager()
    yield mgr
    os.unlink(tmp_path)


def test_get_default(tmp_settings: SettingsManager) -> None:
    """A fresh store returns the DEFAULTS value for known keys."""
    from screen_translate.config.settings import DEFAULTS

    for key, expected in DEFAULTS.items():
        result = tmp_settings.get(key)
        # Type must match (bool preserved as bool, not string)
        if isinstance(expected, bool):
            assert isinstance(result, bool), f"{key}: expected bool, got {type(result)}"
        elif isinstance(expected, int):
            assert isinstance(result, int), f"{key}: expected int, got {type(result)}"


def test_set_and_get(tmp_settings: SettingsManager) -> None:
    """Values written with set() are retrievable with get()."""
    tmp_settings.set("sourceLang", "French")
    assert tmp_settings.get("sourceLang") == "French"


def test_bool_coercion(tmp_settings: SettingsManager) -> None:
    """Boolean values survive a round-trip through QSettings string storage."""
    tmp_settings.set("keep_image", True)
    assert tmp_settings.get("keep_image") is True

    tmp_settings.set("keep_image", False)
    assert tmp_settings.get("keep_image") is False


def test_restore_defaults(tmp_settings: SettingsManager) -> None:
    """restore_defaults() resets all keys to their default values."""
    tmp_settings.set("sourceLang", "Klingon")
    tmp_settings.restore_defaults()
    assert tmp_settings.get("sourceLang") == "English"
