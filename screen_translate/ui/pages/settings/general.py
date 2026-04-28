"""General settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from screen_translate.ui.widgets import (
    SettingsCardGroup,
    WidgetSettingCard,
    load_qta_icon,
    make_switch_setting_card,
)

from .common import bind_combo, bind_line, bind_spin


def build_general_page(dialog: Any) -> QWidget:
    """Build the General settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)
    vl.setContentsMargins(0, 0, 0, 0)
    vl.setSpacing(12)

    grp_app = SettingsCardGroup("App Behavior", w)
    grp_app.addSettingCard(
        make_switch_setting_card(
            icon=load_qta_icon("mdi6.update"),
            title="Check for updates on startup",
            content="Look for newer app releases when Screen Translate launches.",
            checked=bool(dialog.s.get("checkUpdateOnStart", False)),
            on_changed=lambda value: dialog.s.set("checkUpdateOnStart", value),
            parent=grp_app,
        )
    )
    vl.addWidget(grp_app)

    grp_clipboard = SettingsCardGroup("Clipboard and History", w)
    grp_clipboard.addSettingCards(
        [
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.content-copy"),
                title="Auto-copy captured text",
                content="Copy OCR text to the clipboard right after capture.",
                checked=bool(dialog.s.get("auto_copy_captured", False)),
                on_changed=lambda value: dialog.s.set("auto_copy_captured", value),
                parent=grp_clipboard,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.translate"),
                title="Auto-copy translated text",
                content="Copy the translation result to the clipboard automatically.",
                checked=bool(dialog.s.get("auto_copy_translated", False)),
                on_changed=lambda value: dialog.s.set("auto_copy_translated", value),
                parent=grp_clipboard,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.history"),
                title="Save translation history",
                content="Keep past OCR and translation results for later review.",
                checked=bool(dialog.s.get("save_history", False)),
                on_changed=lambda value: dialog.s.set("save_history", value),
                parent=grp_clipboard,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.bell-off-outline"),
                title="Suppress no-text alert",
                content="Hide the warning when OCR does not detect any text.",
                checked=bool(dialog.s.get("supress_no_text_alert", False)),
                on_changed=lambda value: dialog.s.set("supress_no_text_alert", value),
                parent=grp_clipboard,
            ),
        ]
    )
    vl.addWidget(grp_clipboard)

    grp_text = SettingsCardGroup("Text Processing", w)
    grp_text.addSettingCard(
        make_switch_setting_card(
            icon=load_qta_icon("mdi6.wrap"),
            title="Enable newline replacement",
            content="Replace line breaks in OCR text before translation.",
            checked=bool(dialog.s.get("replaceNewLine", False)),
            on_changed=lambda value: dialog.s.set("replaceNewLine", value),
            parent=grp_text,
        )
    )
    grp_text.addSettingCard(
        WidgetSettingCard(
            load_qta_icon("mdi6.format-line-spacing"),
            "Replace newlines with",
            "Choose the text inserted where line breaks are removed.",
            bind_line("replaceNewLineWith", dialog.s, "e.g.  (space)"),
            grp_text,
        )
    )
    vl.addWidget(grp_text)

    grp_logging = SettingsCardGroup("Logging", w)
    grp_logging.addSettingCards(
        [
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.file-document-outline"),
                title="Write log file to disk",
                content="Store runtime logs so issues are easier to inspect later.",
                checked=bool(dialog.s.get("keep_log", False)),
                on_changed=lambda value: dialog.s.set("keep_log", value),
                parent=grp_logging,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.filter-minus-outline"),
                title="Suppress third-party loggers",
                content="Reduce noisy logs from external libraries.",
                checked=bool(dialog.s.get("suppress_third_party_loggers", False)),
                on_changed=lambda value: dialog.s.set(
                    "suppress_third_party_loggers", value
                ),
                parent=grp_logging,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.math-log"),
                "Log level",
                "Choose how verbose the app log should be.",
                bind_combo(
                    "log_level", ["DEBUG", "INFO", "WARNING", "ERROR"], dialog.s
                ),
                grp_logging,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.calendar-clock"),
                "Log rotation days",
                "Automatically remove old log files after this many days.",
                bind_spin("max_log_rotation_days", dialog.s, 1, 365),
                grp_logging,
            ),
        ]
    )
    vl.addWidget(grp_logging)
    vl.addStretch()
    return w
