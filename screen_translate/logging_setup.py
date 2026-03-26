"""Logging configuration for Screen-Translate."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def get_log_path() -> Path:
    """Return the path to the application log file."""
    from platformdirs import user_log_dir

    log_dir = Path(user_log_dir("screen-translate", "Dadangdut33"))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "screen_translate.log"


def setup_logging(level: str = "DEBUG", keep_log: bool = False) -> None:
    """Initialise root logger for Screen-Translate.

    Args:
        level: Log level name (DEBUG, INFO, WARNING, ERROR).
        keep_log: If True, also write logs to a file on disk.
    """
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if keep_log:
        try:
            file_handler = logging.FileHandler(get_log_path(), encoding="utf-8")
            file_handler.setFormatter(logging.Formatter(fmt))
            handlers.append(file_handler)
        except OSError as exc:
            logging.getLogger(__name__).warning("Cannot open log file: %s", exc)

    logging.basicConfig(level=logging.getLevelName(level), format=fmt, handlers=handlers, force=True)


logger: logging.Logger = logging.getLogger("screen_translate")
