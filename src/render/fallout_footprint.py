"""Fallout-style staggered ASCII floor grid (prototype / diagram only).

One screen tile ≈ diamond in an 8×4 char macro-cell band:
  row+0: __XXXX__     (4 glyphs, offset +2)
  row+1: XXXXXXXX     (8 glyphs, full width)
  row+2: __XXXX__     (4 glyphs, offset +2)
  row+3: ____XXXX____ (8 glyphs, offset +4 — waist of the *next* iso row)

Horizontal pitch: 8 char columns per tile column.
Vertical pitch: 4 char rows per iso row band.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.constants import CELL_H, CELL_W

# User reference sketch (28 cols × 9 rows).
FALLOUT_SKETCH_ROWS: tuple[str, ...] = (
    "__aaaa____bbbb____cccc______",
    "aaaaaaaabbbbbbbbcccccccc____",
    "__aaaaddddbbbbeeeeccccffff__",
    "____ddddddddeeeeeeeeffffffff",
    "__ggggddddhhhheeeeiiiiffff__",
    "gggggggghhhhhhhhiiiiiiii____",
    "__ggggjjjjhhhhkkkkiiiillll__",
    "____jjjjjjjjkkkkkkkkllllllll",
    "______jjjj____kkkk____llll__",
)

FALLOUT_TILE_W = 8
FALLOUT_BAND_H = 4
FALLOUT_ACTIVE_H = 3


def fallout_tile_cells_local() -> list[tuple[int, int]]:
    """Char offsets (dx, dy) for rows 0–2 inside one 8×4 macro band."""
    cells: list[tuple[int, int]] = []
    for x in range(2, 6):
        cells.append((x, 0))
    for x in range(0, 8):
        cells.append((x, 1))
    for x in range(2, 6):
        cells.append((x, 2))
    return cells


def fallout_tile_cells(macro_cx: int, macro_cy: int) -> list[tuple[int, int]]:
    """Absolute char cells for one Fallout tile (top-left of 8×4 band = macro_cx, macro_cy)."""
    bx = macro_cx * FALLOUT_TILE_W
    by = macro_cy * FALLOUT_BAND_H
    return [(bx + dx, by + dy) for dx, dy in fallout_tile_cells_local()]


def fallout_tile_pixel_rect(macro_cx: int, macro_cy: int) -> tuple[float, float, float, float]:
    """Axis-aligned 8×3 char bbox (active diamond band, rows 0–2)."""
    bx = macro_cx * FALLOUT_TILE_W
    by = macro_cy * FALLOUT_BAND_H
    return (
        float(bx * CELL_W),
        float(by * CELL_H),
        float((bx + FALLOUT_TILE_W) * CELL_W),
        float((by + FALLOUT_ACTIVE_H) * CELL_H),
    )


def fallout_band_waist_cells_local() -> list[tuple[int, int]]:
    """Row +3 inside macro band (8 wide, offset +4) — next iso row."""
    return [(x, 3) for x in range(4, 12)]


@dataclass(frozen=True)
class FalloutGridMetrics:
    sketch_size_char: tuple[int, int]
    tile_pitch_char: tuple[int, int]
    active_cells_per_tile: int
    bbox_cells_per_tile: int
    bbox_px: tuple[int, int]
    ear_cells_in_bbox: int

    @property
    def ear_percent(self) -> float:
        if self.bbox_cells_per_tile == 0:
            return 0.0
        return 100.0 * self.ear_cells_in_bbox / self.bbox_cells_per_tile


def fallout_grid_metrics() -> FalloutGridMetrics:
    local = fallout_tile_cells_local()
    bbox_cells = FALLOUT_TILE_W * FALLOUT_ACTIVE_H
    local_set = set(local)
    ear = bbox_cells - len(local_set)
    w = max(len(r) for r in FALLOUT_SKETCH_ROWS)
    h = len(FALLOUT_SKETCH_ROWS)
    return FalloutGridMetrics(
        sketch_size_char=(w, h),
        tile_pitch_char=(FALLOUT_TILE_W, FALLOUT_BAND_H),
        active_cells_per_tile=len(local_set),
        bbox_cells_per_tile=bbox_cells,
        bbox_px=(FALLOUT_TILE_W * CELL_W, FALLOUT_ACTIVE_H * CELL_H),
        ear_cells_in_bbox=ear,
    )


def sketch_char_at(cx: int, cy: int) -> str:
    if cy < 0 or cy >= len(FALLOUT_SKETCH_ROWS):
        return " "
    row = FALLOUT_SKETCH_ROWS[cy]
    if cx < 0 or cx >= len(row):
        return " "
    return row[cx]
