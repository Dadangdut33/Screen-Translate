"""Helpers for building Fluent setting-card based settings pages."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import SettingCard, SwitchSettingCard


class WidgetSettingCard(SettingCard):
    """Setting card with a custom trailing widget."""

    def __init__(
        self,
        icon: object,
        title: str,
        content: str | None,
        widget: QWidget,
        parent: QWidget | None = None,
        *,
        stretch: int = 0,
    ) -> None:
        super().__init__(icon, title, content, parent)
        self.controlWidget = widget
        if stretch:
            self.hBoxLayout.addStretch(stretch)
        self.hBoxLayout.addWidget(widget, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class SettingsCardGroup(QWidget):
    """Simpler settings-card section that behaves well inside scroll areas."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardsLayout = QVBoxLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.cardsLayout.setSpacing(2)

        self.titleLabel.setStyleSheet("font-size: 20px; font-weight: 600;")
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addLayout(self.cardsLayout)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def addSettingCard(self, card: QWidget) -> None:
        """Add one setting card to the section."""
        card.setParent(self)
        self.cardsLayout.addWidget(card)

    def addSettingCards(self, cards: list[QWidget]) -> None:
        """Add multiple setting cards to the section."""
        for card in cards:
            self.addSettingCard(card)


def make_switch_setting_card(
    *,
    icon: object,
    title: str,
    content: str,
    checked: bool,
    on_changed: Callable[[bool], None],
    parent: QWidget | None = None,
) -> SwitchSettingCard:
    """Build a switch setting card bound to a callback."""
    card = SwitchSettingCard(icon, title, content, parent=parent)
    card.setChecked(checked)
    card.checkedChanged.connect(on_changed)
    return card


def make_row_widget(*widgets: QWidget, stretch_first: bool = True) -> QWidget:
    """Create a compact trailing row widget for setting cards."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    if stretch_first:
        layout.addStretch(1)
    for widget in widgets:
        layout.addWidget(widget)
    return row
