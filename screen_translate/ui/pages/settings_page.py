"""Settings page - every widget writes immediately via QSettings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from PyQt6.QtCore import QEvent, QSize, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QIcon, QPalette
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import ListWidget
import qtawesome as qta
from screen_translate.ui.pages.settings import (
    build_appearance_page,
    build_capture_page,
    build_general_page,
    build_hotkeys_page,
    build_ocr_overrides_page,
    build_ocr_page,
    build_translation_page,
)
from screen_translate.ui.pages.settings.common import configure_form_layout
from screen_translate.ui.theme.style_sheet import StyleSheet
from screen_translate.ui.widgets.icons import load_qta_icon

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)
_SETTINGS_NAV_ICONS: dict[str, str] = {
    "General": "mdi6.cog-outline",
    "Capture": "mdi6.camera-outline",
    "OCR": "mdi6.text-recognition",
    "OCR Key Override": "mdi6.key-variant",
    "Translation": "mdi6.translate",
    "Hotkeys": "mdi6.keyboard-outline",
    "Appearance": "mdi6.palette-outline",
}


class SettingsPage(QWidget):
    """Embedded settings page that persists changes immediately."""

    def __init__(
        self, controller: AppController, parent: QWidget | None = None
    ) -> None:
        """Create the settings page.

        Args:
            controller: Application controller.
            parent: Optional Qt parent for the embedded widget.
        """
        super().__init__(parent)
        self.controller = controller
        self.s = controller.settings
        self._nav_panel: QWidget | None = None
        self._nav_list: ListWidget | None = None
        self._nav_icon_cache: dict[tuple[str, str], QIcon] = {}
        self._nav_refresh_timer = QTimer(self)
        self._nav_refresh_timer.setSingleShot(True)
        self._nav_refresh_timer.timeout.connect(self._refresh_nav_style)
        self._lazy_page_builders: dict[int, Callable[[], QWidget]] = {}
        self._lazy_page_labels: dict[int, str] = {}

        self.setWindowTitle("Settings")
        self.setObjectName("SettingsPage")
        StyleSheet.SETTINGS_DIALOG.apply(self)
        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        content_row = QHBoxLayout()  # content
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(12)

        self._nav_panel = QWidget()
        self._nav_panel.setFixedWidth(220)
        nav_layout = QVBoxLayout(self._nav_panel)
        nav_layout.setContentsMargins(6, 8, 6, 8)
        nav_layout.setSpacing(4)

        self._pages = _CurrentPageStackedWidget()
        self._pages.setContentsMargins(0, 0, 0, 0)
        self._pages.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._pages.setMinimumWidth(0)
        self._nav_list = ListWidget(self._nav_panel)
        self._nav_list.setIconSize(QSize(18, 18))
        self._nav_list.setSpacing(2)
        self._nav_list.setObjectName("SettingsNavList")
        nav_layout.addWidget(self._nav_list, 1)

        pages: list[tuple[str, QWidget | Callable[[], QWidget]]] = [
            ("General", build_general_page(self)),
            ("Capture", build_capture_page(self)),
            ("OCR", build_ocr_page(self)),
            ("OCR Key Override", build_ocr_overrides_page(self)),
            ("Translation", lambda: build_translation_page(self)),
            ("Hotkeys", build_hotkeys_page(self)),
            ("Appearance", build_appearance_page(self)),
        ]

        for label, page_or_builder in pages:
            if callable(page_or_builder):
                page = self._create_lazy_placeholder_page(label)
                page_index = self._pages.count()
                self._lazy_page_builders[page_index] = page_or_builder
                self._lazy_page_labels[page_index] = label
            else:
                page = page_or_builder
                self._prepare_settings_subpage(page)
            item = QListWidgetItem(self._nav_icon(label), label)
            item.setSizeHint(QSize(0, 40))
            self._nav_list.addItem(item)
            self._pages.addWidget(page)

        self._nav_list.currentRowChanged.connect(self._on_nav_row_changed)
        self._nav_list.setCurrentRow(0)
        self._schedule_nav_style_refresh()

        content_row.addWidget(self._nav_panel)
        content_row.addWidget(self._pages, 1)
        layout.addLayout(content_row)

    def changeEvent(self, event: QEvent) -> None:
        """Refresh palette-aware styling when the active theme changes."""
        super().changeEvent(event)
        if event.type() in (QEvent.Type.PaletteChange, QEvent.Type.StyleChange):
            self._schedule_nav_style_refresh(25)

    def _schedule_nav_style_refresh(self, delay_ms: int = 0) -> None:
        """Coalesce repeated sidebar restyles during palette/theme changes."""
        self._nav_refresh_timer.start(max(0, delay_ms))

    def _refresh_nav_style(self) -> None:
        """Apply sidebar colors derived from the current palette."""
        if self._nav_panel is None or self._nav_list is None:
            return

        palette = self.palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        base_color = palette.color(QPalette.ColorRole.Base)
        panel_color = QColor(base_color if base_color.isValid() else window_color)
        border_color = palette.color(QPalette.ColorRole.Mid)
        text_color = palette.color(QPalette.ColorRole.Text)
        if not text_color.isValid():
            text_color = palette.color(QPalette.ColorRole.WindowText)
        active_bg = palette.color(QPalette.ColorRole.Highlight)

        def _is_dark(color: QColor) -> bool:
            return color.lightnessF() < 0.5

        def _contrast_text_for(color: QColor) -> QColor:
            return QColor("#ffffff" if color.lightnessF() < 0.58 else "#111111")

        is_dark_theme = _is_dark(window_color)
        if is_dark_theme:
            panel_color = panel_color.lighter(118)
            border_color = border_color.lighter(135)
        else:
            panel_color = panel_color.darker(103)
            border_color = border_color.darker(110)
            active_bg = active_bg.darker(112)
        active_text = QColor("#ffffff") if is_dark_theme else QColor("#111111")

        for row in range(self._nav_list.count()):
            item = self._nav_list.item(row)
            if item is not None:
                item.setIcon(self._nav_icon(item.text()))

        nav_palette = self._nav_list.palette()
        nav_palette.setColor(QPalette.ColorRole.Text, text_color)
        nav_palette.setColor(QPalette.ColorRole.WindowText, text_color)
        nav_palette.setColor(QPalette.ColorRole.Highlight, active_bg)
        nav_palette.setColor(QPalette.ColorRole.HighlightedText, active_text)
        self._nav_list.setPalette(nav_palette)
        self._sync_nav_item_colors(text_color=text_color, active_text=active_text)
        self._nav_panel.setStyleSheet(
            f"""
            QWidget {{
                background-color: {panel_color.name(QColor.NameFormat.HexArgb)};
                border: 1px solid {border_color.name(QColor.NameFormat.HexArgb)};
                border-radius: 6px;
            }}
            QListWidget#SettingsNavList {{
                background-color: transparent;
                border: 0;
                outline: 0;
                padding: 0;
                color: {text_color.name(QColor.NameFormat.HexArgb)};
                selection-color: {active_text.name(QColor.NameFormat.HexArgb)};
            }}
            QListWidget#SettingsNavList::item {{
                border: 0;
                border-radius: 6px;
                padding: 8px 10px;
                margin: 0 0 2px 0;
                color: {text_color.name(QColor.NameFormat.HexArgb)};
                background-color: transparent;
            }}
            QListWidget#SettingsNavList::item:selected {{
                background-color: {active_bg.name(QColor.NameFormat.HexArgb)};
                color: {active_text.name(QColor.NameFormat.HexArgb)};
                font-weight: 700;
            }}
            QListWidget#SettingsNavList::item:hover {{
                color: {text_color.name(QColor.NameFormat.HexArgb)};
            }}
            """
        )

    def _sync_nav_item_colors(
        self,
        *,
        text_color: QColor | None = None,
        active_text: QColor | None = None,
    ) -> None:
        """Force nav item foreground colors so selected text stays readable."""
        if self._nav_list is None:
            return
        if text_color is None:
            palette = self.palette()
            text_color = palette.color(QPalette.ColorRole.Text)
            if not text_color.isValid():
                text_color = palette.color(QPalette.ColorRole.WindowText)
        if active_text is None:
            palette = self.palette()
            active_bg = palette.color(QPalette.ColorRole.Highlight)
            window_color = palette.color(QPalette.ColorRole.Window)
            active_text = (
                QColor("#ffffff")
                if window_color.lightnessF() < 0.5
                else QColor("#111111")
            )

        current_row = self._nav_list.currentRow()
        for row in range(self._nav_list.count()):
            item = self._nav_list.item(row)
            if item is None:
                continue
            item.setForeground(
                QBrush(active_text if row == current_row else text_color)
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _prepare_settings_subpage(self, page: QWidget) -> QWidget:
        """Apply consistent sizing/layout rules to a settings subpage."""
        page_layout = page.layout()
        if page_layout is not None:
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(12)
        page.setMinimumWidth(0)
        page.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        return page

    def _create_lazy_placeholder_page(self, label: str) -> QWidget:
        """Create a lightweight placeholder for an expensive settings subpage."""
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        hint = QWidget(page)
        hint_layout = QVBoxLayout(hint)
        hint_layout.setContentsMargins(12, 12, 12, 12)
        hint_layout.setSpacing(6)
        title = QLabel(label, hint)
        title.setObjectName("LazySettingsTitle")
        body = QLabel(
            "This section will be prepared when you open it.",
            hint,
        )
        body.setWordWrap(True)
        hint_layout.addWidget(title)
        hint_layout.addWidget(body)
        layout.addWidget(hint)
        layout.addStretch(1)
        return self._prepare_settings_subpage(page)

    def _on_nav_row_changed(self, row: int) -> None:
        """Switch page and lazily build expensive sections on first open."""
        if row < 0:
            return
        self._ensure_page_built(row)
        self._pages.setCurrentIndex(row)
        self._sync_nav_item_colors()

    def _ensure_page_built(self, row: int) -> None:
        """Build a lazy settings subpage if it has not been created yet."""
        builder = self._lazy_page_builders.get(row)
        if builder is None:
            return
        placeholder = self._pages.widget(row)
        try:
            built_page = self._prepare_settings_subpage(builder())
        except Exception:
            logger.exception(
                "Failed to build lazy settings page: %s",
                self._lazy_page_labels.get(row, row),
            )
            return
        self._pages.removeWidget(placeholder)
        placeholder.deleteLater()
        self._pages.insertWidget(row, built_page)
        del self._lazy_page_builders[row]
        self._lazy_page_labels.pop(row, None)

    def _group_form(self, title: str) -> tuple[QGroupBox, QFormLayout]:
        """Create a titled group box with a ready-to-use form layout."""
        group = QGroupBox(title)
        form = QFormLayout(group)
        configure_form_layout(form)
        return group, form

    def _nav_icon(
        self,
        label: str,
    ) -> QIcon:
        """Return a sidebar icon for the given settings section label."""
        if qta is None:
            return QIcon()
        icon_name = _SETTINGS_NAV_ICONS.get(label)
        if not icon_name:
            return QIcon()
        try:
            icon = load_qta_icon(icon_name)
            return icon
        except Exception as exc:
            logger.debug(
                "Could not load qtawesome icon %s for %s: %s",
                icon_name,
                label,
                exc,
            )
            return QIcon()

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        host = self.window()
        if host is not None and host is not self and hasattr(host, "_open_settings"):
            if hasattr(host, "show_and_raise"):
                host.show_and_raise()
            host._open_settings()
            return


class _CurrentPageStackedWidget(QStackedWidget):
    """Stacked widget whose size hints follow the currently visible page."""

    def sizeHint(self) -> QSize:
        current = self.currentWidget()
        if current is not None:
            return current.sizeHint()
        return super().sizeHint()

    def minimumSizeHint(self) -> QSize:
        current = self.currentWidget()
        if current is not None:
            return current.minimumSizeHint()
        return super().minimumSizeHint()
        self.show()
        self.raise_()
        self.activateWindow()


SettingsDialog = SettingsPage
