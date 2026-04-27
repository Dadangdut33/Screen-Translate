"""Argos Translate backend - fully offline neural translation."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import sys

from .base import TranslationBackend, TranslationError

logger = logging.getLogger(__name__)


def default_argos_package_dir() -> Path:
    """Return the default Argos package directory."""
    from platformdirs import user_data_dir

    return Path(user_data_dir("argos-translate")) / "packages"


def argos_package_dir_from_setting(value: str) -> Path:
    """Return a normalized Argos package directory from settings."""
    raw = value.strip()
    return Path(raw).expanduser() if raw else default_argos_package_dir()


def configure_argos_package_dir(package_dir: str) -> Path:
    """Apply an Argos package directory to the current process."""
    target_dir = argos_package_dir_from_setting(package_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    os.environ["ARGOS_PACKAGES_DIR"] = str(target_dir)
    os.environ["ARGOS_PACKAGE_DIR"] = str(target_dir)
    os.environ["ARGOS_TRANSLATE_PACKAGE_DIR"] = str(target_dir)

    try:
        import argostranslate.settings as argos_settings

        argos_settings.package_data_dir = target_dir
        argos_settings.package_dirs = [target_dir]
        argos_settings.legacy_package_data_dir = target_dir
    except Exception:
        pass

    return target_dir


def argos_package_dir_size(package_dir: str) -> int:
    """Return total size in bytes for the configured Argos package directory."""
    total = 0
    target_dir = configure_argos_package_dir(package_dir)
    for child in target_dir.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                continue
    return total


class ArgosTranslateBackend(TranslationBackend):
    """Offline neural translation via argostranslate.

    Language packs must be downloaded separately.  If none are installed
    the backend will still load but ``available_languages()`` returns an
    empty list and ``translate()`` raises :class:`TranslationError`.
    """

    @property
    def name(self) -> str:
        """Return backend name."""
        return "Argos Translate"

    def available_languages(self) -> list[str]:
        """Return unique language codes from installed packs or the Argos index."""
        try:
            from argostranslate import package, translate

            installed = translate.get_installed_languages()
            codes = {lang.code for lang in installed}
            if not codes:
                try:
                    package.update_package_index()
                    available = package.get_available_packages()
                    for pkg in available:
                        if getattr(pkg, "from_code", ""):
                            codes.add(str(pkg.from_code))
                        if getattr(pkg, "to_code", ""):
                            codes.add(str(pkg.to_code))
                except Exception as exc:
                    logger.debug("argostranslate package index unavailable: %s", exc)
            return sorted(codes)
        except Exception as exc:
            logger.debug("argostranslate unavailable: %s", exc)
            return []

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Argos Translate.

        Args:
            text: Text to translate.
            source_lang: Source language code.
            target_lang: Target language code.
        """
        try:
            from argostranslate import translate

            installed = translate.get_installed_languages()
            src_obj = next(
                (lang for lang in installed if lang.code == source_lang), None
            )
            tgt_obj = next(
                (lang for lang in installed if lang.code == target_lang), None
            )

            if src_obj is None or tgt_obj is None:
                raise TranslationError(
                    f"No installed Argos pack for {source_lang!r} → {target_lang!r}. "
                    "Use the Settings dialog to install language packs."
                )

            translation = src_obj.get_translation(tgt_obj)
            if translation is None:
                raise TranslationError(
                    f"No direct translation pack for {source_lang!r} → {target_lang!r}."
                )
            return str(translation.translate(text))
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc

    @staticmethod
    def install_language_pack(from_lang_code: str, to_lang_code: str) -> None:
        """Download and install an Argos language pack."""
        try:
            from argostranslate import package

            package.update_package_index()
            available = package.get_available_packages()
            pkg = next(
                (
                    p
                    for p in available
                    if p.from_code == from_lang_code and p.to_code == to_lang_code
                ),
                None,
            )
            if pkg is None:
                raise TranslationError(
                    f"No Argos pack found for {from_lang_code!r} → {to_lang_code!r}."
                )
            package.install_from_path(pkg.download())
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(str(exc)) from exc


def load_argos_backend(package_dir: str = "") -> ArgosTranslateBackend | None:
    """Return an ArgosTranslateBackend if the package is installed."""
    try:
        configure_argos_package_dir(package_dir)
        import argostranslate  # noqa: F401

        return ArgosTranslateBackend()
    except ImportError:
        logger.debug("argostranslate not installed - offline backend unavailable")
        return None


def run_argos_install_cli(package_dir: str, pairs: list[tuple[str, str]]) -> None:
    """Install Argos language packs and emit simple progress markers to stdout."""
    configure_argos_package_dir(package_dir)

    from argostranslate import package

    normalized_pairs = [(src.strip(), tgt.strip()) for src, tgt in pairs if src.strip() and tgt.strip()]
    if not normalized_pairs:
        print("STEP 1/1: No Argos language packs selected.", flush=True)
        return

    total = max(1, len(normalized_pairs) * 3)
    step = 0
    for src, tgt in normalized_pairs:
        step += 1
        print(f"STEP {step}/{total}: Updating Argos package index for {src} -> {tgt}", flush=True)
        package.update_package_index()
        available = package.get_available_packages()
        pkg = next(
            (
                item
                for item in available
                if str(getattr(item, "from_code", "")).strip() == src
                and str(getattr(item, "to_code", "")).strip() == tgt
            ),
            None,
        )
        if pkg is None:
            raise RuntimeError(f"No Argos pack found for {src!r} -> {tgt!r}")

        step += 1
        print(f"STEP {step}/{total}: Downloading Argos pack {src} -> {tgt}", flush=True)
        package_path = pkg.download()

        step += 1
        print(f"STEP {step}/{total}: Installing Argos pack {src} -> {tgt}", flush=True)
        package.install_from_path(package_path)


if __name__ == "__main__":
    import json

    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    package_dir = str(payload.get("package_dir", ""))
    pairs = [tuple(item) for item in payload.get("pairs", [])]
    run_argos_install_cli(package_dir, pairs)
