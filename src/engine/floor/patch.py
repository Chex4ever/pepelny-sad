"""Build diag stamp floor patches (tessellation layer)."""
from __future__ import annotations

import random

from src.engine.config import FLOOR_LAYOUT_TILES
from src.engine.floor.types import (
    FLOOR_TILE_A_BG,
    FLOOR_TILE_A_FG,
    FLOOR_TILE_B_BG,
    FLOOR_TILE_B_FG,
    FloorGlyphCell,
)
from src.engine.projection.iso import char_cell_to_iso
from src.prototype.dia_scale.constants import COLOR_FLOOR_ALT_FG, COLOR_FLOOR_FG
from src.prototype.dia_scale.tessellation import stamp_cells_at, stamp_origin, stamp_tip


def _grass_glyph(rng: random.Random) -> tuple[str, tuple[int, int, int]]:
    roll = rng.random()
    if roll < 0.08:
        return ",", COLOR_FLOOR_ALT_FG
    if roll < 0.12:
        return "'", COLOR_FLOOR_ALT_FG
    return ".", COLOR_FLOOR_FG


def floor_tile_anchors(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = FLOOR_LAYOUT_TILES,
) -> list[tuple[int, int, int, int]]:
    center = n_tiles // 2
    ref_tip = stamp_tip(center, center)
    out: list[tuple[int, int, int, int]] = []
    for ty in range(n_tiles):
        for tx in range(n_tiles):
            tip_x, tip_y = stamp_tip(tx, ty)
            ax = feet_cx + tip_x - ref_tip[0]
            ay = feet_cy + tip_y - ref_tip[1]
            out.append((tx, ty, ax, ay))
    return out


def floor_stamp_tile_owners(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = FLOOR_LAYOUT_TILES,
) -> dict[tuple[int, int], tuple[int, int]]:
    center = n_tiles // 2
    ref_ox, ref_oy = stamp_origin(center, center)
    owners: dict[tuple[int, int], tuple[int, int]] = {}
    for ty in range(n_tiles):
        for tx in range(n_tiles):
            ox, oy = stamp_origin(tx, ty)
            for cx, cy in stamp_cells_at(ox, oy):
                gx = feet_cx + cx - ref_ox
                gy = feet_cy + cy - ref_oy
                owners[(gx, gy)] = (tx, ty)
    return owners


def floor_solid_char_cells(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = FLOOR_LAYOUT_TILES,
) -> set[tuple[int, int]]:
    return set(floor_stamp_tile_owners(feet_cx, feet_cy, n_tiles=n_tiles))


def build_floor_patch(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = FLOOR_LAYOUT_TILES,
    seed: int = 0,
) -> list[FloorGlyphCell]:
    owners = floor_stamp_tile_owners(feet_cx, feet_cy, n_tiles=n_tiles)
    cells: dict[tuple[int, int], FloorGlyphCell] = {}
    for (cx, cy), (tx, ty) in owners.items():
        even = (tx + ty) % 2 == 0
        tile_bg = FLOOR_TILE_A_BG if even else FLOOR_TILE_B_BG
        cell_rng = random.Random(seed ^ (cx * 977 + cy * 131 + 0xF100))
        ch, fg = _grass_glyph(cell_rng)
        cells[(cx, cy)] = FloorGlyphCell(
            cx, cy, ch, fg, tile_bg, solid=True, tile_tx=tx, tile_ty=ty,
        )
    return list(cells.values())


def floor_iso_view_offsets(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = FLOOR_LAYOUT_TILES,
) -> frozenset[tuple[int, int]]:
    solid = floor_solid_char_cells(feet_cx, feet_cy, n_tiles=n_tiles)
    return frozenset(
        char_cell_to_iso(cx, cy, ref_cx=feet_cx, ref_cy=feet_cy)
        for cx, cy in solid
    )
