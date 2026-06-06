"""Meadow floor generator for dia_scale char grid."""
from __future__ import annotations

import random

from src.prototype.dia_scale.constants import (
    COLOR_FLOOR_ALT_FG,
    COLOR_FLOOR_BG,
    COLOR_FLOOR_FG,
)
from src.prototype.dia_scale.tessellation import stamp_cells_at, stamp_origins
from src.prototype.dia_scale.world_grid import FloorCell, WorldGrid


def _grass_glyph(rng: random.Random) -> tuple[str, tuple[int, int, int]]:
    roll = rng.random()
    if roll < 0.08:
        return ",", COLOR_FLOOR_ALT_FG
    if roll < 0.12:
        return "'", COLOR_FLOOR_ALT_FG
    return ".", COLOR_FLOOR_FG


def generate_meadow(
    *,
    seed: int,
    nx: int,
    ny: int,
    biome: str = "meadow",
) -> WorldGrid:
    """Fill horiz_brick 2a stamps with grass glyphs."""
    grid = WorldGrid(meta={"seed": seed, "nx": nx, "ny": ny, "biome": biome})
    rng = random.Random(seed ^ 0x1EAD00)
    for tx, ty, ox, oy in stamp_origins(nx, ny):
        tile_rng = random.Random(seed ^ (tx * 977 + ty * 131))
        for cx, cy in stamp_cells_at(ox, oy):
            ch, fg = _grass_glyph(tile_rng)
            grid.set_floor(cx, cy, FloorCell(ch=ch, fg=fg, bg=COLOR_FLOOR_BG))
    return grid
