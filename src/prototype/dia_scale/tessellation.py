"""2a iso-square stamp tessellation (horiz_brick) and camera rotation."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from src.prototype.dia_scale.constants import STAMP_PREVIEW

ISO32_CELLS: frozenset[tuple[int, int]] = frozenset(
    (x, y)
    for y, row in enumerate(STAMP_PREVIEW)
    for x, ch in enumerate(row)
    if ch == "@"
)


def stamp_origin(tx: int, ty: int) -> tuple[int, int]:
    """Horiz_brick placement: gap-free interior (ox=tx*2+(ty%2), oy=ty)."""
    return tx * 2 + (ty % 2), ty


def stamp_origins(nx: int, ny: int) -> list[tuple[int, int, int, int]]:
    """(tx, ty, ox, oy) for each floor tile in patch."""
    return [(tx, ty, *stamp_origin(tx, ty)) for ty in range(ny) for tx in range(nx)]


def stamp_cells_at(ox: int, oy: int) -> set[tuple[int, int]]:
    return {(ox + dx, oy + dy) for dx, dy in ISO32_CELLS}


def rotate_offset(dx: int, dy: int, steps: int) -> tuple[int, int]:
    """Rotate (dx, dy) by steps*90° CCW (same convention as tree_viewer)."""
    s = steps % 4
    if s == 0:
        return dx, dy
    if s == 1:
        return dy, -dx
    if s == 2:
        return -dx, -dy
    return -dy, dx


def world_to_view(cx: int, cy: int, focus_cx: int, focus_cy: int, rotation: int) -> tuple[int, int]:
    return rotate_offset(cx - focus_cx, cy - focus_cy, rotation)


def view_to_world(vx: int, vy: int, focus_cx: int, focus_cy: int, rotation: int) -> tuple[int, int]:
    """Inverse of world_to_view (rotation steps reversed)."""
    dx, dy = rotate_offset(vx, vy, (4 - rotation) % 4)
    return focus_cx + dx, focus_cy + dy


@dataclass(frozen=True)
class CoverageStats:
    tiles: int
    filled_cells: int
    gaps: int
    internal_gaps: int
    seams: int
    coverage_pct: float


def analyze_floor_coverage(nx: int, ny: int) -> CoverageStats:
    """Coverage of horiz_brick stamp union (world-fixed, no rotation)."""
    counts: Counter = Counter()
    for *_ids, ox, oy in stamp_origins(nx, ny):
        for cell in stamp_cells_at(ox, oy):
            counts[cell] += 1
    if not counts:
        return CoverageStats(0, 0, 0, 0, 0, 0.0)
    min_x = min(k[0] for k in counts)
    max_x = max(k[0] for k in counts)
    min_y = min(k[1] for k in counts)
    max_y = max(k[1] for k in counts)
    gaps = internal = seams = 0
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            n = counts[(x, y)]
            if n == 0:
                gaps += 1
                if min_x + 1 <= x <= max_x - 1 and min_y + 1 <= y <= max_y - 1:
                    internal += 1
            elif n > 1:
                seams += 1
    bbox = (max_x - min_x + 1) * (max_y - min_y + 1)
    filled = sum(counts.values())
    return CoverageStats(
        tiles=nx * ny,
        filled_cells=filled,
        gaps=gaps,
        internal_gaps=internal,
        seams=seams,
        coverage_pct=100.0 * (bbox - gaps) / bbox if bbox else 0.0,
    )
