"""OpenRouter LLM translation backend."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import TypeAlias

import pycountry
import requests

from .base import TranslationBackend, TranslationError
from .translators_backend import _import_translators

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
logger = logging.getLogger(__name__)
_CUSTOM_CODE_RE = re.compile(r"[^a-z0-9]+")
_ALIAS_PREFIX = "alias::"
CustomLanguageMap: TypeAlias = dict[str, str]
CustomLanguageRow: TypeAlias = dict[str, str]
CustomLanguageList: TypeAlias = list[CustomLanguageRow]
CustomLanguageSetting: TypeAlias = CustomLanguageMap | CustomLanguageList | str
_LANGUAGE_NAME_OVERRIDES: dict[str, str] = {
    "auto": "Auto Detect",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "iw": "Hebrew",
    "jw": "Javanese",
    "mni-Mtei": "Manipuri (Meitei)",
    "pa-Arab": "Punjabi (Arabic)",
    "pt-PT": "Portuguese (Portugal)",
    "fr-CA": "French (Canada)",
    "fa-AF": "Dari",
    "ms-Arab": "Malay (Arabic)",
    "iu-Latn": "Inuktitut (Latin)",
    "sat-Latn": "Santali (Latin)",
    "crh-Latn": "Crimean Tatar (Latin)",
    "ber-Latn": "Berber (Latin)",
}


@dataclass(slots=True)
class OpenRouterBackendConfig:
    """Configuration for the OpenRouter backend."""

    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "openrouter/free"
    timeout: float = 60.0
    system_prompt_template: str = ""
    user_prompt_template: str = "{{text}}"
    custom_languages: CustomLanguageSetting = ""
    proxies: dict[str, str] | None = None
    debug_logging: bool = False

    def endpoint_url(self) -> str:
        """Return the chat-completions endpoint URL."""
        base = self.base_url.strip().rstrip("/")
        if not base:
            base = "https://openrouter.ai/api/v1"
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/api/v1"):
            return f"{base}/chat/completions"
        return f"{base}/api/v1/chat/completions"


def _normalize_custom_language_entries(raw: CustomLanguageSetting) -> list[tuple[str, str]]:
    """Parse custom language definitions from settings text."""
    if isinstance(raw, dict):
        entries: list[tuple[str, str]] = []
        for code, label in raw.items():
            code_text = str(code).strip()
            label_text = str(label).strip()
            if code_text and label_text:
                entries.append((code_text, label_text))
        return entries

    if isinstance(raw, list):
        entries: list[tuple[str, str]] = []
        for row in raw:
            if isinstance(row, dict):
                code_text = str(row.get("code", "")).strip()
                label_text = str(row.get("name", "")).strip()
                if code_text and label_text:
                    entries.append((code_text, label_text))
        return entries

    entries: list[tuple[str, str]] = []
    parts: list[str] = []
    for block in str(raw).splitlines():
        stripped = block.strip()
        if not stripped:
            continue
        if (
            "," in stripped
            and "|" not in stripped
            and "=" not in stripped
            and ":" not in stripped
        ):
            parts.extend(item.strip() for item in stripped.split(",") if item.strip())
        else:
            parts.append(stripped)

    for part in parts:
        code = ""
        label = ""
        for separator in ("|", "=", ":"):
            if separator in part:
                left, right = part.split(separator, 1)
                code = left.strip()
                label = right.strip()
                break
        if not code:
            label = part.strip()
            code = _custom_language_code(label)
        if code:
            entries.append((code, label or code))
    return entries


def _custom_language_code(label: str) -> str:
    """Build a stable internal code for a plain custom language name."""
    normalized = _CUSTOM_CODE_RE.sub("-", label.strip().lower()).strip("-")
    if not normalized:
        return "custom-language"
    return f"custom-{normalized}"


def _alias_language_code(code: str, label: str) -> str:
    """Build a stable internal key for a custom alias of an existing language code."""
    normalized = _CUSTOM_CODE_RE.sub("-", label.strip().lower()).strip("-")
    suffix = normalized or "alias"
    return f"{_ALIAS_PREFIX}{code}::{suffix}"


def _is_alias_language_code(code: str) -> bool:
    """Return True when *code* is one of our internal alias keys."""
    return code.startswith(_ALIAS_PREFIX)


def _alias_base_code(code: str) -> str:
    """Return the canonical base code for an alias key."""
    if not _is_alias_language_code(code):
        return code
    return code[len(_ALIAS_PREFIX) :].split("::", 1)[0] or code


@lru_cache(maxsize=1)
def _base_language_entries() -> tuple[tuple[str, str], ...]:
    """Return a cached Google Translate language list from the translators library."""
    entries: dict[str, str] = {}
    try:
        ts = _import_translators()
        langs = ts.get_languages(translator="google")
        if isinstance(langs, dict):
            codes: set[str] = set()
            for code, targets in langs.items():
                code_text = str(code).strip()
                if code_text:
                    codes.add(code_text)
                if isinstance(targets, (list, tuple, set)):
                    for target in targets:
                        target_text = str(target).strip()
                        if target_text:
                            codes.add(target_text)
                elif isinstance(targets, dict):
                    for target in targets.keys():
                        target_text = str(target).strip()
                        if target_text:
                            codes.add(target_text)
                elif isinstance(targets, str):
                    target_text = str(targets).strip()
                    if target_text:
                        codes.add(target_text)
            for code_text in sorted(codes):
                entries.setdefault(code_text, _language_display_name(code_text))
        elif isinstance(langs, list):
            for item in langs:
                code_text = str(item).strip()
                if code_text:
                    entries.setdefault(code_text, _language_display_name(code_text))
    except Exception:
        entries = {
            "auto": "Auto Detect",
            "en": "English",
            "id": "Indonesian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh-CN": "Chinese (Simplified)",
            "zh-TW": "Chinese (Traditional)",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "pt": "Portuguese",
            "ru": "Russian",
            "ar": "Arabic",
            "hi": "Hindi",
        }
    return tuple(entries.items())


def _language_display_name(code: str) -> str:
    """Return a human-readable language name for a translation code."""
    normalized = code.strip()
    if not normalized:
        return code
    override = _LANGUAGE_NAME_OVERRIDES.get(normalized)
    if override:
        return override

    try:
        candidate = normalized.replace("_", "-")
        if "-" in candidate:
            language_part, script_or_region = candidate.split("-", 1)
            language = pycountry.languages.get(
                alpha_2=language_part.lower()
            ) or pycountry.languages.get(alpha_3=language_part.lower())
            if language is not None:
                region = pycountry.countries.get(alpha_2=script_or_region.upper())
                if region is not None:
                    return f"{language.name} ({region.name})"
        language = pycountry.languages.get(
            alpha_2=candidate.lower()
        ) or pycountry.languages.get(alpha_3=candidate.lower())
        if language is not None:
            return str(language.name)
    except Exception:
        pass

    return normalized


def language_entries(custom_languages: CustomLanguageSetting = "") -> list[tuple[str, str]]:
    """Return backend language entries for selection lists.

    Built-in/default languages keep their canonical display names. Custom entries are
    appended only when they introduce a new language code.
    """
    entries = list(_base_language_entries())
    base_codes = {code for code, _label in entries}
    seen_custom: set[tuple[str, str]] = set()
    for code, label in _normalize_custom_language_entries(custom_languages):
        pair = (code, label)
        if pair in seen_custom:
            continue
        seen_custom.add(pair)
        if code in base_codes:
            entries.append((_alias_language_code(code, label), label))
        else:
            entries.append((code, label))
            base_codes.add(code)
    return entries


def custom_language_names(custom_languages: CustomLanguageSetting = "") -> list[str]:
    """Return only the display names of user-defined custom languages."""
    names: list[str] = []
    for _code, label in _normalize_custom_language_entries(custom_languages):
        cleaned = label.strip()
        if cleaned:
            names.append(cleaned)
    return names


def prompt_language_names(custom_languages: CustomLanguageSetting = "") -> list[str]:
    """Return all prompt-visible language names, including custom aliases."""
    names = [label for _code, label in _base_language_entries()]
    names.extend(custom_language_names(custom_languages))
    return names


def language_name(code: str, custom_languages: CustomLanguageSetting = "") -> str:
    """Return a friendly name for a language code."""
    normalized = code.strip()
    if not normalized:
        return code
    if normalized.lower() == "auto":
        return "Auto Detect"
    for lang_code, label in language_entries(custom_languages):
        if lang_code == normalized:
            return label
    return _alias_base_code(normalized)


def canonical_language_code(code: str, custom_languages: CustomLanguageSetting = "") -> str:
    """Return the real backend language code for a possibly-aliased selection key."""
    normalized = code.strip()
    if not normalized:
        return code
    if _is_alias_language_code(normalized):
        return _alias_base_code(normalized)
    for lang_code, _label in language_entries(custom_languages):
        if lang_code == normalized:
            return normalized
    return normalized


def display_language_code(code: str, custom_languages: CustomLanguageSetting = "") -> str:
    """Return the short display code shown in UI for a selection key."""
    return canonical_language_code(code, custom_languages)


def format_language_list(custom_languages: CustomLanguageSetting = "") -> str:
    """Return a prompt-ready language list using human-readable names only."""
    names = prompt_language_names(custom_languages)
    if not names:
        return "No languages configured."
    return "\n".join(f"- {label}" for label in names)


def format_custom_language_list(custom_languages: CustomLanguageSetting = "") -> str:
    """Return a prompt-ready custom-language list using names only."""
    names = custom_language_names(custom_languages)
    if not names:
        return "None"
    return "\n".join(f"- {name}" for name in names)


def render_prompt_template(template: str, context: dict[str, str]) -> str:
    """Render a prompt template with ``{{placeholder}}`` values."""

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return context.get(key, match.group(0))

    return _PLACEHOLDER_RE.sub(_replace, template)


class OpenRouterBackend(TranslationBackend):
    """Translation backend for OpenRouter chat-completions APIs."""

    def __init__(self, config: OpenRouterBackendConfig) -> None:
        self._config = config
        self._langs = [code for code, _ in language_entries(config.custom_languages)]

    @property
    def name(self) -> str:
        return "OpenRouter"

    @property
    def requires_api_key(self) -> bool:
        return True

    def available_languages(self) -> list[str]:
        return self._langs

    def available_target_languages(self, source_lang: str) -> list[str]:
        return [lang for lang in self._langs if lang not in {"auto", "Auto"}]

    def language_display_name(self, code: str) -> str:
        """Return the configured display name for one backend language code."""
        return language_name(code, self._config.custom_languages)

    def language_display_code(self, code: str) -> str:
        """Return the short display code for one backend language code."""
        return display_language_code(code, self._config.custom_languages)

    def resolve_language_code(self, code: str) -> str:
        """Return the canonical backend language code for one selection key."""
        return canonical_language_code(code, self._config.custom_languages)

    def _debug(self, message: str, *args: object) -> None:
        """Emit debug logs only when backend debug logging is enabled."""
        if self._config.debug_logging:
            logger.debug(message, *args)

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        api_key = self._config.api_key.strip()
        if not api_key:
            raise TranslationError("OpenRouter API key is required.")
        self._debug(
            "OpenRouter raw selection source_lang=%r target_lang=%r",
            source_lang,
            target_lang,
        )

        context = {
            "text": text,
            "source_language": language_name(
                source_lang, self._config.custom_languages
            ),
            "target_language": language_name(
                target_lang, self._config.custom_languages
            ),
            "language_list": format_language_list(self._config.custom_languages),
            "custom_languages": format_custom_language_list(self._config.custom_languages),
        }
        system_prompt = render_prompt_template(
            self._config.system_prompt_template.strip(),
            context,
        )
        user_prompt = render_prompt_template(
            self._config.user_prompt_template.strip() or "{{text}}",
            context,
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": self._config.model.strip() or "openrouter/free",
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        self._debug(
            "OpenRouter request model=%s source=%s target=%s system_prompt=%r user_prompt=%r",
            payload["model"],
            context["source_language"],
            context["target_language"],
            system_prompt,
            user_prompt,
        )

        try:
            response = requests.post(
                self._config.endpoint_url(),
                headers=headers,
                json=payload,
                timeout=self._config.timeout,
                proxies=self._config.proxies or None,
            )
            response.raise_for_status()
            data = response.json()
            self._debug("OpenRouter raw response: %s", data)
            choices = data.get("choices", [])
            if not choices:
                raise TranslationError("OpenRouter API returned no choices.")
            message = choices[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, list):
                pieces: list[str] = []
                for item in content:
                    if isinstance(item, dict):
                        text_part = item.get("text", "")
                        if isinstance(text_part, str):
                            pieces.append(text_part)
                content = "".join(pieces)
            translated = str(content).strip()
            if not translated:
                raise TranslationError("OpenRouter API returned empty text.")
            self._debug("OpenRouter translated text: %r", translated)
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
            raise TranslationError(f"OpenRouter error: {exc}{suffix}") from exc


def load_openrouter_backend(
    *,
    api_key: str = "",
    base_url: str = "https://openrouter.ai/api/v1",
    model: str = "openrouter/free",
    timeout: float = 60.0,
    debug_logging: bool = False,
    system_prompt_template: str = "",
    user_prompt_template: str = "{{text}}",
    custom_languages: CustomLanguageSetting = "",
    proxies: dict[str, str] | None = None,
) -> OpenRouterBackend:
    """Create a configured OpenRouter backend."""
    return OpenRouterBackend(
        OpenRouterBackendConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout=timeout,
            debug_logging=debug_logging,
            system_prompt_template=system_prompt_template,
            user_prompt_template=user_prompt_template,
            custom_languages=custom_languages,
            proxies=proxies,
        )
    )
