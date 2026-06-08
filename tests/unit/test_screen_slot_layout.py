"""ASCII screen-row floor layout (stamp slots 1..4)."""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_screen_rows_match_user_reference_lines():
    from src.engine.layout.screen_slots import _REFERENCE_ROWS, screen_row_tile_slot

    for sr, seq in enumerate(_REFERENCE_ROWS):
        for sc, (tx, ty, user_slot) in enumerate(seq):
            got = screen_row_tile_slot(sr, sc)
            want = (tx, ty, user_slot - 1)
            assert got == want, f"sr={sr} sc={sc}: got {got}, want {want}"


@pytest.mark.unit
def test_screen_layout_covers_stamp_slots_in_patch():
    from src.engine.layout.screen_slots import build_tile_slot_screen_map

    for n in (5, 15, 25):
        view = build_tile_slot_screen_map(n)
        assert len(view) >= n * n * 4 - 40
        assert view[(0, 0, 0)] == (0, 0)


@pytest.mark.unit
def test_neighbor_tiles_keep_stamp_shape_at_8_14():
    from src.engine.layout.screen_slots import build_tile_slot_screen_map

    view = build_tile_slot_screen_map(25)
    for tx, ty in ((8, 14), (9, 14)):
        cells = [view[(tx, ty, s)] for s in range(4)]
        assert cells[0][0] + 1 == cells[2][0]
        assert cells[1] == (cells[0][0], cells[0][1] + 1)
        assert cells[2] == (cells[0][0] + 1, cells[0][1] + 1)
        assert cells[3] == (cells[0][0] + 1, cells[0][1] + 2)
    assert view[(9, 14, 0)][1] > view[(8, 14, 1)][1]


@pytest.mark.unit
def test_tile_stamp_is_diamond_not_horizontal_line():
    from src.engine.layout.screen_slots import build_tile_slot_screen_map

    view = build_tile_slot_screen_map(5)
    cells = [view[(0, 0, s)] for s in range(4)]
    cols = {c for _r, c in cells}
    rows = {r for r, _c in cells}
    assert len(cols) > 1
    assert len(rows) > 1
    assert cells[0] == (0, 0)


@pytest.mark.unit
def test_camera_anchor_moves_tile_origin():
    """Camera anchor applies to screen-row layout (n>5); 5×5 uses fixed golden canvas."""
    from src.engine.layout.screen_slots import tile_slot_packed_pos

    assert tile_slot_packed_pos(1, 1, 0, cam_tx=1, cam_ty=1, n_tiles=25) == (0, 0)
    assert tile_slot_packed_pos(0, 0, 0, cam_tx=1, cam_ty=1, n_tiles=25) != (0, 0)


@pytest.mark.unit
def test_draw_map_one_glyph_per_solid_char_cell():
    from src.characters.editor_floor import floor_solid_char_cells
    from src.world.editor.editable_world import EditableWorld
    from src.world.editor.ui.viewport import build_world_packed_draw_map

    for n in (5, 25):
        world = EditableWorld(seed=3, width=n, height=n)
        world.fill_blank_grass()
        draw_map, _wx0, _wy0, side = build_world_packed_draw_map(world)
        assert side == n
        from src.engine.layout.golden import resolve_tile_slot_view

        expected = len(resolve_tile_slot_view(n_tiles=n))
        assert len(draw_map) == expected
