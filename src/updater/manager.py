"""Apply incremental updates silently at startup (frozen builds only)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
from pathlib import Path
from typing import Any

from src.updater.config import update_provider_name, update_repo
from src.updater.github_releases import GitHubReleasesProvider
from src.updater.provider import UpdateProvider
from src.updater.util import detect_platform_id, sha256_file
from src.version import compare_versions


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def install_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def main_executable_name() -> str:
    return "pepelny-sad.exe" if sys.platform == "win32" else "pepelny-sad"


def local_manifest_path() -> Path:
    return install_dir() / ".pepelny" / "manifest.json"


def log_path() -> Path:
    path = Path.home() / ".pepelny" / "update.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _log(msg: str) -> None:
    try:
        with log_path().open("a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except OSError:
        pass


def create_provider() -> UpdateProvider:
    name = update_provider_name()
    platform_id = detect_platform_id()
    if name == "github":
        return GitHubReleasesProvider(update_repo(), platform_id)
    raise ValueError(f"Unsupported update provider: {name}")


def load_local_manifest() -> dict[str, Any] | None:
    path = local_manifest_path()
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_local_manifest(manifest: dict[str, Any]) -> None:
    path = local_manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def files_needing_update(local: dict[str, Any] | None, remote: dict[str, Any]) -> list[dict[str, Any]]:
    local_map = {entry["path"]: entry for entry in (local or {}).get("files", [])}
    pending: list[dict[str, Any]] = []
    for entry in remote.get("files", []):
        rel = entry["path"]
        target = install_dir() / rel
        local_entry = local_map.get(rel)
        if not target.is_file():
            pending.append(entry)
            continue
        if local_entry and local_entry.get("sha256") == entry.get("sha256"):
            continue
        if sha256_file(target) == entry.get("sha256"):
            continue
        pending.append(entry)
    return pending


def apply_updates(pending: list[dict[str, Any]], remote: dict[str, Any], provider: UpdateProvider) -> bool:
    staging = install_dir() / ".pepelny" / "staging"
    if staging.exists():
        import shutil

        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    main_exe = main_executable_name()
    main_changed = False

    for entry in pending:
        url = entry.get("url")
        if not url:
            raise ValueError(f"Missing download url for {entry.get('path')}")
        rel = entry["path"]
        staged = staging / rel
        provider.download_file(url, staged)
        if sha256_file(staged) != entry.get("sha256"):
            raise ValueError(f"Checksum mismatch after download: {rel}")
        target = install_dir() / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged, target)
        if rel.replace("\\", "/") == main_exe:
            main_changed = True

    save_local_manifest(remote)
    return main_changed


def maybe_update(provider: UpdateProvider | None = None) -> bool:
    """Check for updates and apply silently. Returns True if executable restart is needed."""
    if not is_frozen():
        return False
    provider = provider or create_provider()
    try:
        local = load_local_manifest()
        remote = provider.fetch_manifest()
        local_version = (local or {}).get("version", "0.0.0")
        remote_version = remote.get("version", "0.0.0")
        if compare_versions(remote_version, local_version) <= 0:
            pending = files_needing_update(local, remote)
            if not pending:
                return False
        else:
            pending = files_needing_update(local, remote)
        if not pending:
            save_local_manifest(remote)
            return False
        _log(f"Updating {len(pending)} file(s) to {remote_version}")
        return apply_updates(pending, remote, provider)
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
        _log(f"Update failed: {exc}")
        return False


def restart_if_needed(restart: bool) -> None:
    if not restart:
        return
    os.execv(sys.executable, [sys.executable] + sys.argv)
