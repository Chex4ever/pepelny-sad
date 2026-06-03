"""Unit tests for incremental updater logic."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.updater.manager import (
    apply_updates,
    files_needing_update,
    load_local_manifest,
    maybe_update,
    save_local_manifest,
)
from src.updater.provider import UpdateProvider
from src.updater.util import sha256_file


class MockProvider(UpdateProvider):
    def __init__(self, manifest: dict, files: dict[str, bytes]):
        self.manifest = manifest
        self.files = files
        self.downloads: list[tuple[str, Path]] = []

    def fetch_manifest(self) -> dict:
        return self.manifest

    def download_file(self, url: str, destination: Path) -> None:
        self.downloads.append((url, destination))
        name = url.rsplit("/", 1)[-1]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.files[name])


def _manifest(version: str, entries: list[tuple[str, bytes]]) -> dict:
    files = []
    for path, data in entries:
        files.append(
            {
                "path": path,
                "sha256": sha256_file_from_bytes(data),
                "size": len(data),
                "url": f"https://example.test/{path.replace('/', '--')}",
            }
        )
    return {"version": version, "platform": "win-x64", "release_tag": f"v{version}", "files": files}


def sha256_file_from_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def test_files_needing_update_detects_missing_and_changed(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    old = install / "game.dat"
    old.write_bytes(b"old")
    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)

    local = {"version": "0.2.8", "files": [{"path": "game.dat", "sha256": sha256_file(old)}]}
    remote = _manifest("0.2.9", [("game.dat", b"new"), ("extra.dll", b"x")])

    pending = files_needing_update(local, remote)
    paths = {e["path"] for e in pending}
    assert paths == {"game.dat", "extra.dll"}


def test_apply_updates_replaces_files(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    target = install / "game.dat"
    target.write_bytes(b"old")
    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)

    remote = _manifest("0.2.9", [("game.dat", b"new")])
    provider = MockProvider(remote, {"game.dat": b"new"})

    changed = apply_updates(remote["files"], remote, provider)
    assert changed is False
    assert target.read_bytes() == b"new"
    assert load_local_manifest()["version"] == "0.2.9"


def test_apply_updates_marks_main_exe_changed(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    exe = install / "pepelny-sad.exe"
    exe.write_bytes(b"v1")
    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)
    monkeypatch.setattr("src.updater.manager.main_executable_name", lambda: "pepelny-sad.exe")

    remote = _manifest("0.2.9", [("pepelny-sad.exe", b"v2")])
    provider = MockProvider(remote, {"pepelny-sad.exe": b"v2"})
    assert apply_updates(remote["files"], remote, provider) is True


def test_maybe_update_skips_when_versions_equal(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    data = b"same"
    f = install / "game.dat"
    f.write_bytes(data)
    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)
    monkeypatch.setattr("src.updater.manager.is_frozen", lambda: True)

    manifest = _manifest("0.2.8", [("game.dat", data)])
    save_local_manifest(manifest)
    provider = MockProvider(manifest, {})
    assert maybe_update(provider) is False
    assert provider.downloads == []


def test_maybe_update_applies_when_remote_newer(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    f = install / "game.dat"
    f.write_bytes(b"old")
    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)
    monkeypatch.setattr("src.updater.manager.is_frozen", lambda: True)

    local = _manifest("0.2.8", [("game.dat", b"old")])
    save_local_manifest(local)
    remote = _manifest("0.2.9", [("game.dat", b"new")])
    provider = MockProvider(remote, {"game.dat": b"new"})
    assert maybe_update(provider) is False
    assert f.read_bytes() == b"new"


def test_save_and_load_local_manifest(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)
    data = {"version": "0.2.8", "files": []}
    save_local_manifest(data)
    loaded = load_local_manifest()
    assert loaded == data
