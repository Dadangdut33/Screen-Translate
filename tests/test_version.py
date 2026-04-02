"""Tests for semantic versioning of the package."""

from __future__ import annotations

import re


def test_version_is_string() -> None:
    """__version__ must be a non-empty string."""
    from screen_translate import __version__

    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_version_semver() -> None:
    """__version__ must match a MAJOR.MINOR.PATCH semver pattern."""
    from screen_translate import __version__

    pattern = re.compile(r"^\d+\.\d+\.\d+")
    assert pattern.match(__version__), f"Non-semver version: {__version__!r}"
