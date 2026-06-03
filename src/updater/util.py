"""Shared release/update helpers (runtime-safe, no tools/ imports)."""
from __future__ import annotations

import hashlib
import platform
import sys
from pathlib import Path


def detect_platform_id() -> str:
    machine = platform.machine().lower()
    if sys.platform == "win32":
        if machine not in ("amd64", "x86_64"):
            raise RuntimeError(f"Unsupported Windows architecture: {machine}")
        return "win-x64"
    if sys.platform.startswith("linux"):
        if machine not in ("amd64", "x86_64"):
            raise RuntimeError(f"Unsupported Linux architecture: {machine}")
        return "linux-x64"
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
