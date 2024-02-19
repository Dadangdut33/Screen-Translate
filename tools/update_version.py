#!/usr/bin/env python
"""Update versions in pyproject.toml."""

import os
import re


def get_version() -> str:
    """Get version from project"""
    with open(os.path.join(os.path.dirname(__file__), "../screen_translate/_version.py"), encoding="utf-8") as f:
        return f.readline().split("=")[1].strip().strip('"').strip("'")


def replace_version(version: str) -> None:
    """Replace version in pyproject.toml"""
    with open(os.path.join(os.path.dirname(__file__), "../pyproject.toml"), encoding="utf-8") as f:
        data = f.read()
    data = re.sub(r'version = ".*"', f'version = "{version}"', data)
    with open(os.path.join(os.path.dirname(__file__), "../pyproject.toml"), "w", encoding="utf-8") as f:
        f.write(data)


def main() -> None:
    version = get_version()
    replace_version(version)


if __name__ == "__main__":
    main()
