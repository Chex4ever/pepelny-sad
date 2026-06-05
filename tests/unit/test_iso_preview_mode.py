"""Preview tools default to game GPU path when GL is available."""
from __future__ import annotations

from src.tools.iso_preview import resolve_preview_mode


def test_resolve_preview_defaults_gpu_or_iso():
    mode = resolve_preview_mode("gpu")
    assert mode in ("gpu", "iso")


def test_resolve_preview_iso_explicit():
    assert resolve_preview_mode("iso") == "iso"
