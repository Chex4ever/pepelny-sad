"""Application version (single source: VERSION file at repo root)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def read_version_file() -> str:
    text = (repo_root() / "VERSION").read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("VERSION file is empty")
    return text


def parse_version(version: str) -> tuple[int, int, int]:
    parts = version.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid semver (expected MAJOR.MINOR.PATCH): {version!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def format_version(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def get_version() -> str:
    return read_version_file()


def compare_versions(a: str, b: str) -> int:
    """Return -1 if a < b, 0 if equal, 1 if a > b."""
    ta, tb = parse_version(a), parse_version(b)
    if ta < tb:
        return -1
    if ta > tb:
        return 1
    return 0


__version__ = get_version()
