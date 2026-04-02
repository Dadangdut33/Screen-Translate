"""Shared widget-binding helpers for settings pages."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QSpinBox


def bind_check(key: str, label: str, settings: Any) -> QCheckBox:
    """Create a checkbox pre-filled from settings and auto-save on toggle."""
    cb = QCheckBox(label)
    cb.setChecked(bool(settings.get(key, False)))
    cb.toggled.connect(lambda v: settings.set(key, v))
    return cb


def bind_line(key: str, settings: Any, placeholder: str = "") -> QLineEdit:
    """Create a line edit pre-filled from settings and auto-save on change."""
    le = QLineEdit()
    le.setText(str(settings.get(key, "")))
    le.setPlaceholderText(placeholder)
    le.textChanged.connect(lambda v: settings.set(key, v))
    return le


def bind_spin(
    key: str, settings: Any, min_val: int = 0, max_val: int = 9999
) -> QSpinBox:
    """Create a spin box pre-filled from settings and auto-save on change."""
    sb = QSpinBox()
    sb.setRange(min_val, max_val)
    sb.setValue(int(settings.get(key, 0)))
    sb.valueChanged.connect(lambda v: settings.set(key, v))
    return sb


def bind_combo(key: str, items: list[str], settings: Any) -> QComboBox:
    """Create a combo box pre-filled from settings and auto-save on change."""
    cb = QComboBox()
    cb.addItems(items)
    saved = settings.get(key, "")
    idx = cb.findText(str(saved))
    cb.setCurrentIndex(max(0, idx))
    cb.currentTextChanged.connect(lambda v: settings.set(key, v))
    return cb


def bind_check_with_callback(
    key: str,
    label: str,
    settings: Any,
    callback: Any,
) -> QCheckBox:
    """Create a checkbox that persists immediately and also runs a callback."""
    cb = QCheckBox(label)
    cb.setChecked(bool(settings.get(key, False)))
    cb.toggled.connect(lambda v: settings.set(key, v))
    cb.toggled.connect(lambda _v: callback())
    return cb


def bind_line_with_callback(
    key: str,
    settings: Any,
    callback: Any,
    placeholder: str = "",
) -> QLineEdit:
    """Create a line edit that persists immediately and also runs a callback."""
    le = QLineEdit()
    le.setText(str(settings.get(key, "")))
    le.setPlaceholderText(placeholder)
    le.textChanged.connect(lambda v: settings.set(key, v))
    le.textChanged.connect(lambda _v: callback())
    return le


def bind_combo_with_callback(
    key: str,
    items: list[str],
    settings: Any,
    callback: Any,
) -> QComboBox:
    """Create a combo box that persists immediately and also runs a callback."""
    cb = QComboBox()
    cb.addItems(items)
    saved = settings.get(key, "")
    idx = cb.findText(str(saved))
    cb.setCurrentIndex(max(0, idx))
    cb.currentTextChanged.connect(lambda v: settings.set(key, v))
    cb.currentTextChanged.connect(lambda _v: callback())
    return cb
