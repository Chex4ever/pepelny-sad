"""Tests for VERSION file and bump script."""
from pathlib import Path

import pytest

from src.version import compare_versions, format_version, parse_version, read_version_file


def test_read_version_matches_file():
    root = Path(__file__).resolve().parents[2]
    expected = (root / "VERSION").read_text(encoding="utf-8").strip()
    assert read_version_file() == expected


def test_parse_version():
    assert parse_version("0.2.8") == (0, 2, 8)


def test_compare_versions():
    assert compare_versions("0.2.8", "0.2.9") == -1
    assert compare_versions("0.3.0", "0.2.9") == 1
    assert compare_versions("1.0.0", "1.0.0") == 0


def test_bump_version_patch(tmp_path, monkeypatch):
    version_file = tmp_path / "VERSION"
    version_file.write_text("0.2.8\n", encoding="utf-8")
    monkeypatch.setattr("tools.bump_version.VERSION_FILE", version_file)
    monkeypatch.setattr("src.version.repo_root", lambda: tmp_path)

    from tools import bump_version

    read_version_file.cache_clear()
    assert bump_version.bump("patch") == "0.2.9"
    assert version_file.read_text(encoding="utf-8").strip() == "0.2.9"


def test_bump_version_minor(tmp_path, monkeypatch):
    version_file = tmp_path / "VERSION"
    version_file.write_text("0.2.8\n", encoding="utf-8")
    monkeypatch.setattr("tools.bump_version.VERSION_FILE", version_file)
    monkeypatch.setattr("src.version.repo_root", lambda: tmp_path)

    from tools import bump_version

    read_version_file.cache_clear()
    assert bump_version.bump("minor") == "0.3.0"


def test_bump_version_major(tmp_path, monkeypatch):
    version_file = tmp_path / "VERSION"
    version_file.write_text("0.2.8\n", encoding="utf-8")
    monkeypatch.setattr("tools.bump_version.VERSION_FILE", version_file)
    monkeypatch.setattr("src.version.repo_root", lambda: tmp_path)

    from tools import bump_version

    read_version_file.cache_clear()
    assert bump_version.bump("major") == "1.0.0"


def test_format_version():
    assert format_version(1, 2, 3) == "1.2.3"
