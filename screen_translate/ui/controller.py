"""Central application controller - coordinates all windows and workers."""

from __future__ import annotations

import logging
from typing import Any

import pyperclip
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QMessageBox

from screen_translate.config.settings import SettingsManager
from screen_translate.core.history import append_history
from screen_translate.core.ocr.base import OCRError
from screen_translate.core.ocr.tesseract import TesseractOCRBackend
from screen_translate.core.translation.argos_backend import load_argos_backend
from screen_translate.core.translation.base import TranslationBackend, TranslationError
from screen_translate.core.translation.deep_translator_backend import load_deep_translator_backends
from screen_translate.core.translation.deepl_official_backend import load_deepl_official_backend

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Worker signals (QObject wrapper so QRunnable can emit signals)
# ---------------------------------------------------------------------------


class _WorkerSignals(QObject):
    """Signals emitted by background workers."""

    finished: pyqtSignal = pyqtSignal(str)
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
            result = self.backend.translate(self.text, self.source_lang, self.target_lang)
            self.signals.finished.emit(result)
        except (TranslationError, Exception) as exc:
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
    ocr_completed: pyqtSignal = pyqtSignal(str)   # recognised text
    ocr_failed: pyqtSignal = pyqtSignal(str)       # error message

    # Translation pipeline
    translation_started: pyqtSignal = pyqtSignal()
    translation_completed: pyqtSignal = pyqtSignal(str)  # translated text
    translation_failed: pyqtSignal = pyqtSignal(str)     # error message

    # Generic status
    status_busy: pyqtSignal = pyqtSignal()
    status_idle: pyqtSignal = pyqtSignal()

    def __init__(self, settings: SettingsManager, parent: QObject | None = None) -> None:
        """Create the controller.

        Args:
            settings: Application settings store.
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self.settings = settings
        self._pool = QThreadPool.globalInstance()

        # Window references (populated by the UI layer)
        self.main_window: Any = None
        self.capture_window: Any = None
        self.snip_overlays: list[Any] = []
        self.query_window: Any = None
        self.result_window: Any = None
        self.mask_window: Any = None
        self.history_window: Any = None
        self.log_window: Any = None
        self.settings_dialog: Any = None
        self.about_dialog: Any = None

        # OCR backend (lazy-init)
        self._ocr_backend: TesseractOCRBackend | None = None

        # Translation backends
        self._backends: dict[str, TranslationBackend] = {}
        self._active_backend_name: str = settings.get("engine", "Google Translate")
        self._load_backends()

    # ------------------------------------------------------------------
    # Backend management
    # ------------------------------------------------------------------

    def _load_backends(self) -> None:
        """Load all available translation backends (skips missing ones)."""
        backends: list[TranslationBackend] = load_deep_translator_backends(
            libre_host=self.settings.get("libre_host", "translate.argosopentech.com"),
            libre_port=self.settings.get("libre_port", ""),
            libre_https=self.settings.get("libre_https", True),
            libre_api_key=self.settings.get("libre_api_key", ""),
        )
        argos = load_argos_backend()
        if argos:
            backends.append(argos)

        deepl_key: str = self.settings.get("deepl_api_key", "")
        deepl_official = load_deepl_official_backend(api_key=deepl_key)
        if deepl_official:
            backends.append(deepl_official)

        self._backends = {b.name: b for b in backends}
        logger.info("Loaded translation backends: %s", list(self._backends))

    def available_backend_names(self) -> list[str]:
        """Return the names of all loaded backends plus 'None' (OCR-only mode).

        Returns:
            List of backend name strings.
        """
        return [*list(self._backends.keys()), "None"]

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
            tes_path: str = self.settings.get("tesseract_loc", "")
            extra_cfg: str = self.settings.get("tesseract_config", "")
            grayscale: bool = self.settings.get("enhance_with_grayscale", True)
            self._ocr_backend = TesseractOCRBackend(
                tesseract_path=tes_path,
                extra_config=extra_cfg,
                grayscale=grayscale,
            )
        return self._ocr_backend

    def reset_ocr_backend(self) -> None:
        """Force re-creation of the OCR backend (e.g. after settings change)."""
        self._ocr_backend = None

    # ------------------------------------------------------------------
    # Async OCR
    # ------------------------------------------------------------------

    def run_ocr(self, pil_image: Any) -> None:
        """Run OCR asynchronously on *pil_image*.

        Emits :attr:`ocr_started`, then either :attr:`ocr_completed` (text)
        or :attr:`ocr_failed` (error message).

        Args:
            pil_image: Pillow Image to process.
        """
        try:
            backend = self.get_ocr_backend()
        except OCRError as exc:
            QMessageBox.critical(None, "Tesseract Not Found", str(exc))
            return

        source_lang: str = self.settings.get("sourceLang", "English")
        extra_config: str = self.settings.get("tesseract_config", "")
        psm5: bool = self.settings.get("tesseract_psm5_vertical", True)

        worker = _OCRWorker(backend, pil_image, source_lang, extra_config, psm5)
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
            QMessageBox.information(None, "No Text Detected", "No text was found in the selected region.")

        self.ocr_completed.emit(text)
        self.status_idle.emit()

        # Auto-translate if not in OCR-only mode
        if self._active_backend_name != "None" and text.strip():
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
        if "not installed" in error or "not in your PATH" in error:
            from screen_translate.core.ocr.tesseract import _platform_install_instructions
            QMessageBox.critical(None, "Tesseract Not Found", _platform_install_instructions())
        else:
            QMessageBox.critical(None, "OCR Error", error)

    # ------------------------------------------------------------------
    # Async translation
    # ------------------------------------------------------------------

    def run_translation(self, text: str) -> None:
        """Translate *text* asynchronously using the active backend.

        Args:
            text: Text to translate.
        """
        backend = self._backends.get(self._active_backend_name)
        if backend is None:
            logger.warning("No translation backend active")
            return

        source_lang: str = self.settings.get("sourceLang", "English")
        target_lang: str = self.settings.get("targetLang", "Japanese")

        worker = _TranslationWorker(backend, text, source_lang, target_lang)
        worker.signals.finished.connect(self._on_translation_done)
        worker.signals.error.connect(self._on_translation_error)
        self.translation_started.emit()
        self.status_busy.emit()
        self._pool.start(worker)

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
            append_history(
                {
                    "from": self.settings.get("sourceLang", ""),
                    "to": self.settings.get("targetLang", ""),
                    "query": "",   # set in _on_ocr_done context
                    "result": result,
                    "engine": self._active_backend_name,
                }
            )

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
        QMessageBox.critical(None, "Translation Error", error)

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
            QMessageBox.warning(None, "No Engine Selected", "Please select a translation engine first.")
            return
        self.run_translation(text)
