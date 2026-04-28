"""Helpers for translation proxy configuration."""

from __future__ import annotations

import os
import random
from contextlib import contextmanager
from typing import Iterator, Protocol


class SettingsLike(Protocol):
    """Minimal settings interface needed for proxy helpers."""

    def get(self, key: str, default: object = None) -> object: ...


def parse_proxy_list(raw: object) -> list[str]:
    """Normalize proxy settings into a clean ordered list of entries."""
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    text = str(raw).replace(",", "\n")
    return [line.strip() for line in text.splitlines() if line.strip()]


def build_translation_proxies(settings: SettingsLike) -> dict[str, str]:
    """Build a requests-style proxy mapping from settings.

    When multiple proxies are configured for a scheme, one is chosen at random.
    """
    if not bool(settings.get("translation_proxy_enabled", False)):
        return {}

    proxies: dict[str, str] = {}
    http_candidates = parse_proxy_list(settings.get("translation_proxy_http", ""))
    https_candidates = parse_proxy_list(settings.get("translation_proxy_https", ""))

    if http_candidates:
        proxies["http"] = random.choice(http_candidates)
    if https_candidates:
        proxies["https"] = random.choice(https_candidates)

    return proxies


def translation_no_proxy(settings: SettingsLike) -> str:
    """Return the configured NO_PROXY value for translation backends."""
    if not bool(settings.get("translation_proxy_enabled", False)):
        return ""
    return ",".join(parse_proxy_list(settings.get("translation_proxy_no_proxy", "")))


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
