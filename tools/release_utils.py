"""Release build helpers: asset naming and platform detection."""
from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def detect_platform_id() -> str:
    from src.updater.util import detect_platform_id as _detect

    return _detect()


def sha256_file(path: Path) -> str:
    from src.updater.util import sha256_file as _sha

    return _sha(path)


def path_to_asset_name(platform_id: str, relpath: str) -> str:
    normalized = relpath.replace("\\", "/")
    return f"{platform_id}--{normalized.replace('/', '--')}"


def asset_name_to_path(platform_id: str, asset_name: str) -> str:
    prefix = f"{platform_id}--"
    if not asset_name.startswith(prefix):
        raise ValueError(f"Unexpected asset name: {asset_name}")
    tail = asset_name[len(prefix) :]
    return tail.replace("--", "/")


def github_download_url(repo: str, tag: str, asset_name: str) -> str:
    return f"https://github.com/{repo}/releases/download/{tag}/{asset_name}"
