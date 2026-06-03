"""Integration: updater with mock provider simulates two changed files."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.updater.manager import maybe_update
from src.updater.provider import UpdateProvider
from tests.unit.test_updater import MockProvider, _manifest


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.integration
def test_updater_downloads_two_changed_files(tmp_path, monkeypatch):
    install = tmp_path / "app"
    install.mkdir()
    a = install / "a.bin"
    b = install / "b.bin"
    a.write_bytes(b"a-old")
    b.write_bytes(b"b-same")

    monkeypatch.setattr("src.updater.manager.install_dir", lambda: install)
    monkeypatch.setattr("src.updater.manager.is_frozen", lambda: True)

    local = {
        "version": "0.2.8",
        "files": [
            {"path": "a.bin", "sha256": _sha(b"a-old")},
            {"path": "b.bin", "sha256": _sha(b"b-same")},
        ],
    }
    from src.updater.manager import save_local_manifest

    save_local_manifest(local)

    remote = _manifest(
        "0.2.9",
        [
            ("a.bin", b"a-new"),
            ("b.bin", b"b-same"),
            ("c.bin", b"c-new"),
        ],
    )
    provider = MockProvider(
        remote,
        {
            "a.bin": b"a-new",
            "c.bin": b"c-new",
        },
    )
    assert maybe_update(provider) is False
    assert a.read_bytes() == b"a-new"
    assert b.read_bytes() == b"b-same"
    assert (install / "c.bin").read_bytes() == b"c-new"
    assert len(provider.downloads) == 2
