"""Biome patch renderer must not leave iso footprint holes (same path as biome_viewer)."""
from __future__ import annotations

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SCRIPT = os.path.join(ROOT, "scripts", "biome_viewer.py")


def _load_viewer():
    spec = importlib.util.spec_from_file_location("biome_viewer", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["biome_viewer"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_meadow_forced_patch_no_footprint_holes():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    from src.constants import init_paths

    init_paths(ROOT)
    import pygame

    pygame.init()
    bv = _load_viewer()
    _c, _q, stats, _holes = bv.prepare_patch(
        0, 0, 12, 12, 4242, "meadow", forced=True, trees=False, render_mode="iso"
    )
    pygame.quit()
    assert stats.internal_holes == 0
    assert stats.unstamped_holes == 0
    assert stats.floor_variants.get("grass_sparse", 0) == 0
