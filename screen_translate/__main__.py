"""Application entry point - constructs QApplication and launches the app."""

from __future__ import annotations

import logging
import os
import signal
import socket
import sys

from PyQt6.QtCore import (
    QCoreApplication,
    QEventLoop,
    QMetaObject,
    QThreadPool,
    QTimer,
    Qt,
    QSocketNotifier,
    QUrl,
    QSize,
)
from PyQt6.QtGui import QColor, QDesktopServices, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from qfluentwidgets import Dialog, IndeterminateProgressBar, Theme, isDarkTheme, setTheme

from screen_translate import __version__
from screen_translate.config.settings import SettingsManager
from screen_translate.core.translation.translators_backend import (
    configure_translators_region,
)
from screen_translate.logging_setup import setup_logging
from screen_translate.ui.overlays import CaptureRegionOverlay, SnipOverlay
from screen_translate.ui.pages import (
    AboutPage,
    HistoryPage,
    LogPage,
    MainWindow,
    OCRImagesPage,
    SettingsPage,
)
from screen_translate.ui.controller import AppController
from screen_translate.ui.pages.main_window import _APP_NAME
from screen_translate.ui.update_check import (
    UpdateCheckWorker,
    detect_install_method,
    is_newer_version,
    releases_url,
    update_instructions,
)
from screen_translate.ui.windows import CaptureWindow, FloatingTextWindow, MaskWindow
from screen_translate.ui.theme.utils import load_icon

logger = logging.getLogger(__name__)

_DEFAULT_THEME = "Dark"


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
    # set size for main window
    # --- Settings (restore before any window is shown) ---
    settings = SettingsManager()
    configure_translators_region(str(settings.get("translators_region", "EN")))

    # --- Logging setup ---
    log_level: str = str(settings.get("log_level", "DEBUG"))
    keep_log: bool = bool(settings.get("keep_log", False))
    suppress_third_party_loggers: bool = bool(
        settings.get("suppress_third_party_loggers", True)
    )
    max_log_rotation_days: int = int(settings.get("max_log_rotation_days", 5))
    setup_logging(
        level=log_level,
        keep_log=keep_log,
        suppress_third_party=suppress_third_party_loggers,
        max_log_rotation=max_log_rotation_days,
    )
    _apply_theme(app, settings)

    logger.info("Screen Translate v%s starting", __version__)

    splash: QSplashScreen | None = None
    if "-s" not in sys.argv:
        splash = _show_startup_splash(app, settings)

    def _bootstrap() -> None:
        """Construct the heavy app objects after the event loop has started."""
        def _pump_ui(message: str | None = None) -> None:
            """Let Qt repaint the splash and advance startup animations."""
            if splash is not None:
                if message:
                    splash.showMessage(
                        f"{_APP_NAME} v{__version__}\n{message}",
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                        QColor("#f5f5f5" if isDarkTheme() else "#202020"),
                    )
                splash.repaint()
            QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)

        try:
            # --- Controller ---
            _pump_ui("Loading controller…")
            controller = AppController(settings)
            app.aboutToQuit.connect(controller.shutdown)
            app._controller = controller  # type: ignore[attr-defined]

            # --- Create all windows (none shown yet) ---
            _pump_ui("Building main window…")
            main_win = MainWindow(controller)
            controller.main_window = main_win
            app._main_window = main_win  # type: ignore[attr-defined]
            _configure_unix_signal_handling(app, main_win)

            _pump_ui("Preparing capture tools…")
            capture_win = CaptureWindow(controller)
            controller.capture_window = capture_win

            for i, _ in enumerate(app.screens()):
                region_overlay = CaptureRegionOverlay(controller, screen_index=i)
                controller.capture_region_overlays.append(region_overlay)

            for i, _ in enumerate(app.screens()):
                overlay = SnipOverlay(controller, screen_index=i)
                controller.snip_overlays.append(overlay)

            _pump_ui("Preparing floating windows…")
            query_win = FloatingTextWindow(controller, role="q")
            result_win = FloatingTextWindow(controller, role="res")
            controller.query_window = query_win
            controller.result_window = result_win

            mask_win = MaskWindow(controller)
            controller.mask_window = mask_win

            _pump_ui("Building pages…")
            history_win = HistoryPage(controller)
            controller.history_window = history_win

            log_win = LogPage(controller)
            controller.log_window = log_win

            ocr_images_page = OCRImagesPage()
            controller.ocr_images_page = ocr_images_page

            about_page = AboutPage()
            controller.about_page = about_page

            _pump_ui("Registering pages…")
            main_win.register_internal_pages(
                history_win,
                log_win,
                ocr_images_page,
                about_page,
                None,
            )

            _pump_ui("Registering hotkeys…")
            _register_hotkeys(controller, settings)

            if "-s" not in sys.argv:
                _pump_ui("Opening main window…")
                main_win.show()
                if splash is not None:
                    splash.finish(main_win)
                logger.info("Main window shown")

                def _load_settings_page() -> None:
                    """Build and register the heavy settings page after the main UI is visible."""
                    if controller.settings_page is not None:
                        return
                    logger.debug("Loading settings page after main window show")
                    settings_page = SettingsPage(controller)
                    controller.settings_page = settings_page
                    main_win.register_settings_page(settings_page)
                controller.create_settings_page = _load_settings_page  # type: ignore[attr-defined]
                controller.start_async_translation_backends_load()
            else:
                if splash is not None:
                    splash.close()
                logger.info("Silent start (-s flag): running in tray only")
                controller.create_settings_page = lambda: None  # type: ignore[attr-defined]
                controller.start_async_translation_backends_load()

            if bool(settings.get("checkUpdateOnStart", True)):
                QTimer.singleShot(
                    1200,
                    lambda: _check_for_updates_on_startup(app, main_win),
                )
        except Exception:
            if splash is not None:
                splash.close()
            logger.exception("Failed during application bootstrap")
            raise

    QTimer.singleShot(50, _bootstrap)
    sys.exit(app.exec())


def _apply_theme(app: QApplication, settings: SettingsManager) -> None:
    """Apply the configured Fluent light/dark theme."""
    theme_name = str(settings.get("theme", _DEFAULT_THEME)).title()
    use_fusion_base_style = bool(settings.get("use_fusion_base_style", False))
    if theme_name not in {"Dark", "Light"}:
        theme_name = _DEFAULT_THEME
        settings.set("theme", theme_name)
    theme = Theme.DARK if theme_name == "Dark" else Theme.LIGHT
    try:
        if use_fusion_base_style:
            app.setStyle("Fusion")
        app.setProperty("useFusionBaseStyle", use_fusion_base_style)
        setTheme(theme, save=False, lazy=True)
        logger.info(
            "Applied QFluentWidgets theme: %s (Fusion base style: %s)",
            theme_name,
            "on" if use_fusion_base_style else "off",
        )
    except Exception as exc:
        logger.warning("Could not apply QFluentWidgets theme %s: %s", theme_name, exc)


def _show_startup_splash(
    app: QApplication,
    settings: SettingsManager,
) -> QSplashScreen:
    """Show a lightweight native splash screen while heavy startup work runs."""
    theme_name = str(settings.get("theme", _DEFAULT_THEME)).title()
    is_dark = theme_name != "Light"
    icon = load_icon()
    pixmap = QPixmap(QSize(420, 260))
    pixmap.fill(QColor("#202020" if is_dark else "#f4f4f4"))

    painter = QPainter(pixmap)
    painter.setRenderHints(
        QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
    )
    if not icon.isNull():
        splash_icon = icon.pixmap(112, 112)
        x = (pixmap.width() - splash_icon.width()) // 2
        y = (pixmap.height() - splash_icon.height()) // 2 - 10
        painter.drawPixmap(x, y, splash_icon)
    painter.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    splash.showMessage(
        f"{_APP_NAME} v{__version__}\nLoading…",
        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
        QColor("#f5f5f5" if is_dark else "#202020"),
    )

    progress = IndeterminateProgressBar(splash, start=True)
    progress.setObjectName("StartupSplashProgress")
    progress.setFixedWidth(220)
    progress.setFixedHeight(6)
    if is_dark:
        progress.setCustomBarColor("#2de2ff", "#2de2ff")
    else:
        progress.setCustomBarColor("#0078d4", "#0078d4")
    progress.move((pixmap.width() - progress.width()) // 2, pixmap.height() - 44)
    splash._progress = progress  # type: ignore[attr-defined]

    screen = app.primaryScreen()
    if screen is not None:
        geometry = screen.availableGeometry()
        splash.move(
            geometry.center().x() - splash.width() // 2,
            geometry.center().y() - splash.height() // 2,
        )

    splash.show()
    splash.raise_()
    progress.show()
    splash.repaint()
    app.processEvents()
    return splash


def _check_for_updates_on_startup(app: QApplication, main_win: MainWindow) -> None:
    """Check for updates shortly after startup and surface the result."""
    worker = UpdateCheckWorker()

    def _cleanup() -> None:
        app.setProperty("_startup_update_worker", None)

    def _on_finished(latest_version: str, release_url: str, release_title: str) -> None:
        _cleanup()
        if not is_newer_version(latest_version, __version__):
            logger.debug("Startup update check: app is up to date")
            return

        logger.info(
            "Startup update check found update: current=%s latest=%s",
            __version__,
            latest_version,
        )
        tray = getattr(main_win, "_tray", None)
        if tray is not None:
            tray.showMessage(
                "Update Available",
                f"Screen Translate {latest_version} is available.",
                tray.MessageIcon.Information,
                8000,
            )

        message = (
            f"A newer version is available: {latest_version}"
            + (f" ({release_title})" if release_title else "")
            + "\n\nDetected install method:\n"
            + detect_install_method()
            + "\n\nHow to update:\n"
            + update_instructions()
            + f"\n\nRelease page:\n{release_url or releases_url()}"
        )
        dialog = Dialog(
            "Update Available",
            message,
            main_win,
        )
        dialog.yesButton.setText("Open Release Page")
        dialog.cancelButton.setText("Later")
        if dialog.exec():
            QDesktopServices.openUrl(QUrl(release_url or releases_url()))

    def _on_error(error: str) -> None:
        _cleanup()
        logger.debug("Startup update check failed: %s", error)

    worker.signals.finished.connect(_on_finished)
    worker.signals.error.connect(_on_error)
    app.setProperty("_startup_update_worker", worker)
    QThreadPool.globalInstance().start(worker)


def _configure_unix_signal_handling(app: QApplication, main_win: MainWindow) -> None:
    """Bridge POSIX signals into Qt and route them through the real app quit path."""
    read_sock, write_sock = socket.socketpair()
    read_sock.setblocking(False)
    write_sock.setblocking(False)

    previous_wakeup_fd = signal.set_wakeup_fd(write_sock.fileno())

    def _handle_signal(sig: int, _frame: object) -> None:
        logger.info("Received signal %s", sig)

    signal.signal(signal.SIGINT, _handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_signal)

    notifier = QSocketNotifier(read_sock.fileno(), QSocketNotifier.Type.Read, app)

    def _drain_signal_socket() -> None:
        try:
            while read_sock.recv(1024):
                pass
        except BlockingIOError:
            pass
        logger.info("Routing terminal signal through main window quit handler")
        QMetaObject.invokeMethod(
            main_win,
            "_quit_app",
            Qt.ConnectionType.QueuedConnection,
        )

    def _cleanup_signal_bridge() -> None:
        notifier.setEnabled(False)
        signal.set_wakeup_fd(previous_wakeup_fd)
        read_sock.close()
        write_sock.close()

    notifier.activated.connect(_drain_signal_socket)
    app.aboutToQuit.connect(_cleanup_signal_bridge)
    app.setProperty("_signal_notifier", notifier)
    app.setProperty("_signal_read_socket_fd", read_sock.fileno())
    app.setProperty("_signal_write_socket_fd", write_sock.fileno())


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
    os.environ.pop("QT_STYLE_OVERRIDE", None)
    os.environ.pop("QT_QPA_PLATFORMTHEME", None)  # disables KDE/GNOME theme injection
    # ----------------------------------------------------------------
    logger.info("--- Welcome to Screen Translate ---")

    main()
