"""Isometric projection and render mode."""
from __future__ import annotations

import pytest

from src.render import render_mode
from src.render.iso_projector import IsoProjector
from src.render.render_mode import is_classic, is_iso
from src.render.viewport import map_view_h, map_view_w


@pytest.fixture
def iso_mode(monkeypatch):
    monkeypatch.setenv("PEPELNY_RENDER", "iso")
    render_mode._MODE = None
    yield
    render_mode._MODE = None


@pytest.fixture
def classic_mode(monkeypatch):
    monkeypatch.setenv("PEPELNY_RENDER", "classic")
    render_mode._MODE = None
    yield
    render_mode._MODE = None


def test_iso_mode_flag(iso_mode):
    assert is_iso()
    assert not is_classic()
    assert map_view_w() == 22
    assert map_view_h() == 16


def test_classic_mode_flag(classic_mode):
    assert is_classic()
    assert map_view_w() == 100


def test_world_to_screen_increases_with_wx_plus_wy():
    p = IsoProjector(origin_x=50, origin_y=10, step_x=2, step_y=1)
    assert p.world_to_screen(0, 0) == (50, 10)
    assert p.world_to_screen(1, 0)[0] > p.world_to_screen(0, 0)[0]
    assert p.world_to_screen(0, 1)[0] < p.world_to_screen(0, 0)[0]


def test_screen_to_world_round_trip():
    p = IsoProjector(origin_x=40, origin_y=20)
    wx0, wy0, vw, vh = 10, 10, 8, 6
    for wx in range(wx0, wx0 + vw):
        for wy in range(wy0, wy0 + vh):
            sx, sy = p.world_to_screen(wx, wy)
            hit = p.screen_to_world(sx, sy, wx0, wy0, vw, vh)
            assert hit == (wx, wy)


def test_z_order_sort_key():
    tiles = [(3, 1, 2), (5, 2, 3), (4, 2, 2)]
    assert [t[1:] for t in sorted(tiles, key=lambda t: t[0])] == [(1, 2), (2, 2), (2, 3)]


def test_load_tile_stencil_grass():
    from src.render.tile_stencil import load_tile_stencil

    s = load_tile_stencil("grass")
    assert len(s.glyphs) > 4
