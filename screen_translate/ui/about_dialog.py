"""About application dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from screen_translate import __version__


class AboutDialog(QDialog):
    """Simple About dialog showing version, license, and links."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the About dialog.

        Args:
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self.setWindowTitle("About Screen Translate")
        self.setFixedSize(400, 300)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel(f"<h2>Screen Translate</h2><h3>v{__version__}</h3>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            "A desktop screen OCR and translation tool.\n"
            "Capture any region on screen and translate it instantly\n"
            "using multiple translation engines."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        license_lbl = QLabel("License: MIT")
        license_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(license_lbl)

        github = QLabel('<a href="https://github.com/Dadangdut33/Screen-Translate">GitHub Repository</a>')
        github.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github.setOpenExternalLinks(True)
        layout.addWidget(github)

        layout.addStretch()

        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn.rejected.connect(self.accept)
        layout.addWidget(btn)
