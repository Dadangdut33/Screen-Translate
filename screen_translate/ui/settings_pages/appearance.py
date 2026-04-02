"""Appearance settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from qt_material import list_themes

from .common import bind_spin


@pyqtSlot(str)
def on_theme_changed(dialog: Any, theme: str) -> None:
    """Persist and apply a qt-material theme."""
    dialog.s.set("theme", theme)
    app = QApplication.instance()
    if app is None:
        return
    dialog._show_theme_overlay()
    try:
        from qt_material import apply_stylesheet

        app.setStyle("Fusion")
        apply_stylesheet(app, theme=theme)
        dialog._schedule_nav_style_refresh(50)
    except ImportError:
        dialog._logger.warning(
            "qt-material is not installed - theme change saved for later"
        )
    except Exception as exc:
        dialog._logger.warning("Could not apply theme %s: %s", theme, exc)
    finally:
        dialog._hide_theme_overlay()


def color_picker_row(dialog: Any, key: str) -> QPushButton:
    """Create a colour-picker button tied to a settings key."""
    btn = QPushButton()
    btn.setFixedWidth(60)

    def apply_button_color(color: QColor) -> None:
        btn.setProperty("selectedColor", color)
        btn.setStyleSheet(f"background-color: {color.name()};")

    stored = QColor(str(dialog.s.get(key, "#000000")))
    apply_button_color(stored if stored.isValid() else QColor("#000000"))

    def pick() -> None:
        current = btn.property("selectedColor")
        initial = (
            current
            if isinstance(current, QColor) and current.isValid()
            else QColor("#000000")
        )
        col = QColorDialog.getColor(initial, dialog, "Select Colour")
        if col.isValid():
            dialog.s.set(key, col.name())
            apply_button_color(col)

    btn.clicked.connect(pick)
    return btn


def build_appearance_page(dialog: Any) -> QWidget:
    """Build the Appearance settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)

    grp_theme, fl_theme = dialog._group_form("Theme")
    dialog._cb_theme = QComboBox()
    dialog._cb_theme.addItems(list_themes())
    saved_theme = str(dialog.s.get("theme", "dark_teal.xml"))
    idx_theme = dialog._cb_theme.findText(saved_theme)
    dialog._cb_theme.setCurrentIndex(max(0, idx_theme))
    dialog._cb_theme.currentTextChanged.connect(
        lambda theme: on_theme_changed(dialog, theme)
    )
    fl_theme.addRow("Theme:", dialog._cb_theme)
    fl_theme.addRow(
        QLabel("qt-material themes apply immediately when the package is installed.")
    )
    vl.addWidget(grp_theme)

    grp_query, fl_query = dialog._group_form("Query Window")
    fl_query.addRow("Font size:", bind_spin("tb_ex_q_font_size", dialog.s, 6, 72))
    fl_query.addRow("Font color:", color_picker_row(dialog, "tb_ex_q_font_color"))
    fl_query.addRow("Background:", color_picker_row(dialog, "tb_ex_q_bg_color"))
    vl.addWidget(grp_query)

    grp_result, fl_result = dialog._group_form("Result Window")
    fl_result.addRow("Font size:", bind_spin("tb_ex_res_font_size", dialog.s, 6, 72))
    fl_result.addRow("Font color:", color_picker_row(dialog, "tb_ex_res_font_color"))
    fl_result.addRow("Background:", color_picker_row(dialog, "tb_ex_res_bg_color"))
    vl.addWidget(grp_result)

    grp_mask, fl_mask = dialog._group_form("Mask Window")
    fl_mask.addRow(
        "Background color:", color_picker_row(dialog, "mask_window_bg_color")
    )
    vl.addWidget(grp_mask)
    vl.addStretch()
    return w
