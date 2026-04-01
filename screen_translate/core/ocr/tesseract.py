"""Tesseract OCR backend using pytesseract + Pillow preprocessing."""

from __future__ import annotations

import logging
import platform
import shutil
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps
from platformdirs import user_data_dir

from .base import OCRBackend, OCRError

logger = logging.getLogger(__name__)

# Removed manual TESSERACT_LANG_MAP to use raw library codes


def _platform_install_instructions() -> str:
    """Return platform-appropriate Tesseract install instructions."""
    sys_name = platform.system()
    if sys_name == "Windows":
        return (
            "Tesseract is not installed or not on PATH.\n\n"
            "Install via winget:\n"
            "  winget install UB-Mannheim.TesseractOCR\n\n"
            "Or download from:\n"
            "  https://github.com/UB-Mannheim/tesseract/wiki"
        )
    elif sys_name == "Darwin":
        return (
            "Tesseract is not installed or not on PATH.\n\n"
            "Install via Homebrew:\n"
            "  brew install tesseract tesseract-lang"
        )
    else:
        return (
            "Tesseract is not installed or not on PATH.\n\n"
            "Install via apt:\n"
            "  sudo apt install tesseract-ocr tesseract-ocr-all"
        )


def check_tesseract(custom_path: str = "") -> None:
    """Verify that Tesseract is available.

    Args:
        custom_path: If non-empty, use this path as the tesseract executable.

    Raises:
        OCRError: Human-readable error with install instructions.
    """
    import pytesseract

    if custom_path:
        pytesseract.pytesseract.tesseract_cmd = custom_path
        return

    if shutil.which("tesseract") is None:
        # Try common default paths before giving up
        defaults = {
            "Windows": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            "Darwin": "/usr/local/bin/tesseract",
        }
        fallback = defaults.get(platform.system(), "")
        if fallback and shutil.which(fallback):
            pytesseract.pytesseract.tesseract_cmd = fallback
        else:
            raise OCRError(_platform_install_instructions())


def _preprocess(image: Image.Image, grayscale: bool = True) -> Image.Image:
    """Apply preprocessing to improve OCR accuracy.

    Steps: convert to RGB → optional grayscale → autocontrast → sharpen.

    Args:
        image: Source Pillow image.
        grayscale: If True, convert to grayscale before thresholding.

    Returns:
        Preprocessed Pillow image ready for OCR.
    """
    img = image.convert("RGB")
    if grayscale:
        img = ImageOps.grayscale(img)  # type: ignore[assignment]
    img = ImageOps.autocontrast(img, cutoff=2)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def _run_cv2_contour_ocr(
    image: Image.Image,
    pytesseract_module: object,
    lang_code: str,
    config: str,
    grayscale: bool,
    background_mode: str,
    save_debug_image: bool,
) -> str:
    """Use OpenCV contour detection to OCR likely text blocks."""
    try:
        import cv2
    except ImportError as exc:
        raise OCRError("opencv-python is required for contour OCR mode.") from exc

    rgb = image.convert("RGB")
    open_cv_image = np.array(rgb)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    gray_img = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    if background_mode == "Auto-Detect":
        is_light = float(np.mean(open_cv_image)) > 127
    else:
        is_light = background_mode == "Light"
    thresh_type = cv2.THRESH_BINARY_INV if is_light else cv2.THRESH_BINARY

    _, thresh = cv2.threshold(gray_img, 0, 255, cv2.THRESH_OTSU | thresh_type)
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))
    dilation = cv2.dilate(thresh, rect_kernel, iterations=1)
    contours, _ = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    ocr_kwargs = {"config": config}
    if lang_code:
        ocr_kwargs["lang"] = lang_code

    if not contours:
        processed = _preprocess(image, grayscale=grayscale)
        return str(pytesseract_module.image_to_string(processed, **ocr_kwargs)).strip()

    logger.debug(
        "OpenCV contour OCR: detected %d contour(s), background=%s, mean=%.2f",
        len(contours),
        "light" if is_light else "dark",
        float(np.mean(open_cv_image)),
    )

    base_img = gray_img if grayscale else open_cv_image
    annotated = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
    chunks: list[str] = []
    for cnt in contours[::-1]:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cropped = base_img[y : y + h, x : x + w]
        text = str(pytesseract_module.image_to_string(cropped, **ocr_kwargs)).strip()
        if text:
            chunks.append(text)

    if save_debug_image:
        _save_cv2_debug_image(annotated)

    return "\n".join(chunks).strip()


def _save_cv2_debug_image(image: np.ndarray) -> None:
    """Save the contour-annotated debug image to the captured directory."""
    try:
        import cv2

        captured_dir = Path(user_data_dir("screen-translate", "Dadangdut33")) / "captured"
        captured_dir.mkdir(parents=True, exist_ok=True)
        path = captured_dir / f"cv2_contour_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        cv2.imwrite(str(path), image)
        logger.info("Saved OpenCV contour debug image to %s", path)
    except Exception as exc:
        logger.exception("Could not save OpenCV contour debug image: %s", exc)


class TesseractOCRBackend(OCRBackend):
    """OCR backend wrapping pytesseract with Pillow-based preprocessing.

    This is the primary OCR engine.  It performs:
    1. Optional grayscale + autocontrast + sharpening via Pillow.
    2. Passes the result to pytesseract with the configured language code.
    """

    def __init__(
        self,
        tesseract_path: str = "",
        extra_config: str = "",
        grayscale: bool = True,
        use_cv2_contour: bool = False,
        save_cv2_contour_image: bool = False,
        background_mode: str = "Auto-Detect",
    ) -> None:
        """Initialise the backend.

        Args:
            tesseract_path: Path to the tesseract executable (empty = use PATH).
            extra_config: Extra pytesseract config flags (e.g. ``--psm 6``).
            grayscale: Whether to convert images to grayscale before OCR.
            use_cv2_contour: Whether to use OpenCV contour-based text block OCR.
            save_cv2_contour_image: Whether to save the contour-annotated debug image.
            background_mode: Threshold background hint: Auto-Detect, Light, or Dark.
        """
        check_tesseract(tesseract_path)
        self._config = extra_config
        self._grayscale = grayscale
        self._use_cv2_contour = use_cv2_contour
        self._save_cv2_contour_image = save_cv2_contour_image
        self._background_mode = background_mode

        import pytesseract  # re-import after path may have been set

        self._pytesseract = pytesseract
        logger.debug(
            "TesseractOCRBackend initialised (path=%r, config=%r, grayscale=%r, cv2_contour=%r, background=%r)",
            tesseract_path,
            extra_config,
            grayscale,
            use_cv2_contour,
            background_mode,
        )

    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Return backend display name."""
        return "Tesseract"

    def detect_languages(self) -> list[str]:
        """Return raw language codes of installed data.

        Returns:
            Sorted list of codes, e.g. ``["eng", "jpn", ...]``.
        """
        return _get_installed_languages(self._pytesseract)

    def extract_text(self, image: Image.Image) -> str:  # type: ignore[override]
        """Run OCR on *image* and return recognised text.

        Args:
            image: Pillow Image to process.

        Returns:
            Recognised text string (may be empty if nothing found).

        Raises:
            OCRError: If tesseract fails or is unavailable.
        """
        try:
            if self._use_cv2_contour:
                result = _run_cv2_contour_ocr(
                    image,
                    self._pytesseract,
                    "",
                    self._config,
                    self._grayscale,
                    self._background_mode,
                    self._save_cv2_contour_image,
                )
            else:
                processed = _preprocess(image, grayscale=self._grayscale)
                result = str(self._pytesseract.image_to_string(processed, config=self._config))
            return result.strip()
        except Exception as exc:
            raise OCRError(str(exc)) from exc

    def extract_text_with_lang(
        self,
        image: Image.Image,
        lang_code: str,
        extra_config: str = "",
        psm5_vertical: bool = True,
    ) -> str:
        """Run OCR with a specific language code.

        Args:
            image: Pillow Image to process.
            lang_code: Language code.
            extra_config: Additional pytesseract config string.
            psm5_vertical: Auto-add ``--psm 5`` for vertical-script languages.

        Returns:
            Recognised text string.

        Raises:
            OCRError: If the language is unknown or tesseract fails.
        """
        config = extra_config or self._config
        if "--psm" not in config and psm5_vertical and "_vert" in lang_code:
            config = (config + " --psm 5").strip()

        try:
            if self._use_cv2_contour:
                result = _run_cv2_contour_ocr(
                    image,
                    self._pytesseract,
                    lang_code,
                    config,
                    self._grayscale,
                    self._background_mode,
                    self._save_cv2_contour_image,
                )
            else:
                processed = _preprocess(image, grayscale=self._grayscale)
                result = str(self._pytesseract.image_to_string(processed, lang=lang_code, config=config))
            return result.strip()
        except Exception as exc:
            raise OCRError(str(exc)) from exc


@lru_cache(maxsize=1)
def _get_installed_languages(pytesseract_module: object) -> list[str]:  # type: ignore[type-arg]
    """Cache the result of get_languages() as it requires a subprocess call.

    Args:
        pytesseract_module: The pytesseract module (used as cache key).

    Returns:
        Sorted list of display names for installed languages.
    """
    import pytesseract as pt

    try:
        codes: list[str] = pt.get_languages(config="")
    except Exception:
        codes = []

    names: list[str] = [code for code in codes if code != "osd"]
    names.sort()
    return names
