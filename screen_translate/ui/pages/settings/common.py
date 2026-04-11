"""Shared widget-binding helpers for settings pages."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QFormLayout
from qfluentwidgets import CheckBox, ComboBox, LineEdit, SpinBox


def bind_check(key: str, label: str, settings: Any) -> CheckBox:
    """Create a checkbox pre-filled from settings and auto-save on toggle."""
    cb = CheckBox(label)
    cb.setChecked(bool(settings.get(key, False)))
    cb.toggled.connect(lambda v: settings.set(key, v))
    return cb


def bind_line(key: str, settings: Any, placeholder: str = "") -> LineEdit:
    """Create a line edit pre-filled from settings and auto-save on change."""
    le = LineEdit()
    le.setText(str(settings.get(key, "")))
    le.setPlaceholderText(placeholder)
    le.textChanged.connect(lambda v: settings.set(key, v))
    return le


def bind_spin(
    key: str, settings: Any, min_val: int = 0, max_val: int = 9999
) -> SpinBox:
    """Create a spin box pre-filled from settings and auto-save on change."""
    sb = SpinBox()
    sb.setRange(min_val, max_val)
    sb.setValue(int(settings.get(key, 0)))
    sb.valueChanged.connect(lambda v: settings.set(key, v))
    return sb


def bind_combo(key: str, items: list[str], settings: Any) -> ComboBox:
    """Create a combo box pre-filled from settings and auto-save on change."""
    cb = ComboBox()
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
) -> CheckBox:
    """Create a checkbox that persists immediately and also runs a callback."""
    cb = CheckBox(label)
    cb.setChecked(bool(settings.get(key, False)))
    cb.toggled.connect(lambda v: settings.set(key, v))
    cb.toggled.connect(lambda _v: callback())
    return cb


def bind_line_with_callback(
    key: str,
    settings: Any,
    callback: Any,
    placeholder: str = "",
) -> LineEdit:
    """Create a line edit that persists immediately and also runs a callback."""
    le = LineEdit()
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
) -> ComboBox:
    """Create a combo box that persists immediately and also runs a callback."""
    cb = ComboBox()
    cb.addItems(items)
    saved = settings.get(key, "")
    idx = cb.findText(str(saved))
    cb.setCurrentIndex(max(0, idx))
    cb.currentTextChanged.connect(lambda v: settings.set(key, v))
    cb.currentTextChanged.connect(lambda _v: callback())
    return cb


def configure_form_layout(form: QFormLayout) -> None:
    """Make settings forms shrink and wrap more gracefully in narrow viewports."""
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
