#!/usr/bin/env python3
"""Bump VERSION file (patch/minor/major)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.version import format_version, parse_version, read_version_file


def bump(part: str) -> str:
    major, minor, patch = parse_version(read_version_file())
    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Unknown part: {part}")
    new_version = format_version(major, minor, patch)
    VERSION_FILE.write_text(new_version + "\n", encoding="utf-8")
    return new_version


def main() -> int:
    parser = argparse.ArgumentParser(description="Bump VERSION file")
    parser.add_argument(
        "part",
        nargs="?",
        default="patch",
        choices=("patch", "minor", "major"),
        help="Semver segment to increment (default: patch)",
    )
    args = parser.parse_args()
    new_version = bump(args.part)
    print(new_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
