"""World columns → diag stamp floor patch."""
from __future__ import annotations

import pytest

from src.engine.config import FLOOR_LAYOUT_TILES
from src.engine.floor.draw_map import floor_packed_draw_map_from_cells
from src.engine.floor.world_patch import build_floor_patch_from_world
from src.world.chunk import Chunk


@pytest.mark.unit
def test_world_patch_maps_to_screen_row_layout():
    chunk = Chunk(0, 0)
    chunk.set(2, 2, ".", stencil_id="meadow")

    def get_column(wx, wy):
        if wx == 2 and wy == 2:
            return chunk.to_column(2, 2)
        return None

    n = FLOOR_LAYOUT_TILES
    by_char = build_floor_patch_from_world(
        get_column, wx0=0, wy0=0, n_tiles=n,
    )
    draw = floor_packed_draw_map_from_cells(by_char, 0, 0, n_tiles=n)
    from src.engine.layout.golden import resolve_tile_slot_view

    assert len(draw) == len(resolve_tile_slot_view(n_tiles=n))
    assert len(by_char) == 60
