"""Tests for release asset naming and hashing."""
from pathlib import Path

from src.updater.util import sha256_file
from tools.release_utils import asset_name_to_path, path_to_asset_name


def test_path_to_asset_name():
    assert path_to_asset_name("win-x64", "pepelny-sad.exe") == "win-x64--pepelny-sad.exe"
    assert path_to_asset_name("linux-x64", "_internal/foo.so") == "linux-x64--_internal--foo.so"


def test_asset_name_to_path_roundtrip():
    platform_id = "win-x64"
    rel = "_internal/lib/foo.dll"
    asset = path_to_asset_name(platform_id, rel)
    assert asset_name_to_path(platform_id, asset) == rel


def test_sha256_file(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"hello")
    assert sha256_file(f) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_pepelny_sad_spec_paths_point_at_repo_root():
    repo = Path(__file__).resolve().parents[2]
    spec_dir = repo / "tools"
    root = spec_dir.parent
    assert root == repo
    assert (root / "main.py").is_file()
    assert (root / "assets").is_dir()
    assert (root / "src" / "data").is_dir()
