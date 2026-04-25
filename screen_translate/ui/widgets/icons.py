"""Utils for icons."""

from PyQt6.QtGui import QIcon

from qfluentwidgets import (
    isDarkTheme,
)
import qtawesome as qta


def load_qta_icon(icon_name: str) -> QIcon:
    """Create a theme aware icon with an explicit disabled-state color."""
    if isDarkTheme():
        color = "#f4f4f4"
        disabled = "#6f6f6f"
    else:
        color = "#1c1c1c"
        disabled = "#9a9a9a"
    normal_icon = qta.icon(icon_name, color=color)
    disabled_icon = qta.icon(icon_name, color=disabled)
    icon = QIcon()
    for size in (16, 18, 20, 24, 32):
        icon.addPixmap(normal_icon.pixmap(size, size), QIcon.Mode.Normal)
        icon.addPixmap(disabled_icon.pixmap(size, size), QIcon.Mode.Disabled)
    return icon
