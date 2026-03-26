"""Tesseract OCR backend using pytesseract + Pillow preprocessing."""

from __future__ import annotations

import logging
import platform
import shutil
from functools import lru_cache

from PIL import Image, ImageFilter, ImageOps

from .base import OCRBackend, OCRError

logger = logging.getLogger(__name__)

# Language display name → tesseract code (kept from original LangCode.py)
TESSERACT_LANG_MAP: dict[str, str] = {
    "Auto": "auto",
    "Afrikaans": "afr",
    "Amharic": "amh",
    "Arabic": "ara",
    "Assemese": "asm",
    "Azerbaijani": "aze_cyrl",
    "Belarusian": "bel",
    "Bengali": "ben",
    "Tibetan": "bod",
    "Bosnian": "bos",
    "Bulgarian": "bul",
    "Catalan": "cat",
    "Cebuano": "ceb",
    "Czech": "ces",
    "Chinese Simplified": "chi_sim",
    "Chinese Simplified (Vertical)": "chi_sim_vert",
    "Chinese Traditional": "chi_tra",
    "Chinese Traditional (Vertical)": "chi_tra_vert",
    "Welsh": "cym",
    "Danish": "dan",
    "German": "deu",
    "Greek": "ell",
    "English": "eng",
    "Esperanto": "epo",
    "Estonian": "est",
    "Basque": "eus",
    "Faroese": "fao",
    "Persian": "fas",
    "Filipino": "fil",
    "Finnish": "fin",
    "French": "fra",
    "Western Frisian": "fry",
    "Scottish Gaelic": "gla",
    "Irish": "gle",
    "Galician": "glg",
    "Gujarati": "guj",
    "Haitian": "hat",
    "Hebrew": "heb",
    "Hindi": "hin",
    "Croatian": "hrv",
    "Hungarian": "hun",
    "Armenian": "hye",
    "Indonesian": "ind",
    "Icelandic": "isl",
    "Italian": "ita",
    "Javanese": "jav",
    "Japanese": "jpn",
    "Japanese (Vertical)": "jpn_vert",
    "Kannada": "kan",
    "Georgian": "kat",
    "Kazakh": "kaz",
    "Khmer": "khm",
    "Kirghiz": "kir",
    "Korean": "kor",
    "Lao": "lao",
    "Latin": "lat",
    "Latvian": "lav",
    "Lithuanian": "lit",
    "Luxembourgish": "ltz",
    "Malayalam": "mal",
    "Marathi": "mar",
    "Macedonian": "mkd",
    "Maltese": "mlt",
    "Mongolian": "mon",
    "Maori": "mri",
    "Malay": "msa",
    "Burmese": "mya",
    "Nepali": "nep",
    "Dutch": "nld",
    "Norwegian": "nor",
    "Punjabi": "pan",
    "Polish": "pol",
    "Portuguese": "por",
    "Romanian": "ron",
    "Russian": "rus",
    "Sanskrit": "san",
    "Sinhala": "sin",
    "Slovak": "slk",
    "Slovenian": "slv",
    "Spanish": "spa",
    "Albanian": "sqi",
    "Serbian": "srp",
    "Sundanese": "sun",
    "Swahili": "swa",
    "Swedish": "swe",
    "Tamil": "tam",
    "Tatar": "tat",
    "Telugu": "tel",
    "Tajik": "tgk",
    "Tagalog": "tgl",
    "Thai": "tha",
    "Turkish": "tur",
    "Ukrainian": "ukr",
    "Urdu": "urd",
    "Uzbek": "uzb",
    "Vietnamese": "vie",
    "Yiddish": "yid",
    "Yoruba": "yor",
}

# Reverse map: tesseract code → display name
_REVERSE_MAP: dict[str, str] = {v: k for k, v in TESSERACT_LANG_MAP.items() if v != "auto"}


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
    ) -> None:
        """Initialise the backend.

        Args:
            tesseract_path: Path to the tesseract executable (empty = use PATH).
            extra_config: Extra pytesseract config flags (e.g. ``--psm 6``).
            grayscale: Whether to convert images to grayscale before OCR.
        """
        check_tesseract(tesseract_path)
        self._config = extra_config
        self._grayscale = grayscale

        import pytesseract  # re-import after path may have been set

        self._pytesseract = pytesseract
        logger.debug("TesseractOCRBackend initialised (path=%r, config=%r)", tesseract_path, extra_config)

    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Return backend display name."""
        return "Tesseract"

    def detect_languages(self) -> list[str]:
        """Return display names of languages whose data is installed.

        Returns:
            Sorted list of display names, e.g. ``["English", "Japanese", ...]``.
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
            processed = _preprocess(image, grayscale=self._grayscale)
            result: str = self._pytesseract.image_to_string(processed, config=self._config)
            return result.strip()
        except Exception as exc:
            raise OCRError(str(exc)) from exc

    def extract_text_with_lang(
        self,
        image: Image.Image,
        lang_display_name: str,
        extra_config: str = "",
        psm5_vertical: bool = True,
    ) -> str:
        """Run OCR with a specific language code.

        Args:
            image: Pillow Image to process.
            lang_display_name: Display name such as ``"Japanese (Vertical)"``.
            extra_config: Additional pytesseract config string.
            psm5_vertical: Auto-add ``--psm 5`` for vertical-script languages.

        Returns:
            Recognised text string.

        Raises:
            OCRError: If the language is unknown or tesseract fails.
        """
        lang_code = TESSERACT_LANG_MAP.get(lang_display_name)
        if lang_code is None:
            raise OCRError(f"Unknown language: {lang_display_name!r}")

        config = extra_config or self._config
        if "--psm" not in config and psm5_vertical and "Vertical" in lang_display_name:
            config = (config + " --psm 5").strip()

        try:
            processed = _preprocess(image, grayscale=self._grayscale)
            result: str = self._pytesseract.image_to_string(processed, lang=lang_code, config=config)
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

    names: list[str] = []
    for code in codes:
        if code in _REVERSE_MAP:
            names.append(_REVERSE_MAP[code])
        elif code != "osd":  # skip 'osd' (orientation detection script)
            names.append(code)  # fall back to raw code
    names.sort()
    return names
