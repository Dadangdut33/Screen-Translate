"""Helpers for managing an app-local LibreTranslate installation."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_dir


def default_local_libretranslate_dir() -> Path:
    """Return the default app-managed LibreTranslate directory."""
    return Path(user_config_dir("screen-translate", "Dadangdut33")) / "libretranslate"


def local_libretranslate_dir_from_setting(value: str) -> Path:
    """Return a normalized local LibreTranslate directory from settings."""
    raw = value.strip()
    return Path(raw).expanduser() if raw else default_local_libretranslate_dir()


def _venv_dir(install_dir: Path) -> Path:
    return install_dir / "venv"


def local_libretranslate_python(install_dir: Path) -> Path:
    """Return the managed venv Python executable path."""
    if os.name == "nt":
        return _venv_dir(install_dir) / "Scripts" / "python.exe"
    return _venv_dir(install_dir) / "bin" / "python"


def local_libretranslate_command(install_dir: Path) -> Path:
    """Return the managed LibreTranslate executable path."""
    if os.name == "nt":
        return _venv_dir(install_dir) / "Scripts" / "libretranslate.exe"
    return _venv_dir(install_dir) / "bin" / "libretranslate"


def local_libretranslate_server_command(install_dir: Path, port: str) -> list[str]:
    """Return the command used to run the managed local LibreTranslate server."""
    resolved_port = port.strip() or "5000"
    return [
        str(local_libretranslate_command(install_dir)),
        "--host",
        "127.0.0.1",
        "--port",
        resolved_port,
    ]


def local_libretranslate_setup_steps(install_dir: Path) -> list[list[str]]:
    """Return subprocess command steps needed to install LibreTranslate locally."""
    python_executable = local_libretranslate_python(install_dir)
    return [
        [sys.executable, "-m", "venv", str(_venv_dir(install_dir))],
        [str(python_executable), "-m", "pip", "install", "--upgrade", "pip"],
        [str(python_executable), "-m", "pip", "install", "--upgrade", "libretranslate"],
    ]


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                continue
    return total


def _query_package_version(python_executable: Path, package_name: str) -> str:
    if not python_executable.exists():
        return ""
    try:
        result = subprocess.run(
            [
                str(python_executable),
                "-c",
                (
                    "import importlib.metadata as m; "
                    f"print(m.version({package_name!r}))"
                ),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return ""
    return result.stdout.strip()


@dataclass(slots=True)
class LocalLibreTranslateInfo:
    """Summary of the managed LibreTranslate installation."""

    install_dir: Path
    venv_dir: Path
    python_executable: Path
    command_executable: Path
    installed: bool
    package_version: str
    size_bytes: int

    @property
    def installed_items(self) -> list[str]:
        """Return human-readable installed component lines."""
        items = []
        if self.python_executable.exists():
            items.append("Python virtual environment")
        if self.package_version:
            items.append(f"libretranslate=={self.package_version}")
        if self.command_executable.exists():
            items.append(f"Executable: {self.command_executable.name}")
        return items


def inspect_local_libretranslate(install_dir: Path) -> LocalLibreTranslateInfo:
    """Inspect the current local LibreTranslate installation state."""
    python_executable = local_libretranslate_python(install_dir)
    command_executable = local_libretranslate_command(install_dir)
    package_version = _query_package_version(python_executable, "libretranslate")

    return LocalLibreTranslateInfo(
        install_dir=install_dir,
        venv_dir=_venv_dir(install_dir),
        python_executable=python_executable,
        command_executable=command_executable,
        installed=bool(package_version or command_executable.exists()),
        package_version=package_version,
        size_bytes=_directory_size(install_dir),
    )
