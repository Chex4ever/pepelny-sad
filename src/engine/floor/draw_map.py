"""Packed layout draw map — per-tile diag 3×2 stamp on unified diamond canvas."""
from __future__ import annotations

from dataclasses import replace

from src.engine.config import FLOOR_LAYOUT_TILES
from src.engine.floor.patch import build_floor_patch
from src.engine.floor.types import FloorGlyphCell
from src.engine.layout.golden import STAMP_CELL_ORDER
from src.engine.projection.packed import layout_cell_to_screen
from src.prototype.dia_scale.tessellation import stamp_origin


def floor_packed_draw_map_from_cells(
    by_char: dict[tuple[int, int], FloorGlyphCell],
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = FLOOR_LAYOUT_TILES,
    get_column=None,
    wx0: int = 0,
    wy0: int = 0,
    cam_tx: int = 0,
    cam_ty: int = 0,
    glyph_for_tile=None,
    slot_view: dict[tuple[int, int, int], tuple[int, int]] | None = None,
) -> dict[tuple[int, int], FloorGlyphCell]:
    """Map packed layout (col, row) → floor cell — one glyph per solid stamp cell."""
    _ = get_column
    from src.engine.layout.golden import resolve_tile_slot_view

    center = n_tiles // 2
    ref_ox, ref_oy = stamp_origin(center, center)
    if slot_view is None:
        slot_view = resolve_tile_slot_view(
            n_tiles=n_tiles,
            feet_cx=feet_cx,
            feet_cy=feet_cy,
            cam_tx=cam_tx,
            cam_ty=cam_ty,
        )
    out: dict[tuple[int, int], FloorGlyphCell] = {}
    for (tx, ty, slot), (row, col) in slot_view.items():
        ox, oy = stamp_origin(tx, ty)
        dx, dy = STAMP_CELL_ORDER[slot]
        gx = feet_cx + ox - ref_ox + dx
        gy = feet_cy + oy - ref_oy + dy
        cell = by_char.get((gx, gy))
        if cell is None:
            continue
        ch = glyph_for_tile(tx, ty) if glyph_for_tile is not None else cell.ch
        out[(col, row)] = replace(cell, ch=ch, tile_tx=tx, tile_ty=ty)
    return out


def floor_packed_draw_map(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = FLOOR_LAYOUT_TILES,
    seed: int = 0,
) -> dict[tuple[int, int], FloorGlyphCell]:
    """Map packed layout (col, row) → floor cell — golden 5×5 or scaled patch diamond."""
    if n_tiles == FLOOR_LAYOUT_TILES:
        by_char: dict[tuple[int, int], FloorGlyphCell] = {
            (c.cx, c.cy): c
            for c in build_floor_patch(feet_cx, feet_cy, n_tiles=n_tiles, seed=seed)
        }
        return floor_packed_draw_map_from_cells(by_char, feet_cx, feet_cy, n_tiles=n_tiles)
    raise ValueError(
        f"packed draw map helper is only for {FLOOR_LAYOUT_TILES}×{FLOOR_LAYOUT_TILES}; "
        f"use floor_packed_draw_map_from_cells() for {n_tiles}×{n_tiles}"
    )


def floor_packed_layout_offsets(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = FLOOR_LAYOUT_TILES,
    seed: int = 0,
) -> frozenset[tuple[int, int]]:
    draw = floor_packed_draw_map(feet_cx, feet_cy, n_tiles=n_tiles, seed=seed)
    return frozenset(layout_cell_to_screen(col, row) for col, row in draw)
