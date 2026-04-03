"""Main application window (QMainWindow)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pycountry
from PyQt6.QtCore import QSize, Qt, pyqtSlot
from PyQt6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenu,
    QSlider,
    QSplitter,
    QStatusBar,
    QSystemTrayIcon,
    QTextEdit,
    QToolBar,
)
from qfluentwidgets import ComboBox, PrimaryPushButton, ProgressBar, PushButton

from screen_translate import __version__
from screen_translate.ui.style_sheet import StyleSheet
from screen_translate.ui.utils import load_icon

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)

_APP_NAME = "Screen Translate"
_COMBOBOX_HEIGHT = 36
_COMBOBOX_POPUP_MAX_HEIGHT = 320
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
_OCR_INCOMPATIBLE_SUFFIX = " [incompatible with Tesseract OCR]"


class MainWindow(QMainWindow):
    """Primary application shell.

    Contains the query/result text areas, toolbar with language selectors,
    menubar, system tray icon, and status bar.
    """

    def __init__(self, controller: AppController) -> None:
        """Create the main window.

        Args:
            controller: Application controller that owns this window.
        """
        super().__init__()
        self.controller = controller
        self._notified_hidden = False

        self.setWindowTitle(f"{_APP_NAME} v{__version__}")
        self.setMinimumSize(QSize(700, 280))
        self.resize(950, 340)
        StyleSheet.MAIN_WINDOW.apply(self)

        icon = load_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)

        self._build_ui()
        self._build_menubar()
        self._build_tray()
        self._connect_signals()
        self._restore_state()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create toolbar and central split editor."""
        # --- Central widget: splitter with query + result ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.tb_query = QTextEdit()
        self.tb_query.setPlaceholderText("Paste or type text here to translate…")
        self.tb_query.setAcceptRichText(False)

        self.tb_result = QTextEdit()
        self.tb_result.setPlaceholderText("Translation result will appear here…")
        self.tb_result.setReadOnly(False)

        splitter.addWidget(self.tb_query)
        splitter.addWidget(self.tb_result)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        # --- Toolbar ---
        bar = QToolBar("Main Toolbar")
        bar.setMovable(False)
        bar.setIconSize(QSize(16, 16))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, bar)

        self.btn_translate = PrimaryPushButton("Translate")
        self.btn_translate.setToolTip("Translate typed text (no OCR)")
        bar.addWidget(self.btn_translate)

        self.btn_capture = PrimaryPushButton("Capture & Translate")
        self.btn_capture.setToolTip(
            "Capture the region inside the Capture Window and translate"
        )
        bar.addWidget(self.btn_capture)

        self.btn_snip = PrimaryPushButton("Snip -> Translate")
        self.btn_snip.setToolTip(
            "Draw a selection on any monitor to capture and translate (Ctrl+Alt+T)"
        )
        bar.addWidget(self.btn_snip)

        bar.addWidget(QLabel("Opacity:"))
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(10, 100)
        self.slider_opacity.setValue(80)
        self.slider_opacity.setFixedWidth(100)
        self.slider_opacity.setToolTip("Capture Window opacity")
        bar.addWidget(self.slider_opacity)

        bar.addWidget(QLabel("Engine:"))
        self.cb_engine = ComboBox()
        self.cb_engine.setMinimumWidth(160)
        self.cb_engine.setMaximumHeight(_COMBOBOX_HEIGHT)
        bar.addWidget(self.cb_engine)

        bar.addWidget(QLabel("From:"))
        self.cb_source = ComboBox()
        self.cb_source.setMinimumWidth(140)
        self.cb_source.setMaximumHeight(_COMBOBOX_HEIGHT)
        # self.cb_source.view().setMaximumHeight(_COMBOBOX_POPUP_MAX_HEIGHT)
        bar.addWidget(self.cb_source)

        bar.addWidget(QLabel("To:"))
        self.cb_target = ComboBox()
        self.cb_target.setMinimumWidth(140)
        self.cb_target.setMaximumHeight(_COMBOBOX_HEIGHT)
        # self.cb_target.view().setMaximumHeight(_COMBOBOX_POPUP_MAX_HEIGHT)
        bar.addWidget(self.cb_target)

        self.btn_swap = PushButton("⮁ Swap")
        self.btn_swap.setToolTip("Swap source and target languages and text")
        bar.addWidget(self.btn_swap)

        self.btn_clear = PushButton("✕ Clear")
        self.btn_clear.setToolTip("Clear both text areas")
        bar.addWidget(self.btn_clear)

        # --- Status bar ---
        self.progress = ProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setVisible(False)
        self.progress.setMaximumWidth(120)
        status_bar = QStatusBar()
        status_bar.addPermanentWidget(self.progress)
        self.setStatusBar(status_bar)

    def _build_menubar(self) -> None:
        """Build the application menu bar."""
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        self._act_always_top = QAction("Always on Top", self, checkable=True)
        self._act_always_top.triggered.connect(self._toggle_always_on_top)
        file_menu.addAction(self._act_always_top)
        file_menu.addSeparator()
        file_menu.addAction("Hide to Tray", self._hide_to_tray)
        file_menu.addAction("Exit Application", self._quit_app)

        # View
        view_menu = mb.addMenu("&View")
        self._add_menu_action(
            view_menu, "Settings", self._open_settings, QKeySequence("F2")
        )
        self._add_menu_action(
            view_menu, "History", self._open_history, QKeySequence("F3")
        )
        self._add_menu_action(
            view_menu, "Captured Images", self._open_captured_dir, QKeySequence("F4")
        )
        view_menu.addAction("Log", self._open_log)

        # Generate
        gen_menu = mb.addMenu("&Generate")
        self._add_menu_action(
            gen_menu, "Capture Window", self._open_capture_window, QKeySequence("F5")
        )
        self._add_menu_action(
            gen_menu, "Mask Window", self._open_mask_window, QKeySequence("Ctrl+Alt+F5")
        )
        self._add_menu_action(
            gen_menu, "Query Window", self._open_query_window, QKeySequence("F6")
        )
        self._add_menu_action(
            gen_menu, "Result Window", self._open_result_window, QKeySequence("F7")
        )

        # Get
        get_menu = mb.addMenu("&Get")
        get_menu.addAction("Tesseract OCR", self._open_tesseract_link)
        get_menu.addAction("LibreTranslate", self._open_libre_link)

        # Help
        help_menu = mb.addMenu("&Help")
        help_menu.addAction(
            "GitHub Repository",
            lambda: self._open_url("https://github.com/Dadangdut33/Screen-Translate"),
        )
        help_menu.addAction("Open CHANGELOG", self._open_changelog)
        help_menu.addSeparator()
        self._add_menu_action(help_menu, "About", self._open_about, QKeySequence("F1"))

    def _add_menu_action(
        self,
        menu: QMenu,
        text: str,
        slot: object,
        shortcut: QKeySequence | None = None,
    ) -> QAction:
        """Create a QAction with an optional shortcut and add it to *menu*."""
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _build_tray(self) -> None:
        """Build the system tray icon."""
        icon = load_icon()
        self._tray = QSystemTrayIcon(icon if not icon.isNull() else QIcon(), self)
        self._tray.setToolTip(f"{_APP_NAME} v{__version__}")

        tray_menu = QMenu()
        tray_menu.addAction(f"{_APP_NAME} {__version__}").setEnabled(False)
        tray_menu.addSeparator()
        tray_menu.addAction("Snip & Translate", self._trigger_snip)
        tray_menu.addAction("Open Capture Window", self._open_capture_window)
        tray_menu.addSeparator()
        view_sub = tray_menu.addMenu("View")
        view_sub.addAction("Settings", self._open_settings)
        view_sub.addAction("History", self._open_history)
        view_sub.addAction("Log", self._open_log)
        tray_menu.addSeparator()
        tray_menu.addAction("Show Main Window", self.show_and_raise)
        tray_menu.addAction("Exit", self._quit_app)

        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _connect_signals(self) -> None:
        """Wire all widget signals to slots."""
        self.btn_translate.clicked.connect(self._on_translate_clicked)
        self.btn_capture.clicked.connect(self._on_capture_clicked)
        self.btn_snip.clicked.connect(self._trigger_snip)
        self.btn_swap.clicked.connect(self._swap_languages)
        self.btn_clear.clicked.connect(self._clear_text)
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        self.cb_engine.currentTextChanged.connect(self._on_engine_changed)
        self.cb_source.currentIndexChanged.connect(self._on_source_changed)
        self.cb_target.currentIndexChanged.connect(self._on_target_changed)

        ctrl = self.controller
        ctrl.ocr_started.connect(self._on_busy)
        ctrl.translation_started.connect(self._on_busy)
        ctrl.status_idle.connect(self._on_idle)
        ctrl.ocr_completed.connect(self._on_ocr_result)
        ctrl.translation_completed.connect(self._on_translation_result)

    def _restore_state(self) -> None:
        """Populate comboboxes from settings."""
        s = self.controller.settings

        # Engine list
        self.cb_engine.blockSignals(True)
        for name in self.controller.available_backend_names():
            self.cb_engine.addItem(name)
        saved_engine = s.get("engine", "translators-google")
        idx = self.cb_engine.findText(saved_engine)
        if idx < 0:
            idx = 0
        self.cb_engine.setCurrentIndex(max(0, idx))
        self.cb_engine.blockSignals(False)

        self._refresh_lang_combos()
        self.refresh_ocr_compatibility_state()

    def _refresh_lang_combos(self) -> None:
        """Update source/target language combos for the active backend."""
        s = self.controller.settings
        engine_name = self.cb_engine.currentText()
        backend = self.controller._backends.get(engine_name)

        langs = backend.available_languages() if backend else []
        src_langs = langs
        tgt_langs = [lang for lang in langs if lang != "auto" and lang != "Auto"]

        self.cb_source.blockSignals(True)
        self.cb_target.blockSignals(True)
        self.cb_source.clear()
        self.cb_target.clear()
        self._populate_language_combo(
            self.cb_source,
            src_langs,
            mark_ocr_compat=True,
            prefix_code=True,
        )
        self._populate_language_combo(self.cb_target, tgt_langs)

        saved_src = s.get("sourceLang", "auto")
        saved_tgt = s.get("targetLang", "en")

        idx_src = self._find_language_index(self.cb_source, saved_src)
        if idx_src < 0:
            idx_src = self._find_language_index(self.cb_source, "auto")
        if idx_src < 0 and self.cb_source.count() > 0:
            idx_src = 0

        idx_tgt = self._find_language_index(self.cb_target, saved_tgt)
        if idx_tgt < 0:
            idx_tgt = self._find_language_index(self.cb_target, "en")
        if idx_tgt < 0 and self.cb_target.count() > 0:
            idx_tgt = 0

        self.cb_source.setCurrentIndex(max(0, idx_src))
        self.cb_target.setCurrentIndex(max(0, idx_tgt))

        is_none = engine_name == "None"
        has_languages = bool(langs)
        self.cb_source.setEnabled(not is_none and has_languages)
        self.cb_target.setEnabled(not is_none and has_languages)
        self.cb_source.blockSignals(False)
        self.cb_target.blockSignals(False)

        self._persist_selected_language(self.cb_source, "sourceLang")
        self._persist_selected_language(self.cb_target, "targetLang")
        self.refresh_ocr_compatibility_state()

    def _populate_language_combo(
        self,
        combo: ComboBox,
        languages: list[str],
        *,
        mark_ocr_compat: bool = False,
        prefix_code: bool = False,
    ) -> None:
        """Populate a language combo with display labels while keeping the code as user data."""
        for code in languages:
            combo.addItem(
                self._language_label(
                    code,
                    mark_ocr_compat=mark_ocr_compat,
                    prefix_code=prefix_code,
                ),
                code,
            )

    def _language_label(
        self,
        code: str,
        *,
        mark_ocr_compat: bool = False,
        prefix_code: bool = False,
    ) -> str:
        """Return a human-friendly label for a backend language code."""
        label = self._base_language_label(code)
        if prefix_code:
            label = f"[{code.upper()}] {label}"
        if mark_ocr_compat and not self.controller.is_selected_source_ocr_compatible(
            code
        ):
            return f"{label}{_OCR_INCOMPATIBLE_SUFFIX}"
        return label

    def _base_language_label(self, code: str) -> str:
        """Return the human-friendly label for a language code without compatibility suffixes."""
        override = _LANGUAGE_NAME_OVERRIDES.get(code)
        if override:
            return override

        normalized = code.replace("_", "-")
        try:
            if "-" in normalized:
                language_part, script_or_region = normalized.split("-", 1)
                language = pycountry.languages.get(
                    alpha_2=language_part
                ) or pycountry.languages.get(alpha_3=language_part)
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

    def refresh_ocr_compatibility_state(self) -> None:
        """Refresh OCR action availability based on source-language compatibility."""
        ocr_backend = self.controller.active_ocr_backend_name()
        selected_source = self.cb_source.currentData()
        is_compatible = self.controller.is_selected_source_ocr_compatible(
            selected_source if isinstance(selected_source, str) else None
        )
        capture_enabled = ocr_backend != "Tesseract" or is_compatible
        disabled_reason = (
            "Selected source language is incompatible with Tesseract OCR."
            if not capture_enabled
            else ""
        )

        self.btn_capture.setEnabled(capture_enabled)
        self.btn_snip.setEnabled(capture_enabled)
        self.btn_capture.setToolTip(
            disabled_reason
            or "Capture the region inside the Capture Window and translate"
        )
        self.btn_snip.setToolTip(
            disabled_reason
            or "Draw a selection on any monitor to capture and translate (Ctrl+Alt+T)"
        )

    def _find_language_index(self, combo: ComboBox, code: str) -> int:
        """Find the combobox index for a language code stored as user data."""
        for idx in range(combo.count()):
            if combo.itemData(idx) == code:
                return idx
        return -1

    def _persist_selected_language(self, combo: ComboBox, key: str) -> None:
        """Persist the currently selected language code."""
        code = combo.currentData()
        if isinstance(code, str) and code:
            self.controller.settings.set(key, code)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _on_translate_clicked(self) -> None:
        """Translate typed text (no OCR)."""
        text = self.tb_query.toPlainText()
        if not text.strip():
            return
        self.controller.translate_text(text)

    @pyqtSlot()
    def _on_capture_clicked(self) -> None:
        """Trigger capture-window OCR."""
        if not self.btn_capture.isEnabled():
            return
        if self.controller.capture_window:
            self.controller.capture_window.trigger_capture()

    @pyqtSlot()
    def _trigger_snip(self) -> None:
        """Launch snip-and-translate mode across all monitors."""
        if not self.btn_snip.isEnabled():
            return
        s = self.controller.settings
        if s.get("hide_mw_on_cap", False):
            self.hide()
        if self.controller.query_window:
            self.controller.query_window.setVisible(False)
        if self.controller.result_window:
            self.controller.result_window.setVisible(False)

        self.controller.start_snip_capture()

    @pyqtSlot(str)
    def _on_engine_changed(self, name: str) -> None:
        """React to engine combobox change."""
        self.controller.set_active_backend(name)
        self._refresh_lang_combos()

    @pyqtSlot(int)
    def _on_source_changed(self, _: int) -> None:
        """Persist new source language."""
        self._persist_selected_language(self.cb_source, "sourceLang")
        self.refresh_ocr_compatibility_state()

    @pyqtSlot(int)
    def _on_target_changed(self, _: int) -> None:
        """Persist new target language."""
        self._persist_selected_language(self.cb_target, "targetLang")

    @pyqtSlot()
    def _swap_languages(self) -> None:
        """Swap source/target languages and text."""
        src = self.cb_source.currentData()
        tgt = self.cb_target.currentData()
        if isinstance(tgt, str):
            tgt_idx = self._find_language_index(self.cb_source, tgt)
            if tgt_idx >= 0:
                self.cb_source.setCurrentIndex(tgt_idx)
        if isinstance(src, str):
            src_idx = self._find_language_index(self.cb_target, src)
            if src_idx >= 0:
                self.cb_target.setCurrentIndex(src_idx)
        q = self.tb_query.toPlainText()
        r = self.tb_result.toPlainText()
        self.tb_query.setPlainText(r)
        self.tb_result.setPlainText(q)

    @pyqtSlot()
    def _clear_text(self) -> None:
        """Clear both text areas."""
        self.tb_query.clear()
        self.tb_result.clear()
        if self.controller.query_window:
            self.controller.query_window.set_text("")
        if self.controller.result_window:
            self.controller.result_window.set_text("")

    @pyqtSlot(int)
    def _on_opacity_changed(self, val: int) -> None:
        """Update capture window opacity from slider."""
        opacity = val / 100.0
        if self.controller.capture_window:
            self.controller.capture_window.set_overlay_opacity(opacity)

    @pyqtSlot()
    def _on_busy(self) -> None:
        """Show busy indicator."""
        self.progress.setVisible(True)

    @pyqtSlot()
    def _on_idle(self) -> None:
        """Hide busy indicator."""
        self.progress.setVisible(False)

    @pyqtSlot(str)
    def _on_ocr_result(self, text: str) -> None:
        """Populate query area with recognised text."""
        self.tb_query.setPlainText(text)
        if self.controller.query_window:
            self.controller.query_window.set_text(text)
        # Restore hidden windows
        s = self.controller.settings
        if s.get("hide_mw_on_cap", False):
            self.show_and_raise()
        if self.controller.query_window and s.get(
            "show_query_window_after_capture", True
        ):
            self.controller.query_window.setVisible(True)
        if self.controller.result_window and s.get(
            "show_result_window_after_capture", True
        ):
            self.controller.result_window.setVisible(True)

    @pyqtSlot(str)
    def _on_translation_result(self, text: str) -> None:
        """Populate result area with translated text."""
        self.tb_result.setPlainText(text)
        if self.controller.result_window:
            self.controller.result_window.set_text(text)

    @pyqtSlot()
    def _toggle_always_on_top(self) -> None:
        """Toggle always-on-top window flag."""
        checked = self._act_always_top.isChecked()
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _open_settings(self) -> None:
        if self.controller.settings_dialog:
            self.controller.settings_dialog.show_and_raise()

    def _open_history(self) -> None:
        if self.controller.history_window:
            self.controller.history_window.show_and_raise()

    def _open_log(self) -> None:
        if self.controller.log_window:
            self.controller.log_window.show_and_raise()

    def _open_about(self) -> None:
        if self.controller.about_dialog:
            self.controller.about_dialog.exec()

    def _open_capture_window(self) -> None:
        if self.controller.capture_window:
            self.controller.capture_window.show_and_raise()

    def _open_mask_window(self) -> None:
        if self.controller.mask_window:
            self.controller.mask_window.show_and_raise()

    def _open_query_window(self) -> None:
        if self.controller.query_window:
            self.controller.query_window.show_and_raise()

    def _open_result_window(self) -> None:
        if self.controller.result_window:
            self.controller.result_window.show_and_raise()

    def _open_captured_dir(self) -> None:
        import os
        import subprocess
        import sys

        from platformdirs import user_data_dir

        d = os.path.join(user_data_dir("screen-translate", "Dadangdut33"), "captured")
        os.makedirs(d, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(d)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", d])
        else:
            subprocess.Popen(["xdg-open", d])

    def _open_tesseract_link(self) -> None:
        self._open_url("https://github.com/UB-Mannheim/tesseract/wiki")

    def _open_libre_link(self) -> None:
        self._open_url("https://libretranslate.com")

    def _open_changelog(self) -> None:
        self._open_url(
            "https://github.com/Dadangdut33/Screen-Translate/blob/main/CHANGELOG.md"
        )

    def _open_url(self, url: str) -> None:
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl(url))

    # ------------------------------------------------------------------
    # Window management
    # ------------------------------------------------------------------

    def show_and_raise(self) -> None:
        """Show the window and bring it to the foreground."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _hide_to_tray(self) -> None:
        """Minimise to tray (show notification once)."""
        self.hide()
        if not self._notified_hidden:
            self._tray.showMessage(
                _APP_NAME,
                "Screen Translate is still running in the background.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
            self._notified_hidden = True

    def _quit_app(self) -> None:
        """Exit the application cleanly."""
        from PyQt6.QtWidgets import QApplication

        self._tray.hide()
        QApplication.quit()

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Show main window on tray icon double-click."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_raise()

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        """Hide to tray instead of closing."""
        event.ignore()
        self._hide_to_tray()
