"""Main application window using QFluentWidgets' FluentWindow shell."""

from __future__ import annotations

import logging
import platform
from typing import TYPE_CHECKING

import pycountry
from PyQt6.QtCore import QObject, QRunnable, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QSplitter,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon as FIF,
    FluentWindow,
    IndeterminateProgressBar,
    MessageBox,
    NavigationItemPosition,
    SmoothScrollArea,
    ToolButton,
    isDarkTheme,
)
import qtawesome as qta

from screen_translate import __version__
from screen_translate.core.ocr.language_compat import resolve_tesseract_language_code
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
_SETTINGS_PLACEHOLDER_ROUTE = "settings_launch"
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
_OCR_INCOMPATIBLE_SUFFIX = "  ⚠"


class _LanguageLoadSignals(QObject):
    """Signals emitted by background language-loading work."""

    finished = pyqtSignal(int, object, object)
    error = pyqtSignal(int, str)


class _LanguageLoadWorker(QRunnable):
    """Load backend language data off the UI thread."""

    def __init__(self, request_id: int, backend: object, source_code: str) -> None:
        super().__init__()
        self.request_id = request_id
        self.backend = backend
        self.source_code = source_code
        self.signals = _LanguageLoadSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:
        try:
            langs = (
                list(self.backend.available_languages())
                if self.backend is not None
                and hasattr(self.backend, "available_languages")
                else []
            )
            if self.backend is not None and hasattr(
                self.backend, "available_target_languages"
            ):
                targets = list(
                    self.backend.available_target_languages(self.source_code)
                )
            else:
                targets = [lang for lang in langs if lang not in {"auto", "Auto"}]
            self.signals.finished.emit(self.request_id, langs, targets)
        except Exception as exc:
            self.signals.error.emit(self.request_id, str(exc))


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
        self._lang_request_id = 0
        self._lang_loading = False
        self._applying_saved_size = False

        self.setWindowTitle(f"{_APP_NAME} v{__version__}")
        self.setMinimumSize(QSize(700, 300))
        self._apply_initial_size()
        StyleSheet.MAIN_WINDOW.apply(self)

        icon = load_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)

        self._build_ui()
        self._build_tray()
        self._connect_signals()
        self._restore_state()

    def _apply_initial_size(self) -> None:
        """Apply either the saved size or the configured initial size."""
        settings = self.controller.settings
        width = max(700, int(settings.get("main_window_initial_width", 950)))
        height = max(300, int(settings.get("main_window_initial_height", 600)))
        saved = str(settings.get("main_window_size", "")).strip()
        if bool(settings.get("save_main_window_size", True)) and saved:
            try:
                width_text, height_text = saved.split(",", 1)
                width = max(700, int(width_text))
                height = max(300, int(height_text))
            except ValueError:
                logger.warning("Invalid main_window_size setting: %r", saved)
        self._applying_saved_size = True
        self.resize(width, height)
        self._applying_saved_size = False

    def _persist_window_size(self) -> None:
        """Persist the current main window size when enabled."""
        if self._applying_saved_size:
            return
        if not bool(self.controller.settings.get("save_main_window_size", True)):
            return
        size = self.size()
        self.controller.settings.set(
            "main_window_size", f"{size.width()},{size.height()}"
        )

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
        self.progress = IndeterminateProgressBar(status_host, start=False)
        self.progress.setVisible(False)
        self.progress.setFixedWidth(180)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet(
            """
            IndeterminateProgressBar {
                background-color: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
            }
            IndeterminateProgressBar::chunk {
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
        self.cb_engine.setMinimumWidth(180)
        self.cb_engine.setMaximumHeight(_COMBOBOX_HEIGHT)
        self.cb_engine.setPlaceholderText("Choose engine")
        controls_layout.addWidget(self.cb_engine)

        controls_layout.addWidget(QLabel("From:"))
        self.cb_source = SuggestionComboBox()
        self.cb_source.setMinimumWidth(140)
        self.cb_source.setMaximumHeight(_COMBOBOX_HEIGHT)
        self.cb_source.setPlaceholderText("Source language")
        self.cb_source.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        controls_layout.addWidget(self.cb_source, 1)

        controls_layout.addWidget(QLabel("To:"))
        self.cb_target = SuggestionComboBox()
        self.cb_target.setMinimumWidth(140)
        self.cb_target.setMaximumHeight(_COMBOBOX_HEIGHT)
        self.cb_target.setPlaceholderText("Target language")
        self.cb_target.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        controls_layout.addWidget(self.cb_target, 1)

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

        self.btn_language_help = ToolButton(
            load_qta_icon("mdi6.help-circle-outline"), controls
        )
        self.btn_language_help.setObjectName("WorkspaceActionButton")
        self.btn_language_help.setToolTip("Explain OCR compatibility markers")
        self.btn_language_help.setFixedSize(38, 38)
        self.btn_language_help.setIconSize(QSize(18, 18))
        controls_layout.addWidget(self.btn_language_help)
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
            (
                "snip",
                load_qta_icon("mdi6.crop"),
                "Snip & Translate",
                self._trigger_snip,
            ),
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
        settings_page: QWidget | None = None,
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
        if settings_page is not None:
            self.register_settings_page(settings_page)
        else:
            self._ensure_settings_placeholder()
        self._add_navigation_items()

    def register_settings_page(self, settings_page: QWidget) -> None:
        """Embed the settings page into the main stacked area."""
        self._remove_settings_placeholder()
        self._settings_page = self._embed_page_widget(
            settings_page,
            "settings",
            FIF.SETTING,
            "Settings",
            NavigationItemPosition.BOTTOM,
        )

    def _ensure_settings_placeholder(self) -> None:
        """Show a lightweight Settings nav item before the real page is built."""
        if self._settings_page is not None:
            return
        self.navigationInterface.addItem(
            routeKey=_SETTINGS_PLACEHOLDER_ROUTE,
            icon=FIF.SETTING,
            text="Settings",
            onClick=self._open_settings,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
            tooltip=None,
        )

    def _remove_settings_placeholder(self) -> None:
        """Remove the temporary Settings nav item if it exists."""
        try:
            self.navigationInterface.panel.removeWidget(_SETTINGS_PLACEHOLDER_ROUTE)
        except Exception:
            pass

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
        self.btn_language_help.clicked.connect(self._show_language_help)
        self.cb_engine.committed.connect(self._on_engine_changed)
        self.cb_source.committed.connect(self._on_source_changed)
        self.cb_target.committed.connect(self._on_target_changed)

        ctrl = self.controller
        ctrl.ocr_started.connect(self._on_busy)
        ctrl.translation_started.connect(self._on_busy)
        ctrl.status_idle.connect(self._on_idle)
        ctrl.ocr_completed.connect(self._on_ocr_result)
        ctrl.translation_completed.connect(self._on_translation_result)
        ctrl.translation_backends_reloaded.connect(self._restore_state)
        ctrl.translation_backends_loading.connect(self._on_backends_loading_changed)

    def _restore_state(self) -> None:
        """Populate comboboxes from settings."""
        s = self.controller.settings

        # Engine list
        self.cb_engine.blockSignals(True)
        self.cb_engine.clear()
        for name in self.controller.available_backend_names():
            self.cb_engine.addItem(name)
        self.cb_engine.refresh_completer()
        saved_engine = s.get("engine", "translators-google")
        idx = self.cb_engine.findText(saved_engine)
        if idx < 0:
            idx = 0
        self.cb_engine.setCurrentIndex(max(0, idx))
        self.cb_engine.blockSignals(False)
        self._on_backends_loading_changed(
            not self.controller.translation_backends_ready()
        )
        self._refresh_lang_combos()

    def _refresh_lang_combos(self) -> None:
        """Update source/target language combos for the active backend asynchronously."""
        s = self.controller.settings
        engine_name = self.cb_engine.currentText()
        backend = self.controller._backends.get(engine_name)
        if engine_name == "None" or backend is None:
            self.cb_source.blockSignals(True)
            self.cb_target.blockSignals(True)
            self.cb_source.clear()
            self.cb_target.clear()
            self.cb_source.blockSignals(False)
            self.cb_target.blockSignals(False)
            self.cb_source.setEnabled(False)
            self.cb_target.setEnabled(False)
            self.refresh_ocr_compatibility_state()
            return

        saved_src = str(s.get("sourceLang", "auto"))
        request_source = saved_src or "auto"
        self._lang_request_id += 1
        request_id = self._lang_request_id
        worker = _LanguageLoadWorker(request_id, backend, request_source)
        worker.signals.finished.connect(self._on_languages_loaded)
        worker.signals.error.connect(self._on_languages_load_error)
        self._set_languages_loading(True)
        self.controller._pool.start(worker)

    def _refresh_target_combo(
        self,
        target_candidates: list[str],
        *,
        saved_target: str | None = None,
    ) -> None:
        """Refresh the target-language combo for the selected source language."""
        self.cb_target.clear()
        self._populate_language_combo(
            self.cb_target,
            target_candidates,
            backend_name=self.cb_engine.currentText().strip(),
        )
        self.cb_target.refresh_completer()

        target_code = saved_target or str(
            self.controller.settings.get("targetLang", "en")
        )
        idx_tgt = self._find_language_index(self.cb_target, target_code)
        if idx_tgt < 0:
            idx_tgt = self._find_language_index(self.cb_target, "en")
        if idx_tgt < 0 and self.cb_target.count() > 0:
            idx_tgt = 0
        if idx_tgt >= 0:
            self.cb_target.setCurrentIndex(idx_tgt)

    def _populate_language_combo(
        self,
        combo: SuggestionComboBox,
        languages: list[str],
        *,
        mark_ocr_compat: bool = False,
        prefix_code: bool = False,
        incompatible_codes: set[str] | None = None,
        backend_name: str | None = None,
    ) -> None:
        """Populate a language combo with display labels while keeping the code as user data."""
        for code in self._sorted_language_codes(
            languages,
            backend_name=backend_name,
            keep_auto_first=True,
        ):
            combo.addItem(
                self._language_label(
                    code,
                    mark_ocr_compat=mark_ocr_compat,
                    prefix_code=prefix_code,
                    incompatible_codes=incompatible_codes,
                    backend_name=backend_name,
                ),
                userData=code,
            )

    def _language_label(
        self,
        code: str,
        *,
        mark_ocr_compat: bool = False,
        prefix_code: bool = False,
        incompatible_codes: set[str] | None = None,
        backend_name: str | None = None,
    ) -> str:
        """Return a human-friendly label for a backend language code."""
        label = self._base_language_label(code, backend_name=backend_name)
        if prefix_code:
            display_code = self._display_language_code(code, backend_name=backend_name)
            label = f"[{display_code.upper()}] {label}"
        if (
            mark_ocr_compat
            and incompatible_codes is not None
            and code in incompatible_codes
        ):
            return f"{label}{_OCR_INCOMPATIBLE_SUFFIX}"
        return label

    def _ocr_incompatible_codes(
        self, languages: list[str], backend_name: str
    ) -> set[str]:
        """Return the set of translation language codes incompatible with current OCR settings."""
        if self.controller.active_ocr_backend_name() != "Tesseract":
            return set()
        installed = self.controller.installed_ocr_languages()
        overrides = self.controller.backend_ocr_overrides(backend_name)
        return {
            code
            for code in languages
            if resolve_tesseract_language_code(
                self.controller.normalize_backend_language_code(backend_name, code),
                installed,
                overrides=overrides,
            )
            is None
        }

    def _base_language_label(self, code: str, backend_name: str | None = None) -> str:
        """Return the human-friendly label for a language code without compatibility suffixes."""
        if backend_name:
            backend = self.controller._backends.get(backend_name)
            backend_label = getattr(backend, "language_display_name", None)
            if callable(backend_label):
                try:
                    label = str(backend_label(code)).strip()
                    if label:
                        return label
                except Exception:
                    pass

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

    def _display_language_code(self, code: str, backend_name: str | None = None) -> str:
        """Return the short visible code used in UI for a backend language entry."""
        if backend_name:
            backend = self.controller._backends.get(backend_name)
            backend_code = getattr(backend, "language_display_code", None)
            if callable(backend_code):
                try:
                    label_code = str(backend_code(code)).strip()
                    if label_code:
                        return label_code
                except Exception:
                    pass
        return code

    def _sorted_language_codes(
        self,
        languages: list[str],
        *,
        backend_name: str | None = None,
        keep_auto_first: bool = True,
    ) -> list[str]:
        """Sort codes by their visible language label instead of raw code."""
        unique = list(dict.fromkeys(languages))
        if not unique:
            return unique

        def sort_key(code: str) -> tuple[str, str]:
            return (
                self._base_language_label(code, backend_name=backend_name).casefold(),
                code.casefold(),
            )

        if keep_auto_first and "auto" in unique:
            return [
                "auto",
                *sorted((code for code in unique if code != "auto"), key=sort_key),
            ]
        if keep_auto_first and "Auto" in unique:
            return [
                "Auto",
                *sorted((code for code in unique if code != "Auto"), key=sort_key),
            ]
        return sorted(unique, key=sort_key)

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
        backend = self.controller._backends.get(self.cb_engine.currentText())
        selected_source = self.cb_source.currentData()
        source_code = selected_source if isinstance(selected_source, str) else "auto"
        self._lang_request_id += 1
        request_id = self._lang_request_id
        worker = _LanguageLoadWorker(request_id, backend, source_code)
        worker.signals.finished.connect(self._on_languages_loaded)
        worker.signals.error.connect(self._on_languages_load_error)
        self._set_languages_loading(True)
        self.controller._pool.start(worker)
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
        self.progress.start()

    @pyqtSlot(bool)
    def _on_backends_loading_changed(self, loading: bool) -> None:
        """Reflect backend-loading state in the main translation controls."""
        self.cb_engine.setEnabled(not loading)
        self.cb_source.setEnabled(
            not loading and not self._lang_loading and self.cb_source.count() > 0
        )
        self.cb_target.setEnabled(
            not loading and not self._lang_loading and self.cb_target.count() > 0
        )
        self.btn_translate.setEnabled(not loading)
        if loading:
            self._progress_label.setText("Loading backends…")
            self._progress_label.setVisible(True)
            self.progress.setVisible(True)
            self.progress.start()
        elif not self._lang_loading:
            self._progress_label.setText("Working...")
            self._progress_label.setVisible(False)
            self.progress.setVisible(False)
            self.progress.stop()

    def _set_languages_loading(self, loading: bool) -> None:
        """Reflect active language-list loading in the main controls."""
        self._lang_loading = loading
        backends_loading = not self.controller.translation_backends_ready()
        self.cb_source.setEnabled(
            not loading and not backends_loading and self.cb_source.count() > 0
        )
        self.cb_target.setEnabled(
            not loading and not backends_loading and self.cb_target.count() > 0
        )
        self.btn_translate.setEnabled(not loading and not backends_loading)
        if loading:
            self._progress_label.setText("Loading languages…")
            self._progress_label.setVisible(True)
            self.progress.setVisible(True)
            self.progress.start()
        elif not backends_loading:
            self._progress_label.setText("Working...")
            self._progress_label.setVisible(False)
            self.progress.setVisible(False)
            self.progress.stop()

    @pyqtSlot(int, object, object)
    def _on_languages_loaded(
        self,
        request_id: int,
        langs_obj: object,
        targets_obj: object,
    ) -> None:
        """Populate language combos after background loading completes."""
        if request_id != self._lang_request_id:
            return
        langs = list(langs_obj) if isinstance(langs_obj, list) else []
        targets = list(targets_obj) if isinstance(targets_obj, list) else []
        s = self.controller.settings
        backend_name = self.cb_engine.currentText().strip()
        incompatible_codes = self._ocr_incompatible_codes(langs, backend_name)

        self.cb_source.blockSignals(True)
        self.cb_target.blockSignals(True)
        self.cb_source.clear()
        self._populate_language_combo(
            self.cb_source,
            langs,
            mark_ocr_compat=True,
            prefix_code=bool(
                self.controller.settings.get("show_source_language_codes", False)
            ),
            incompatible_codes=incompatible_codes,
            backend_name=backend_name,
        )
        self.cb_source.refresh_completer()

        saved_src = str(s.get("sourceLang", "auto"))
        idx_src = self._find_language_index(self.cb_source, saved_src)
        if idx_src < 0:
            idx_src = self._find_language_index(self.cb_source, "auto")
        if idx_src < 0 and self.cb_source.count() > 0:
            idx_src = 0
        if idx_src >= 0:
            self.cb_source.setCurrentIndex(idx_src)

        self._refresh_target_combo(targets, saved_target=str(s.get("targetLang", "en")))
        self.cb_source.blockSignals(False)
        self.cb_target.blockSignals(False)

        self._persist_selected_language(self.cb_source, "sourceLang")
        self._persist_selected_language(self.cb_target, "targetLang")
        self.refresh_ocr_compatibility_state()
        self._set_languages_loading(False)

    @pyqtSlot(int, str)
    def _on_languages_load_error(self, request_id: int, error: str) -> None:
        """Handle background language-loading failure."""
        if request_id != self._lang_request_id:
            return
        logger.warning("Failed to load backend languages: %s", error)
        self.cb_source.blockSignals(True)
        self.cb_target.blockSignals(True)
        self.cb_source.clear()
        self.cb_target.clear()
        self.cb_source.blockSignals(False)
        self.cb_target.blockSignals(False)
        self.refresh_ocr_compatibility_state()
        self._set_languages_loading(False)

    @pyqtSlot()
    def _show_language_help(self) -> None:
        """Explain the OCR compatibility warning marker in the source-language list."""
        box = MessageBox(
            "OCR Compatibility",
            (
                "A ⚠ marker means that the selected translation language does not currently "
                "map / match into the OCR languages.\n\n"
                "When using OCR, capture and snipping are disabled for those "
                "source languages until you either choose a compatible language or add an "
                "OCR Key Override in Settings."
            ),
            self,
        )
        box.yesButton.setText("OK")
        box.cancelButton.hide()
        box.exec()

    @pyqtSlot()
    def _on_idle(self) -> None:
        """Hide busy indicator."""
        self._progress_label.setVisible(False)
        self.progress.setVisible(False)
        self.progress.stop()

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
        if self.controller.settings_page is None and hasattr(
            self.controller, "create_settings_page"
        ):
            self.controller.create_settings_page()  # type: ignore[attr-defined]
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
        self.controller.shutdown()
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
        self._persist_window_size()
        self._hide_to_tray()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Persist window size changes while the user resizes the main window."""
        super().resizeEvent(event)
        self._persist_window_size()
