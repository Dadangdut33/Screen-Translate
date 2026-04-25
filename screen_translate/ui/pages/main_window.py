"""Main application window using QFluentWidgets' FluentWindow shell."""

from __future__ import annotations

import logging
import platform
from typing import TYPE_CHECKING

import pycountry
from PyQt6.QtCore import QSize, Qt, pyqtSlot
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QSplitter,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon as FIF,
    FluentWindow,
    NavigationItemPosition,
    ProgressBar,
    SmoothScrollArea,
    ToolButton,
    isDarkTheme,
)
import qtawesome as qta

from screen_translate import __version__
from qfluentwidgets.common.router import qrouter
from screen_translate.ui.widgets import SuggestionComboBox
from screen_translate.ui.theme.style_sheet import StyleSheet
from screen_translate.ui.theme.utils import load_icon
from screen_translate.ui.widgets.icons import load_qta_icon

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)

_APP_NAME = "Screen Translate"
_COMBOBOX_HEIGHT = 36
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


class _PageScrollArea(SmoothScrollArea):
    """Simple scroll wrapper used for long stacked pages."""

    def __init__(self, widget: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        widget.show()
        container = QWidget(self)
        container.setObjectName("ContentScrollContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 12, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(widget)

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.enableTransparentBackground()
        self.setFrameShape(self.Shape.NoFrame)
        self.viewport().setObjectName("ContentScrollViewport")
        self.setWidget(container)
        self.setObjectName("ContentScrollArea")


class MainWindow(FluentWindow):
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
        self._is_quitting = False
        self._history_page: QWidget | None = None
        self._log_page: QWidget | None = None
        self._ocr_images_page: QWidget | None = None
        self._about_page: QWidget | None = None
        self._settings_page: QWidget | None = None

        self.setWindowTitle(f"{_APP_NAME} v{__version__}")
        self.setMinimumSize(QSize(700, 300))
        self.resize(950, 600)
        StyleSheet.MAIN_WINDOW.apply(self)

        icon = load_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)

        self._build_ui()
        self._build_tray()
        self._connect_signals()
        self._restore_state()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create the FluentWindow content and page content."""
        self.widgetLayout.removeWidget(self.stackedWidget)
        self.stackedWidget.setObjectName("MainStackedWidget")
        content_shell = QWidget(self)
        content_shell.setObjectName("MainContentShell")
        content_layout = QVBoxLayout(content_shell)
        content_layout.setContentsMargins(0, 0, 18, 12)
        content_layout.setSpacing(10)
        content_layout.addWidget(self.stackedWidget, 1)
        self.widgetLayout.addWidget(content_shell, 1)

        from screen_translate.ui.pages.tools_page import ToolsPage

        self._workspace_page = self._wrap_scroll_page(self._build_workspace_page())
        self._workspace_page.setObjectName("translate")
        self._tools_page = self._wrap_scroll_page(ToolsPage(self))
        self._tools_page.setObjectName("tools")

        self._add_sub_interface(self._workspace_page, FIF.EDIT, "Translate")
        self._add_sub_interface(self._tools_page, FIF.APPLICATION, "Tools")

        self.switchTo(self._workspace_page)
        self.navigationInterface.setCurrentItem("translate")

        status_host = QWidget(content_shell)
        status_layout = QHBoxLayout(status_host)
        status_layout.setContentsMargins(16, 0, 16, 6)
        status_layout.setSpacing(10)
        status_layout.addStretch(1)
        self._progress_label = QLabel("Working...", status_host)
        self._progress_label.setVisible(False)
        status_layout.addWidget(self._progress_label)
        self.progress = ProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setVisible(False)
        self.progress.setFixedWidth(180)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet(
            """
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #2de2ff;
                border-radius: 4px;
            }
            """
        )
        status_layout.addWidget(self.progress)
        content_layout.addWidget(status_host)

    def _build_workspace_page(self) -> QWidget:
        """Build the main translation workspace page."""
        page = QWidget(self)
        page.setObjectName("WorkspacePage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        controls = QWidget(page)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)

        self.btn_translate = ToolButton(load_qta_icon("mdi6.translate"), controls)
        self.btn_translate.setObjectName("WorkspaceActionButton")
        self.btn_translate.setToolTip("Translate typed text (no OCR)")
        self.btn_translate.setFixedSize(38, 38)
        self.btn_translate.setIconSize(QSize(18, 18))
        controls_layout.addWidget(self.btn_translate)

        self.btn_capture = ToolButton(load_qta_icon("mdi6.camera-outline"), controls)
        self.btn_capture.setObjectName("WorkspaceActionButton")
        self.btn_capture.setToolTip(
            "Capture the region inside the Capture Window and translate"
        )
        self.btn_capture.setFixedSize(38, 38)
        self.btn_capture.setIconSize(QSize(18, 18))
        controls_layout.addWidget(self.btn_capture)

        self.btn_snip = ToolButton(load_qta_icon("mdi6.crop"), controls)
        self.btn_snip.setObjectName("WorkspaceActionButton")
        self.btn_snip.setToolTip(
            "Draw a selection on any monitor to capture and translate"
        )
        self.btn_snip.setFixedSize(38, 38)
        self.btn_snip.setIconSize(QSize(18, 18))
        controls_layout.addWidget(self.btn_snip)

        controls_layout.addWidget(QLabel("Engine:"))
        self.cb_engine = SuggestionComboBox()
        self.cb_engine.setMinimumWidth(160)
        self.cb_engine.setMaximumHeight(_COMBOBOX_HEIGHT)
        self.cb_engine.setPlaceholderText("Choose engine")
        controls_layout.addWidget(self.cb_engine)

        controls_layout.addWidget(QLabel("From:"))
        self.cb_source = SuggestionComboBox()
        self.cb_source.setMinimumWidth(140)
        self.cb_source.setMaximumHeight(_COMBOBOX_HEIGHT)
        self.cb_source.setPlaceholderText("Source language")
        controls_layout.addWidget(self.cb_source)

        controls_layout.addWidget(QLabel("To:"))
        self.cb_target = SuggestionComboBox()
        self.cb_target.setMinimumWidth(140)
        self.cb_target.setMaximumHeight(_COMBOBOX_HEIGHT)
        self.cb_target.setPlaceholderText("Target language")
        controls_layout.addWidget(self.cb_target)

        self.btn_swap = ToolButton(load_qta_icon("mdi6.swap-horizontal"), controls)
        self.btn_swap.setObjectName("WorkspaceActionButton")
        self.btn_swap.setToolTip("Swap source and target languages and text")
        self.btn_swap.setFixedSize(38, 38)
        self.btn_swap.setIconSize(QSize(18, 18))
        controls_layout.addWidget(self.btn_swap)

        self.btn_clear = ToolButton(load_qta_icon("mdi6.broom"), controls)
        self.btn_clear.setObjectName("WorkspaceActionButton")
        self.btn_clear.setToolTip("Clear both text areas")
        self.btn_clear.setFixedSize(38, 38)
        self.btn_clear.setIconSize(QSize(18, 18))
        controls_layout.addWidget(self.btn_clear)
        controls_layout.addStretch(1)
        layout.addWidget(controls)

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
        layout.addWidget(splitter, 1)
        return page

    def _add_navigation_items(self) -> None:
        """Populate the left Fluent navigation bar."""
        self.navigationInterface.addSeparator()

        for route_key, icon, text, slot in [
            ("capture_window", FIF.CAMERA, "Capture Window", self._open_capture_window),
            ("snip", FIF.CUT, "Snip & Translate", self._trigger_snip),
        ]:
            self.navigationInterface.addItem(
                routeKey=route_key,
                icon=icon,
                text=text,
                onClick=slot,
                selectable=False,
                position=NavigationItemPosition.SCROLL,
            )

    def register_internal_pages(
        self,
        history_page: QWidget,
        log_page: QWidget,
        ocr_images_page: QWidget,
        about_page: QWidget,
        settings_page: QWidget,
    ) -> None:
        """Embed auxiliary windows into the main stacked area."""
        self._history_page = self._embed_page_widget(
            history_page, "history", FIF.HISTORY, "History", NavigationItemPosition.TOP
        )
        self._ocr_images_page = self._embed_page_widget(
            ocr_images_page,
            "ocr_images",
            FIF.PHOTO,
            "OCR Images",
            NavigationItemPosition.TOP,
        )
        self._log_page = self._embed_page_widget(
            log_page,
            "log",
            load_qta_icon("mdi6.console"),
            "Log",
            NavigationItemPosition.TOP,
        )
        self._about_page = self._embed_page_widget(
            about_page, "about", FIF.INFO, "About", NavigationItemPosition.BOTTOM
        )
        self._settings_page = self._embed_page_widget(
            settings_page,
            "settings",
            FIF.SETTING,
            "Settings",
            NavigationItemPosition.BOTTOM,
        )
        self._add_navigation_items()

    def _embed_page_widget(
        self,
        widget: QWidget,
        route_key: str,
        icon: object,
        text: str,
        position: NavigationItemPosition,
    ) -> QWidget:
        """Turn an auxiliary widget into a Fluent stacked page."""
        widget.setParent(None)
        widget.setWindowFlags(Qt.WindowType.Widget)
        scroll_page = self._wrap_scroll_page(widget)
        scroll_page.setObjectName(route_key)
        self._add_sub_interface(scroll_page, icon, text, position=position)
        return scroll_page

    def _add_sub_interface(
        self,
        interface: QWidget,
        icon: object,
        text: str,
        position: NavigationItemPosition = NavigationItemPosition.TOP,
        parent: QWidget | str | None = None,
        *,
        is_transparent: bool = False,
    ) -> QWidget:
        """Add a Fluent sub-interface without enabling the built-in nav tooltip."""
        if not interface.objectName():
            raise ValueError("The object name of `interface` can't be empty string.")

        parent_route_key = parent
        if parent and isinstance(parent, QWidget):
            parent_route_key = parent.objectName()
            if not parent_route_key:
                raise ValueError("The object name of `parent` can't be empty string.")

        interface.setProperty("isStackedTransparent", is_transparent)
        self.stackedWidget.addWidget(interface)

        route_key = interface.objectName()
        self.navigationInterface.addItem(
            routeKey=route_key,
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=None,
            parentRouteKey=parent_route_key,
        )

        if self.stackedWidget.count() == 1:
            self.stackedWidget.currentChanged.connect(self._onCurrentInterfaceChanged)
            self.navigationInterface.setCurrentItem(route_key)
            qrouter.setDefaultRouteKey(self.stackedWidget, route_key)

        self._updateStackedBackground()
        return interface

    def _wrap_scroll_page(self, widget: QWidget) -> _PageScrollArea:
        """Wrap a page widget in a Fluent scroll area."""
        return _PageScrollArea(widget, self.stackedWidget)

    def _show_stack_page(self, page: QWidget, route_key: str) -> None:
        """Show a stacked page and sync the Fluent navigation indicator."""
        self.switchTo(page)
        self.navigationInterface.setCurrentItem(route_key)

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
        self.cb_engine.committed.connect(self._on_engine_changed)
        self.cb_source.committed.connect(self._on_source_changed)
        self.cb_target.committed.connect(self._on_target_changed)

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
        self.cb_engine.refresh_completer()
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
        self.cb_source.refresh_completer()
        self.cb_target.refresh_completer()

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
        combo: SuggestionComboBox,
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
                userData=code,
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
            or "Draw a selection on any monitor to capture and translate"
        )

    def _find_language_index(self, combo: SuggestionComboBox, code: str) -> int:
        """Find the combobox index for a language code stored as user data."""
        for idx in range(combo.count()):
            if combo.itemData(idx) == code:
                return idx
        return -1

    def _persist_selected_language(self, combo: SuggestionComboBox, key: str) -> None:
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

    @pyqtSlot(int)
    def _on_engine_changed(self, _: int) -> None:
        """React to engine combobox change."""
        name = self.cb_engine.currentText().strip()
        if not name:
            return
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
        self._persist_selected_language(self.cb_source, "sourceLang")
        self._persist_selected_language(self.cb_target, "targetLang")
        self.refresh_ocr_compatibility_state()

    @pyqtSlot()
    def _clear_text(self) -> None:
        """Clear both text areas."""
        self.tb_query.clear()
        self.tb_result.clear()
        if self.controller.query_window:
            self.controller.query_window.set_text("")
        if self.controller.result_window:
            self.controller.result_window.set_text("")

    @pyqtSlot()
    def _on_busy(self) -> None:
        """Show busy indicator."""
        self._progress_label.setVisible(True)
        self.progress.setVisible(True)

    @pyqtSlot()
    def _on_idle(self) -> None:
        """Hide busy indicator."""
        self._progress_label.setVisible(False)
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

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _open_settings(self) -> None:
        if self.controller.settings_page and self._settings_page is not None:
            self._show_stack_page(self._settings_page, "settings")

    def _open_history(self) -> None:
        if self.controller.history_window and self._history_page is not None:
            self.controller.history_window._load()
            self._show_stack_page(self._history_page, "history")

    def _open_log(self) -> None:
        if self.controller.log_window and self._log_page is not None:
            self._show_stack_page(self._log_page, "log")

    def _open_ocr_images(self) -> None:
        if self.controller.ocr_images_page and self._ocr_images_page is not None:
            self.controller.ocr_images_page.refresh_gallery()
            self._show_stack_page(self._ocr_images_page, "ocr_images")

    def _open_about(self) -> None:
        if self.controller.about_page and self._about_page is not None:
            self._show_stack_page(self._about_page, "about")

    def _open_capture_window(self) -> None:
        if self.controller.capture_window:
            self.controller.capture_window.show_and_raise()

    def _close_capture_window(self) -> None:
        if self.controller.capture_window:
            self.controller.capture_window.hide()

    def _open_mask_window(self) -> None:
        if self.controller.mask_window:
            self.controller.mask_window.show_and_raise()

    def _close_mask_window(self) -> None:
        if self.controller.mask_window:
            self.controller.mask_window.hide()

    def _open_query_window(self) -> None:
        if self.controller.query_window:
            self.controller.query_window.show_and_raise()

    def _close_query_window(self) -> None:
        if self.controller.query_window:
            self.controller.query_window.hide()

    def _open_result_window(self) -> None:
        if self.controller.result_window:
            self.controller.result_window.show_and_raise()

    def _close_result_window(self) -> None:
        if self.controller.result_window:
            self.controller.result_window.hide()

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

        self._is_quitting = True
        self._tray.hide()
        self._close_auxiliary_windows_for_quit()
        self.close()
        QApplication.quit()

    def _close_auxiliary_windows_for_quit(self) -> None:
        """Close or hide all app-owned top-level helper windows before quitting."""
        controller = self.controller

        for overlay in controller.snip_overlays:
            overlay.hide()
            overlay.close()
        for overlay in controller.capture_region_overlays:
            overlay.hide()
            overlay.close()

        for window in (
            controller.capture_window,
            controller.query_window,
            controller.result_window,
            controller.mask_window,
        ):
            if window is None:
                continue
            window.hide()
            window.close()

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Show main window on tray icon double-click."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_raise()

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        """Hide to tray instead of closing."""
        if self._is_quitting:
            event.accept()
            return
        event.ignore()
        self._hide_to_tray()
