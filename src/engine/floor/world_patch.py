"""Build diag stamp floor from world chunk columns."""
from __future__ import annotations

from src.engine.config import FLOOR_LAYOUT_TILES
from src.engine.floor.patch import floor_stamp_tile_owners
from src.engine.floor.types import (
    FLOOR_TILE_A_BG,
    FLOOR_TILE_A_FG,
    FLOOR_TILE_B_BG,
    FLOOR_TILE_B_FG,
    FloorGlyphCell,
)


def build_floor_patch_from_world(
    get_column,
    *,
    wx0: int,
    wy0: int,
    n_tiles: int = FLOOR_LAYOUT_TILES,
    feet_cx: int = 0,
    feet_cy: int = 0,
) -> dict[tuple[int, int], FloorGlyphCell]:
    """Map world tiles onto diag stamp char cells (3×2 stamp lattice).

    ``get_column(wx, wy)`` returns a Column-like object with floor_ch, fg, bg
    or None if missing.
    """
    owners = floor_stamp_tile_owners(feet_cx, feet_cy, n_tiles=n_tiles)
    cells: dict[tuple[int, int], FloorGlyphCell] = {}
    for (cx, cy), (tx, ty) in owners.items():
        wx, wy = wx0 + tx, wy0 + ty
        col = get_column(wx, wy)
        even = (tx + ty) % 2 == 0
        if col is not None:
            ch = col.floor_ch
            fg = col.fg
            bg = col.bg
        else:
            ch = "."
            fg = FLOOR_TILE_A_FG if even else FLOOR_TILE_B_FG
            bg = FLOOR_TILE_A_BG if even else FLOOR_TILE_B_BG
        cells[(cx, cy)] = FloorGlyphCell(
            cx, cy, ch, fg, bg, solid=True, tile_tx=tx, tile_ty=ty,
        )
    return cells


def world_column_getter(world):
    """Adapter for EditableWorld."""

    def get_column(wx: int, wy: int):
        b = world.bounds
        if not (b.wx0 <= wx < b.wx0 + b.width and b.wy0 <= wy < b.wy0 + b.height):
            return None
        chunk, lx, ly = world.chunk_for_world(wx, wy)
        return chunk.to_column(lx, ly)

    return get_column
