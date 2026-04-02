"""Shared screen capture helpers for capture-window and snip flows."""

from __future__ import annotations

import io
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from platformdirs import user_data_dir
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QImage, QPixmap

logger = logging.getLogger(__name__)


def pixmap_to_pil(pixmap: QPixmap) -> object | None:
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


def captured_dir() -> Path:
    """Return the application's captured-images directory."""
    return Path(user_data_dir("screen-translate", "Dadangdut33")) / "captured"


def capture_filename(prefix: str = "capture") -> str:
    """Generate a timestamped filename for external capture tools."""
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"


def save_cropped_image(image: Any, prefix: str = "cropped_capture") -> None:
    """Persist a captured image for debugging."""
    try:
        output_path = captured_dir() / capture_filename(prefix=prefix)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        logger.info("Saved cropped capture to %s", output_path)
    except Exception as exc:
        logger.exception("Could not save cropped capture: %s", exc)


def capture_rect_image(
    capture_rect: QRect,
    screen: Any,
    *,
    keep_full_image: bool,
    backend: str,
) -> object | None:
    """Capture a global rectangle, falling back to external tools when needed."""
    if screen is None:
        return None

    pixmap: QPixmap = screen.grabWindow(
        0,
        capture_rect.x(),
        capture_rect.y(),
        capture_rect.width(),
        capture_rect.height(),
    )
    if not pixmap.isNull():
        return pixmap_to_pil(pixmap)

    return _capture_with_external_tool(
        capture_rect,
        screen,
        keep_full_image=keep_full_image,
        backend=backend,
    )


def capture_interactive_region_image(
    *,
    keep_full_image: bool,
    backend: str,
) -> object | None:
    """Capture a user-selected screen region via desktop-native tools."""
    if backend == "Spectacle":
        return _capture_interactive_with_spectacle(keep_full_image=keep_full_image)
    if backend == "GNOME Shell":
        return _capture_interactive_with_gnome_shell(keep_full_image=keep_full_image)

    return None


def preferred_interactive_snip_backend() -> str | None:
    """Return the preferred desktop-native interactive snip backend, if any."""
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if session != "wayland":
        return None
    if "kde" in desktop or "plasma" in desktop:
        return "Spectacle"
    if "gnome" in desktop:
        return "GNOME Shell"
    return None


def _capture_with_grim(x: int, y: int, width: int, height: int) -> object | None:
    """Use grim as a Wayland-friendly capture fallback for a screen region."""
    if shutil.which("grim") is None:
        return None

    logger.debug(
        "Attempting grim capture for region x=%d y=%d width=%d height=%d",
        x,
        y,
        width,
        height,
    )
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
        logger.error(
            "grim region capture failed with stderr: %s",
            exc.stderr.decode(errors="replace").strip(),
        )
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

    logger.debug(
        "Attempting Spectacle capture for region %s with keep_full_image=%s",
        capture_rect.getRect(),
        keep_full_image,
    )
    try:
        from PIL import Image

        output_dir = captured_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = output_dir / capture_filename(prefix="full_capture")

        try:
            result = subprocess.run(
                ["spectacle", "-b", "-n", "-f", "-o", str(tmp_path)],
                check=True,
                capture_output=True,
            )
            if result.stderr:
                logger.debug(
                    "spectacle stderr: %s",
                    result.stderr.decode(errors="replace").strip(),
                )

            with Image.open(tmp_path) as image:
                virtual_geometry = (
                    screen.virtualGeometry() if screen is not None else capture_rect
                )
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
                    (
                        virtual_geometry.getRect()
                        if hasattr(virtual_geometry, "getRect")
                        else virtual_geometry
                    ),
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
        logger.error(
            "spectacle full capture failed with stderr: %s",
            exc.stderr.decode(errors="replace").strip(),
        )
        return None
    except Exception as exc:
        logger.exception("spectacle full capture failed: %s", exc)
        return None


def _capture_with_gnome_shell(
    capture_rect: QRect,
    *,
    keep_full_image: bool,
) -> object | None:
    """Use GNOME Shell's screenshot D-Bus API for area capture."""
    if shutil.which("gdbus") is None:
        return None

    logger.debug(
        "Attempting GNOME Shell capture for region %s with keep_full_image=%s",
        capture_rect.getRect(),
        keep_full_image,
    )
    try:
        from PIL import Image

        output_dir = captured_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = output_dir / capture_filename(prefix="gnome_capture")

        result = subprocess.run(
            [
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.gnome.Shell.Screenshot",
                "--object-path",
                "/org/gnome/Shell/Screenshot",
                "--method",
                "org.gnome.Shell.Screenshot.ScreenshotArea",
                str(capture_rect.x()),
                str(capture_rect.y()),
                str(max(1, capture_rect.width())),
                str(max(1, capture_rect.height())),
                "false",
                str(tmp_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        success, filename_used = _parse_gnome_screenshot_result(result.stdout)
        if not success:
            logger.error(
                "GNOME Shell ScreenshotArea reported failure for rect %s",
                capture_rect.getRect(),
            )
            return None

        final_path = Path(filename_used) if filename_used else tmp_path
        with Image.open(final_path) as image:
            return image.convert("RGB")
    except subprocess.CalledProcessError as exc:
        logger.error(
            "GNOME Shell ScreenshotArea failed with stderr: %s",
            exc.stderr.strip(),
        )
        return None
    except Exception as exc:
        logger.exception("GNOME Shell ScreenshotArea failed: %s", exc)
        return None
    finally:
        if not keep_full_image:
            for candidate in (locals().get("tmp_path"), locals().get("final_path")):
                if isinstance(candidate, Path):
                    try:
                        candidate.unlink()
                    except OSError:
                        pass


def _capture_interactive_with_gnome_shell(*, keep_full_image: bool) -> object | None:
    """Use GNOME Shell's native area picker and screenshot D-Bus methods."""
    if shutil.which("gdbus") is None:
        return None

    logger.debug(
        "Attempting GNOME Shell interactive capture with keep_full_image=%s",
        keep_full_image,
    )
    try:
        result = subprocess.run(
            [
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.gnome.Shell.Screenshot",
                "--object-path",
                "/org/gnome/Shell/Screenshot",
                "--method",
                "org.gnome.Shell.Screenshot.SelectArea",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        capture_rect = _parse_gnome_select_area_result(result.stdout)
        if (
            capture_rect is None
            or capture_rect.width() < 4
            or capture_rect.height() < 4
        ):
            return None
        return _capture_with_gnome_shell(
            capture_rect,
            keep_full_image=keep_full_image,
        )
    except subprocess.CalledProcessError as exc:
        logger.error(
            "GNOME Shell SelectArea failed with stderr: %s",
            exc.stderr.strip(),
        )
        return None
    except Exception as exc:
        logger.exception("GNOME Shell SelectArea failed: %s", exc)
        return None


def _capture_interactive_with_spectacle(*, keep_full_image: bool) -> object | None:
    """Use Spectacle's native region picker and return the captured image."""
    if shutil.which("spectacle") is None:
        return None

    try:
        from PIL import Image

        output_dir = captured_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = output_dir / capture_filename(prefix="snip_capture")

        try:
            result = subprocess.run(
                ["spectacle", "-b", "-n", "-r", "-o", str(tmp_path)],
                check=True,
                capture_output=True,
            )
            if result.stderr:
                logger.debug(
                    "spectacle snip stderr: %s",
                    result.stderr.decode(errors="replace").strip(),
                )

            with Image.open(tmp_path) as image:
                pil_image = image.convert("RGB")
                logger.debug(
                    "Spectacle snip image loaded from %s with size=%s",
                    tmp_path,
                    pil_image.size,
                )
                return pil_image
        finally:
            if not keep_full_image:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
    except subprocess.CalledProcessError as exc:
        logger.error(
            "spectacle snip capture failed with stderr: %s",
            exc.stderr.decode(errors="replace").strip(),
        )
        return None
    except Exception as exc:
        logger.exception("spectacle snip capture failed: %s", exc)
        return None


def _parse_gnome_select_area_result(output: str) -> QRect | None:
    """Parse `gdbus` output from GNOME Shell SelectArea."""
    matches = re.findall(r"-?\d+", output)
    if len(matches) < 4:
        logger.error("Could not parse GNOME Shell SelectArea output: %r", output)
        return None
    x, y, width, height = [int(value) for value in matches[:4]]
    return QRect(x, y, max(1, width), max(1, height))


def _parse_gnome_screenshot_result(output: str) -> tuple[bool, str]:
    """Parse `gdbus` output from GNOME Shell ScreenshotArea."""
    success_match = re.search(r"\b(true|false)\b", output, flags=re.IGNORECASE)
    filename_match = re.search(r"'([^']+)'", output)
    success = bool(success_match and success_match.group(1).lower() == "true")
    filename_used = filename_match.group(1) if filename_match else ""
    return success, filename_used


def _capture_with_external_tool(
    capture_rect: QRect,
    screen: object,
    *,
    keep_full_image: bool,
    backend: str,
) -> object | None:
    """Try platform-specific external capture tools when Qt screen grab is blocked."""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    session = os.environ.get("DESKTOP_SESSION", "").lower()

    if backend == "Spectacle":
        return _capture_with_spectacle(
            capture_rect,
            screen,
            keep_full_image=keep_full_image,
        )
    if backend == "GNOME Shell":
        return _capture_with_gnome_shell(
            capture_rect,
            keep_full_image=keep_full_image,
        )
    if backend == "grim":
        return _capture_with_grim(
            capture_rect.x(),
            capture_rect.y(),
            capture_rect.width(),
            capture_rect.height(),
        )

    if "kde" in desktop or "plasma" in desktop or "plasma" in session:
        image = _capture_with_spectacle(
            capture_rect,
            screen,
            keep_full_image=keep_full_image,
        )
        if image is not None:
            return image

    if "gnome" in desktop or "gnome" in session:
        image = _capture_with_gnome_shell(
            capture_rect,
            keep_full_image=keep_full_image,
        )
        if image is not None:
            return image

    # fall back to grim for Wayland
    return _capture_with_grim(
        capture_rect.x(),
        capture_rect.y(),
        capture_rect.width(),
        capture_rect.height(),
    )
