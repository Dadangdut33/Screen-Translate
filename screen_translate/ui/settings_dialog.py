"""Settings dialog - every widget writes immediately via QSettings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
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

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)


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
        self._tes_path = QLineEdit(str(self.s.get("tesseract_loc", "")))
        self._tes_path.setPlaceholderText("Leave empty to use system PATH")
        self._tes_path.textChanged.connect(lambda v: self.s.set("tesseract_loc", v))
        row.addWidget(self._tes_path)
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._browse_tesseract)
        row.addWidget(btn_browse)
        fl.addRow("Tesseract path:", row)

        fl.addRow("Extra config:", _bind_line("tesseract_config", self.s, "--psm 6"))
        fl.addRow(_bind_check("tesseract_psm5_vertical", "Auto PSM 5 for vertical scripts", self.s))
        fl.addRow(_bind_check("enhance_with_grayscale", "Grayscale + autocontrast preprocessing", self.s))

        # Offset corrections
        grp = QGroupBox("Capture Offset Correction")
        grp_f = QFormLayout(grp)
        grp_f.addRow("Offset X:", _bind_spin("offSetX", self.s, -500, 500))
        grp_f.addRow("Offset Y:", _bind_spin("offSetY", self.s, -500, 500))
        grp_f.addRow("Offset W:", _bind_spin("offSetW", self.s, -500, 500))
        grp_f.addRow("Offset H:", _bind_spin("offSetH", self.s, -500, 500))
        fl.addRow(grp)

        # Background hint
        fl.addRow("Background type:", _bind_combo("enhance_background", ["Auto-Detect", "Light", "Dark"], self.s))

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
        saved = self.s.get("engine", "Google Translate")
        idx = self._cb_backend.findText(saved)
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
