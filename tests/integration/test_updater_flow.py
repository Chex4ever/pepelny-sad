"""Integration: chained updates via mock provider."""
from __future__ import annotations

import io
import json
import zipfile

import pytest

from src.updater.manager import maybe_update, save_local_version
from src.updater.provider import UpdateProvider
from src.updater.update_package import UpdatePackageInfo


def _zip_update(to_version: str, applies_from: list[str], path: str, data: bytes) -> bytes:
    import hashlib

    digest = hashlib.sha256(data).hexdigest()
    meta = {
        "to_version": to_version,
        "platform": "win-x64",
        "applies_from": applies_from,
        "files": [{"path": path, "sha256": digest, "size": len(data)}],
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("update.json", json.dumps(meta))
        zf.writestr(path, data)
    return buf.getvalue()


class ChainProvider(UpdateProvider):
    def __init__(self):
        self.zips = {
            "0.2.9": _zip_update("0.2.9", ["0.2.8"], "a.bin", b"a9"),
            "0.2.10": _zip_update("0.2.10", ["0.2.9"], "b.bin", b"b10"),
        }

    def list_update_packages(self) -> list[UpdatePackageInfo]:
        return [
            UpdatePackageInfo("0.2.10", "win-x64", ("0.2.9",), "u10", "v0.2.10"),
            UpdatePackageInfo("0.2.9", "win-x64", ("0.2.8",), "u9", "v0.2.9"),
        ]

    def download_bytes(self, url: str) -> bytes:
        return self.zips["0.2.9" if url == "u9" else "0.2.10"]


@pytest.mark.integration
def test_updater_chain_applies_two_packages(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)
    monkeypatch.setattr("src.updater.manager.is_frozen", lambda: True)
    save_local_version("0.2.8", "win-x64")

    assert maybe_update(ChainProvider()) is False
    assert (install / "a.bin").read_bytes() == b"a9"
    assert (install / "b.bin").read_bytes() == b"b10"
