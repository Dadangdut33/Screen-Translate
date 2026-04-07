"""General settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from .common import bind_check, bind_combo, bind_line, bind_spin


def build_general_page(dialog: Any) -> QWidget:
    """Build the General settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)

    grp_app, fl_app = dialog._group_form("App Behavior")
    fl_app.addRow(
        bind_check("checkUpdateOnStart", "Check for updates on startup", dialog.s)
    )
    vl.addWidget(grp_app)

    grp_clipboard, fl_clipboard = dialog._group_form("Clipboard and History")
    fl_clipboard.addRow(
        bind_check(
            "auto_copy_captured", "Auto-copy captured text to clipboard", dialog.s
        )
    )
    fl_clipboard.addRow(
        bind_check(
            "auto_copy_translated", "Auto-copy translated text to clipboard", dialog.s
        )
    )
    fl_clipboard.addRow(
        bind_check("save_history", "Save translation history", dialog.s)
    )
    fl_clipboard.addRow(
        bind_check(
            "supress_no_text_alert", "Suppress 'no text detected' alert", dialog.s
        )
    )
    vl.addWidget(grp_clipboard)

    grp_text, fl_text = dialog._group_form("Text Processing")
    fl_text.addRow(
        bind_check("replaceNewLine", "Enable newline replacement", dialog.s)
    )
    fl_text.addRow(
        "Replace newlines with:",
        bind_line("replaceNewLineWith", dialog.s, "e.g.  (space)"),
    )
    vl.addWidget(grp_text)

    grp_logging, fl_logging = dialog._group_form("Logging")
    fl_logging.addRow(bind_check("keep_log", "Write log file to disk", dialog.s))
    fl_logging.addRow(
        bind_check(
            "suppress_third_party_loggers",
            "Suppress noisy third-party loggers",
            dialog.s,
        )
    )
    fl_logging.addRow(
        "Log level:",
        bind_combo("log_level", ["DEBUG", "INFO", "WARNING", "ERROR"], dialog.s),
    )
    fl_logging.addRow(
        "Max log rotation (days):",
        bind_spin("max_log_rotation_days", dialog.s, 1, 365),
    )
    vl.addWidget(grp_logging)
    vl.addStretch()
    return w
