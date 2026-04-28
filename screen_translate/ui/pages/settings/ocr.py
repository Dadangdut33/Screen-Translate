"""OCR settings page."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QFileDialog, QVBoxLayout, QWidget
from qfluentwidgets import ComboBox, PushButton

from screen_translate.ui.widgets import (
    SettingsCardGroup,
    WidgetSettingCard,
    load_qta_icon,
    make_row_widget,
    make_switch_setting_card,
)

from .common import (
    bind_combo_with_callback,
    bind_line_with_callback,
    bind_spin,
)
from .ocr_overrides import refresh_ocr_override_table


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
    vl.setContentsMargins(0, 0, 0, 0)
    vl.setSpacing(12)

    grp_engine = SettingsCardGroup("Tesseract", w)

    dialog._cb_ocr_backend = ComboBox()
    dialog._cb_ocr_backend.addItems(dialog.controller.available_ocr_backend_names())
    saved_ocr_backend = str(dialog.s.get("ocr_backend", "Tesseract"))
    idx_ocr_backend = dialog._cb_ocr_backend.findText(saved_ocr_backend)
    dialog._cb_ocr_backend.setCurrentIndex(max(0, idx_ocr_backend))
    dialog._cb_ocr_backend.currentTextChanged.connect(
        lambda name: on_ocr_backend_changed(dialog, name)
    )
    grp_engine.addSettingCard(
        WidgetSettingCard(
            load_qta_icon("mdi6.text-recognition"),
            "OCR backend",
            "Choose which OCR engine Screen Translate should use.",
            dialog._cb_ocr_backend,
            grp_engine,
        )
    )

    dialog._tes_path = bind_line_with_callback(
        "tesseract_loc",
        dialog.s,
        dialog.controller.reset_ocr_backend,
        "Leave empty to use system PATH",
    )
    btn_browse = PushButton("Browse…")
    btn_browse.clicked.connect(lambda: browse_tesseract(dialog))
    grp_engine.addSettingCard(
        WidgetSettingCard(
            load_qta_icon("mdi6.file-find-outline"),
            "Tesseract path",
            "Point to a specific Tesseract executable, or leave empty to use PATH.",
            make_row_widget(dialog._tes_path, btn_browse, stretch_first=False),
            grp_engine,
        )
    )

    grp_engine.addSettingCard(
        WidgetSettingCard(
            load_qta_icon("mdi6.tune"),
            "Extra config",
            "Pass additional Tesseract command-line options.",
            bind_line_with_callback(
                "tesseract_config",
                dialog.s,
                dialog.controller.reset_ocr_backend,
                "--psm 6",
            ),
            grp_engine,
        )
    )

    grp_engine.addSettingCards(
        [
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.format-text-rotation-angle-up"),
                title="Auto PSM 5 for vertical scripts",
                content="Automatically use a layout mode better suited for vertical text.",
                checked=bool(dialog.s.get("tesseract_psm5_vertical", False)),
                on_changed=lambda _value: (
                    dialog.s.set("tesseract_psm5_vertical", _value),
                    dialog.controller.reset_ocr_backend(),
                ),
                parent=grp_engine,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.image-filter-hdr"),
                title="Grayscale + autocontrast preprocessing",
                content="Preprocess the image before OCR to improve readability.",
                checked=bool(dialog.s.get("enhance_with_grayscale", False)),
                on_changed=lambda _value: (
                    dialog.s.set("enhance_with_grayscale", _value),
                    dialog.controller.reset_ocr_backend(),
                ),
                parent=grp_engine,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.vector-polyline"),
                title="Use OpenCV contour text detection",
                content="Use OpenCV contour detection to isolate text regions before OCR.",
                checked=bool(dialog.s.get("enhance_with_cv2_contour", False)),
                on_changed=lambda _value: (
                    dialog.s.set("enhance_with_cv2_contour", _value),
                    dialog.controller.reset_ocr_backend(),
                ),
                parent=grp_engine,
            ),
            make_switch_setting_card(
                icon=load_qta_icon("mdi6.bug-outline"),
                title="Save OpenCV contoured debug image",
                content="Save the intermediate OpenCV contour result for debugging.",
                checked=bool(dialog.s.get("save_cv2_contour_image", False)),
                on_changed=lambda _value: (
                    dialog.s.set("save_cv2_contour_image", _value),
                    dialog.controller.reset_ocr_backend(),
                ),
                parent=grp_engine,
            ),
        ]
    )

    grp_engine.addSettingCard(
        WidgetSettingCard(
            load_qta_icon("mdi6.invert-colors"),
            "Background type",
            "Tell OCR whether the image background should be treated as light, dark, or auto-detected.",
            bind_combo_with_callback(
                "enhance_background",
                ["Auto-Detect", "Light", "Dark"],
                dialog.s,
                dialog.controller.reset_ocr_backend,
            ),
            grp_engine,
        )
    )
    vl.addWidget(grp_engine)

    grp_offset = SettingsCardGroup("Capture Offset Correction", w)
    grp_offset.addSettingCards(
        [
            WidgetSettingCard(
                load_qta_icon("mdi6.axis-x-arrow"),
                "Offset X",
                "Horizontal offset correction applied to capture coordinates.",
                bind_spin("offSetX", dialog.s, -500, 500),
                grp_offset,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.axis-y-arrow"),
                "Offset Y",
                "Vertical offset correction applied to capture coordinates.",
                bind_spin("offSetY", dialog.s, -500, 500),
                grp_offset,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.arrow-expand-horizontal"),
                "Offset W",
                "Width correction applied to the captured region.",
                bind_spin("offSetW", dialog.s, -500, 500),
                grp_offset,
            ),
            WidgetSettingCard(
                load_qta_icon("mdi6.arrow-expand-vertical"),
                "Offset H",
                "Height correction applied to the captured region.",
                bind_spin("offSetH", dialog.s, -500, 500),
                grp_offset,
            ),
        ]
    )
    vl.addWidget(grp_offset)
    vl.addStretch()
    return w
