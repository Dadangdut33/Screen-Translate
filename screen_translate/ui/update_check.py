"""Shared update-check helpers for About page and startup checks."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import semver

_RELEASES_URL = "https://github.com/Dadangdut33/Screen-Translate/releases"
_LATEST_RELEASE_API = (
    "https://api.github.com/repos/Dadangdut33/Screen-Translate/releases/latest"
)


class UpdateCheckSignals(QObject):
    """Signals emitted by the update-check worker."""

    finished = pyqtSignal(str, str, str)  # version, url, release title
    error = pyqtSignal(str)


class UpdateCheckWorker(QRunnable):
    """Fetch the latest GitHub release metadata in a background thread."""

    def __init__(self) -> None:
        super().__init__()
        self.signals = UpdateCheckSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self) -> None:
        try:
            request = urllib.request.Request(
                _LATEST_RELEASE_API,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "screen-translate",
                },
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))

            version = str(payload.get("tag_name", "")).strip()
            url = str(payload.get("html_url", "")).strip()
            title = str(payload.get("name", "") or version).strip()
            if not version or not url:
                raise RuntimeError("Latest release metadata was incomplete.")
            self.signals.finished.emit(version, url, title)
        except urllib.error.URLError as exc:
            self.signals.error.emit(f"Could not reach GitHub: {exc.reason}")
        except Exception as exc:
            self.signals.error.emit(str(exc))


def releases_url() -> str:
    """Return the GitHub releases page URL."""
    return _RELEASES_URL


def parse_semver(value: str) -> semver.Version:
    """Parse a version string into a semver.Version object.

    A leading ``v`` is tolerated because GitHub tags often include it.
    """
    normalized = value.strip().lstrip("vV")
    return semver.Version.parse(normalized)


def is_newer_version(candidate: str, current: str) -> bool:
    """Return True when *candidate* is newer than *current*."""
    try:
        return parse_semver(candidate) > parse_semver(current)
    except ValueError:
        return False


def detect_install_method() -> str:
    """Infer how the app was installed."""
    if getattr(sys, "frozen", False):
        return "Frozen executable"

    executable = Path(sys.executable)
    executable_text = str(executable).lower()
    if "pipx" in executable_text:
        return "pipx-managed package"

    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / ".git").exists() and (repo_root / "pyproject.toml").exists():
        return "Source checkout / editable install"

    return "Installed Python package"


def detect_run_method() -> str:
    """Infer how the current process was launched."""
    if getattr(sys, "frozen", False):
        return f"Executable: {Path(sys.executable).name}"

    argv0 = Path(sys.argv[0]).name if sys.argv else ""
    if argv0 == "screen-translate":
        return "Console script: screen-translate"
    if sys.argv and sys.argv[0].endswith("__main__.py"):
        return "Module: python -m screen_translate"
    return f"Python entrypoint: {argv0 or Path(sys.executable).name}"


def update_instructions() -> str:
    """Return a short update guide based on the current install method."""
    method = detect_install_method()
    if method == "Frozen executable":
        return (
            "Download the latest release from GitHub and replace your current app "
            "build with the new package."
        )
    if method == "pipx-managed package":
        return "Run `pipx upgrade screen-translate`."
    if method == "Source checkout / editable install":
        return "Pull the latest changes, then reinstall if needed with `pip install -e .`."
    return "Run `pip install -U screen-translate` in the same Python environment."
