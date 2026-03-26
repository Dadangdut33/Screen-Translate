"""Application entry point - constructs QApplication and launches the app."""

from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication

from screen_translate import __version__
from screen_translate.config.settings import SettingsManager
from screen_translate.logging_setup import setup_logging
from screen_translate.ui.about_dialog import AboutDialog
from screen_translate.ui.capture_window import CaptureWindow
from screen_translate.ui.controller import AppController
from screen_translate.ui.detached_window import DetachedWindow
from screen_translate.ui.history_window import HistoryWindow
from screen_translate.ui.log_window import LogWindow
from screen_translate.ui.main_window import MainWindow
from screen_translate.ui.mask_window import MaskWindow
from screen_translate.ui.settings_dialog import SettingsDialog
from screen_translate.ui.snip_overlay import SnipOverlay

logger = logging.getLogger(__name__)


def main() -> None:
    """Create QApplication, construct all windows, and start the event loop.

    This is the sole entry point declared in pyproject.toml.
    """
    # --- QApplication must be the first Qt object created ---
    app = QApplication(sys.argv)
    app.setApplicationName("screen-translate")
    app.setApplicationDisplayName("Screen Translate")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Dadangdut33")
    # Keep running when the last window is hidden (tray mode)
    app.setQuitOnLastWindowClosed(False)

    # --- Settings (restore before any window is shown) ---
    settings = SettingsManager()

    # --- Logging setup ---
    log_level: str = str(settings.get("log_level", "DEBUG"))
    keep_log: bool = bool(settings.get("keep_log", False))
    setup_logging(level=log_level, keep_log=keep_log)
    logger.info("Screen Translate v%s starting", __version__)

    # --- Controller ---
    controller = AppController(settings)

    # --- Create all windows (none shown yet) ---
    main_win = MainWindow(controller)
    controller.main_window = main_win

    capture_win = CaptureWindow(controller)
    controller.capture_window = capture_win

    # Multi-monitor snip overlays
    for i, _ in enumerate(app.screens()):
        overlay = SnipOverlay(controller, screen_index=i)
        controller.snip_overlays.append(overlay)

    query_win = DetachedWindow(controller, role="q")
    result_win = DetachedWindow(controller, role="res")
    controller.query_window = query_win
    controller.result_window = result_win

    mask_win = MaskWindow(controller)
    controller.mask_window = mask_win

    history_win = HistoryWindow(controller)
    controller.history_window = history_win

    log_win = LogWindow(controller)
    controller.log_window = log_win

    settings_dlg = SettingsDialog(controller, parent=main_win)
    controller.settings_dialog = settings_dlg

    about_dlg = AboutDialog(parent=main_win)
    controller.about_dialog = about_dlg

    # --- Register global hotkeys (if keyboard package is available) ---
    _register_hotkeys(controller, settings)

    # --- Show the main window (unless launched silent with -s) ---
    if "-s" not in sys.argv:
        main_win.show()
        logger.info("Main window shown")
    else:
        logger.info("Silent start (-s flag): running in tray only")

    sys.exit(app.exec())


def _register_hotkeys(controller: AppController, settings: SettingsManager) -> None:
    """Register global hotkeys from settings, silently skipping on failure.

    Args:
        controller: Application controller.
        settings: Settings store.
    """
    try:
        import keyboard

        snip_hk: str = str(settings.get("hk_snip_cap", "ctrl+alt+t"))
        cap_hk: str = str(settings.get("hk_cap_window", ""))

        if snip_hk:
            keyboard.add_hotkey(snip_hk, lambda: _trigger_snip(controller))
            logger.debug("Registered snip hotkey: %s", snip_hk)

        if cap_hk:
            keyboard.add_hotkey(cap_hk, lambda: _trigger_capture(controller))
            logger.debug("Registered capture hotkey: %s", cap_hk)

    except ImportError:
        logger.warning("'keyboard' package not installed - global hotkeys disabled")
    except Exception as exc:
        logger.warning("Could not register hotkeys: %s", exc)


def _trigger_snip(controller: AppController) -> None:
    """Thread-safe snip trigger invoked by the keyboard library.

    Args:
        controller: Application controller.
    """
    from PyQt6.QtCore import QMetaObject, Qt

    if controller.main_window:
        QMetaObject.invokeMethod(
            controller.main_window,
            "_trigger_snip",
            Qt.ConnectionType.QueuedConnection,
        )


def _trigger_capture(controller: AppController) -> None:
    """Thread-safe capture trigger invoked by the keyboard library.

    Args:
        controller: Application controller.
    """
    from PyQt6.QtCore import QMetaObject, Qt

    if controller.capture_window:
        QMetaObject.invokeMethod(
            controller.capture_window,
            "trigger_capture",
            Qt.ConnectionType.QueuedConnection,
        )


if __name__ == "__main__":
    main()
