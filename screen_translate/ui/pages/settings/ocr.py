"""OCR settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtWidgets import QFormLayout, QGroupBox, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import ComboBox, PushButton

from .common import (
    bind_check_with_callback,
    bind_combo_with_callback,
    bind_line_with_callback,
    bind_spin,
)
from .ocr_overrides import refresh_ocr_override_table


@pyqtSlot(str)
def on_ocr_backend_changed(dialog: Any, name: str) -> None:
    """Persist OCR backend selection and refresh OCR-dependent UI."""
    dialog.controller.set_active_ocr_backend(name)
    if dialog.controller.main_window:
        dialog.controller.main_window.refresh_ocr_compatibility_state()
    if hasattr(dialog, "_cb_override_backend"):
        refresh_ocr_override_table(dialog, dialog._cb_override_backend.currentText())


def browse_tesseract(dialog: Any) -> None:
    """Open a file dialog to locate the tesseract executable."""
    path, _ = QFileDialog.getOpenFileName(dialog, "Locate Tesseract Executable")
    if path:
        dialog._tes_path.setText(path)
        dialog.controller.reset_ocr_backend()


def build_ocr_page(dialog: Any) -> QWidget:
    """Build the OCR settings page."""
    w = QWidget()
    vl = QVBoxLayout(w)

    grp_engine, fl_engine = dialog._group_form("Tesseract")
    dialog._cb_ocr_backend = ComboBox()
    dialog._cb_ocr_backend.addItems(dialog.controller.available_ocr_backend_names())
    saved_ocr_backend = str(dialog.s.get("ocr_backend", "Tesseract"))
    idx_ocr_backend = dialog._cb_ocr_backend.findText(saved_ocr_backend)
    dialog._cb_ocr_backend.setCurrentIndex(max(0, idx_ocr_backend))
    dialog._cb_ocr_backend.currentTextChanged.connect(
        lambda name: on_ocr_backend_changed(dialog, name)
    )
    fl_engine.addRow("OCR backend:", dialog._cb_ocr_backend)

    row = QHBoxLayout()
    dialog._tes_path = bind_line_with_callback(
        "tesseract_loc",
        dialog.s,
        dialog.controller.reset_ocr_backend,
        "Leave empty to use system PATH",
    )
    row.addWidget(dialog._tes_path)
    btn_browse = PushButton("Browse…")
    btn_browse.clicked.connect(lambda: browse_tesseract(dialog))
    row.addWidget(btn_browse)
    fl_engine.addRow("Tesseract path:", row)

    fl_engine.addRow(
        "Extra config:",
        bind_line_with_callback(
            "tesseract_config",
            dialog.s,
            dialog.controller.reset_ocr_backend,
            "--psm 6",
        ),
    )
    fl_engine.addRow(
        bind_check_with_callback(
            "tesseract_psm5_vertical",
            "Auto PSM 5 for vertical scripts",
            dialog.s,
            dialog.controller.reset_ocr_backend,
        )
    )
    fl_engine.addRow(
        bind_check_with_callback(
            "enhance_with_grayscale",
            "Grayscale + autocontrast preprocessing",
            dialog.s,
            dialog.controller.reset_ocr_backend,
        )
    )
    fl_engine.addRow(
        bind_check_with_callback(
            "enhance_with_cv2_contour",
            "Use OpenCV contour text detection",
            dialog.s,
            dialog.controller.reset_ocr_backend,
        )
    )
    fl_engine.addRow(
        bind_check_with_callback(
            "save_cv2_contour_image",
            "Save OpenCV contoured debug image",
            dialog.s,
            dialog.controller.reset_ocr_backend,
        )
    )
    fl_engine.addRow(
        "Background type:",
        bind_combo_with_callback(
            "enhance_background",
            ["Auto-Detect", "Light", "Dark"],
            dialog.s,
            dialog.controller.reset_ocr_backend,
        ),
    )
    vl.addWidget(grp_engine)

    grp = QGroupBox("Capture Offset Correction")
    grp_f = QFormLayout(grp)
    grp_f.addRow("Offset X:", bind_spin("offSetX", dialog.s, -500, 500))
    grp_f.addRow("Offset Y:", bind_spin("offSetY", dialog.s, -500, 500))
    grp_f.addRow("Offset W:", bind_spin("offSetW", dialog.s, -500, 500))
    grp_f.addRow("Offset H:", bind_spin("offSetH", dialog.s, -500, 500))
    vl.addWidget(grp)
    vl.addStretch()
    return w
