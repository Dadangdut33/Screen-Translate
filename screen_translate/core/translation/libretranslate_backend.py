"""LibreTranslate backend with configurable local/remote endpoint support."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from .base import TranslationBackend, TranslationError

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LibreTranslateConfig:
    """Configuration for a LibreTranslate endpoint."""

    use_local: bool = False
    local_port: str = "5000"
    host: str = "translate.argosopentech.com"
    port: str = ""
    use_https: bool = True
    api_key: str = ""
    proxies: dict[str, str] | None = None
    timeout: float = 20.0

    def base_url(self) -> str:
        """Return the configured base URL."""
        if self.use_local:
            port = self.local_port.strip() or "5000"
            return f"http://127.0.0.1:{port}"

        scheme = "https" if self.use_https else "http"
        host = self.host.strip() or "translate.argosopentech.com"
        port = self.port.strip()
        if port:
            return f"{scheme}://{host}:{port}"
        return f"{scheme}://{host}"


class LibreTranslateBackend(TranslationBackend):
    """LibreTranslate backend using the public/local HTTP API."""

    def __init__(self, config: LibreTranslateConfig) -> None:
        self._config = config
        self._langs: list[str] = []
        self._targets_by_source: dict[str, list[str]] = {}

    def invalidate_languages_cache(self) -> None:
        """Clear the cached supported-language list."""
        self._langs = []
        self._targets_by_source = {}

    @property
    def name(self) -> str:
        """Return backend name."""
        return "LibreTranslate"

    def available_languages(self) -> list[str]:
        """Return supported language codes from the configured endpoint."""
        if self._langs:
            return self._langs

        url = f"{self._config.base_url().rstrip('/')}/languages"
        try:
            response = requests.get(
                url,
                timeout=self._config.timeout,
                proxies=self._config.proxies or None,
            )
            response.raise_for_status()
            data = response.json()
            codes: set[str] = set()
            targets_by_source: dict[str, list[str]] = {}
            for item in data:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("code", "")).strip()
                if not code:
                    continue
                codes.add(code)
                raw_targets = item.get("targets", [])
                targets = sorted(
                    {
                        str(target).strip()
                        for target in raw_targets
                        if str(target).strip()
                    }
                )
                targets_by_source[code] = targets
                codes.update(targets)

            normalized = sorted(code for code in codes if code)
            self._targets_by_source = targets_by_source
            self._langs = ["auto", *normalized] if normalized else ["auto"]
        except Exception as exc:
            logger.warning("Failed to load LibreTranslate languages from %s: %s", url, exc)
            self._langs = ["auto"]

        return self._langs

    def available_target_languages(self, source_lang: str) -> list[str]:
        """Return target languages reachable from the given source language."""
        self.available_languages()
        source = source_lang.strip()
        if not source or source in {"auto", "Auto"}:
            union: set[str] = set()
            for targets in self._targets_by_source.values():
                union.update(targets)
            return sorted(union)
        return list(self._targets_by_source.get(source, []))

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text with the configured LibreTranslate endpoint."""
        url = f"{self._config.base_url().rstrip('/')}/translate"
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text",
        }
        api_key = self._config.api_key.strip()
        if api_key:
            payload["api_key"] = api_key

        try:
            response = requests.post(
                url,
                data=payload,
                timeout=self._config.timeout,
                proxies=self._config.proxies or None,
            )
            response.raise_for_status()
            data = response.json()
            translated = str(data.get("translatedText", "")).strip()
            if not translated:
                raise TranslationError("LibreTranslate returned an empty response.")
            return translated
        except TranslationError:
            raise
        except Exception as exc:
            detail = ""
            response = getattr(exc, "response", None)
            if response is not None:
                try:
                    detail = response.text.strip()
                except Exception:
                    detail = ""
            suffix = f" ({detail})" if detail else ""
            raise TranslationError(f"LibreTranslate error: {exc}{suffix}") from exc


def load_libretranslate_backend(
    *,
    use_local: bool = False,
    local_port: str = "5000",
    host: str = "translate.argosopentech.com",
    port: str = "",
    use_https: bool = True,
    api_key: str = "",
    proxies: dict[str, str] | None = None,
) -> LibreTranslateBackend:
    """Create a configured LibreTranslate backend."""
    config = LibreTranslateConfig(
        use_local=use_local,
        local_port=local_port,
        host=host,
        port=port,
        use_https=use_https,
        api_key=api_key,
        proxies=proxies,
    )
    return LibreTranslateBackend(config)
