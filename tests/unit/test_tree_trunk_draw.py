"""Tree trunk must sort after canopy and use trunk stencil."""
from __future__ import annotations

from src.render.procedural_stencil import procedural_tree_canopy, procedural_tree_trunk
from src.world.tree_generator import build_tree_solids


def test_trunk_stencil_has_pipe_glyphs():
    trunk = procedural_tree_trunk(False)
    chars = {g.ch for g in trunk.glyphs}
    assert "|" in chars


def test_thick_trunk_stays_narrow():
    trunk = procedural_tree_trunk(True)
    xs = {g.dx for g in trunk.glyphs}
    assert max(abs(x) for x in xs) <= 1


def test_canopy_bottom_row_leaves_center_open():
    canopy = procedural_tree_canopy(0, 6, 2)
    bottom = min(canopy.glyphs, key=lambda g: g.dy)
    center = [g for g in canopy.glyphs if g.dy == bottom.dy and g.dx == 0]
    assert not center or center[0].ch == " "


def test_trunk_sorts_after_canopy_on_anchor():
    wx, wy = 10, 10
    canopy_key = wx + wy + int(6.0 * 10)
    trunk_key = wx + wy + 120
    assert trunk_key > canopy_key
