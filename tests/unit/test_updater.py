"""Unit tests for chained update application."""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from src.updater.manager import apply_update_package, maybe_update, save_local_version
from src.updater.provider import UpdateProvider
from src.updater.update_package import UpdatePackageInfo
from src.updater.util import sha256_file


class MockProvider(UpdateProvider):
    def __init__(self, packages: list[UpdatePackageInfo], zips: dict[str, bytes]):
        self.packages = packages
        self.zips = zips
        self.downloads: list[str] = []

    def list_update_packages(self) -> list[UpdatePackageInfo]:
        return self.packages

    def download_bytes(self, url: str) -> bytes:
        self.downloads.append(url)
        for pkg in self.packages:
            if pkg.download_url == url:
                return self.zips[pkg.to_version]
        raise KeyError(url)


def _make_zip(to_version: str, applies_from: list[str], files: dict[str, bytes]) -> bytes:
    meta = {
        "to_version": to_version,
        "platform": "win-x64",
        "applies_from": applies_from,
        "files": [
            {"path": path, "sha256": sha256_file_from_bytes(data), "size": len(data)}
            for path, data in files.items()
        ],
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("update.json", json.dumps(meta))
        for path, data in files.items():
            zf.writestr(path, data)
    return buf.getvalue()


def sha256_file_from_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def test_apply_update_package(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    target = install / "game.dat"
    target.write_bytes(b"old")
    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)

    pkg = UpdatePackageInfo("0.2.9", "win-x64", ("0.2.8",), "https://x/0.2.9.zip", "v0.2.9")
    payload = _make_zip("0.2.9", ["0.2.8"], {"game.dat": b"new"})
    apply_update_package(payload, pkg, "0.2.8")
    assert target.read_bytes() == b"new"


def test_maybe_update_chains_packages(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    f = install / "game.dat"
    f.write_bytes(b"v8")
    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)
    monkeypatch.setattr("src.updater.manager.is_frozen", lambda: True)
    save_local_version("0.2.8", "win-x64")

    packages = [
        UpdatePackageInfo("0.2.9", "win-x64", ("0.2.8",), "https://x/9", "v0.2.9"),
        UpdatePackageInfo("0.2.10", "win-x64", ("0.2.9",), "https://x/10", "v0.2.10"),
    ]
    zips = {
        "0.2.9": _make_zip("0.2.9", ["0.2.8"], {"game.dat": b"v9"}),
        "0.2.10": _make_zip("0.2.10", ["0.2.9"], {"game.dat": b"v10"}),
    }
    provider = MockProvider(packages, zips)
    assert maybe_update(provider) is False
    assert f.read_bytes() == b"v10"
    assert len(provider.downloads) == 2
