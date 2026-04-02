"""Settings dialog - every widget writes immediately via QSettings."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

import pycountry
from PyQt6.QtCore import QEvent, QSize, Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
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
    QHeaderView,
    QProgressBar,
    QStackedWidget,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta

from screen_translate.core.ocr.language_compat import resolve_tesseract_language_code
from screen_translate.core.translation.translators_backend import (
    configure_translators_region,
)

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
_SETTINGS_NAV_ICONS: dict[str, str] = {
    "General": "mdi6.cog-outline",
    "Capture": "mdi6.camera-outline",
    "OCR": "mdi6.text-recognition",
    "OCR Key Override": "mdi6.key-variant",
    "Translation": "mdi6.translate",
    "Hotkeys": "mdi6.keyboard-outline",
    "Appearance": "mdi6.palette-outline",
}

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


def _bind_spin(
    key: str, settings: Any, min_val: int = 0, max_val: int = 9999
) -> QSpinBox:
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

    def __init__(
        self, controller: AppController, parent: QWidget | None = None
    ) -> None:
        """Create the settings dialog.

        Args:
            controller: Application controller.
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self.controller = controller
        self.s = controller.settings
        self._nav_panel: QWidget | None = None
        self._theme_overlay: QWidget | None = None
        self._nav_icon_cache: dict[tuple[str, str, str, str], QIcon] = {}
        self._nav_refresh_timer = QTimer(self)
        self._nav_refresh_timer.setSingleShot(True)
        self._nav_refresh_timer.timeout.connect(self._refresh_nav_style)

        self.setWindowTitle("Settings")
        self.setMinimumSize(900, 700)
        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(4)

        self._nav_panel = QWidget()
        self._nav_panel.setFixedWidth(220)
        nav_layout = QVBoxLayout(self._nav_panel)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(4)

        self._pages = QStackedWidget()
        self._nav_buttons = QButtonGroup(self)
        self._nav_buttons.setExclusive(True)

        pages = [
            ("General", self._tab_general()),
            ("Capture", self._tab_capture()),
            ("OCR", self._tab_ocr()),
            ("OCR Key Override", self._tab_ocr_overrides()),
            ("Translation", self._tab_translation()),
            ("Hotkeys", self._tab_hotkeys()),
            ("Appearance", self._tab_appearance()),
        ]

        for index, (label, page) in enumerate(pages):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("navItem", True)
            btn.setProperty("navLabel", label)
            btn.installEventFilter(self)
            btn.toggled.connect(
                lambda _checked, button=btn: self._update_nav_button_icon(button)
            )
            btn.setIconSize(QSize(18, 18))
            btn.clicked.connect(
                lambda _checked, i=index: self._pages.setCurrentIndex(i)
            )
            # decrease padding
            btn.setStyleSheet("padding-top: 2px; padding-bottom: 2px;")

            self._nav_buttons.addButton(btn, index)
            nav_layout.addWidget(btn)
            self._pages.addWidget(page)

        nav_layout.addStretch(1)
        first_button = self._nav_buttons.button(0)
        if first_button is not None:
            first_button.setChecked(True)
        self._pages.setCurrentIndex(0)
        self._schedule_nav_style_refresh()

        content_row.addWidget(self._nav_panel)
        content_row.addWidget(self._pages, 1)
        layout.addLayout(content_row)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.hide)
        layout.addWidget(btn_box)
        self._build_theme_overlay()

    def _build_theme_overlay(self) -> None:
        """Create a lightweight overlay shown while the app theme is updating."""
        overlay = QWidget(self)
        overlay.setObjectName("themeLoadingOverlay")
        overlay.hide()

        outer = QVBoxLayout(overlay)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        card = QWidget(overlay)
        card.setObjectName("themeLoadingCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(10)

        title = QLabel("Applying theme...", card)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("themeLoadingTitle")
        card_layout.addWidget(title)

        progress = QProgressBar(card)
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        progress.setFixedWidth(240)
        card_layout.addWidget(progress, 0, Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        outer.addStretch(1)

        self._theme_overlay = overlay
        self._sync_theme_overlay_style()
        overlay.setGeometry(self.rect())

    def _sync_theme_overlay_style(self) -> None:
        """Update the loading overlay colors from the current palette."""
        if self._theme_overlay is None:
            return
        palette = self.palette()
        window = palette.color(QPalette.ColorRole.Window)
        base = palette.color(QPalette.ColorRole.Base)
        text = palette.color(QPalette.ColorRole.WindowText)
        border = palette.color(QPalette.ColorRole.Mid)

        scrim = QColor(window)
        scrim.setAlpha(150)
        card_bg = QColor(base if base.isValid() else window)
        if window.lightnessF() < 0.5:
            card_bg = card_bg.lighter(112)
        else:
            card_bg = card_bg.darker(104)

        self._theme_overlay.setStyleSheet(
            f"""
            QWidget#themeLoadingOverlay {{
                background-color: {scrim.name(QColor.NameFormat.HexArgb)};
            }}
            QWidget#themeLoadingCard {{
                background-color: {card_bg.name(QColor.NameFormat.HexArgb)};
                border: 1px solid {border.name(QColor.NameFormat.HexArgb)};
                border-radius: 10px;
            }}
            QLabel#themeLoadingTitle {{
                color: {text.name(QColor.NameFormat.HexArgb)};
                font-size: 14px;
                font-weight: 600;
            }}
            """
        )

    def _show_theme_overlay(self) -> None:
        """Display the temporary theme-loading overlay."""
        if self._theme_overlay is None:
            return
        self._sync_theme_overlay_style()
        self._theme_overlay.setGeometry(self.rect())
        self._theme_overlay.raise_()
        self._theme_overlay.show()
        QApplication.processEvents()

    def _hide_theme_overlay(self) -> None:
        """Hide the temporary theme-loading overlay."""
        if self._theme_overlay is not None:
            self._theme_overlay.hide()

    def changeEvent(self, event: QEvent) -> None:
        """Refresh palette-aware styling when the active theme changes."""
        super().changeEvent(event)
        if event.type() in (QEvent.Type.PaletteChange, QEvent.Type.StyleChange):
            self._schedule_nav_style_refresh(25)

    def eventFilter(self, obj: Any, event: QEvent) -> bool:
        """Keep sidebar icons in sync with hover and checked state."""
        if isinstance(obj, QPushButton) and obj.property("navItem") is True:
            if event.type() in (
                QEvent.Type.Enter,
                QEvent.Type.Leave,
                QEvent.Type.HoverEnter,
                QEvent.Type.HoverLeave,
            ):
                self._update_nav_button_icon(obj)
        return super().eventFilter(obj, event)

    def _schedule_nav_style_refresh(self, delay_ms: int = 0) -> None:
        """Coalesce repeated sidebar restyles during palette/theme changes."""
        self._nav_refresh_timer.start(max(0, delay_ms))

    def _nav_state_colors(self) -> tuple[QColor, QColor, QColor]:
        """Return text, active, and hover colors for nav items."""
        palette = self.palette()
        text_color = palette.color(QPalette.ColorRole.WindowText)
        active_bg = palette.color(QPalette.ColorRole.Highlight)
        if active_bg.alpha() == 255:
            active_bg.setAlpha(245)
        active_text = QColor("#ffffff" if active_bg.lightnessF() < 0.58 else "#111111")
        if palette.color(QPalette.ColorRole.Window).lightnessF() < 0.5:
            hover_text = QColor(active_text)
        else:
            hover_bg = active_bg.lighter(112)
            hover_text = QColor(
                "#ffffff" if hover_bg.lightnessF() < 0.58 else "#111111"
            )
        return text_color, active_text, hover_text

    def _update_nav_button_icon(self, button: QPushButton) -> None:
        """Apply the correct icon color for one nav button."""
        label = button.property("navLabel")
        if not isinstance(label, str):
            return
        text_color, active_text, hover_text = self._nav_state_colors()
        if button.isChecked():
            icon_color = active_text
        elif button.underMouse():
            icon_color = hover_text
        else:
            icon_color = text_color
        icon = self._nav_icon(label, icon_color)
        if not icon.isNull():
            button.setIcon(icon)

    def _refresh_nav_style(self) -> None:
        """Apply sidebar colors derived from the current palette."""
        if self._nav_panel is None:
            return

        palette = self.palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        base_color = palette.color(QPalette.ColorRole.Base)
        panel_color = QColor(base_color if base_color.isValid() else window_color)
        border_color = palette.color(QPalette.ColorRole.Mid)
        text_color = palette.color(QPalette.ColorRole.WindowText)
        active_bg = palette.color(QPalette.ColorRole.Highlight)

        def _is_dark(color: QColor) -> bool:
            return color.lightnessF() < 0.5

        if _is_dark(window_color):
            panel_color = panel_color.lighter(118)
            border_color = border_color.lighter(135)
        else:
            panel_color = panel_color.darker(103)
            border_color = border_color.darker(110)

        if active_bg.alpha() == 255:
            active_bg.setAlpha(245)
        active_text = QColor("#ffffff" if active_bg.lightnessF() < 0.58 else "#111111")
        if _is_dark(window_color):
            hover_bg = QColor(active_bg)
            hover_text = QColor(active_text)
        else:
            hover_bg = active_bg.lighter(112)
            hover_text = QColor(
                "#ffffff" if hover_bg.lightnessF() < 0.58 else "#111111"
            )
        for button in self._nav_buttons.buttons():
            self._update_nav_button_icon(button)

        self._sync_theme_overlay_style()
        self._nav_panel.setStyleSheet(
            f"""
            QWidget {{
                background-color: {panel_color.name(QColor.NameFormat.HexArgb)};
                border: 1px solid {border_color.name(QColor.NameFormat.HexArgb)};
                border-radius: 6px;
            }}
            QPushButton[navItem="true"] {{
                border: 0;
                border-radius: 6px;
                padding: 12px 14px;
                text-align: left;
                font-weight: 600;
                background-color: transparent;
                color: {text_color.name(QColor.NameFormat.HexArgb)};
            }}
            QPushButton[navItem="true"]:hover {{
                background-color: {hover_bg.name(QColor.NameFormat.HexArgb)};
                color: {hover_text.name(QColor.NameFormat.HexArgb)};
            }}
            QPushButton[navItem="true"]:checked {{
                font-weight: 700;
                background-color: {active_bg.name(QColor.NameFormat.HexArgb)};
                color: {active_text.name(QColor.NameFormat.HexArgb)};
            }}
            """
        )

    # ------------------------------------------------------------------
    # Tab: General
    # ------------------------------------------------------------------

    def _tab_general(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)

        grp_behavior, fl_behavior = self._group_form("Behavior")
        fl_behavior.addRow(
            _bind_check(
                "auto_copy_captured", "Auto-copy captured text to clipboard", self.s
            )
        )
        fl_behavior.addRow(
            _bind_check(
                "auto_copy_translated", "Auto-copy translated text to clipboard", self.s
            )
        )
        fl_behavior.addRow(
            _bind_check("save_history", "Save translation history", self.s)
        )
        fl_behavior.addRow(
            _bind_check(
                "supress_no_text_alert", "Suppress 'no text detected' alert", self.s
            )
        )
        fl_behavior.addRow(
            "Replace newlines with:",
            _bind_line("replaceNewLineWith", self.s, "e.g.  (space)"),
        )
        fl_behavior.addRow(
            _bind_check("replaceNewLine", "Enable newline replacement", self.s)
        )
        vl.addWidget(grp_behavior)

        grp_logging, fl_logging = self._group_form("Logging")
        fl_logging.addRow(_bind_check("keep_log", "Write log file to disk", self.s))
        fl_logging.addRow(
            _bind_check(
                "suppress_third_party_loggers",
                "Suppress noisy third-party loggers",
                self.s,
            )
        )
        fl_logging.addRow(
            "Log level:",
            _bind_combo("log_level", ["DEBUG", "INFO", "WARNING", "ERROR"], self.s),
        )
        fl_logging.addRow(
            "Max log rotation (days):",
            _bind_spin("max_log_rotation_days", self.s, 1, 365),
        )
        vl.addWidget(grp_logging)
        vl.addStretch()
        return w

    def _tab_capture(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)

        grp_mode, fl_mode = self._group_form("Capture Backend")
        fl_mode.addRow(
            "Capture mode for capture window:",
            _bind_combo_with_callback(
                "capture_mode",
                ["Floating Window", "Virtual Overlay"],
                self.s,
                self._refresh_capture_window_ui,
            ),
        )
        if sys.platform.startswith("linux"):
            fl_mode.addRow(
                "Capture backend:",
                _bind_combo(
                    "capture_backend",
                    ["Auto", "Spectacle", "GNOME Shell", "grim"],
                    self.s,
                ),
            )
        fl_mode.addRow(
            _bind_check("keep_image", "Save captured images to disk", self.s)
        )
        fl_mode.addRow(
            _bind_check(
                "save_cropped_image", "Also save the final cropped capture", self.s
            )
        )
        fl_mode.addRow(
            _bind_check(
                "suppress_missing_capture_file_errors",
                "Suppress missing-file errors from external capture tools",
                self.s,
            )
        )
        vl.addWidget(grp_mode)

        grp_visibility, fl_visibility = self._group_form("Window Visibility")
        fl_visibility.addRow(
            _bind_check("hide_mw_on_cap", "Hide main window during capture", self.s)
        )
        fl_visibility.addRow(
            _bind_check("hide_ex_qw_on_cap", "Hide query window during capture", self.s)
        )
        fl_visibility.addRow(
            _bind_check(
                "hide_ex_resw_on_cap", "Hide result window during capture", self.s
            )
        )
        fl_visibility.addRow(
            _bind_check(
                "show_query_window_after_capture",
                "Show query window after capture",
                self.s,
            )
        )
        fl_visibility.addRow(
            _bind_check(
                "show_result_window_after_capture",
                "Show result window after capture",
                self.s,
            )
        )
        vl.addWidget(grp_visibility)
        vl.addStretch()
        return w

    # ------------------------------------------------------------------
    # Tab: OCR
    # ------------------------------------------------------------------

    def _tab_ocr(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)

        # Tesseract path
        grp_engine, fl_engine = self._group_form("Tesseract")
        self._cb_ocr_backend = QComboBox()
        self._cb_ocr_backend.addItems(self.controller.available_ocr_backend_names())
        saved_ocr_backend = str(self.s.get("ocr_backend", "Tesseract"))
        idx_ocr_backend = self._cb_ocr_backend.findText(saved_ocr_backend)
        self._cb_ocr_backend.setCurrentIndex(max(0, idx_ocr_backend))
        self._cb_ocr_backend.currentTextChanged.connect(self._on_ocr_backend_changed)
        fl_engine.addRow("OCR backend:", self._cb_ocr_backend)
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
        fl_engine.addRow("Tesseract path:", row)

        fl_engine.addRow(
            "Extra config:",
            _bind_line_with_callback(
                "tesseract_config",
                self.s,
                self.controller.reset_ocr_backend,
                "--psm 6",
            ),
        )
        fl_engine.addRow(
            _bind_check_with_callback(
                "tesseract_psm5_vertical",
                "Auto PSM 5 for vertical scripts",
                self.s,
                self.controller.reset_ocr_backend,
            )
        )
        fl_engine.addRow(
            _bind_check_with_callback(
                "enhance_with_grayscale",
                "Grayscale + autocontrast preprocessing",
                self.s,
                self.controller.reset_ocr_backend,
            )
        )
        fl_engine.addRow(
            _bind_check_with_callback(
                "enhance_with_cv2_contour",
                "Use OpenCV contour text detection",
                self.s,
                self.controller.reset_ocr_backend,
            )
        )
        fl_engine.addRow(
            _bind_check_with_callback(
                "save_cv2_contour_image",
                "Save OpenCV contoured debug image",
                self.s,
                self.controller.reset_ocr_backend,
            )
        )
        fl_engine.addRow(
            "Background type:",
            _bind_combo_with_callback(
                "enhance_background",
                ["Auto-Detect", "Light", "Dark"],
                self.s,
                self.controller.reset_ocr_backend,
            ),
        )
        vl.addWidget(grp_engine)

        # Offset corrections
        grp = QGroupBox("Capture Offset Correction")
        grp_f = QFormLayout(grp)
        grp_f.addRow("Offset X:", _bind_spin("offSetX", self.s, -500, 500))
        grp_f.addRow("Offset Y:", _bind_spin("offSetY", self.s, -500, 500))
        grp_f.addRow("Offset W:", _bind_spin("offSetW", self.s, -500, 500))
        grp_f.addRow("Offset H:", _bind_spin("offSetH", self.s, -500, 500))
        vl.addWidget(grp)
        vl.addStretch()
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
        libre_fl.addRow(
            "Host:", _bind_line("libre_host", self.s, "translate.argosopentech.com")
        )
        libre_fl.addRow("Port:", _bind_line("libre_port", self.s, "5000 or blank"))
        libre_fl.addRow(_bind_check("libre_https", "Use HTTPS", self.s))
        libre_fl.addRow("API Key:", _bind_line("libre_api_key", self.s, "optional"))
        vl.addWidget(grp_libre)

        self._cb_translators_region = QComboBox()
        self._cb_translators_region.addItems(["EN", "CN", "Auto"])
        saved_region = str(self.s.get("translators_region", "EN"))
        idx_region = self._cb_translators_region.findText(saved_region)
        self._cb_translators_region.setCurrentIndex(max(0, idx_region))
        self._cb_translators_region.currentTextChanged.connect(
            self._on_translators_region_changed
        )
        gfl.addRow("translators region:", self._cb_translators_region)

        self._update_deepl_visibility(self._cb_backend.currentText())
        vl.addStretch()
        return w

    def _tab_ocr_overrides(self) -> QWidget:
        """Build the per-backend OCR language override editor."""
        w = QWidget()
        vl = QVBoxLayout(w)

        grp_tl_backend, fl_tl_backend = self._group_form(
            "Per-Backend OCR Language Overrides"
        )
        self._cb_override_backend = QComboBox()
        backend_names = [
            name for name in self.controller.available_backend_names() if name != "None"
        ]
        self._cb_override_backend.addItems(backend_names)
        active_backend = self.controller.active_backend_name()
        idx_backend = self._cb_override_backend.findText(active_backend)
        self._cb_override_backend.setCurrentIndex(max(0, idx_backend))
        self._cb_override_backend.currentTextChanged.connect(
            self._refresh_ocr_override_table
        )
        fl_tl_backend.addRow("Translation backend:", self._cb_override_backend)
        fl_tl_backend.addRow(
            QLabel(
                "All backend language codes are shown here. In this menu, "
                "you can set custom overrides to resolve them to compatible Tesseract codes. "
                "This is useful when a backend's language code doesn't match the standard."
            )
        )
        vl.addWidget(grp_tl_backend)

        grp_data_filter, fl_data_filter = self._group_form(
            "Filtering and Display Options"
        )
        self._le_ocr_override_search = QLineEdit()
        self._le_ocr_override_search.setPlaceholderText(
            "Search by language code, name, resolved code, or override…"
        )
        self._le_ocr_override_search.textChanged.connect(
            self._apply_ocr_override_filter
        )

        fl_data_filter.addRow("Search:", self._le_ocr_override_search)
        self._chk_show_incompatible = QCheckBox("Show incompatible languages")
        self._chk_show_incompatible.setChecked(True)
        self._chk_show_incompatible.toggled.connect(
            lambda _checked: self._apply_ocr_override_filter()
        )
        fl_data_filter.addRow(self._chk_show_incompatible)
        vl.addWidget(grp_data_filter)

        self._tbl_ocr_overrides = QTableWidget(0, 4)
        self._tbl_ocr_overrides.setHorizontalHeaderLabels(
            ["Code", "Name", "Resolved", "Tesseract Key Override"]
        )
        header = self._tbl_ocr_overrides.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self._tbl_ocr_overrides.setColumnWidth(2, 130)
        self._tbl_ocr_overrides.setColumnWidth(3, 230)
        header.setSortIndicatorShown(True)
        self._tbl_ocr_overrides.setSortingEnabled(True)
        self._tbl_ocr_overrides.verticalHeader().setVisible(False)

        vl.addWidget(self._tbl_ocr_overrides, 1)
        self._refresh_ocr_override_table(self._cb_override_backend.currentText())
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
        self._grp_deepl.setVisible(
            "deepl" in name.lower() and "official" in name.lower()
        )

    @pyqtSlot(str)
    def _on_translators_region_changed(self, region: str) -> None:
        """Persist and apply the translators region mode immediately."""
        self.s.set("translators_region", region)
        configure_translators_region(region)

    @pyqtSlot(str)
    def _refresh_ocr_override_table(self, backend_name: str) -> None:
        """Refresh the override table for the selected translation backend."""
        if not hasattr(self, "_tbl_ocr_overrides"):
            return

        backend = self.controller._backends.get(backend_name)
        installed = self.controller.installed_ocr_languages()
        backend_overrides = self.controller.backend_ocr_overrides(backend_name)
        languages = backend.available_languages() if backend is not None else []
        sorting_was_enabled = self._tbl_ocr_overrides.isSortingEnabled()
        self._tbl_ocr_overrides.setSortingEnabled(False)

        rows: list[tuple[str, str, str, str]] = []
        for language_code in languages:
            built_in = resolve_tesseract_language_code(
                language_code, installed, overrides={}
            )
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
                    self._language_name(language_code),
                    resolved_display,
                    current_override,
                )
            )
        self._tbl_ocr_overrides.setRowCount(len(rows))
        for row_index, (
            language_code,
            language_name,
            resolved_display,
            current_override,
        ) in enumerate(rows):
            code_item = QTableWidgetItem(language_code)
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item = QTableWidgetItem(language_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            resolved_item = QTableWidgetItem(resolved_display)
            resolved_item.setFlags(resolved_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._tbl_ocr_overrides.setItem(row_index, 0, code_item)
            self._tbl_ocr_overrides.setItem(row_index, 1, name_item)
            self._tbl_ocr_overrides.setItem(row_index, 2, resolved_item)

            combo = QComboBox()
            combo.addItem("(none)", "")
            for tesseract_code in installed:
                combo.addItem(tesseract_code, tesseract_code)
            current_index = combo.findData(current_override)
            combo.setCurrentIndex(max(0, current_index))
            combo.currentIndexChanged.connect(
                lambda _idx, b=backend_name, lang=language_code, c=combo: self._set_ocr_override(
                    b,
                    lang,
                    str(c.currentData() or ""),
                )
            )
            self._tbl_ocr_overrides.setCellWidget(row_index, 3, combo)
        self._tbl_ocr_overrides.setSortingEnabled(sorting_was_enabled)
        self._apply_ocr_override_filter()

    @pyqtSlot(str)
    def _apply_ocr_override_filter(self, text: str = "") -> None:
        """Filter OCR override rows by search text."""
        if not hasattr(self, "_tbl_ocr_overrides"):
            return

        needle = text.strip().lower()
        show_incompatible = (
            self._chk_show_incompatible.isChecked()
            if hasattr(self, "_chk_show_incompatible")
            else True
        )
        for row_index in range(self._tbl_ocr_overrides.rowCount()):
            values: list[str] = []
            for column in range(3):
                item = self._tbl_ocr_overrides.item(row_index, column)
                if item is not None:
                    values.append(item.text())
            combo = self._tbl_ocr_overrides.cellWidget(row_index, 3)
            if isinstance(combo, QComboBox):
                values.append(combo.currentText())
                current_data = combo.currentData()
                if isinstance(current_data, str):
                    values.append(current_data)
            haystack = " ".join(values).lower()
            resolved_item = self._tbl_ocr_overrides.item(row_index, 2)
            is_incompatible = (
                resolved_item is not None and resolved_item.text() == "[Incompatible]"
            )
            self._tbl_ocr_overrides.setRowHidden(
                row_index,
                (not show_incompatible and is_incompatible)
                or (bool(needle) and needle not in haystack),
            )

    def _set_ocr_override(
        self,
        backend_name: str,
        language_code: str,
        tesseract_code: str,
    ) -> None:
        """Persist an OCR override and refresh dependent UI."""
        self.controller.set_backend_ocr_override(
            backend_name,
            language_code,
            tesseract_code,
        )
        if self.controller.main_window:
            self.controller.main_window._refresh_lang_combos()
        self._refresh_ocr_override_table(backend_name)

    @pyqtSlot(str)
    def _on_ocr_backend_changed(self, name: str) -> None:
        """Persist OCR backend selection and refresh OCR-dependent UI."""
        self.controller.set_active_ocr_backend(name)
        if self.controller.main_window:
            self.controller.main_window.refresh_ocr_compatibility_state()
        if hasattr(self, "_cb_override_backend"):
            self._refresh_ocr_override_table(self._cb_override_backend.currentText())

    # ------------------------------------------------------------------
    # Tab: Hotkeys
    # ------------------------------------------------------------------

    def _tab_hotkeys(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        grp, fl = self._group_form("Global Hotkeys")
        fl.addRow(
            QLabel(
                "Hotkeys require the 'keyboard' package and may need root on Linux.\n"
                "Leave blank to disable."
            )
        )
        fl.addRow("Snip & Translate:", _bind_line("hk_snip_cap", self.s, "ctrl+alt+t"))
        fl.addRow("Snip delay (ms):", _bind_spin("hk_snip_cap_delay", self.s, 0, 5000))
        fl.addRow(
            "Capture Window:", _bind_line("hk_cap_window", self.s, "e.g. ctrl+alt+c")
        )
        fl.addRow(
            "Capture delay (ms):", _bind_spin("hk_cap_window_delay", self.s, 0, 5000)
        )
        vl.addWidget(grp)
        vl.addStretch()
        return w

    # ------------------------------------------------------------------
    # Tab: Appearance
    # ------------------------------------------------------------------

    def _tab_appearance(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)

        grp_theme, fl_theme = self._group_form("Theme")
        self._cb_theme = QComboBox()
        self._cb_theme.addItems(_QT_MATERIAL_THEMES)
        saved_theme = str(self.s.get("theme", "dark_teal.xml"))
        idx_theme = self._cb_theme.findText(saved_theme)
        self._cb_theme.setCurrentIndex(max(0, idx_theme))
        self._cb_theme.currentTextChanged.connect(self._on_theme_changed)
        fl_theme.addRow("Theme:", self._cb_theme)
        fl_theme.addRow(
            QLabel(
                "qt-material themes apply immediately when the package is installed."
            )
        )
        vl.addWidget(grp_theme)

        grp_query, fl_query = self._group_form("Query Window")
        fl_query.addRow("Font size:", _bind_spin("tb_ex_q_font_size", self.s, 6, 72))
        fl_query.addRow("Font color:", self._color_picker_row("tb_ex_q_font_color"))
        fl_query.addRow("Background:", self._color_picker_row("tb_ex_q_bg_color"))
        vl.addWidget(grp_query)

        grp_result, fl_result = self._group_form("Result Window")
        fl_result.addRow("Font size:", _bind_spin("tb_ex_res_font_size", self.s, 6, 72))
        fl_result.addRow("Font color:", self._color_picker_row("tb_ex_res_font_color"))
        fl_result.addRow("Background:", self._color_picker_row("tb_ex_res_bg_color"))
        vl.addWidget(grp_result)

        grp_mask, fl_mask = self._group_form("Mask Window")
        fl_mask.addRow(
            "Background color:", self._color_picker_row("mask_window_bg_color")
        )
        vl.addWidget(grp_mask)
        vl.addStretch()
        return w

    @pyqtSlot(str)
    def _on_theme_changed(self, theme: str) -> None:
        """Persist and apply a qt-material theme."""
        self.s.set("theme", theme)
        app = QApplication.instance()
        if app is None:
            return
        self._show_theme_overlay()
        try:
            from qt_material import apply_stylesheet

            app.setStyle("Fusion")
            apply_stylesheet(app, theme=theme)
            self._schedule_nav_style_refresh(50)
        except ImportError:
            logger.warning(
                "qt-material is not installed - theme change saved for later"
            )
        except Exception as exc:
            logger.warning("Could not apply theme %s: %s", theme, exc)
        finally:
            self._hide_theme_overlay()

    def resizeEvent(self, event: Any) -> None:
        """Keep the theme-loading overlay sized to the dialog."""
        super().resizeEvent(event)
        if self._theme_overlay is not None:
            self._theme_overlay.setGeometry(self.rect())

    def _color_picker_row(self, key: str) -> QPushButton:
        """Create a colour-picker button tied to *key*.

        Args:
            key: Settings key for the colour (hex string).

        Returns:
            Configured QPushButton.
        """
        btn = QPushButton()
        btn.setFixedWidth(60)

        def apply_button_color(color: QColor) -> None:
            btn.setProperty("selectedColor", color)
            btn.setStyleSheet(f"background-color: {color.name()};")

        stored = QColor(str(self.s.get(key, "#000000")))
        apply_button_color(stored if stored.isValid() else QColor("#000000"))

        def pick() -> None:
            current = btn.property("selectedColor")
            initial = current if isinstance(current, QColor) and current.isValid() else QColor("#000000")
            col = QColorDialog.getColor(initial, self, "Select Colour")
            if col.isValid():
                self.s.set(key, col.name())
                apply_button_color(col)

        btn.clicked.connect(pick)
        return btn

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _group_form(self, title: str) -> tuple[QGroupBox, QFormLayout]:
        """Create a titled group box with a ready-to-use form layout."""
        group = QGroupBox(title)
        form = QFormLayout(group)
        return group, form

    def _nav_icon(
        self,
        label: str,
        color: QColor,
    ) -> QIcon:
        """Return a sidebar icon for the given settings section label."""
        if qta is None:
            return QIcon()
        icon_name = _SETTINGS_NAV_ICONS.get(label)
        if not icon_name:
            return QIcon()
        try:
            color_key = (
                label,
                color.name(QColor.NameFormat.HexArgb),
                "",
                "",
            )
            cached_icon = self._nav_icon_cache.get(color_key)
            if cached_icon is not None:
                return cached_icon

            kwargs: dict[str, Any] = {"color": QColor(color)}
            icon = qta.icon(icon_name, **kwargs)
            self._nav_icon_cache[color_key] = icon
            return icon
        except Exception as exc:
            logger.debug(
                "Could not load qtawesome icon %s for %s: %s",
                icon_name,
                label,
                exc,
            )
            return QIcon()

    def _language_name(self, code: str) -> str:
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

    def _browse_tesseract(self) -> None:
        """Open a file dialog to locate the tesseract executable."""
        path, _ = QFileDialog.getOpenFileName(self, "Locate Tesseract Executable")
        if path:
            self._tes_path.setText(path)
            self.controller.reset_ocr_backend()

    def _refresh_capture_window_ui(self) -> None:
        """Apply capture-mode UI changes immediately to the capture window."""
        if self.controller.capture_window:
            self.controller.capture_window._sync_mode_ui()

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        self.show()
        self.raise_()
        self.activateWindow()
