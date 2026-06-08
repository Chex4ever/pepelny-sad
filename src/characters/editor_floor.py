"""Deprecated: use ``src.engine.floor``. Thin re-export for existing imports."""
from __future__ import annotations

from src.engine.config import FLOOR_LAYOUT_TILES as EDITOR_FLOOR_TILES, editor_floor_patch_tiles
from src.engine.floor import *  # noqa: F403
from src.engine.floor import (
    FloorGlyphCell,
    build_floor_patch,
    floor_iso_view_offsets,
    floor_packed_draw_map,
    floor_packed_layout_offsets,
    floor_row_gap_count,
    floor_row_span_holes,
    floor_solid_char_cells,
    floor_tile_anchors,
    packed_canvas_row_gap_count,
    rasterize_floor_packed_view,
)
from src.engine.floor.checks import assert_floor_has_no_holes, floor_solid_has_internal_holes
from src.engine.floor.patch import floor_stamp_tile_owners
from src.engine.projection.iso import char_cell_to_iso
from src.prototype.dia_scale.tessellation import stamp_origin, stamp_tip

# Legacy names
floor_screen_offset = char_cell_to_iso
floor_iso_screen_offset = char_cell_to_iso


def floor_iso_view_offsets_span_filled(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> frozenset[tuple[int, int]]:
    return floor_packed_layout_offsets(feet_cx, feet_cy, n_tiles=n_tiles)


def floor_iso_draw_map(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
    seed: int = 0,
) -> dict[tuple[int, int], FloorGlyphCell]:
    by_iso: dict[tuple[int, int], FloorGlyphCell] = {}
    for cell in build_floor_patch(feet_cx, feet_cy, n_tiles=n_tiles, seed=seed):
        su, sv = char_cell_to_iso(cell.cx, cell.cy, ref_cx=feet_cx, ref_cy=feet_cy)
        by_iso[(su, sv)] = cell
    by_row: dict[int, list[int]] = {}
    for su, sv in by_iso:
        by_row.setdefault(sv, []).append(su)
    out = dict(by_iso)
    for sv, us in by_row.items():
        u_lo, u_hi = min(us), max(us)
        for su in range(u_lo, u_hi + 1):
            if (su, sv) in out:
                continue
            nearest = min(us, key=lambda u: abs(u - su))
            out[(su, sv)] = by_iso[(nearest, sv)]
    return out


def floor_tile_anchor_iso_offsets(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> frozenset[tuple[int, int]]:
    return frozenset(
        char_cell_to_iso(ax, ay, ref_cx=feet_cx, ref_cy=feet_cy)
        for _tx, _ty, ax, ay in floor_tile_anchors(feet_cx, feet_cy, n_tiles=n_tiles)
    )


def floor_patch_bounds(
    cells: list[FloorGlyphCell],
    ref_cx: int,
    ref_cy: int,
) -> tuple[int, int, int, int]:
    if not cells:
        return 0, 0, 0, 0
    sus, svs = [], []
    for c in cells:
        su, sv = char_cell_to_iso(c.cx, c.cy, ref_cx=ref_cx, ref_cy=ref_cy)
        sus.append(su)
        svs.append(sv)
    return min(sus), max(sus), min(svs), max(svs)


def floor_tile_index_bounds(
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> tuple[int, int, int, int]:
    return 0, 0, n_tiles - 1, n_tiles - 1


def floor_stamp_char_cells(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int | None = None,
) -> set[tuple[int, int]]:
    n = EDITOR_FLOOR_TILES if n_tiles is None else n_tiles
    center = n // 2
    ref_ox, ref_oy = stamp_origin(center, center)
    from src.prototype.dia_scale.tessellation import stamp_cells_at

    stamps: set[tuple[int, int]] = set()
    for ty in range(n):
        for tx in range(n):
            ox, oy = stamp_origin(tx, ty)
            for cx, cy in stamp_cells_at(ox, oy):
                gx = feet_cx + cx - ref_ox
                gy = feet_cy + cy - ref_oy
                stamps.add((gx, gy))
    return stamps
