"""OpenRouter settings section."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PyQt6.QtGui import QTextOption
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QHeaderView, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import CheckBox, LineEdit, PlainTextEdit, PushButton, TableWidget

from screen_translate.core.translation.openrouter_backend import (
    CustomLanguageList,
    language_entries,
)
from screen_translate.ui.widgets import InfoBannerCard

from .shared import make_reload_line_edit, refresh_translation_runtime

if TYPE_CHECKING:
    from screen_translate.ui.pages.settings_page import SettingsPage


class _ReloadPlainTextEdit(PlainTextEdit):
    """Plain-text editor that persists immediately and reloads on focus-out."""

    def __init__(
        self,
        dialog: SettingsPage,
        key: str,
        *,
        placeholder: str = "",
        on_commit: Callable[[], None] | None = None,
        fixed_height: int = 120,
    ) -> None:
        super().__init__()
        self._dialog = dialog
        self._key = key
        self._on_commit = on_commit
        self.setPlaceholderText(placeholder)
        self.setPlainText(str(dialog.s.get(key, "")))
        self.setFixedHeight(fixed_height)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.textChanged.connect(self._persist)

    def _persist(self) -> None:
        self._dialog.s.set(self._key, self.toPlainText())

    def focusOutEvent(self, event) -> None:  # type: ignore[override]
        super().focusOutEvent(event)
        if self._on_commit is not None:
            self._on_commit()


def _openrouter_custom_languages(dialog: SettingsPage) -> CustomLanguageList:
    """Return the configured custom OpenRouter languages as normalized rows."""
    raw = dialog.s.get("openrouter_custom_languages", [])
    rows: CustomLanguageList = []
    if isinstance(raw, dict):
        for code, label in raw.items():
            code_text = str(code).strip()
            label_text = str(label).strip()
            if code_text and label_text:
                rows.append({"code": code_text, "name": label_text})
        return rows
    if isinstance(raw, list):
        for row in raw:
            if not isinstance(row, dict):
                continue
            code_text = str(row.get("code", "")).strip()
            label_text = str(row.get("name", "")).strip()
            if code_text and label_text:
                rows.append({"code": code_text, "name": label_text})
    return rows


def _set_openrouter_custom_languages(
    dialog: SettingsPage, rows: CustomLanguageList
) -> None:
    """Persist custom OpenRouter languages and refresh runtime."""
    dialog.s.set("openrouter_custom_languages", rows)
    refresh_translation_runtime(dialog)
    if hasattr(dialog, "_cb_override_backend") and hasattr(
        dialog, "_tbl_ocr_overrides"
    ):
        try:
            from screen_translate.ui.pages.settings.ocr_overrides import (
                refresh_ocr_override_table,
            )

            backend_name = dialog._cb_override_backend.currentText()
            if backend_name == "OpenRouter":
                refresh_ocr_override_table(dialog, backend_name)
        except Exception:
            pass


def _refresh_openrouter_language_table(dialog: SettingsPage) -> None:
    """Rebuild the OpenRouter language preview table."""
    table: TableWidget | None = getattr(dialog, "_tbl_openrouter_languages", None)
    if table is None:
        return

    custom_rows = _openrouter_custom_languages(dialog)
    default_entries = list(language_entries([]))
    custom_entries = sorted(
        [(row["code"], row["name"]) for row in custom_rows],
        key=lambda item: item[1].lower(),
    )
    rows = [(code, label, "Default") for code, label in default_entries] + [
        (code, label, "Custom") for code, label in custom_entries
    ]

    table.setRowCount(len(rows))
    for row, (code, label, source) in enumerate(rows):
        for col, value in enumerate((code, label, source)):
            item = QTableWidgetItem(value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, item)

        if source == "Custom":
            btn = PushButton("Delete")
            btn.clicked.connect(
                lambda _checked=False, c=code, l=label: _delete_openrouter_custom_language(
                    dialog, c, l
                )
            )
            table.setCellWidget(row, 3, btn)
        else:
            table.setCellWidget(row, 3, None)
    _filter_openrouter_language_table(
        dialog,
        (
            dialog._openrouter_language_search.text()
            if hasattr(dialog, "_openrouter_language_search")
            else ""
        ),
    )


def _filter_openrouter_language_table(dialog: SettingsPage, text: str = "") -> None:
    """Filter OpenRouter language rows by code, name, or source."""
    table: TableWidget | None = getattr(dialog, "_tbl_openrouter_languages", None)
    if table is None:
        return
    needle = text.strip().lower()
    for row in range(table.rowCount()):
        values: list[str] = []
        for column in range(3):
            item = table.item(row, column)
            if item is not None:
                values.append(item.text())
        haystack = " ".join(values).lower()
        table.setRowHidden(row, bool(needle) and needle not in haystack)


def _add_openrouter_custom_language(dialog: SettingsPage) -> None:
    """Add or update a custom OpenRouter language entry from the form controls."""
    code_widget: LineEdit | None = getattr(dialog, "_openrouter_custom_code", None)
    name_widget: LineEdit | None = getattr(dialog, "_openrouter_custom_name", None)
    hint_label: QLabel | None = getattr(dialog, "_lbl_openrouter_custom_hint", None)
    if code_widget is None or name_widget is None:
        return

    code = code_widget.text().strip()
    name = name_widget.text().strip()
    if not code or not name:
        if hint_label is not None:
            hint_label.setText("Both language code and display name are required.")
        return

    rows = _openrouter_custom_languages(dialog)
    if not any(row["code"] == code and row["name"] == name for row in rows):
        rows.append({"code": code, "name": name})
    _set_openrouter_custom_languages(dialog, rows)
    _refresh_openrouter_language_table(dialog)
    code_widget.clear()
    name_widget.clear()
    if hint_label is not None:
        hint_label.setText("Custom language saved.")


def _delete_openrouter_custom_language(
    dialog: SettingsPage, code: str, name: str
) -> None:
    """Delete one custom OpenRouter language entry."""
    rows = _openrouter_custom_languages(dialog)
    filtered = [
        row for row in rows if not (row["code"] == code and row["name"] == name)
    ]
    if len(filtered) == len(rows):
        return
    _set_openrouter_custom_languages(dialog, filtered)
    _refresh_openrouter_language_table(dialog)


def build_openrouter_section(dialog: SettingsPage) -> QWidget:
    """Build the OpenRouter settings section."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    layout.addWidget(
        InfoBannerCard(
            "OpenRouter",
            "LLM-backed translation backend using OpenRouter's chat-completions API. You can be creative with "
            "the prompt templates to support different translation styles or even non-translation tasks"
            ", but the default is optimized for concise and accurate translations."
            "\n\nPrompt templates support placeholders such as {{source_language}}, "
            "{{target_language}}, {{text}}, {{language_list}}, and {{custom_languages}}.",
            page,
            icon_name="mdi6.router-network",
        )
    )

    grp_api, fl_api = dialog._group_form("Connection")
    fl_api.addRow(
        QLabel(
            "Use an OpenRouter-compatible /api/v1 base URL. "
            "The backend will call the chat completions endpoint under that base URL."
        )
    )
    dialog._openrouter_base_url = make_reload_line_edit(
        dialog,
        "openrouter_base_url",
        "https://openrouter.ai/api/v1",
    )
    dialog._openrouter_api_key = make_reload_line_edit(
        dialog,
        "openrouter_api_key",
        "Enter API key…",
        password=True,
    )
    dialog._openrouter_model = make_reload_line_edit(
        dialog,
        "openrouter_model",
        "openrouter/free",
    )
    dialog._openrouter_timeout = make_reload_line_edit(
        dialog,
        "openrouter_timeout",
        "60",
    )
    fl_api.addRow("Base URL:", dialog._openrouter_base_url)
    fl_api.addRow("API key:", dialog._openrouter_api_key)
    fl_api.addRow("Model:", dialog._openrouter_model)
    fl_api.addRow("Timeout (seconds):", dialog._openrouter_timeout)
    dialog._openrouter_debug_logging = CheckBox(
        "Enable debug logging for prompt and response"
    )
    dialog._openrouter_debug_logging.setChecked(
        bool(dialog.s.get("openrouter_debug_logging", False))
    )
    dialog._openrouter_debug_logging.toggled.connect(
        lambda checked: (
            dialog.s.set("openrouter_debug_logging", checked),
            refresh_translation_runtime(dialog),
        )
    )
    fl_api.addRow(dialog._openrouter_debug_logging)
    layout.addWidget(grp_api)

    grp_prompt, fl_prompt = dialog._group_form("Prompt Templates")
    lbl_prompt = QLabel(
        "Customize the system and user prompt templates for OpenRouter translation."
    )
    lbl_prompt.setWordWrap(True)
    fl_prompt.addRow(lbl_prompt)
    dialog._openrouter_system_prompt = _ReloadPlainTextEdit(
        dialog,
        "openrouter_system_prompt_template",
        placeholder="System prompt template…",
        on_commit=lambda: refresh_translation_runtime(dialog),
        fixed_height=150,
    )
    dialog._openrouter_user_prompt = _ReloadPlainTextEdit(
        dialog,
        "openrouter_user_prompt_template",
        placeholder="User prompt template…",
        on_commit=lambda: refresh_translation_runtime(dialog),
        fixed_height=90,
    )
    fl_prompt.addRow("System template:", dialog._openrouter_system_prompt)
    fl_prompt.addRow("User template:", dialog._openrouter_user_prompt)
    layout.addWidget(grp_prompt)

    grp_languages, fl_languages = dialog._group_form("Language Injection")
    lbl_lang = QLabel("Add custom language code/name pairs for OpenRouter. ")
    lbl_lang.setWordWrap(True)
    fl_languages.addRow(lbl_lang)
    dialog._openrouter_custom_code = LineEdit()
    dialog._openrouter_custom_code.setPlaceholderText("Code, e.g. tlh")
    dialog._openrouter_custom_name = LineEdit()
    dialog._openrouter_custom_name.setPlaceholderText("Display name, e.g. Klingon")
    dialog._btn_openrouter_add_custom = PushButton("Add / Update")
    dialog._btn_openrouter_add_custom.clicked.connect(
        lambda: _add_openrouter_custom_language(dialog)
    )
    fl_languages.addRow("Custom code:", dialog._openrouter_custom_code)
    fl_languages.addRow("Custom name:", dialog._openrouter_custom_name)
    fl_languages.addRow("", dialog._btn_openrouter_add_custom)
    dialog._lbl_openrouter_custom_hint = QLabel(
        "Default languages come from Google Translate List. Only custom rows can be deleted."
    )
    dialog._lbl_openrouter_custom_hint.setWordWrap(True)
    fl_languages.addRow(dialog._lbl_openrouter_custom_hint)

    dialog._openrouter_language_search = LineEdit()
    dialog._openrouter_language_search.setPlaceholderText(
        "Search by language code, name, or source…"
    )
    dialog._openrouter_language_search.textChanged.connect(
        lambda text: _filter_openrouter_language_table(dialog, text)
    )
    fl_languages.addRow(dialog._openrouter_language_search)

    dialog._tbl_openrouter_languages = TableWidget()
    dialog._tbl_openrouter_languages.setColumnCount(4)
    dialog._tbl_openrouter_languages.setHorizontalHeaderLabels(
        ["Code", "Name", "Source", "Action"]
    )
    dialog._tbl_openrouter_languages.setRowCount(0)
    dialog._tbl_openrouter_languages.verticalHeader().setVisible(False)
    header = dialog._tbl_openrouter_languages.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
    dialog._tbl_openrouter_languages.setMinimumHeight(220)
    dialog._tbl_openrouter_languages.setSortingEnabled(True)
    _refresh_openrouter_language_table(dialog)
    fl_languages.addRow(dialog._tbl_openrouter_languages)

    layout.addWidget(grp_languages)
    layout.addStretch()
    return page
