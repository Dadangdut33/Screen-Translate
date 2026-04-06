"""OCR key override settings page."""

from __future__ import annotations

from typing import Any

import pycountry
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CheckBox, ComboBox, LineEdit, TableWidget

from screen_translate.core.ocr.language_compat import resolve_tesseract_language_code

_LANGUAGE_NAME_OVERRIDES: dict[str, str] = {
    "auto": "Auto Detect",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "iw": "Hebrew",
    "jw": "Javanese",
    "mni-Mtei": "Manipuri (Meitei)",
    "pa-Arab": "Punjabi (Arabic)",
    "pt-PT": "Portuguese (Portugal)",
    "fr-CA": "French (Canada)",
    "fa-AF": "Dari",
    "ms-Arab": "Malay (Arabic)",
    "iu-Latn": "Inuktitut (Latin)",
    "sat-Latn": "Santali (Latin)",
    "crh-Latn": "Crimean Tatar (Latin)",
    "ber-Latn": "Berber (Latin)",
}


def language_name(code: str) -> str:
    """Return a human-friendly language name for a backend language code."""
    override = _LANGUAGE_NAME_OVERRIDES.get(code)
    if override:
        return override

    normalized = code.replace("_", "-")
    try:
        if "-" in normalized:
            language_part, script_or_region = normalized.split("-", 1)
            language = pycountry.languages.get(
                alpha_2=language_part.lower()
            ) or pycountry.languages.get(alpha_3=language_part.lower())
            if language is not None:
                region = pycountry.countries.get(alpha_2=script_or_region.upper())
                if region is not None:
                    return f"{language.name} ({region.name})"
        language = pycountry.languages.get(
            alpha_2=normalized.lower()
        ) or pycountry.languages.get(alpha_3=normalized.lower())
        if language is not None:
            return str(language.name)
    except (KeyError, AttributeError):
        pass

    return code


def refresh_ocr_override_table(dialog: Any, backend_name: str) -> None:
    """Refresh the override table for the selected translation backend."""
    if not hasattr(dialog, "_tbl_ocr_overrides"):
        return

    backend = dialog.controller._backends.get(backend_name)
    installed = dialog.controller.installed_ocr_languages()
    backend_overrides = dialog.controller.backend_ocr_overrides(backend_name)
    languages = backend.available_languages() if backend is not None else []
    sorting_was_enabled = dialog._tbl_ocr_overrides.isSortingEnabled()
    dialog._tbl_ocr_overrides.setSortingEnabled(False)

    rows: list[tuple[str, str, str, str]] = []
    for language_code in languages:
        current_override = backend_overrides.get(language_code, "")
        resolved_with_override = resolve_tesseract_language_code(
            language_code,
            installed,
            overrides=backend_overrides,
        )
        resolved_display = resolved_with_override or "[Incompatible]"
        rows.append(
            (
                language_code,
                language_name(language_code),
                resolved_display,
                current_override,
            )
        )
    dialog._tbl_ocr_overrides.setRowCount(len(rows))
    for row_index, (
        language_code,
        resolved_display_name,
        resolved_display,
        current_override,
    ) in enumerate(rows):
        code_item = QTableWidgetItem(language_code)
        code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        name_item = QTableWidgetItem(resolved_display_name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        resolved_item = QTableWidgetItem(resolved_display)
        resolved_item.setFlags(resolved_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        dialog._tbl_ocr_overrides.setItem(row_index, 0, code_item)
        dialog._tbl_ocr_overrides.setItem(row_index, 1, name_item)
        dialog._tbl_ocr_overrides.setItem(row_index, 2, resolved_item)

        combo = ComboBox()
        combo.blockSignals(True)
        combo.addItem("(none)", userData="")
        for tesseract_code in installed:
            combo.addItem(tesseract_code, userData=tesseract_code)
        combo.setProperty("backendName", backend_name)
        combo.setProperty("languageCode", language_code)
        current_index = combo.findData(current_override)
        combo.setCurrentIndex(max(0, current_index))
        combo.blockSignals(False)
        combo.currentIndexChanged.connect(
            lambda _idx, c=combo: _on_ocr_override_combo_changed(dialog, c)
        )
        dialog._tbl_ocr_overrides.setCellWidget(row_index, 3, combo)
    dialog._tbl_ocr_overrides.setSortingEnabled(sorting_was_enabled)
    apply_ocr_override_filter(dialog)


def apply_ocr_override_filter(dialog: Any, text: str = "") -> None:
    """Filter OCR override rows by search text."""
    if not hasattr(dialog, "_tbl_ocr_overrides"):
        return

    needle = text.strip().lower()
    show_incompatible = (
        dialog._chk_show_incompatible.isChecked()
        if hasattr(dialog, "_chk_show_incompatible")
        else True
    )
    for row_index in range(dialog._tbl_ocr_overrides.rowCount()):
        values: list[str] = []
        for column in range(3):
            item = dialog._tbl_ocr_overrides.item(row_index, column)
            if item is not None:
                values.append(item.text())
        combo = dialog._tbl_ocr_overrides.cellWidget(row_index, 3)
        if isinstance(combo, ComboBox):
            values.append(combo.currentText())
            current_data = combo.currentData()
            if isinstance(current_data, str):
                values.append(current_data)
        haystack = " ".join(values).lower()
        resolved_item = dialog._tbl_ocr_overrides.item(row_index, 2)
        is_incompatible = (
            resolved_item is not None and resolved_item.text() == "[Incompatible]"
        )
        dialog._tbl_ocr_overrides.setRowHidden(
            row_index,
            (not show_incompatible and is_incompatible)
            or (bool(needle) and needle not in haystack),
        )


def set_ocr_override(
    dialog: Any,
    backend_name: str,
    language_code: str,
    tesseract_code: str,
    row_index: int | None = None,
) -> None:
    """Persist an OCR override and refresh dependent UI."""
    dialog.controller.set_backend_ocr_override(
        backend_name,
        language_code,
        tesseract_code,
    )
    if dialog.controller.main_window:
        dialog.controller.main_window._refresh_lang_combos()

    installed = dialog.controller.installed_ocr_languages()
    resolved = resolve_tesseract_language_code(
        language_code,
        installed,
        overrides=dialog.controller.backend_ocr_overrides(backend_name),
    )
    resolved_display = resolved or "[Incompatible]"

    if row_index is not None and 0 <= row_index < dialog._tbl_ocr_overrides.rowCount():
        resolved_item = dialog._tbl_ocr_overrides.item(row_index, 2)
        if resolved_item is not None:
            resolved_item.setText(resolved_display)
        combo = dialog._tbl_ocr_overrides.cellWidget(row_index, 3)
        if isinstance(combo, ComboBox):
            combo.blockSignals(True)
            current_index = combo.findData(tesseract_code)
            combo.setCurrentIndex(max(0, current_index))
            combo.blockSignals(False)
        apply_ocr_override_filter(dialog)
        return

    refresh_ocr_override_table(dialog, backend_name)


def _find_override_combo_row(dialog: Any, combo: ComboBox) -> int | None:
    """Return the row index for a combo embedded in the override table."""
    for row_index in range(dialog._tbl_ocr_overrides.rowCount()):
        if dialog._tbl_ocr_overrides.cellWidget(row_index, 3) is combo:
            return row_index
    return None


def _on_ocr_override_combo_changed(dialog: Any, combo: ComboBox) -> None:
    """Handle override combo changes using combo properties instead of lambda-captured rows."""
    backend_name = combo.property("backendName")
    language_code = combo.property("languageCode")
    if not isinstance(backend_name, str) or not isinstance(language_code, str):
        return

    row_index = _find_override_combo_row(dialog, combo)
    set_ocr_override(
        dialog,
        backend_name,
        language_code,
        str(combo.currentData() or ""),
        row_index=row_index,
    )


def build_ocr_overrides_page(dialog: Any) -> QWidget:
    """Build the per-backend OCR override page."""
    w = QWidget()
    vl = QVBoxLayout(w)

    grp_tl_backend, fl_tl_backend = dialog._group_form(
        "Per-Backend OCR Language Overrides"
    )
    dialog._cb_override_backend = ComboBox()
    backend_names = [
        name for name in dialog.controller.available_backend_names() if name != "None"
    ]
    dialog._cb_override_backend.addItems(backend_names)
    active_backend = dialog.controller.active_backend_name()
    idx_backend = dialog._cb_override_backend.findText(active_backend)
    dialog._cb_override_backend.setCurrentIndex(max(0, idx_backend))
    dialog._cb_override_backend.currentTextChanged.connect(
        lambda name: refresh_ocr_override_table(dialog, name)
    )
    fl_tl_backend.addRow("Translation backend:", dialog._cb_override_backend)
    fl_tl_backend.addRow(
        BodyLabel(
            "All backend language codes are shown here. In this menu, "
            "you can set custom overrides to resolve them to compatible Tesseract codes. "
            "This is useful when a backend's language code doesn't match the standard."
        )
    )
    vl.addWidget(grp_tl_backend)

    grp_data_filter, fl_data_filter = dialog._group_form("Filtering and Display Options")
    dialog._le_ocr_override_search = LineEdit()
    dialog._le_ocr_override_search.setPlaceholderText(
        "Search by language code, name, resolved code, or override…"
    )
    dialog._le_ocr_override_search.textChanged.connect(
        lambda text: apply_ocr_override_filter(dialog, text)
    )

    fl_data_filter.addRow("Search:", dialog._le_ocr_override_search)
    dialog._chk_show_incompatible = CheckBox("Show incompatible languages")
    dialog._chk_show_incompatible.setChecked(True)
    dialog._chk_show_incompatible.toggled.connect(
        lambda _checked: apply_ocr_override_filter(dialog)
    )
    fl_data_filter.addRow(dialog._chk_show_incompatible)
    vl.addWidget(grp_data_filter)

    dialog._tbl_ocr_overrides = TableWidget()
    dialog._tbl_ocr_overrides.setRowCount(0)
    dialog._tbl_ocr_overrides.setColumnCount(4)
    dialog._tbl_ocr_overrides.setHorizontalHeaderLabels(
        ["Code", "Name", "Resolved", "Tesseract Key Override"]
    )
    header = dialog._tbl_ocr_overrides.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
    dialog._tbl_ocr_overrides.setColumnWidth(2, 130)
    dialog._tbl_ocr_overrides.setColumnWidth(3, 230)
    header.setSortIndicatorShown(True)
    dialog._tbl_ocr_overrides.setSortingEnabled(True)
    dialog._tbl_ocr_overrides.verticalHeader().setVisible(False)

    vl.addWidget(dialog._tbl_ocr_overrides, 1)
    refresh_ocr_override_table(dialog, dialog._cb_override_backend.currentText())
    return w
