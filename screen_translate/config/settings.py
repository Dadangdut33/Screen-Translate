"""Screen-Translate configuration and settings management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir
from PyQt6.QtCore import QSettings

# ---------------------------------------------------------------------------
# Single canonical location for the settings file
# ---------------------------------------------------------------------------
SETTINGS_PATH: str = str(
    Path(user_config_dir("screen-translate", "Dadangdut33")) / "settings.ini"
)

# ---------------------------------------------------------------------------
DEFAULTS: dict[str, Any] = {
    # App
    "checkUpdateOnStart": True,
    "keep_image": True,
    "save_cropped_image": False,
    "auto_copy_captured": True,
    "auto_copy_translated": False,
    "save_history": True,
    "supress_no_text_alert": True,
    "run_on_startup": False,
    "theme": "Dark",
    # Logging
    "keep_log": True,
    "log_level": "DEBUG",
    "suppress_third_party_loggers": True,
    "max_log_rotation_days": 5,
    "auto_scroll_log": True,
    "auto_refresh_log": True,
    # Capture window offsets
    "offSetX": 0,
    "offSetY": 0,
    "offSetW": 0,
    "offSetH": 0,
    # Runtime option
    "engine": "translators-google",
    "sourceLang": "auto",
    "targetLang": "en",
    "translators_region": "EN",
    "capture_mode": "Floating Window",
    "capture_backend": "Auto",
    "suppress_missing_capture_file_errors": True,
    "ocr_backend": "Tesseract",
    "ocr_language_overrides": {},
    # OCR / Tesseract
    "tesseract_loc": "",
    "tesseract_config": "",
    "tesseract_psm5_vertical": True,
    "replaceNewLine": True,
    "replaceNewLineWith": " ",
    "enhance_with_cv2_contour": False,
    "save_cv2_contour_image": False,
    # Capture enhancement
    "enhance_background": "Auto-Detect",
    "enhance_with_grayscale": True,
    # Window hide on capture
    "hide_mw_on_cap": False,
    "hide_ex_qw_on_cap": True,
    "hide_ex_resw_on_cap": True,
    "show_query_window_after_capture": True,
    "show_result_window_after_capture": True,
    # Mask window
    "mask_window_bg_color": "#555555",
    "capture_window_bg_color": "#000000",
    # LibreTranslate
    "libre_api_key": "",
    "libre_host": "translate.argosopentech.com",
    "libre_port": "",
    "libre_https": True,
    # DeepL official
    "deepl_api_key": "",
    # Hotkeys
    "hk_cap_window": "",
    "hk_cap_window_delay": 1000,
    "hk_snip_cap": "ctrl+alt+t",
    "hk_snip_cap_delay": 0,
    # Detached / floating window appearance
    "tb_mw_q_font": "",
    "tb_mw_q_font_size": 10,
    "tb_mw_res_font": "",
    "tb_mw_res_font_size": 10,
    "tb_ex_q_font": "",
    "tb_ex_q_font_size": 12,
    "tb_ex_q_font_color": "#FFFFFF",
    "tb_ex_q_bg_color": "#000000",
    "tb_ex_res_font": "",
    "tb_ex_res_font_size": 12,
    "tb_ex_res_font_color": "#FFFFFF",
    "tb_ex_res_bg_color": "#000000",
    # Capture window geometry (stored as x,y,w,h string)
    "capture_window_geometry": "",
    "capture_region_geometry": "",
    # Query/result window geometries
    "ex_qw_geometry": "",
    "ex_resw_geometry": "",
}


class SettingsManager:
    """Thin wrapper around QSettings providing typed get/set and factory defaults.

    All settings are persisted to an INI file at *SETTINGS_PATH* so that
    every change is saved immediately without an explicit "Save" action.
    """

    def __init__(self) -> None:
        """Create or open the persistent settings store."""
        # Ensure the parent directory exists
        Path(SETTINGS_PATH).parent.mkdir(parents=True, exist_ok=True)
        self._qs = QSettings(SETTINGS_PATH, QSettings.Format.IniFormat)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the stored value for *key*, falling back to *DEFAULTS* then *default*.

        Args:
            key: Settings key name.
            default: Fallback when the key is absent from both the store and DEFAULTS.

        Returns:
            The stored or default value, cast to the type of the default.
        """
        fallback: Any = DEFAULTS.get(key, default)
        raw = self._qs.value(key, fallback)

        # QSettings reads everything as strings; coerce back to bool/int/float
        if isinstance(fallback, bool):
            if isinstance(raw, str):
                return raw.lower() in ("true", "1", "yes")
            return bool(raw)
        if isinstance(fallback, int):
            try:
                return int(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return fallback
        if isinstance(fallback, float):
            try:
                return float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return fallback
        if isinstance(fallback, dict):
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    return fallback
            if isinstance(raw, dict):
                return raw
            return fallback
        return raw

    def set(self, key: str, value: Any) -> None:
        """Persist *value* for *key* immediately to disk.

        Args:
            key: Settings key name.
            value: New value to persist.
        """
        if isinstance(value, dict):
            self._qs.setValue(key, json.dumps(value, sort_keys=True))
        else:
            self._qs.setValue(key, value)
        self._qs.sync()

    def restore_defaults(self) -> None:
        """Wipe all stored settings and rewrite defaults."""
        self._qs.clear()
        for key, val in DEFAULTS.items():
            self.set(key, val)

    def all_keys(self) -> list[str]:
        """Return all keys currently stored.

        Returns:
            List of key strings.
        """
        return self._qs.allKeys()  # type: ignore[return-value]

    # Convenience attribute-style access --------------------------------

    def __getitem__(self, key: str) -> Any:
        """Support dict-style read access."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Support dict-style write access."""
        self.set(key, value)
