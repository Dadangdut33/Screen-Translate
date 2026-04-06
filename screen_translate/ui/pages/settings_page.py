"""Settings page - every widget writes immediately via QSettings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QEvent, QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QListWidgetItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, ListWidget, ProgressBar
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
from screen_translate.ui.theme.style_sheet import StyleSheet

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
        self._logger = logger
        self._nav_panel: QWidget | None = None
        self._nav_list: ListWidget | None = None
        self._theme_overlay: QWidget | None = None
        self._nav_icon_cache: dict[tuple[str, str], QIcon] = {}
        self._nav_refresh_timer = QTimer(self)
        self._nav_refresh_timer.setSingleShot(True)
        self._nav_refresh_timer.timeout.connect(self._refresh_nav_style)

        self.setWindowTitle("Settings")
        self.setObjectName("SettingsPage")
        StyleSheet.SETTINGS_DIALOG.apply(self)
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
        nav_layout.setSpacing(8)

        self._pages = QStackedWidget()
        self._nav_list = ListWidget(self._nav_panel)
        self._nav_list.setIconSize(QSize(18, 18))
        self._nav_list.setSpacing(4)
        self._nav_list.setObjectName("SettingsNavList")
        nav_layout.addWidget(self._nav_list, 1)

        pages = [
            ("General", build_general_page(self)),
            ("Capture", build_capture_page(self)),
            ("OCR", build_ocr_page(self)),
            ("OCR Key Override", build_ocr_overrides_page(self)),
            ("Translation", build_translation_page(self)),
            ("Hotkeys", build_hotkeys_page(self)),
            ("Appearance", build_appearance_page(self)),
        ]

        for index, (label, page) in enumerate(pages):
            item = QListWidgetItem(self._nav_icon(label), label)
            item.setSizeHint(QSize(0, 40))
            self._nav_list.addItem(item)
            self._pages.addWidget(page)

        self._nav_list.currentRowChanged.connect(self._pages.setCurrentIndex)
        self._nav_list.setCurrentRow(0)
        self._pages.setCurrentIndex(0)
        self._schedule_nav_style_refresh()

        content_row.addWidget(self._nav_panel)
        content_row.addWidget(self._pages, 1)
        layout.addLayout(content_row)
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

        title = BodyLabel("Applying theme...", card)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("themeLoadingTitle")
        card_layout.addWidget(title)

        progress = ProgressBar(card)
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

        for row in range(self._nav_list.count()):
            item = self._nav_list.item(row)
            if item is not None:
                item.setIcon(self._nav_icon(item.text()))

        self._sync_theme_overlay_style()
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
            }}
            QListWidget#SettingsNavList::item {{
                border: 0;
                border-radius: 6px;
                padding: 10px 12px;
                margin: 0 0 4px 0;
                color: {text_color.name(QColor.NameFormat.HexArgb)};
            }}
            QListWidget#SettingsNavList::item:selected {{
                background-color: {active_bg.name(QColor.NameFormat.HexArgb)};
            }}
            """
        )

    def resizeEvent(self, event: Any) -> None:
        """Keep the theme-loading overlay sized to the dialog."""
        super().resizeEvent(event)
        if self._theme_overlay is not None:
            self._theme_overlay.setGeometry(self.rect())

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
    ) -> QIcon:
        """Return a sidebar icon for the given settings section label."""
        if qta is None:
            return QIcon()
        icon_name = _SETTINGS_NAV_ICONS.get(label)
        if not icon_name:
            return QIcon()
        try:
            color = self.palette().color(QPalette.ColorRole.WindowText)
            color_key = (label, color.name(QColor.NameFormat.HexArgb))
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

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        host = self.window()
        if host is not None and host is not self and hasattr(host, "_open_settings"):
            if hasattr(host, "show_and_raise"):
                host.show_and_raise()
            host._open_settings()
            return
        self.show()
        self.raise_()
        self.activateWindow()


SettingsDialog = SettingsPage
