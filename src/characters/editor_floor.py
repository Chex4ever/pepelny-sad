"""Editor floor: 5×5 diag iso-square tiles (1 m), drawn with game 2:1 iso projection."""
from __future__ import annotations

import random
from dataclasses import dataclass

from src.constants import ISO_STEP_X, ISO_STEP_Y
from src.prototype.dia_scale.constants import COLOR_FLOOR_ALT_FG, COLOR_FLOOR_FG
from src.prototype.dia_scale.tessellation import stamp_cells_at, stamp_origin, stamp_tip
from src.render.iso_footprint import internal_footprint_holes
from src.render.iso_character_view import EDITOR_FLOOR_TILES

# Checkerboard per tile (tx, ty).
FLOOR_TILE_A_BG = (32, 48, 30)
FLOOR_TILE_B_BG = (48, 38, 28)
FLOOR_TILE_A_FG = COLOR_FLOOR_FG
FLOOR_TILE_B_FG = (145, 120, 85)


@dataclass(frozen=True)
class FloorGlyphCell:
    cx: int
    cy: int
    ch: str
    fg: tuple[int, int, int]
    bg: tuple[int, int, int]
    solid: bool = True
    tile_tx: int = 0
    tile_ty: int = 0


def _grass_glyph(rng: random.Random) -> tuple[str, tuple[int, int, int]]:
    roll = rng.random()
    if roll < 0.08:
        return ",", COLOR_FLOOR_ALT_FG
    if roll < 0.12:
        return "'", COLOR_FLOOR_ALT_FG
    return ".", COLOR_FLOOR_FG


def floor_iso_screen_offset(
    cx: int,
    cy: int,
    *,
    ref_cx: int,
    ref_cy: int,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> tuple[int, int]:
    """Game 2:1 iso screen offset (same formula as IsoProjector, origin at ref)."""
    dx, dy = cx - ref_cx, cy - ref_cy
    su = int(round((dx - dy) * step_x))
    sv = int(round((dx + dy) * step_y))
    return su, sv


def floor_screen_offset(
    cx: int,
    cy: int,
    *,
    ref_cx: int,
    ref_cy: int,
) -> tuple[int, int]:
    """Screen cell for a floor char — iso projection relative to feet."""
    return floor_iso_screen_offset(cx, cy, ref_cx=ref_cx, ref_cy=ref_cy)


def floor_tile_anchors(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> list[tuple[int, int, int, int]]:
    """(tx, ty, tip_cx, tip_cy) for n×n diag patch centered on feet."""
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
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> dict[tuple[int, int], tuple[int, int]]:
    """Char cell → owning floor tile (tx, ty) for every ``@`` in the 5×5 stamp patch."""
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
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> set[tuple[int, int]]:
    """All ``@`` stamp char cells in the 1 m diag floor patch."""
    return set(floor_stamp_tile_owners(feet_cx, feet_cy, n_tiles=n_tiles))


def floor_stamp_char_cells(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> set[tuple[int, int]]:
    """Char cells covered by @@_/_@@ grass stencil glyphs."""
    center = n_tiles // 2
    ref_ox, ref_oy = stamp_origin(center, center)
    stamps: set[tuple[int, int]] = set()
    for ty in range(n_tiles):
        for tx in range(n_tiles):
            ox, oy = stamp_origin(tx, ty)
            for cx, cy in stamp_cells_at(ox, oy):
                gx = feet_cx + cx - ref_ox
                gy = feet_cy + cy - ref_oy
                stamps.add((gx, gy))
    return stamps


def build_floor_patch(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
    seed: int = 0,
) -> list[FloorGlyphCell]:
    """1 m diag stamp floor: checkerboard per (tx, ty), grass on each ``@`` cell."""
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
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> frozenset[tuple[int, int]]:
    """Iso screen (su, sv) for every ``@`` stamp cell (one char cell → one screen cell)."""
    solid = floor_solid_char_cells(feet_cx, feet_cy, n_tiles=n_tiles)
    return frozenset(
        floor_screen_offset(cx, cy, ref_cx=feet_cx, ref_cy=feet_cy)
        for cx, cy in solid
    )


def floor_iso_view_offsets_span_filled(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> frozenset[tuple[int, int]]:
    """Iso screen cells used when drawing the editor floor (row spans filled, no gaps)."""
    return frozenset(floor_iso_draw_map(feet_cx, feet_cy, n_tiles=n_tiles))


def floor_iso_draw_map(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
    seed: int = 0,
) -> dict[tuple[int, int], FloorGlyphCell]:
    """Map iso (su, sv) → floor cell for renderer; fills horizontal gaps per row."""
    by_iso: dict[tuple[int, int], FloorGlyphCell] = {}
    for cell in build_floor_patch(feet_cx, feet_cy, n_tiles=n_tiles, seed=seed):
        su, sv = floor_screen_offset(
            cell.cx, cell.cy, ref_cx=feet_cx, ref_cy=feet_cy,
        )
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


def floor_row_gap_count(view: frozenset[tuple[int, int]] | set[tuple[int, int]]) -> int:
    """Count empty cells between leftmost and rightmost floor cell in each row."""
    if not view:
        return 0
    by_row: dict[int, list[int]] = {}
    for u, v in view:
        by_row.setdefault(v, []).append(u)
    gaps = 0
    for us in by_row.values():
        us.sort()
        for left, right in zip(us, us[1:]):
            gaps += right - left - 1
    return gaps


def floor_row_span_holes(view: frozenset[tuple[int, int]] | set[tuple[int, int]]) -> list[tuple[int, int, int]]:
    """(row_v, missing_count, span_width) for rows not fully filled between min and max u."""
    if not view:
        return []
    by_row: dict[int, list[int]] = {}
    for u, v in view:
        by_row.setdefault(v, []).append(u)
    out: list[tuple[int, int, int]] = []
    for v, us in by_row.items():
        us.sort()
        span = us[-1] - us[0] + 1
        if len(us) != span:
            out.append((v, span - len(us), span))
    return out


def assert_floor_has_no_holes(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> None:
    """Raise AssertionError if editor iso floor or packed layout golden has row gaps."""
    span = floor_iso_view_offsets_span_filled(feet_cx, feet_cy, n_tiles=n_tiles)
    iso_gaps = floor_row_gap_count(span)
    if iso_gaps:
        raise AssertionError(f"editor iso floor has {iso_gaps} row gap(s) on screen")
    internal = internal_footprint_holes(set(span))
    if internal:
        raise AssertionError(f"floor has {len(internal)} internal holes, e.g. {internal[:4]}")
    packed = rasterize_floor_packed_view(feet_cx, feet_cy, n_tiles=n_tiles)
    gaps = packed_canvas_row_gap_count(packed)
    if gaps:
        raise AssertionError(f"packed layout golden has {gaps} row gap(s)")


def packed_canvas_row_gap_count(rows: tuple[str, ...]) -> int:
    """Count empty cells between leftmost and rightmost glyph in each canvas row."""
    gaps = 0
    for row in rows:
        cols = [i for i, ch in enumerate(row) if ch != "_"]
        if len(cols) < 2:
            continue
        for left, right in zip(cols, cols[1:]):
            gaps += right - left - 1
    return gaps


def rasterize_floor_packed_view(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
    empty: str = "_",
) -> tuple[str, ...]:
    """19×10 packed alphabet canvas from diag tessellation + display test tiles."""
    from src.characters.editor_floor_test_tiles import render_packed_test_floor

    _ = empty
    return render_packed_test_floor(
        n_tiles,
        feet_cx=feet_cx,
        feet_cy=feet_cy,
        use_orientation=False,
    )


def floor_tile_anchor_iso_offsets(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> frozenset[tuple[int, int]]:
    """Iso screen positions of the 25 tile tips."""
    return frozenset(
        floor_screen_offset(ax, ay, ref_cx=feet_cx, ref_cy=feet_cy)
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
        su, sv = floor_screen_offset(c.cx, c.cy, ref_cx=ref_cx, ref_cy=ref_cy)
        sus.append(su)
        svs.append(sv)
    return min(sus), max(sus), min(svs), max(svs)


def floor_solid_has_internal_holes(
    feet_cx: int,
    feet_cy: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> list[tuple[int, int]]:
    """Empty iso-screen cells fully surrounded by span-filled editor floor (should be none)."""
    return internal_footprint_holes(
        floor_iso_view_offsets_span_filled(feet_cx, feet_cy, n_tiles=n_tiles)
    )


def floor_tile_index_bounds(
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> tuple[int, int, int, int]:
    """Inclusive tile index ranges (tx_lo, ty_lo, tx_hi, ty_hi) for centered patch."""
    return 0, 0, n_tiles - 1, n_tiles - 1
