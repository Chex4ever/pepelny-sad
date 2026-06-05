"""Screen-cell coverage for one 2:1 isometric ground tile."""
from __future__ import annotations

from src.constants import CELL_H, CELL_W, ISO_STEP_X, ISO_STEP_Y


def _point_in_polygon(px: float, py: float, verts: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(verts)
    for i in range(n):
        x0, y0 = verts[i]
        x1, y1 = verts[(i + 1) % n]
        if ((y0 > py) != (y1 > py)) and (
            px < (x1 - x0) * (py - y0) / (y1 - y0 + 1e-9) + x0
        ):
            inside = not inside
    return inside


def _cell_hits_diamond(
    rx: int,
    ry: int,
    *,
    step_x: int,
    step_y: int,
) -> bool:
    verts = [
        (0.0, 0.0),
        (float(step_x), float(step_y)),
        (0.0, float(2 * step_y)),
        (float(-step_x), float(step_y)),
    ]
    for corner in ((rx, ry), (rx + 1, ry), (rx, ry + 1), (rx + 1, ry + 1)):
        if _point_in_polygon(corner[0] + 0.01, corner[1] + 0.01, verts):
            return True
    return False


def iso_footprint_cells(
    anchor_cx: int,
    anchor_cy: int,
    *,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> list[tuple[int, int]]:
    """All char cells that intersect the iso tile diamond (anchor = bottom tip)."""
    cells: list[tuple[int, int]] = []
    for rx in range(-step_x, step_x + 1):
        for ry in range(-step_y, 2 * step_y + 1):
            if _cell_hits_diamond(rx, ry, step_x=step_x, step_y=step_y):
                cells.append((anchor_cx + rx, anchor_cy + ry))
    return cells


def iso_footprint_pixel_rect(
    anchor_cx: int,
    anchor_cy: int,
    *,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> tuple[float, float, float, float]:
    """Axis-aligned pixel bounds covering the iso ground diamond (for GPU fill)."""
    cells = iso_footprint_cells(
        anchor_cx, anchor_cy, step_x=step_x, step_y=step_y
    )
    if not cells:
        x0 = float(anchor_cx * CELL_W)
        y0 = float(anchor_cy * CELL_H)
        return x0, y0, x0 + CELL_W, y0 + CELL_H
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return (
        float(min(xs) * CELL_W),
        float(min(ys) * CELL_H),
        float((max(xs) + 1) * CELL_W),
        float((max(ys) + 1) * CELL_H),
    )


def union_footprint(anchors: list[tuple[int, int]], **kwargs) -> set[tuple[int, int]]:
    covered: set[tuple[int, int]] = set()
    for ax, ay in anchors:
        covered.update(iso_footprint_cells(ax, ay, **kwargs))
    return covered


def internal_footprint_holes(covered: set[tuple[int, int]]) -> list[tuple[int, int]]:
    """Empty cells fully surrounded by covered cells (real holes in the meadow)."""
    if not covered:
        return []
    min_x = min(c[0] for c in covered)
    max_x = max(c[0] for c in covered)
    min_y = min(c[1] for c in covered)
    max_y = max(c[1] for c in covered)
    holes: list[tuple[int, int]] = []
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            if (x, y) in covered:
                continue
            neighbors = (
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1),
            )
            if all(n in covered for n in neighbors):
                holes.append((x, y))
    return holes


def footprint_coverage_gaps(
    anchors: list[tuple[int, int]],
    *,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> list[tuple[int, int]]:
    """Legacy name: internal holes inside the meadow union."""
    return internal_footprint_holes(union_footprint(anchors, step_x=step_x, step_y=step_y))
