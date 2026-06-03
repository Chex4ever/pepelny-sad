"""Update package format and naming."""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.version import compare_versions, format_version, parse_version


def version_dashed(version: str) -> str:
    return version.replace(".", "-")


def version_from_dashed(dashed: str) -> str:
    parts = dashed.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid dashed version: {dashed!r}")
    return format_version(int(parts[0]), int(parts[1]), int(parts[2]))


def update_package_filename(to_version: str, platform_id: str) -> str:
    return f"pepelny-sad-update-{version_dashed(to_version)}-{platform_id}.zip"


def parse_update_package_filename(name: str, platform_id: str) -> str | None:
    """Return to_version if name matches this platform's update package."""
    suffix = f"-{platform_id}.zip"
    prefix = "pepelny-sad-update-"
    if not name.startswith(prefix) or not name.endswith(suffix):
        return None
    dashed = name[len(prefix) : -len(suffix)]
    try:
        return version_from_dashed(dashed)
    except ValueError:
        return None


def previous_patch_version(version: str) -> str:
    major, minor, patch = parse_version(version)
    if patch <= 0:
        raise ValueError(f"No previous patch for {version}")
    return format_version(major, minor, patch - 1)


@dataclass(frozen=True)
class UpdatePackageInfo:
    to_version: str
    platform_id: str
    applies_from: tuple[str, ...]
    download_url: str
    release_tag: str


def read_update_json_from_zip(zip_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open("update.json") as fp:
            return json.loads(fp.read().decode("utf-8"))


def plan_update_chain(current_version: str, packages: list[UpdatePackageInfo]) -> list[UpdatePackageInfo]:
    """Pick nearest applicable update packages until no step remains."""
    chain: list[UpdatePackageInfo] = []
    version = current_version
    applicable = list(packages)

    while True:
        candidates = [
            pkg
            for pkg in applicable
            if version in pkg.applies_from and compare_versions(pkg.to_version, version) > 0
        ]
        if not candidates:
            break
        step = min(candidates, key=lambda p: parse_version(p.to_version))
        chain.append(step)
        version = step.to_version
        applicable = [p for p in applicable if compare_versions(p.to_version, version) > 0]
    return chain
