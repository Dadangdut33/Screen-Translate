"""Capture settings page."""

from __future__ import annotations

import sys
from typing import Any

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from .common import bind_check, bind_combo, bind_combo_with_callback


def refresh_capture_window_ui(dialog: Any) -> None:
    """Apply capture-mode UI changes immediately to the capture window."""
    if dialog.controller.capture_window:
        dialog.controller.capture_window._sync_mode_ui()


def build_capture_page(dialog: Any) -> QWidget:
    """Build the Capture settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)

    grp_mode, fl_mode = dialog._group_form("Capture Backend")
    fl_mode.addRow(
        "Capture mode for capture window:",
        bind_combo_with_callback(
            "capture_mode",
            ["Floating Window", "Virtual Overlay"],
            dialog.s,
            lambda: refresh_capture_window_ui(dialog),
        ),
    )
    if sys.platform.startswith("linux"):
        fl_mode.addRow(
            "Capture backend:",
            bind_combo(
                "capture_backend",
                ["Auto", "Spectacle", "GNOME Shell", "grim"],
                dialog.s,
            ),
        )
    fl_mode.addRow(bind_check("keep_image", "Save captured images to disk", dialog.s))
    fl_mode.addRow(
        bind_check(
            "save_cropped_image", "Also save the final cropped capture", dialog.s
        )
    )
    fl_mode.addRow(
        bind_check(
            "suppress_missing_capture_file_errors",
            "Suppress missing-file errors from external capture tools",
            dialog.s,
        )
    )
    vl.addWidget(grp_mode)

    grp_visibility, fl_visibility = dialog._group_form("Window Visibility")
    fl_visibility.addRow(
        bind_check("hide_mw_on_cap", "Hide main window during capture", dialog.s)
    )
    fl_visibility.addRow(
        bind_check("hide_ex_qw_on_cap", "Hide query window during capture", dialog.s)
    )
    fl_visibility.addRow(
        bind_check("hide_ex_resw_on_cap", "Hide result window during capture", dialog.s)
    )
    fl_visibility.addRow(
        bind_check(
            "show_query_window_after_capture",
            "Show query window after capture",
            dialog.s,
        )
    )
    fl_visibility.addRow(
        bind_check(
            "show_result_window_after_capture",
            "Show result window after capture",
            dialog.s,
        )
    )
    vl.addWidget(grp_visibility)
    vl.addStretch()
    return w
