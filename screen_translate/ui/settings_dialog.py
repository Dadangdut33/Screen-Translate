"""Settings dialog - every widget writes immediately via QSettings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from screen_translate.core.translation.translators_backend import configure_translators_region

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)

_QT_MATERIAL_THEMES: list[str] = [
    "dark_teal.xml",
    "dark_blue.xml",
    "dark_amber.xml",
    "light_blue.xml",
    "light_cyan_500.xml",
    "light_amber.xml",
]


# ---------------------------------------------------------------------------
# Helper - create a widget and immediately wire it to persist its value
# ---------------------------------------------------------------------------


def _bind_check(key: str, label: str, settings: Any) -> QCheckBox:
    """Create a QCheckBox pre-filled from QSettings and wired for auto-save.

    Args:
        key: Settings key.
        label: Checkbox label text.
        settings: SettingsManager instance.

    Returns:
        Configured QCheckBox.
    """
    cb = QCheckBox(label)
    cb.setChecked(bool(settings.get(key, False)))
    cb.toggled.connect(lambda v: settings.set(key, v))
    return cb


def _bind_line(key: str, settings: Any, placeholder: str = "") -> QLineEdit:
    """Create a QLineEdit pre-filled from QSettings and wired for auto-save.

    Args:
        key: Settings key.
        settings: SettingsManager instance.
        placeholder: Placeholder text.

    Returns:
        Configured QLineEdit.
    """
    le = QLineEdit()
    le.setText(str(settings.get(key, "")))
    le.setPlaceholderText(placeholder)
    le.textChanged.connect(lambda v: settings.set(key, v))
    return le


def _bind_spin(key: str, settings: Any, min_val: int = 0, max_val: int = 9999) -> QSpinBox:
    """Create a QSpinBox pre-filled from QSettings and wired for auto-save.

    Args:
        key: Settings key.
        settings: SettingsManager instance.
        min_val: Minimum spin value.
        max_val: Maximum spin value.

    Returns:
        Configured QSpinBox.
    """
    sb = QSpinBox()
    sb.setRange(min_val, max_val)
    sb.setValue(int(settings.get(key, 0)))
    sb.valueChanged.connect(lambda v: settings.set(key, v))
    return sb


def _bind_combo(key: str, items: list[str], settings: Any) -> QComboBox:
    """Create a QComboBox pre-filled from QSettings and wired for auto-save.

    Args:
        key: Settings key.
        items: Items to populate.
        settings: SettingsManager instance.

    Returns:
        Configured QComboBox.
    """
    cb = QComboBox()
    cb.addItems(items)
    saved = settings.get(key, "")
    idx = cb.findText(str(saved))
    cb.setCurrentIndex(max(0, idx))
    cb.currentTextChanged.connect(lambda v: settings.set(key, v))
    return cb


def _bind_check_with_callback(
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


def _bind_line_with_callback(
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


def _bind_combo_with_callback(
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


class SettingsDialog(QDialog):
    """Application settings editor.

    All changes are persisted immediately. Widgets are organised in a tabbed layout.
    """

    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        """Create the settings dialog.

        Args:
            controller: Application controller.
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self.controller = controller
        self.s = controller.settings

        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._tab_general(), "General")
        tabs.addTab(self._tab_ocr(), "OCR")
        tabs.addTab(self._tab_translation(), "Translation")
        tabs.addTab(self._tab_hotkeys(), "Hotkeys")
        tabs.addTab(self._tab_appearance(), "Appearance")
        layout.addWidget(tabs)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.hide)
        layout.addWidget(btn_box)

    # ------------------------------------------------------------------
    # Tab: General
    # ------------------------------------------------------------------

    def _tab_general(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)

        fl.addRow(_bind_check("keep_image", "Save captured images to disk", self.s))
        fl.addRow(_bind_check("save_cropped_image", "Also save the final cropped capture", self.s))
        fl.addRow(_bind_check("auto_copy_captured", "Auto-copy captured text to clipboard", self.s))
        fl.addRow(_bind_check("auto_copy_translated", "Auto-copy translated text to clipboard", self.s))
        fl.addRow(_bind_check("save_history", "Save translation history", self.s))
        fl.addRow(_bind_check("supress_no_text_alert", "Suppress 'no text detected' alert", self.s))
        fl.addRow(_bind_check("hide_mw_on_cap", "Hide main window during capture", self.s))
        fl.addRow(_bind_check("hide_ex_qw_on_cap", "Hide query window during capture", self.s))
        fl.addRow(_bind_check("hide_ex_resw_on_cap", "Hide result window during capture", self.s))
        fl.addRow(_bind_check("keep_log", "Write log file to disk", self.s))

        fl.addRow("Log level:", _bind_combo("log_level", ["DEBUG", "INFO", "WARNING", "ERROR"], self.s))
        fl.addRow("Replace newlines with:", _bind_line("replaceNewLineWith", self.s, "e.g.  (space)"))
        fl.addRow(_bind_check("replaceNewLine", "Enable newline replacement", self.s))

        return w

    # ------------------------------------------------------------------
    # Tab: OCR
    # ------------------------------------------------------------------

    def _tab_ocr(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)

        # Tesseract path
        row = QHBoxLayout()
        self._tes_path = _bind_line_with_callback(
            "tesseract_loc",
            self.s,
            self.controller.reset_ocr_backend,
            "Leave empty to use system PATH",
        )
        row.addWidget(self._tes_path)
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._browse_tesseract)
        row.addWidget(btn_browse)
        fl.addRow("Tesseract path:", row)

        fl.addRow(
            "Extra config:",
            _bind_line_with_callback(
                "tesseract_config",
                self.s,
                self.controller.reset_ocr_backend,
                "--psm 6",
            ),
        )
        fl.addRow(
            _bind_check_with_callback(
                "tesseract_psm5_vertical",
                "Auto PSM 5 for vertical scripts",
                self.s,
                self.controller.reset_ocr_backend,
            )
        )
        fl.addRow(
            _bind_check_with_callback(
                "enhance_with_grayscale",
                "Grayscale + autocontrast preprocessing",
                self.s,
                self.controller.reset_ocr_backend,
            )
        )
        fl.addRow(
            _bind_check_with_callback(
                "enhance_with_cv2_contour",
                "Use OpenCV contour text detection",
                self.s,
                self.controller.reset_ocr_backend,
            )
        )
        fl.addRow(
            _bind_check_with_callback(
                "save_cv2_contour_image",
                "Save OpenCV contoured debug image",
                self.s,
                self.controller.reset_ocr_backend,
            )
        )

        # Offset corrections
        grp = QGroupBox("Capture Offset Correction")
        grp_f = QFormLayout(grp)
        grp_f.addRow("Offset X:", _bind_spin("offSetX", self.s, -500, 500))
        grp_f.addRow("Offset Y:", _bind_spin("offSetY", self.s, -500, 500))
        grp_f.addRow("Offset W:", _bind_spin("offSetW", self.s, -500, 500))
        grp_f.addRow("Offset H:", _bind_spin("offSetH", self.s, -500, 500))
        fl.addRow(grp)

        # Background hint
        fl.addRow(
            "Background type:",
            _bind_combo_with_callback(
                "enhance_background",
                ["Auto-Detect", "Light", "Dark"],
                self.s,
                self.controller.reset_ocr_backend,
            ),
        )
        fl.addRow(
            "Capture mode:",
            _bind_combo("capture_mode", ["Floating Window", "Virtual Overlay"], self.s),
        )

        return w

    # ------------------------------------------------------------------
    # Tab: Translation
    # ------------------------------------------------------------------

    def _tab_translation(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)

        # Backend selection (visual only - actual switch goes through controller)
        grp = QGroupBox("Active Backend")
        gfl = QFormLayout(grp)
        self._cb_backend = QComboBox()
        for name in self.controller.available_backend_names():
            self._cb_backend.addItem(name)
        saved = self.s.get("engine", "translators-google")
        idx = self._cb_backend.findText(saved)
        if idx < 0:
            idx = 0
        self._cb_backend.setCurrentIndex(max(0, idx))
        self._cb_backend.currentTextChanged.connect(self._on_backend_changed)
        gfl.addRow("Backend:", self._cb_backend)
        vl.addWidget(grp)

        # DeepL official key (shown only when DeepL official selected)
        self._grp_deepl = QGroupBox("DeepL Official API Key")
        deepl_fl = QFormLayout(self._grp_deepl)
        self._deepl_key = QLineEdit(str(self.s.get("deepl_api_key", "")))
        self._deepl_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._deepl_key.setPlaceholderText("Enter DEEPL_API_KEY…")
        self._deepl_key.textChanged.connect(lambda v: self.s.set("deepl_api_key", v))
        deepl_fl.addRow("API Key:", self._deepl_key)
        vl.addWidget(self._grp_deepl)

        # LibreTranslate settings
        grp_libre = QGroupBox("LibreTranslate Server")
        libre_fl = QFormLayout(grp_libre)
        libre_fl.addRow("Host:", _bind_line("libre_host", self.s, "translate.argosopentech.com"))
        libre_fl.addRow("Port:", _bind_line("libre_port", self.s, "5000 or blank"))
        libre_fl.addRow(_bind_check("libre_https", "Use HTTPS", self.s))
        libre_fl.addRow("API Key:", _bind_line("libre_api_key", self.s, "optional"))
        vl.addWidget(grp_libre)

        self._cb_translators_region = QComboBox()
        self._cb_translators_region.addItems(["EN", "CN", "Auto"])
        saved_region = str(self.s.get("translators_region", "EN"))
        idx_region = self._cb_translators_region.findText(saved_region)
        self._cb_translators_region.setCurrentIndex(max(0, idx_region))
        self._cb_translators_region.currentTextChanged.connect(self._on_translators_region_changed)
        gfl.addRow("translators region:", self._cb_translators_region)

        self._update_deepl_visibility(self._cb_backend.currentText())
        vl.addStretch()
        return w

    @pyqtSlot(str)
    def _on_backend_changed(self, name: str) -> None:
        """Switch active backend and update API key visibility."""
        self.controller.set_active_backend(name)
        self._update_deepl_visibility(name)
        # Refresh language combos in main window
        if self.controller.main_window:
            self.controller.main_window._refresh_lang_combos()

    def _update_deepl_visibility(self, name: str) -> None:
        """Show DeepL key field only when the official backend is selected."""
        self._grp_deepl.setVisible("deepl" in name.lower() and "official" in name.lower())

    @pyqtSlot(str)
    def _on_translators_region_changed(self, region: str) -> None:
        """Persist and apply the translators region mode immediately."""
        self.s.set("translators_region", region)
        configure_translators_region(region)

    # ------------------------------------------------------------------
    # Tab: Hotkeys
    # ------------------------------------------------------------------

    def _tab_hotkeys(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)

        fl.addRow(
            QLabel(
                "Hotkeys require the 'keyboard' package and may need root on Linux.\n"
                "Leave blank to disable."
            )
        )
        fl.addRow("Snip & Translate:", _bind_line("hk_snip_cap", self.s, "ctrl+alt+t"))
        fl.addRow("Snip delay (ms):", _bind_spin("hk_snip_cap_delay", self.s, 0, 5000))
        fl.addRow("Capture Window:", _bind_line("hk_cap_window", self.s, "e.g. ctrl+alt+c"))
        fl.addRow("Capture delay (ms):", _bind_spin("hk_cap_window_delay", self.s, 0, 5000))
        return w

    # ------------------------------------------------------------------
    # Tab: Appearance
    # ------------------------------------------------------------------

    def _tab_appearance(self) -> QWidget:
        w = QWidget()
        fl = QFormLayout(w)

        self._cb_theme = QComboBox()
        self._cb_theme.addItems(_QT_MATERIAL_THEMES)
        saved_theme = str(self.s.get("theme", "dark_teal.xml"))
        idx_theme = self._cb_theme.findText(saved_theme)
        self._cb_theme.setCurrentIndex(max(0, idx_theme))
        self._cb_theme.currentTextChanged.connect(self._on_theme_changed)
        fl.addRow("Theme:", self._cb_theme)
        fl.addRow(QLabel("qt-material themes apply immediately when the package is installed."))

        fl.addRow(QLabel(""))
        fl.addRow(QLabel("Query Window (floating):"))
        fl.addRow("Font size:", _bind_spin("tb_ex_q_font_size", self.s, 6, 72))
        fl.addRow("Font color:", self._color_picker_row("tb_ex_q_font_color"))
        fl.addRow("Background:", self._color_picker_row("tb_ex_q_bg_color"))

        fl.addRow(QLabel(""))
        fl.addRow(QLabel("Result Window (floating):"))
        fl.addRow("Font size:", _bind_spin("tb_ex_res_font_size", self.s, 6, 72))
        fl.addRow("Font color:", self._color_picker_row("tb_ex_res_font_color"))
        fl.addRow("Background:", self._color_picker_row("tb_ex_res_bg_color"))

        fl.addRow(QLabel(""))
        fl.addRow(QLabel("Mask Window:"))
        fl.addRow("Background color:", self._color_picker_row("mask_window_bg_color"))
        return w

    @pyqtSlot(str)
    def _on_theme_changed(self, theme: str) -> None:
        """Persist and apply a qt-material theme."""
        self.s.set("theme", theme)
        app = QApplication.instance()
        if app is None:
            return
        try:
            from qt_material import apply_stylesheet

            app.setStyle("Fusion")
            apply_stylesheet(app, theme=theme)
        except ImportError:
            logger.warning("qt-material is not installed - theme change saved for later")
        except Exception as exc:
            logger.warning("Could not apply theme %s: %s", theme, exc)

    def _color_picker_row(self, key: str) -> QPushButton:
        """Create a colour-picker button tied to *key*.

        Args:
            key: Settings key for the colour (hex string).

        Returns:
            Configured QPushButton.
        """
        btn = QPushButton()
        current: str = str(self.s.get(key, "#000000"))
        btn.setStyleSheet(f"background-color: {current};")
        btn.setFixedWidth(60)

        def pick() -> None:
            col = QColorDialog.getColor(QColor(current), self, "Select Colour")
            if col.isValid():
                self.s.set(key, col.name())
                btn.setStyleSheet(f"background-color: {col.name()};")

        btn.clicked.connect(pick)
        return btn

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _browse_tesseract(self) -> None:
        """Open a file dialog to locate the tesseract executable."""
        path, _ = QFileDialog.getOpenFileName(self, "Locate Tesseract Executable")
        if path:
            self._tes_path.setText(path)
            self.controller.reset_ocr_backend()

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        self.show()
        self.raise_()
        self.activateWindow()
