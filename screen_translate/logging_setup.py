"""Logging configuration for Screen-Translate."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from loguru import logger

_THIRD_PARTY_LOGGERS = (
    "urllib3",
    "urllib3.connectionpool",
    "httpx",
    "httpcore",
    "hpack",
    "h2",
    "h11",
    "aioquic",
    "quic",
)


class _InterceptHandler(logging.Handler):
    """Forward standard-library logging records into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.bind(logger_name=record.name).opt(
            depth=depth,
            exception=record.exc_info,
        ).log(level, record.getMessage())


def get_log_dir() -> Path:
    """Return the directory containing application log files."""
    from platformdirs import user_config_dir

    log_dir = Path(user_config_dir("screen-translate", "Dadangdut33")) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_path() -> Path:
    """Return the path to the application log file."""
    return get_log_dir() / "screen_translate.log"


def setup_logging(
    level: str = "DEBUG",
    keep_log: bool = False,
    suppress_third_party: bool = True,
    max_log_rotation: int = 5,
) -> None:
    """Initialise application logging through loguru."""
    _configure_stdlib_intercept()
    set_log_level(level)
    logger.remove()
    logger.add(
        sys.stdout,
        level=level.upper(),
        format=_loguru_format(),
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    if keep_log:
        logger.add(
            str(get_log_path()),
            level=level.upper(),
            format=_loguru_format(),
            rotation="00:00",
            retention=max(1, max_log_rotation),
            encoding="utf-8",
            enqueue=True,
            backtrace=False,
            diagnose=False,
        )

    if suppress_third_party:
        _quiet_third_party_loggers()


def set_log_level(level: str) -> None:
    """Update stdlib logger thresholds and return value storage callers can use."""
    normalized = level.upper()
    logging.getLogger().setLevel(getattr(logging, normalized, logging.DEBUG))


def _configure_stdlib_intercept() -> None:
    """Route standard logging into loguru."""
    root_logger = logging.getLogger()
    root_logger.handlers = [_InterceptHandler()]
    root_logger.setLevel(logging.DEBUG)

    for name in list(logging.root.manager.loggerDict):
        std_logger = logging.getLogger(name)
        std_logger.handlers = []
        std_logger.propagate = True


def _loguru_format() -> str:
    """Return the shared loguru format string."""
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss,SSS}</green> "
        "[<level>{level}</level>] "
        "{extra[logger_name]}: {message}"
    )


def _quiet_third_party_loggers() -> None:
    """Reduce noisy dependency logs while keeping app logs at the chosen level."""
    for logger_name in _THIRD_PARTY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


__all__ = ["get_log_dir", "get_log_path", "logger", "set_log_level", "setup_logging"]
