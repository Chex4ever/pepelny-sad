"""Engine projection and floor unit tests."""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_char_cell_to_iso_focus_is_origin():
    from src.engine.projection.iso import char_cell_to_iso

    assert char_cell_to_iso(10, 10, ref_cx=10, ref_cy=10) == (0, 0)
    assert char_cell_to_iso(12, 10, ref_cx=10, ref_cy=10) == (4, 2)


@pytest.mark.unit
def test_layout_cell_to_screen_feet_anchor():
    from src.engine.layout.golden import PACKED_LAYOUT_FEET_COL, PACKED_LAYOUT_FEET_ROW
    from src.engine.projection.packed import LayoutFeet, layout_cell_to_screen

    feet = LayoutFeet(col=PACKED_LAYOUT_FEET_COL, row=PACKED_LAYOUT_FEET_ROW)
    assert layout_cell_to_screen(PACKED_LAYOUT_FEET_COL, PACKED_LAYOUT_FEET_ROW, feet=feet) == (0, 0)


@pytest.mark.unit
def test_world_to_screen_round_trip():
    from src.engine.projection.world import screen_to_world, world_to_screen

    focus = (20, 30)
    wx, wy = 22, 31
    sx, sy = world_to_screen(wx, wy, focus_wx=focus[0], focus_wy=focus[1], origin_x=60, origin_y=40)
    back = screen_to_world(sx, sy, focus_wx=focus[0], focus_wy=focus[1], origin_x=60, origin_y=40)
    assert back == (wx, wy)


@pytest.mark.unit
def test_floor_packed_draw_map_uses_screen_row_layout():
    from src.engine.config import EDITOR_FLOOR_TILES
    from src.engine.floor.draw_map import floor_packed_draw_map
    from src.engine.layout.screen_slots import tile_slot_packed_pos

    n = EDITOR_FLOOR_TILES
    draw = floor_packed_draw_map(0, 0, n_tiles=n, seed=0)
    from src.engine.layout.golden import resolve_tile_slot_view

    assert len(draw) == len(resolve_tile_slot_view(n_tiles=n))
    stamp = [tile_slot_packed_pos(0, 0, s, n_tiles=n) for s in range(4)]
    assert len({r for r, _c in stamp}) > 1
    assert all((col, row) in draw for row, col in stamp)


@pytest.mark.unit
def test_editor_floor_patch_tiles_is_5m():
    from src.constants import TILES_PER_M_XY
    from src.engine.config import DEFAULT_EDITOR_FLOOR_METERS, EDITOR_FLOOR_TILES, editor_floor_patch_tiles

    assert EDITOR_FLOOR_TILES == TILES_PER_M_XY == 5
    assert editor_floor_patch_tiles() == int(DEFAULT_EDITOR_FLOOR_METERS * TILES_PER_M_XY)
