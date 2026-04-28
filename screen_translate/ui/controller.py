"""Central application controller - coordinates all windows and workers."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pyperclip
from PyQt6.QtCore import (
    QObject,
    QRect,
    QProcess,
    QProcessEnvironment,
    QThreadPool,
    QRunnable,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtWidgets import QApplication, QMessageBox

from screen_translate.config.settings import SettingsManager
from screen_translate.core.history import append_history
from screen_translate.core.ocr_images import (
    link_history_to_ocr_run,
    list_ocr_images_for_run,
    new_ocr_run_id,
)
from screen_translate.core.ocr.language_compat import (
    is_tesseract_language_compatible,
    resolve_tesseract_language_code,
)
from screen_translate.core.ocr.base import OCRError
from screen_translate.core.ocr.tesseract import TesseractOCRBackend
from screen_translate.core.translation.argos_backend import (
    argos_package_dir_from_setting,
    load_argos_backend,
)
from screen_translate.core.translation.base import TranslationBackend, TranslationError
from screen_translate.core.translation.deepl_official_backend import (
    load_deepl_official_backend,
)
from screen_translate.core.translation.libretranslate_backend import (
    load_libretranslate_backend,
)
from screen_translate.core.translation.libretranslate_local import (
    inspect_local_libretranslate,
    local_libretranslate_dir_from_setting,
    local_libretranslate_server_command,
)
from screen_translate.core.translation.openrouter_backend import (
    load_openrouter_backend,
)
from screen_translate.core.translation.proxy import (
    build_translation_proxies,
    translation_no_proxy,
)
from screen_translate.core.translation.translators_backend import (
    get_all_translators_backends,
)
from screen_translate.ui.screen_capture import (
    CaptureCancelledError,
    capture_filename,
    capture_interactive_region_image,
    preferred_interactive_snip_backend,
    save_cropped_image,
    captured_dir,
)

if TYPE_CHECKING:
    from screen_translate.ui.overlays.capture_region_overlay import (
        CaptureRegionOverlay,
    )
    from screen_translate.ui.overlays.snip_overlay import SnipOverlay
    from screen_translate.ui.pages.about_page import AboutPage
    from screen_translate.ui.pages.history_page import HistoryPage
    from screen_translate.ui.pages.log_page import LogPage
    from screen_translate.ui.pages.main_window import MainWindow
    from screen_translate.ui.pages.ocr_images_page import OCRImagesPage
    from screen_translate.ui.pages.settings_page import SettingsPage
    from screen_translate.ui.windows.capture_window import CaptureWindow
    from screen_translate.ui.windows.floating_text_window import FloatingTextWindow
    from screen_translate.ui.windows.mask_window import MaskWindow

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _TranslationRequest:
    """Validated translation request."""

    backend: TranslationBackend
    text: str
    source_lang: str
    target_lang: str


@dataclass(slots=True)
class _SnipCaptureOptions:
    """Settings that affect native snip capture behavior."""

    keep_full_image: bool
    save_cropped_image: bool


# ---------------------------------------------------------------------------
# Worker signals (QObject wrapper so QRunnable can emit signals)
# ---------------------------------------------------------------------------


class _WorkerSignals(QObject):
    """Signals emitted by background workers."""

    finished: pyqtSignal = pyqtSignal(str)
    error: pyqtSignal = pyqtSignal(str)


class _BackendDiscoverySignals(QObject):
    """Signals emitted by the background backend discovery worker."""

    finished: pyqtSignal = pyqtSignal(object)
    error: pyqtSignal = pyqtSignal(str)


class _OCRWorker(QRunnable):
    """Runs OCR in a thread-pool thread and emits the result."""

    def __init__(
        self,
        backend: TesseractOCRBackend,
        pil_image: Any,  # PIL.Image.Image - avoiding Qt in core
        source_lang: str,
        extra_config: str,
        psm5_vertical: bool,
        run_id: str | None,
    ) -> None:
        """Initialise the worker.

        Args:
            backend: TesseractOCRBackend instance.
            pil_image: Pillow image to process.
            source_lang: Language display name used for tesseract.
            extra_config: Extra tesseract config flags.
            psm5_vertical: Pass --psm 5 for vertical-script languages.
        """
        super().__init__()
        self.backend = backend
        self.pil_image = pil_image
        self.source_lang = source_lang
        self.extra_config = extra_config
        self.psm5_vertical = psm5_vertical
        self.run_id = run_id
        self.signals = _WorkerSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:
        """Execute OCR and emit result or error signal."""
        try:
            text = self.backend.extract_text_with_lang(
                self.pil_image,
                self.source_lang,
                extra_config=self.extra_config,
                psm5_vertical=self.psm5_vertical,
                run_id=self.run_id,
            )
            self.signals.finished.emit(text)
        except (OCRError, Exception) as exc:
            self.signals.error.emit(str(exc))


class _TranslationWorker(QRunnable):
    """Runs translation in a thread-pool thread and emits the result."""

    def __init__(
        self,
        backend: TranslationBackend,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> None:
        """Initialise the worker.

        Args:
            backend: TranslationBackend instance.
            text: Text to translate.
            source_lang: Source language display name.
            target_lang: Target language display name.
        """
        super().__init__()
        self.backend = backend
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.signals = _WorkerSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:
        """Execute translation and emit result or error signal."""
        try:
            result = self.backend.translate(
                self.text, self.source_lang, self.target_lang
            )
            self.signals.finished.emit(result)
        except (TranslationError, Exception) as exc:
            self.signals.error.emit(str(exc))


class _BackendDiscoveryWorker(QRunnable):
    """Discover translation backends off the UI thread."""

    def __init__(self, settings_snapshot: dict[str, object]) -> None:
        super().__init__()
        self.settings_snapshot = settings_snapshot
        self.signals = _BackendDiscoverySignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:
        """Discover translation backends and emit them back to the UI thread."""
        try:
            backends = AppController.discover_translation_backends_from_snapshot(
                self.settings_snapshot
            )
            self.signals.finished.emit(backends)
        except Exception as exc:
            self.signals.error.emit(str(exc))


# ---------------------------------------------------------------------------
# AppController
# ---------------------------------------------------------------------------


class AppController(QObject):
    """Central coordinator that owns all windows and manages workers.

    The controller holds references to every window and exposes Qt signals
    so that components can communicate without tight coupling.
    """

    # OCR pipeline
    ocr_started: pyqtSignal = pyqtSignal()
    ocr_completed: pyqtSignal = pyqtSignal(str)  # recognised text
    ocr_failed: pyqtSignal = pyqtSignal(str)  # error message

    # Translation pipeline
    translation_started: pyqtSignal = pyqtSignal()
    translation_completed: pyqtSignal = pyqtSignal(str)  # translated text
    translation_failed: pyqtSignal = pyqtSignal(str)  # error message

    # Generic status
    status_busy: pyqtSignal = pyqtSignal()
    status_idle: pyqtSignal = pyqtSignal()
    translation_backends_loading: pyqtSignal = pyqtSignal(bool)
    translation_backends_reloaded: pyqtSignal = pyqtSignal()

    def __init__(
        self, settings: SettingsManager, parent: QObject | None = None
    ) -> None:
        """Create the controller.

        Args:
            settings: Application settings store.
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self.settings = settings
        self._pool = QThreadPool.globalInstance()

        # Window references (populated by the UI layer)
        self.main_window: MainWindow | None = None
        self.capture_window: CaptureWindow | None = None
        self.capture_region_overlays: list[CaptureRegionOverlay] = []
        self.snip_overlays: list[SnipOverlay] = []
        self.query_window: FloatingTextWindow | None = None
        self.result_window: FloatingTextWindow | None = None
        self.mask_window: MaskWindow | None = None
        self.history_window: HistoryPage | None = None
        self.log_window: LogPage | None = None
        self.ocr_images_page: OCRImagesPage | None = None
        self.settings_page: SettingsPage | None = None
        self.about_page: AboutPage | None = None

        # OCR backend (lazy-init)
        self._ocr_backend: TesseractOCRBackend | None = None
        self._capture_region_rect: QRect | None = self._load_capture_region_rect()
        self._pending_history_query: str = ""
        self._pending_ocr_run_id: str = ""
        self._libre_server_process: QProcess | None = None
        self._libre_server_port: str = ""

        # Translation backends
        self._backends: dict[str, TranslationBackend] = {}
        self._active_backend_name: str = settings.get("engine", "translators-google")
        self._backend_load_in_progress = False

    # ------------------------------------------------------------------
    # Backend management
    # ------------------------------------------------------------------

    def _load_backends(self) -> None:
        """Load all available translation backends (skips missing ones)."""
        backends = self._discover_translation_backends()
        self._backends = {b.name: b for b in backends}
        logger.info("Loaded translation backends: %s", list(self._backends))

    def _discover_translation_backends(self) -> list[TranslationBackend]:
        """Discover all configured translation backends."""
        return self.discover_translation_backends_from_snapshot(
            self._translation_backend_settings_snapshot()
        )

    @staticmethod
    def discover_translation_backends_from_snapshot(
        snapshot: dict[str, object],
    ) -> list[TranslationBackend]:
        """Discover translation backends from a plain settings snapshot."""
        class _SettingsProxy:
            def __init__(self, values: dict[str, object]) -> None:
                self._values = values

            def get(self, key: str, default: object = None) -> object:
                return self._values.get(key, default)

        settings = _SettingsProxy(snapshot)
        proxies = build_translation_proxies(settings)
        no_proxy = translation_no_proxy(settings)

        backends: list[TranslationBackend] = get_all_translators_backends(proxies=proxies)

        argos = load_argos_backend(
            package_dir=str(settings.get("argos_package_dir", ""))
        )
        if argos:
            backends.append(argos)

        libre = load_libretranslate_backend(
            use_local=bool(settings.get("libre_use_local", False)),
            local_port=str(settings.get("libre_local_port", "5000")),
            host=str(settings.get("libre_host", "translate.argosopentech.com")),
            port=str(settings.get("libre_port", "")),
            use_https=bool(settings.get("libre_https", True)),
            api_key=str(settings.get("libre_api_key", "")),
            proxies=proxies,
        )
        backends.append(libre)

        openrouter_backend = load_openrouter_backend(
            api_key=str(settings.get("openrouter_api_key", "")),
            base_url=str(settings.get("openrouter_base_url", "https://openrouter.ai/api/v1")),
            model=str(settings.get("openrouter_model", "openrouter/free")),
            timeout=float(settings.get("openrouter_timeout", 60)),
            debug_logging=bool(settings.get("openrouter_debug_logging", False)),
            system_prompt_template=str(
                settings.get("openrouter_system_prompt_template", "")
            ),
            user_prompt_template=str(settings.get("openrouter_user_prompt_template", "{{text}}")),
            custom_languages=settings.get("openrouter_custom_languages", {}),
            proxies=proxies,
        )
        backends.append(openrouter_backend)

        deepl_key = str(settings.get("deepl_api_key", ""))
        deepl_official = load_deepl_official_backend(
            api_key=deepl_key,
            proxies=proxies,
            no_proxy=no_proxy,
        )
        if deepl_official:
            backends.append(deepl_official)

        return backends

    def _translation_backend_settings_snapshot(self) -> dict[str, object]:
        """Capture backend-related settings for worker-thread discovery."""
        keys = [
            "translation_proxy_enabled",
            "translation_proxy_http",
            "translation_proxy_https",
            "translation_proxy_no_proxy",
            "argos_package_dir",
            "libre_use_local",
            "libre_local_port",
            "libre_host",
            "libre_port",
            "libre_https",
            "libre_api_key",
            "deepl_api_key",
            "openrouter_api_key",
            "openrouter_base_url",
            "openrouter_model",
            "openrouter_timeout",
            "openrouter_debug_logging",
            "openrouter_system_prompt_template",
            "openrouter_user_prompt_template",
            "openrouter_custom_languages",
            "translators_region",
        ]
        return {key: self.settings.get(key, "") for key in keys}

    def start_async_translation_backends_load(self) -> None:
        """Load translation backends in the background for smoother startup."""
        if self._backend_load_in_progress:
            return
        self._backend_load_in_progress = True
        self.translation_backends_loading.emit(True)
        worker = _BackendDiscoveryWorker(self._translation_backend_settings_snapshot())
        worker.signals.finished.connect(self._on_async_backends_loaded)
        worker.signals.error.connect(self._on_async_backends_error)
        self._pool.start(worker)

    @pyqtSlot(object)
    def _on_async_backends_loaded(self, backends: object) -> None:
        """Apply asynchronously discovered translation backends."""
        self._backend_load_in_progress = False
        self.translation_backends_loading.emit(False)
        if not isinstance(backends, list):
            logger.warning("Async backend discovery returned unexpected result")
            return
        self._backends = {b.name: b for b in backends if hasattr(b, "name")}
        logger.info("Loaded translation backends: %s", list(self._backends))
        if self._active_backend_name not in self._backends and self._backends:
            self._active_backend_name = next(iter(self._backends))
            self.settings.set("engine", self._active_backend_name)
        self.translation_backends_reloaded.emit()

    @pyqtSlot(str)
    def _on_async_backends_error(self, error: str) -> None:
        """Handle background backend discovery failure."""
        self._backend_load_in_progress = False
        self.translation_backends_loading.emit(False)
        logger.warning("Async translation backend discovery failed: %s", error)

    def reload_translation_backends(self) -> None:
        """Reload translation backends after settings changes."""
        previous = self._active_backend_name
        self._reconcile_local_libretranslate_server()
        self._load_backends()
        if previous in self._backends or previous == "None":
            self._active_backend_name = previous
        elif self._backends:
            self._active_backend_name = next(iter(self._backends))
        else:
            self._active_backend_name = "None"
        self.settings.set("engine", self._active_backend_name)

    def invalidate_translation_backend_languages(self, backend_name: str) -> None:
        """Clear cached language data for a specific backend, if supported."""
        backend = self._backends.get(backend_name)
        if backend is None:
            return
        invalidate = getattr(backend, "invalidate_languages_cache", None)
        if callable(invalidate):
            invalidate()

    def _local_libre_port(self) -> str:
        """Return the configured local LibreTranslate port."""
        return str(self.settings.get("libre_local_port", "5000")).strip() or "5000"

    def _local_libre_package_dir(self) -> str:
        """Return the package/model directory used by managed local LibreTranslate."""
        raw = str(self.settings.get("libre_local_package_dir", "")).strip()
        if raw:
            return str(argos_package_dir_from_setting(raw))
        return str(
            argos_package_dir_from_setting(
                str(self.settings.get("argos_package_dir", ""))
            )
        )

    def local_libretranslate_enabled(self) -> bool:
        """Return True when the local managed LibreTranslate mode is enabled."""
        return bool(self.settings.get("libre_use_local", False))

    def local_libretranslate_endpoint(self) -> str:
        """Return the configured local LibreTranslate endpoint."""
        return f"http://127.0.0.1:{self._local_libre_port()}"

    def is_local_libretranslate_running(self, timeout: float = 1.5) -> bool:
        """Return True if a local LibreTranslate server responds on the configured port."""
        import requests

        try:
            response = requests.get(
                f"{self.local_libretranslate_endpoint().rstrip('/')}/languages",
                timeout=timeout,
            )
            return bool(response.ok)
        except Exception:
            return False

    def _reconcile_local_libretranslate_server(self) -> None:
        """Stop the managed local LibreTranslate server when settings no longer match."""
        if not self.local_libretranslate_enabled():
            self.stop_local_libretranslate_server()
            return

        configured_port = self._local_libre_port()
        if (
            self._libre_server_process is not None
            and self._libre_server_process.state() != QProcess.ProcessState.NotRunning
            and self._libre_server_port != configured_port
        ):
            self.stop_local_libretranslate_server()

    def ensure_local_libretranslate_server_started(self, timeout: float = 20.0) -> bool:
        """Start the managed local LibreTranslate server if needed and wait until ready."""
        if not self.local_libretranslate_enabled():
            return False
        if self.is_local_libretranslate_running():
            return True

        install_dir = local_libretranslate_dir_from_setting(
            str(self.settings.get("libre_local_dir", ""))
        )
        info = inspect_local_libretranslate(install_dir)
        if not info.command_executable.exists():
            logger.warning("Managed local LibreTranslate command not found at %s", info.command_executable)
            return False

        port = self._local_libre_port()
        process = self._libre_server_process
        if process is None or process.state() == QProcess.ProcessState.NotRunning:
            process = QProcess(self)
            process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            env = QProcessEnvironment.systemEnvironment()
            argos_dir = self._local_libre_package_dir()
            env.insert("ARGOS_PACKAGES_DIR", argos_dir)
            env.insert("ARGOS_PACKAGE_DIR", argos_dir)
            env.insert("ARGOS_TRANSLATE_PACKAGE_DIR", argos_dir)
            process.setProcessEnvironment(env)
            process.readyReadStandardOutput.connect(
                lambda proc=process: self._log_libre_server_output(proc)
            )
            self._libre_server_process = process
            command = local_libretranslate_server_command(install_dir, port)
            logger.info("Starting managed local LibreTranslate server: %s", command)
            process.start(command[0], command[1:])
            if not process.waitForStarted(5000):
                logger.warning("Managed local LibreTranslate server failed to start")
                return False
        self._libre_server_port = port

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_local_libretranslate_running(timeout=1.0):
                return True
            if (
                self._libre_server_process is not None
                and self._libre_server_process.state() == QProcess.ProcessState.NotRunning
            ):
                break
            time.sleep(0.25)
        logger.warning("Managed local LibreTranslate server did not become reachable in time")
        return False

    def stop_local_libretranslate_server(self) -> None:
        """Stop the managed local LibreTranslate server if this app started it."""
        process = self._libre_server_process
        if process is None:
            return
        if process.state() != QProcess.ProcessState.NotRunning:
            logger.info("Stopping managed local LibreTranslate server")
            process.terminate()
            if not process.waitForFinished(4000):
                process.kill()
                process.waitForFinished(2000)
        process.deleteLater()
        self._libre_server_process = None
        self._libre_server_port = ""

    def _log_libre_server_output(self, process: QProcess) -> None:
        """Log managed LibreTranslate server output safely."""
        try:
            output = bytes(process.readAllStandardOutput()).decode(errors="replace").strip()
        except RuntimeError:
            return
        if output:
            logger.debug("LibreTranslate local server: %s", output)

    def ensure_backend_ready(self, backend_name: str) -> bool:
        """Prepare a backend for use if it requires runtime setup."""
        if backend_name == "LibreTranslate" and self.local_libretranslate_enabled():
            ready = self.ensure_local_libretranslate_server_started()
            if ready:
                self.invalidate_translation_backend_languages("LibreTranslate")
            return ready
        return True

    def available_backend_names(self) -> list[str]:
        """Return the names of all loaded backends plus 'None' (OCR-only mode).

        Returns:
            List of backend name strings.
        """
        return [*list(self._backends.keys()), "None"]

    def translation_backends_ready(self) -> bool:
        """Return True when translation backends have finished loading."""
        return bool(self._backends) and not self._backend_load_in_progress

    def active_backend_name(self) -> str:
        """Return the name of the currently active backend.

        Returns:
            Backend name string.
        """
        return self._active_backend_name

    def set_active_backend(self, name: str) -> None:
        """Switch to a different backend and persist the choice.

        Args:
            name: Backend display name, or ``"None"`` to disable translation.
        """
        self._active_backend_name = name
        self.settings.set("engine", name)
        logger.debug("Active backend → %s", name)

    def get_ocr_backend(self) -> TesseractOCRBackend:
        """Return (and lazily create) the Tesseract OCR backend.

        Returns:
            Initialised TesseractOCRBackend.

        Raises:
            OCRError: If Tesseract is not found on PATH.
        """
        if self._ocr_backend is None:
            self._ocr_backend = self._build_ocr_backend()
        return self._ocr_backend

    def _build_ocr_backend(self) -> TesseractOCRBackend:
        """Create a Tesseract backend from current settings."""
        return TesseractOCRBackend(
            tesseract_path=self.settings.get("tesseract_loc", ""),
            extra_config=self.settings.get("tesseract_config", ""),
            grayscale=self.settings.get("enhance_with_grayscale", True),
            use_cv2_contour=self.settings.get("enhance_with_cv2_contour", False),
            save_cv2_contour_image=self.settings.get("save_cv2_contour_image", False),
            background_mode=self.settings.get("enhance_background", "Auto-Detect"),
        )

    def available_ocr_backend_names(self) -> list[str]:
        """Return the available OCR backend names."""
        return ["Tesseract"]

    def active_ocr_backend_name(self) -> str:
        """Return the current OCR backend selection."""
        return str(self.settings.get("ocr_backend", "Tesseract"))

    def set_active_ocr_backend(self, name: str) -> None:
        """Persist the current OCR backend selection."""
        self.settings.set("ocr_backend", name)
        self.reset_ocr_backend()

    def installed_ocr_languages(self) -> list[str]:
        """Return installed language codes for the active OCR backend."""
        try:
            return self.get_ocr_backend().detect_languages()
        except OCRError:
            return []

    def ocr_language_overrides(self) -> dict[str, dict[str, str]]:
        """Return the configured per-backend OCR language overrides."""
        raw = self.settings.get("ocr_language_overrides", {})
        if not isinstance(raw, dict):
            return {}
        normalized: dict[str, dict[str, str]] = {}
        for backend_name, mapping in raw.items():
            if not isinstance(backend_name, str) or not isinstance(mapping, dict):
                continue
            cleaned = {
                str(lang_code): str(ocr_code)
                for lang_code, ocr_code in mapping.items()
                if str(lang_code).strip() and str(ocr_code).strip()
            }
            normalized[backend_name] = cleaned
        return normalized

    def backend_ocr_overrides(self, backend_name: str) -> dict[str, str]:
        """Return OCR language overrides for a specific translation backend."""
        return dict(self.ocr_language_overrides().get(backend_name, {}))

    def normalize_backend_language_code(
        self,
        backend_name: str,
        language_code: str,
    ) -> str:
        """Return the canonical backend language code for a UI selection key."""
        backend = self._backends.get(backend_name)
        resolver = getattr(backend, "resolve_language_code", None)
        if callable(resolver):
            try:
                resolved = str(resolver(language_code)).strip()
                if resolved:
                    return resolved
            except Exception:
                pass
        return language_code

    def set_backend_ocr_override(
        self,
        backend_name: str,
        language_code: str,
        tesseract_code: str,
    ) -> None:
        """Persist a Tesseract override for a backend/language pair."""
        overrides = self.ocr_language_overrides()
        backend_overrides = dict(overrides.get(backend_name, {}))
        normalized_lang = language_code.strip()
        normalized_tesseract = tesseract_code.strip()
        if normalized_tesseract:
            backend_overrides[normalized_lang] = normalized_tesseract
        else:
            backend_overrides.pop(normalized_lang, None)

        if backend_overrides:
            overrides[backend_name] = backend_overrides
        else:
            overrides.pop(backend_name, None)
        self.settings.set("ocr_language_overrides", overrides)

    def incompatible_languages_for_backend(
        self,
        backend_name: str,
    ) -> list[tuple[str, str | None]]:
        """Return backend language codes with their resolved Tesseract code or None."""
        backend = self._backends.get(backend_name)
        if backend is None:
            return []
        installed = self.installed_ocr_languages()
        overrides = self.backend_ocr_overrides(backend_name)
        result: list[tuple[str, str | None]] = []
        for lang_code in backend.available_languages():
            resolved = resolve_tesseract_language_code(
                self.normalize_backend_language_code(backend_name, lang_code),
                installed,
                overrides=overrides,
            )
            if resolved is None:
                result.append((lang_code, None))
        return result

    def reset_ocr_backend(self) -> None:
        """Force re-creation of the OCR backend (e.g. after settings change)."""
        self._ocr_backend = None

    def _load_capture_region_rect(self) -> QRect | None:
        raw = str(self.settings.get("capture_region_geometry", "")).strip()
        if not raw:
            return None
        try:
            x_str, y_str, w_str, h_str = raw.split(",")
            return QRect(int(x_str), int(y_str), max(1, int(w_str)), max(1, int(h_str)))
        except ValueError:
            logger.warning("Invalid capture_region_geometry setting: %r", raw)
            return None

    def get_capture_region(self) -> QRect | None:
        """Return the stored capture region for virtual overlay mode."""
        return (
            QRect(self._capture_region_rect)
            if self._capture_region_rect is not None
            else None
        )

    def set_capture_region(self, rect: QRect) -> None:
        """Persist the capture region selected by the virtual overlay."""
        normalized = rect.normalized()
        self._capture_region_rect = QRect(normalized)
        self.settings.set(
            "capture_region_geometry",
            f"{normalized.x()},{normalized.y()},{normalized.width()},{normalized.height()}",
        )

    def start_capture_region_selection(self) -> bool:
        """Launch the persistent capture-region selector across all screens."""
        if not self.capture_region_overlays:
            logger.warning("No capture region overlays available")
            return False
        for overlay in self.capture_region_overlays:
            overlay.start_selection()
        return True

    def _resolve_ocr_language(self, selected_lang: str) -> str:
        """Map the UI language selection to an installed Tesseract language code."""
        installed = self.installed_ocr_languages()
        resolved = resolve_tesseract_language_code(
            self.normalize_backend_language_code(self.active_backend_name(), selected_lang),
            installed,
            overrides=self.backend_ocr_overrides(self.active_backend_name()),
        )
        return resolved or selected_lang

    def is_selected_source_ocr_compatible(
        self,
        selected_lang: str | None = None,
        backend_name: str | None = None,
    ) -> bool:
        """Return True if the current source language can be OCRed by the active backend."""
        ocr_backend_name = self.active_ocr_backend_name()
        lang = selected_lang or str(self.settings.get("sourceLang", "auto"))
        translation_backend = backend_name or self.active_backend_name()
        if ocr_backend_name == "Tesseract":
            normalized_lang = self.normalize_backend_language_code(
                translation_backend, lang
            )
            return is_tesseract_language_compatible(
                normalized_lang,
                self.installed_ocr_languages(),
                overrides=self.backend_ocr_overrides(translation_backend),
            )
        return True

    # ------------------------------------------------------------------
    # Async OCR
    # ------------------------------------------------------------------

    def run_ocr(self, pil_image: Any, run_id: str | None = None) -> None:
        """Run OCR asynchronously on *pil_image*.

        Emits :attr:`ocr_started`, then either :attr:`ocr_completed` (text)
        or :attr:`ocr_failed` (error message).

        Args:
            pil_image: Pillow Image to process.
        """
        try:
            backend = self.get_ocr_backend()
        except OCRError as exc:
            self._show_critical("Tesseract Not Found", str(exc))
            return

        source_lang: str = self._resolve_ocr_language(
            str(self.settings.get("sourceLang", "auto"))
        )
        extra_config: str = self.settings.get("tesseract_config", "")
        psm5: bool = self.settings.get("tesseract_psm5_vertical", True)

        effective_run_id = run_id or self._pending_ocr_run_id or new_ocr_run_id()
        self._pending_ocr_run_id = effective_run_id
        if bool(self.settings.get("save_cropped_image", False)):
            save_cropped_image(
                pil_image,
                prefix="ocr_input",
                run_id=effective_run_id,
                tag="ocr_input",
                source="ocr",
            )
        worker = _OCRWorker(
            backend,
            pil_image,
            source_lang,
            extra_config,
            psm5,
            effective_run_id,
        )
        worker.signals.finished.connect(self._on_ocr_done)
        worker.signals.error.connect(self._on_ocr_error)
        self.ocr_started.emit()
        self.status_busy.emit()
        self._pool.start(worker)

    @pyqtSlot(str)
    def _on_ocr_done(self, text: str) -> None:
        """Handle successful OCR result.

        Args:
            text: Recognised text.
        """
        logger.info("OCR succeeded (%d chars)", len(text))

        replace_nl: bool = self.settings.get("replaceNewLine", True)
        replacer: str = self.settings.get("replaceNewLineWith", " ")
        if replace_nl and replacer != "\n":
            text = text.replace("\n", replacer)

        if self.settings.get("auto_copy_captured", False):
            pyperclip.copy(text)

        alert: bool = not self.settings.get("supress_no_text_alert", True)
        if alert and not text.strip():
            self._show_info(
                "No Text Detected", "No text was found in the selected region."
            )

        self.ocr_completed.emit(text)
        self.status_idle.emit()
        if self.ocr_images_page is not None:
            self.ocr_images_page.refresh_gallery()

        # Auto-translate if not in OCR-only mode
        if self._active_backend_name != "None" and text.strip():
            self._pending_history_query = text
            self.run_translation(text)

    @pyqtSlot(str)
    def _on_ocr_error(self, error: str) -> None:
        """Handle OCR failure.

        Args:
            error: Error message string.
        """
        logger.error("OCR failed: %s", error)
        self.ocr_failed.emit(error)
        self.status_idle.emit()
        self._pending_ocr_run_id = ""
        if self.ocr_images_page is not None:
            self.ocr_images_page.refresh_gallery()
        if "not installed" in error or "not in your PATH" in error:
            from screen_translate.core.ocr.tesseract import (
                _platform_install_instructions,
            )

            self._show_critical("Tesseract Not Found", _platform_install_instructions())
        else:
            self._show_critical("OCR Error", error)

    # ------------------------------------------------------------------
    # Async translation
    # ------------------------------------------------------------------

    def run_translation(self, text: str) -> None:
        """Translate *text* asynchronously using the active backend.

        Args:
            text: Text to translate.
        """
        request = self._build_translation_request(text)
        if request is None:
            return

        worker = _TranslationWorker(
            request.backend,
            request.text,
            request.source_lang,
            request.target_lang,
        )
        worker.signals.finished.connect(self._on_translation_done)
        worker.signals.error.connect(self._on_translation_error)
        self.translation_started.emit()
        self.status_busy.emit()
        self._pool.start(worker)

    def _build_translation_request(self, text: str) -> _TranslationRequest | None:
        """Validate the current translation request against backend capabilities."""
        backend = self._backends.get(self._active_backend_name)
        if backend is None:
            logger.warning("No translation backend active")
            return None
        if not self.ensure_backend_ready(self._active_backend_name):
            self._show_warning(
                "LibreTranslate Unavailable",
                "The managed local LibreTranslate server could not be started. "
                "Please run setup again or review the local install settings.",
            )
            return None

        supported_languages = backend.available_languages()
        if not supported_languages:
            self._show_warning(
                "Languages Unavailable",
                f"{self._active_backend_name} could not load its supported languages.",
            )
            return None

        source_lang: str = str(self.settings.get("sourceLang", "auto"))
        target_lang: str = str(self.settings.get("targetLang", "en"))

        if source_lang and source_lang not in supported_languages:
            source_lang = (
                "auto" if "auto" in supported_languages else supported_languages[0]
            )
            self.settings.set("sourceLang", source_lang)

        target_candidates = [
            lang for lang in supported_languages if lang not in {"auto", "Auto"}
        ]
        if target_lang not in target_candidates:
            if not target_candidates:
                self._show_warning(
                    "No Target Language",
                    f"{self._active_backend_name} did not provide any target languages.",
                )
                return None
            target_lang = target_candidates[0]
            self.settings.set("targetLang", target_lang)

        return _TranslationRequest(
            backend=backend,
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
        )

    @pyqtSlot(str)
    def _on_translation_done(self, result: str) -> None:
        """Handle successful translation result.

        Args:
            result: Translated text.
        """
        logger.info("Translation succeeded (%d chars)", len(result))

        if self.settings.get("auto_copy_translated", False):
            pyperclip.copy(result)

        if self.settings.get("save_history", True):
            run_id = self._pending_ocr_run_id
            ocr_records = list_ocr_images_for_run(run_id) if run_id else []
            entry = append_history(
                {
                    "from": self.settings.get("sourceLang", ""),
                    "to": self.settings.get("targetLang", ""),
                    "query": self._pending_history_query,
                    "result": result,
                    "engine": self._active_backend_name,
                    "ocr_run_id": run_id,
                    "ocr_image_tags": [record.tag for record in ocr_records],
                    "ocr_image_paths": [record.path for record in ocr_records],
                }
            )
            if run_id:
                link_history_to_ocr_run(run_id, entry.id)
            if self.history_window is not None:
                self.history_window._load()
            if self.ocr_images_page is not None:
                self.ocr_images_page.refresh_gallery()
        self._pending_history_query = ""
        self._pending_ocr_run_id = ""

        self.translation_completed.emit(result)
        self.status_idle.emit()

    @pyqtSlot(str)
    def _on_translation_error(self, error: str) -> None:
        """Handle translation failure.

        Args:
            error: Error message string.
        """
        logger.error("Translation failed: %s", error)
        self.translation_failed.emit(error)
        self.status_idle.emit()
        self._pending_history_query = ""
        self._pending_ocr_run_id = ""
        self._show_critical("Translation Error", error)

    # ------------------------------------------------------------------
    # Text-only translation (no OCR)
    # ------------------------------------------------------------------

    def translate_text(self, text: str) -> None:
        """Translate typed text (no OCR) using the active backend.

        Args:
            text: Text entered by the user.
        """
        if not text.strip():
            return
        if self._active_backend_name == "None":
            self._show_warning(
                "No Engine Selected", "Please select a translation engine first."
            )
            return
        self._pending_history_query = text
        self.run_translation(text)

    def start_snip_capture(self) -> bool:
        """Start snip capture, using external region tools when needed on Wayland."""
        native_backend = preferred_interactive_snip_backend()
        if native_backend is not None:
            return self._start_native_snip_capture(native_backend)

        for overlay in self.snip_overlays:
            overlay.start_snip()
        return True

    def _start_native_snip_capture(self, backend: str) -> bool:
        """Use a desktop-native interactive region picker and screenshot backend."""
        output_dir = captured_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        options = self._snip_capture_options()

        try:
            run_id = new_ocr_run_id()
            self._pending_ocr_run_id = run_id
            pil_image = capture_interactive_region_image(
                keep_full_image=options.keep_full_image,
                backend=backend,
                run_id=run_id,
            )
            if pil_image is None:
                self._show_critical(
                    "Snip Capture Failed",
                    f"{backend} failed to capture the selected region.",
                )
                return False

            if options.save_cropped_image:
                save_cropped_image(
                    pil_image,
                    prefix="cropped_snip",
                    run_id=run_id,
                    tag="snip_cropped",
                    source=backend.lower().replace(" ", "-"),
                )

            if options.keep_full_image and backend not in {"Spectacle", "GNOME Shell"}:
                normalized_path = output_dir / capture_filename(prefix="snip_capture")
                pil_image.save(normalized_path)
                logger.info("Saved snip capture to %s", normalized_path)
            self.run_ocr(pil_image, run_id=run_id)
            return True
        except CaptureCancelledError:
            logger.info("%s snip capture canceled by user", backend)
            return False
        except FileNotFoundError as exc:
            if bool(self.settings.get("suppress_missing_capture_file_errors", True)):
                logger.info(
                    "%s snip capture ended without an output file: %s",
                    backend,
                    exc,
                )
                return False
            logger.exception("%s snip capture file missing: %s", backend, exc)
            self._show_critical("Snip Capture Failed", str(exc))
            return False
        except Exception as exc:
            logger.exception("%s snip capture failed: %s", backend, exc)
            self._show_critical("Snip Capture Failed", str(exc))
            return False

    def _snip_capture_options(self) -> _SnipCaptureOptions:
        """Return the current settings for native snip capture."""
        return _SnipCaptureOptions(
            keep_full_image=bool(self.settings.get("keep_image", True)),
            save_cropped_image=bool(self.settings.get("save_cropped_image", False)),
        )

    def show_test_dialog(self) -> None:
        """Show a test dialog for verifying controller-owned message boxes."""
        self._show_info(
            "Controller Dialog Test",
            "This is a test dialog opened from the controller using a styled QMessageBox.",
        )

    def _show_info(self, title: str, message: str) -> None:
        """Show an informational message box."""
        self._exec_message_box(QMessageBox.Icon.Information, title, message)

    def _show_warning(self, title: str, message: str) -> None:
        """Show a warning message box."""
        self._exec_message_box(QMessageBox.Icon.Warning, title, message)

    def _show_critical(self, title: str, message: str) -> None:
        """Show an error message box."""
        self._exec_message_box(QMessageBox.Icon.Critical, title, message)

    def _exec_message_box(
        self,
        icon: QMessageBox.Icon,
        title: str,
        message: str,
    ) -> None:
        """Show a palette-aware QMessageBox for controller-level alerts."""
        palette = QApplication.palette()
        window_color = palette.window().color()
        text_color = palette.windowText().color()
        button_color = palette.button().color()
        button_text_color = palette.buttonText().color()
        border_color = palette.mid().color()
        highlight_color = palette.highlight().color()

        box = QMessageBox(self.main_window)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(message)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setDefaultButton(QMessageBox.StandardButton.Ok)
        box.setStyleSheet(
            f"""
            QMessageBox {{
                background-color: {window_color.name()};
            }}
            QMessageBox QLabel {{
                color: {text_color.name()};
            }}
            QMessageBox QPushButton {{
                background-color: {button_color.name()};
                color: {button_text_color.name()};
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QMessageBox QPushButton:hover {{
                border-color: {highlight_color.name()};
            }}
            """
        )
        box.exec()

    def shutdown(self) -> None:
        """Release managed runtime processes owned by the controller."""
        self.stop_local_libretranslate_server()
