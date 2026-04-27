"""Helpers for translation proxy configuration."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator


def build_translation_proxies(settings: Any) -> dict[str, str]:
    """Build a requests-style proxy mapping from settings."""
    if not bool(settings.get("translation_proxy_enabled", False)):
        return {}

    proxies: dict[str, str] = {}
    http_proxy = str(settings.get("translation_proxy_http", "")).strip()
    https_proxy = str(settings.get("translation_proxy_https", "")).strip()

    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy

    return proxies


def translation_no_proxy(settings: Any) -> str:
    """Return the configured NO_PROXY value for translation backends."""
    if not bool(settings.get("translation_proxy_enabled", False)):
        return ""
    return str(settings.get("translation_proxy_no_proxy", "")).strip()


@contextmanager
def temporary_proxy_env(
    proxies: dict[str, str] | None = None,
    no_proxy: str = "",
) -> Iterator[None]:
    """Temporarily apply proxy environment variables for network libraries."""
    proxies = proxies or {}
    previous = {
        "HTTP_PROXY": os.environ.get("HTTP_PROXY"),
        "HTTPS_PROXY": os.environ.get("HTTPS_PROXY"),
        "NO_PROXY": os.environ.get("NO_PROXY"),
    }

    try:
        if proxies.get("http"):
            os.environ["HTTP_PROXY"] = proxies["http"]
        else:
            os.environ.pop("HTTP_PROXY", None)

        if proxies.get("https"):
            os.environ["HTTPS_PROXY"] = proxies["https"]
        else:
            os.environ.pop("HTTPS_PROXY", None)

        if no_proxy:
            os.environ["NO_PROXY"] = no_proxy
        else:
            os.environ.pop("NO_PROXY", None)

        yield
    finally:
        for key, value in previous.items():
            if value:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)
