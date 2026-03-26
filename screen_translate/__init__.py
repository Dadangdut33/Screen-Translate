"""Screen-Translate: screen OCR and translation desktop application."""

from __future__ import annotations

import logging
import re
from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

_logger = logging.getLogger(__name__)

try:
    __version__: str = version("screen-translate")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+")
if not _SEMVER_RE.match(__version__):
    _logger.warning("Non-semver version string detected: %s", __version__)
