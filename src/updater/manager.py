"""Apply chained update packages silently at startup (frozen builds only)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

from src.updater.config import update_provider_name, update_repo
from src.updater.github_releases import GitHubReleasesProvider
from src.updater.provider import UpdateProvider
from src.updater.update_package import UpdatePackageInfo, plan_update_chain
from src.updater.util import detect_platform_id, sha256_file
from src.version import get_version


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


def local_version() -> str:
    path = local_manifest_path()
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version"):
            return str(data["version"])
    version_file = install_dir() / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return get_version()


def save_local_version(version: str, platform_id: str) -> None:
    path = local_manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"version": version, "platform": platform_id}, indent=2) + "\n",
        encoding="utf-8",
    )


def apply_update_package(package_bytes: bytes, expected: UpdatePackageInfo, current_version: str) -> bool:
    """Apply one update zip. Returns True if main executable changed."""
    with zipfile.ZipFile(BytesIO(package_bytes), "r") as zf:
        meta = json.loads(zf.read("update.json").decode("utf-8"))
        if meta.get("to_version") != expected.to_version:
            raise ValueError("Update package version mismatch")
        if current_version not in meta.get("applies_from", []):
            raise ValueError(f"Update {expected.to_version} does not apply from {current_version}")

        staging = install_dir() / ".pepelny" / "staging"
        if staging.exists():
            import shutil

            shutil.rmtree(staging)
        staging.mkdir(parents=True, exist_ok=True)

        main_exe = main_executable_name()
        main_changed = False
        for entry in meta.get("files", []):
            rel = entry["path"]
            data = zf.read(rel)
            if sha256_file_from_bytes(data) != entry.get("sha256"):
                raise ValueError(f"Checksum mismatch in package: {rel}")
            staged = staging / rel
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(data)
            target = install_dir() / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged, target)
            if rel.replace("\\", "/") == main_exe:
                main_changed = True

    save_local_version(expected.to_version, expected.platform_id)
    return main_changed


def sha256_file_from_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def maybe_update(provider: UpdateProvider | None = None) -> bool:
    """Download and apply chained update packages. Returns True if restart needed."""
    if not is_frozen():
        return False
    provider = provider or create_provider()
    try:
        current = local_version()
        packages = provider.list_update_packages()
        chain = plan_update_chain(current, packages)
        if not chain:
            return False

        restart = False
        version = current
        for step in chain:
            _log(f"Applying update {version} -> {step.to_version}")
            payload = provider.download_bytes(step.download_url)
            if apply_update_package(payload, step, version):
                restart = True
            version = step.to_version
        return restart
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        _log(f"Update failed: {exc}")
        return False


def restart_if_needed(restart: bool) -> None:
    if not restart:
        return
    os.execv(sys.executable, [sys.executable] + sys.argv)


# Backwards compat for tests importing old helpers
def load_local_manifest() -> dict[str, Any] | None:
    path = local_manifest_path()
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_local_manifest(manifest: dict[str, Any]) -> None:
    save_local_version(str(manifest.get("version", "0.0.0")), str(manifest.get("platform", detect_platform_id())))
