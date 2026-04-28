"""Reusable inline information banner card."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel

from .icons import load_qta_icon


class InfoBannerCard(QFrame):
    """Simple reusable info card for explanatory inline banners."""

    def __init__(
        self,
        title: str,
        content: str,
        parent: QWidget | None = None,
        *,
        icon_name: str = "mdi6.information-outline",
    ) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            """
            QFrame {
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.03);
            }
            QLabel {
                border: none;
                background: transparent;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        icon_label = QLabel(self)
        icon_label.setPixmap(load_qta_icon(icon_name).pixmap(18, 18))
        layout.addWidget(icon_label, 0)
        layout.setAlignment(icon_label, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(6)

        self.titleLabel = QLabel(title, self)
        self.titleLabel.setStyleSheet("font-weight: 600;")
        self.contentLabel = BodyLabel(content, self)
        self.contentLabel.setWordWrap(True)

        text_layout.addWidget(self.titleLabel)
        text_layout.addWidget(self.contentLabel)
        layout.addLayout(text_layout, 1)

    def setTitle(self, title: str) -> None:
        """Set the title text."""
        self.titleLabel.setText(title)

    def setContent(self, content: str) -> None:
        """Set the body content."""
        self.contentLabel.setText(content)
