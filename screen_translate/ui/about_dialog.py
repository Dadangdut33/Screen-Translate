"""About application page."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PushButton, TitleLabel

from screen_translate import __version__
from screen_translate.ui.style_sheet import StyleSheet
from screen_translate.ui.utils import load_icon


class AboutDialog(QWidget):
    """About page showing version, license, and links."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the About dialog.

        Args:
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setObjectName("AboutPage")
        StyleSheet.AUXILIARY_WINDOW.apply(self)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(0)

        outer.addStretch(1)

        card_row = QHBoxLayout()
        card_row.addStretch(1)

        card = QFrame(self)
        card.setObjectName("AboutCard")
        card.setMinimumWidth(520)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(14)

        icon_label = QLabel(card)
        icon = load_icon()
        if not icon.isNull():
            pixmap = icon.pixmap(72, 72)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_label)

        title = TitleLabel("Screen Translate", card)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        version = BodyLabel(f"Version {__version__}", card)
        version.setObjectName("AboutVersion")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(version)

        desc = BodyLabel(
            "A desktop screen OCR and translation tool.\n"
            "Capture any region on screen and translate it instantly\n"
            "using multiple translation engines.",
            card,
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        meta = BodyLabel("License: MIT", card)
        meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(meta)

        github_btn = PushButton("Open GitHub Repository", card)
        github_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/Dadangdut33/Screen-Translate")
            )
        )
        card_layout.addWidget(github_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        card_row.addWidget(card)
        card_row.addStretch(1)
        outer.addLayout(card_row)
        outer.addStretch(1)
