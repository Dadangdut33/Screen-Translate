"""Transparent, draggable/resizable capture overlay window."""

from __future__ import annotations

import io
import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from platformdirs import user_data_dir
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSlot
from PyQt6.QtGui import (
    QAction,
    QColor,
    QContextMenuEvent,
    QImage,
    QMouseEvent,
    QPainter,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

from screen_translate.ui.utils import load_icon

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)


class CaptureWindow(QWidget):
    """Floating semi-transparent overlay used for continuous OCR capture.

    The user positions and resizes this window over the region of interest.
    Clicking *Capture & Translate* grabs pixels exactly under the window
    and submits them to the OCR pipeline.
    """

    def __init__(self, controller: AppController) -> None:
        """Create the capture window.

        Args:
            controller: Application controller.
        """
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.controller = controller
        self._drag_pos: QPoint | None = None
        self._is_hidden_titlebar = False
        self._overlay_opacity = 0.8

        icon = load_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)

        self.setMinimumSize(200, 80)
        self.resize(600, 150)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self._build_ui()
        self._build_context_menu()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        top_row = QHBoxLayout()

        self._drag_label = QLabel("▶ Drag")
        self._drag_label.setToolTip("Drag here to move the window")
        self._drag_label.setCursor(Qt.CursorShape.OpenHandCursor)
        top_row.addWidget(self._drag_label)

        self._btn_capture = QPushButton("Capture & Translate")
        self._btn_capture.clicked.connect(self.trigger_capture)
        top_row.addWidget(self._btn_capture)

        self._btn_set_region = QPushButton("Set Region")
        self._btn_set_region.clicked.connect(self._open_virtual_region_selector)
        top_row.addWidget(self._btn_set_region)

        top_row.addStretch()

        self._lbl_opacity = QLabel("Opacity 80%")
        top_row.addWidget(self._lbl_opacity)

        self._lbl_mode = QLabel("")
        top_row.addWidget(self._lbl_mode)

        layout.addLayout(top_row)
        layout.addStretch()

        # Size grip in bottom-right corner
        grip_row = QHBoxLayout()
        grip_row.addStretch()
        grip_row.addWidget(QSizeGrip(self))
        layout.addLayout(grip_row)

        # Drag interactions
        self._drag_label.mousePressEvent = self._drag_press  # type: ignore[method-assign]
        self._drag_label.mouseMoveEvent = self._drag_move  # type: ignore[method-assign]
        self._drag_label.mouseReleaseEvent = self._drag_release  # type: ignore[method-assign]

    def _build_context_menu(self) -> None:
        self._ctx_menu = QMenu(self)
        self._act_topmost = QAction("Always on Top", self, checkable=True, checked=True)
        self._act_topmost.triggered.connect(self._toggle_topmost)
        self._ctx_menu.addAction(self._act_topmost)
        self._ctx_menu.addSeparator()
        self._ctx_menu.addAction(
            "Increase Opacity (+10%)", lambda: self._adjust_opacity(0.1)
        )
        self._ctx_menu.addAction(
            "Decrease Opacity (-10%)", lambda: self._adjust_opacity(-0.1)
        )
        self._ctx_menu.addSeparator()
        self._ctx_menu.addAction("Set Capture Region", self._open_virtual_region_selector)
        self._ctx_menu.addSeparator()
        self._ctx_menu.addAction("Close", self.hide)

    # ------------------------------------------------------------------
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # type: ignore[override]
        """Show the context menu on right-click."""
        self._ctx_menu.exec(event.globalPos())

    def paintEvent(self, event: object) -> None:  # type: ignore[override]
        """Draw a semi-transparent tinted background."""
        painter = QPainter(self)
        alpha = max(20, min(220, int(160 * self._overlay_opacity)))
        painter.fillRect(self.rect(), QColor(0, 0, 0, alpha))

    def _drag_press(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            self._drag_label.setCursor(Qt.CursorShape.ClosedHandCursor)

    def _drag_move(self, event: QMouseEvent) -> None:
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _drag_release(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        self._drag_label.setCursor(Qt.CursorShape.OpenHandCursor)

    @pyqtSlot()
    def trigger_capture(self) -> None:
        """Grab the screen region beneath this window and start OCR."""

        self._sync_mode_ui()
        geo = self.geometry()
        global_top_left = self.mapToGlobal(QPoint(0, 0))
        frame_top_left = self.frameGeometry().topLeft()
        was_visible = self.isVisible()
        if was_visible:
            self.hide()
        QApplication.processEvents()

        # Apply user offset from settings
        sx: int = int(self.controller.settings.get("offSetX", 0))
        sy: int = int(self.controller.settings.get("offSetY", 0))
        sw: int = int(self.controller.settings.get("offSetW", 0))
        sh: int = int(self.controller.settings.get("offSetH", 0))

        capture_mode = str(self.controller.settings.get("capture_mode", "Floating Window"))
        if capture_mode == "Virtual Overlay":
            stored_rect = self.controller.get_capture_region()
            if stored_rect is None:
                logger.info("No virtual capture region is set yet; opening selector.")
                if was_visible:
                    self.show()
                self._open_virtual_region_selector()
                return
            capture_rect = QRect(
                stored_rect.x() + sx,
                stored_rect.y() + sy,
                max(1, stored_rect.width() + sw),
                max(1, stored_rect.height() + sh),
            )
        else:
            capture_rect = QRect(
                global_top_left.x() + sx,
                global_top_left.y() + sy,
                max(1, geo.width() + sw),
                max(1, geo.height() + sh),
            )
        screen = QApplication.screenAt(capture_rect.center()) or QApplication.primaryScreen()
        save_full_image = bool(self.controller.settings.get("keep_image", True))
        save_cropped_image = bool(self.controller.settings.get("save_cropped_image", False))
        logger.debug(
            "Capture trigger: mode=%s window_geo=%s mapToGlobal=%s frame_top_left=%s stored_region=%s offsets=(%d,%d,%d,%d) capture_rect=%s screen=%s",
            capture_mode,
            geo.getRect(),
            (global_top_left.x(), global_top_left.y()),
            (frame_top_left.x(), frame_top_left.y()),
            self.controller.get_capture_region().getRect() if self.controller.get_capture_region() is not None else None,
            sx,
            sy,
            sw,
            sh,
            capture_rect.getRect(),
            screen.name() if screen is not None else "None",
        )
        if screen is not None:
            logger.debug(
                "Capture screen geometry=%s virtual_geometry=%s",
                screen.geometry().getRect(),
                screen.virtualGeometry().getRect(),
            )
        if screen:
            pixmap: QPixmap = screen.grabWindow(
                0,
                capture_rect.x(),
                capture_rect.y(),
                capture_rect.width(),
                capture_rect.height(),
            )
            if pixmap.isNull():
                pil_img = _capture_with_external_tool(
                    capture_rect,
                    screen,
                    keep_full_image=save_full_image,
                )
                if pil_img is not None:
                    if save_cropped_image:
                        _save_cropped_image(pil_img)
                    self.controller.run_ocr(pil_img)
                else:
                    logger.error(
                        "Screen capture returned a null pixmap. This can happen on Linux/Wayland when "
                        "the compositor blocks direct screen grabs."
                    )
            else:
                pil_img = _pixmap_to_pil(pixmap)
                if pil_img is not None:
                    if save_cropped_image:
                        _save_cropped_image(pil_img)
                    self.controller.run_ocr(pil_img)
                else:
                    logger.error("Could not convert captured pixmap to PIL image")

        if was_visible:
            self.show()
            self.raise_()
            self.activateWindow()

    @pyqtSlot(bool)
    def _toggle_topmost(self, checked: bool) -> None:
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def set_overlay_opacity(self, opacity: float) -> None:
        """Adjust the overlay tint strength without relying on window-manager opacity."""
        self._overlay_opacity = min(1.0, max(0.1, opacity))
        pct = int(self._overlay_opacity * 100)
        self._lbl_opacity.setText(f"Opacity {pct}%")
        self.update()

    def _adjust_opacity(self, delta: float) -> None:
        self.set_overlay_opacity(self._overlay_opacity + delta)

    def _sync_mode_ui(self) -> None:
        """Update helper controls based on the current capture mode."""
        capture_mode = str(self.controller.settings.get("capture_mode", "Floating Window"))
        is_virtual = capture_mode == "Virtual Overlay"
        self._btn_set_region.setVisible(is_virtual)
        self._lbl_mode.setText("Virtual Overlay" if is_virtual else "Floating Window")
        self._drag_label.setText("Set with overlay" if is_virtual else "▶ Drag")
        self._drag_label.setToolTip(
            "Use Set Region to define the virtual capture area"
            if is_virtual
            else "Drag here to move the window"
        )

    def _open_virtual_region_selector(self) -> None:
        """Open the persistent virtual region selector."""
        self.controller.start_capture_region_selection()

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        self._sync_mode_ui()
        self.show()
        self.raise_()
        self.activateWindow()


def _pixmap_to_pil(pixmap: QPixmap) -> object | None:
    """Convert a QPixmap to a Pillow Image."""
    try:
        from PIL import Image

        img = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB32)
        bits = img.bits()
        if bits is None:
            return None
        bits.setsize(img.sizeInBytes())
        return Image.frombytes(
            "RGB",
            (img.width(), img.height()),
            bytes(bits),
            "raw",
            "BGRX",
        )
    except Exception as exc:
        logger.exception("capture pixmap_to_pil failed: %s", exc)
        return None


def _capture_with_grim(x: int, y: int, width: int, height: int) -> object | None:
    """Use grim as a Wayland-friendly capture fallback for a screen region."""
    if shutil.which("grim") is None:
        return None

    try:
        from PIL import Image

        geometry = f"{x},{y} {max(1, width)}x{max(1, height)}"
        result = subprocess.run(
            ["grim", "-g", geometry, "-"],
            check=True,
            capture_output=True,
        )
        if not result.stdout:
            return None
        image = Image.open(io.BytesIO(result.stdout))
        return image.convert("RGB")
    except subprocess.CalledProcessError as exc:
        logger.error("grim region capture failed with stderr: %s", exc.stderr.decode(errors="replace").strip())
        return None
    except Exception as exc:
        logger.exception("grim region capture failed: %s", exc)
        return None


def _capture_with_spectacle(
    capture_rect: QRect,
    screen: object,
    *,
    keep_full_image: bool,
) -> object | None:
    """Use Spectacle background mode and crop the requested region locally."""
    if shutil.which("spectacle") is None:
        return None

    try:
        from PIL import Image

        captured_dir = _captured_dir()
        captured_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = captured_dir / _capture_filename(prefix="full_capture")

        try:
            result = subprocess.run(
                ["spectacle", "-b", "-n", "-f", "-o", str(tmp_path)],
                check=True,
                capture_output=True,
            )
            if result.stderr:
                logger.debug("spectacle stderr: %s", result.stderr.decode(errors="replace").strip())

            with Image.open(tmp_path) as image:
                virtual_geometry = screen.virtualGeometry() if screen is not None else capture_rect
                crop_left = max(0, capture_rect.x() - virtual_geometry.x())
                crop_top = max(0, capture_rect.y() - virtual_geometry.y())
                crop_right = max(crop_left + 1, crop_left + capture_rect.width())
                crop_bottom = max(crop_top + 1, crop_top + capture_rect.height())
                crop_box = (
                    crop_left,
                    crop_top,
                    min(image.width, crop_right),
                    min(image.height, crop_bottom),
                )
                logger.debug(
                    "Spectacle crop: file=%s image_size=%s virtual_geometry=%s capture_rect=%s crop_box=%s keep_full=%s",
                    tmp_path,
                    image.size,
                    virtual_geometry.getRect() if hasattr(virtual_geometry, "getRect") else virtual_geometry,
                    capture_rect.getRect(),
                    crop_box,
                    keep_full_image,
                )
                return image.convert("RGB").crop(crop_box)
        finally:
            if not keep_full_image:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
    except subprocess.CalledProcessError as exc:
        logger.error("spectacle full capture failed with stderr: %s", exc.stderr.decode(errors="replace").strip())
        return None
    except Exception as exc:
        logger.exception("spectacle full capture failed: %s", exc)
        return None


def _capture_with_external_tool(
    capture_rect: QRect,
    screen: object,
    *,
    keep_full_image: bool,
) -> object | None:
    """Try platform-specific external capture tools when Qt screen grab is blocked."""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    session = os.environ.get("DESKTOP_SESSION", "").lower()

    if "kde" in desktop or "plasma" in desktop or "plasma" in session:
        image = _capture_with_spectacle(
            capture_rect,
            screen,
            keep_full_image=keep_full_image,
        )
        if image is not None:
            return image

    return _capture_with_grim(
        capture_rect.x(),
        capture_rect.y(),
        capture_rect.width(),
        capture_rect.height(),
    )


def _captured_dir() -> Path:
    """Return the application's captured-images directory."""
    return Path(user_data_dir("screen-translate", "Dadangdut33")) / "captured"


def _capture_filename(prefix: str = "capture") -> str:
    """Generate a timestamped filename for external capture tools."""
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"


def _save_cropped_image(image: object) -> None:
    """Persist the final cropped capture image for debugging."""
    try:
        output_path = _captured_dir() / _capture_filename(prefix="cropped_capture")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        logger.info("Saved cropped capture to %s", output_path)
    except Exception as exc:
        logger.exception("Could not save cropped capture: %s", exc)
