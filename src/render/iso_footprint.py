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


def iso_footprint_geom_pixel_rect(
    anchor_cx: int,
    anchor_cy: int,
    *,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> tuple[float, float, float, float]:
    """Footprint AABB used by GPU diamond geom (matches iso_renderer _diamond_geom)."""
    x0 = float((anchor_cx - step_x) * CELL_W)
    y0 = float((anchor_cy - step_y) * CELL_H)
    x1 = float((anchor_cx + step_x + 1) * CELL_W)
    y1 = float((anchor_cy + 2 * step_y + 1) * CELL_H)
    return x0, y0, x1, y1


def iso_footprint_bbox_size(
    *,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> tuple[float, float]:
    """Width/height of iso_footprint_geom_pixel_rect (for GPU footprint AABB detection)."""
    return float((2 * step_x + 1) * CELL_W), float((3 * step_y + 1) * CELL_H)


def pixel_inside_iso_diamond(
    px: float,
    py: float,
    bounds_x0: float,
    bounds_y0: float,
    *,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> bool:
    """Same iso bound test as GPU inside_iso_diamond (pixel center coordinates)."""
    half_w = float(step_x * CELL_W)
    mid_h = float(step_y * CELL_H)
    tip_x = bounds_x0 + half_w
    tip_y = bounds_y0 + mid_h
    dx = px - tip_x
    dy = py - tip_y
    ax = abs(dx)
    if dy >= 0.0:
        return ax / half_w + dy / (2.0 * mid_h) <= 1.001
    return ax / half_w + (-dy) / mid_h <= 1.001


def footprint_bbox_ear_cells(
    anchor_cx: int,
    anchor_cy: int,
    *,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> list[tuple[int, int]]:
    """Char cells inside footprint AABB but outside the iso diamond (AABB corner ears)."""
    x0, y0, x1, y1 = iso_footprint_pixel_rect(
        anchor_cx, anchor_cy, step_x=step_x, step_y=step_y
    )
    diamond = set(iso_footprint_cells(anchor_cx, anchor_cy, step_x=step_x, step_y=step_y))
    cx_lo = int(x0 // CELL_W)
    cy_lo = int(y0 // CELL_H)
    cx_hi = int((x1 - 1) // CELL_W)
    cy_hi = int((y1 - 1) // CELL_H)
    ears: list[tuple[int, int]] = []
    for cx in range(cx_lo, cx_hi + 1):
        for cy in range(cy_lo, cy_hi + 1):
            if (cx, cy) not in diamond:
                ears.append((cx, cy))
    return ears


def footprint_coverage_gaps(
    anchors: list[tuple[int, int]],
    *,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> list[tuple[int, int]]:
    """Legacy name: internal holes inside the meadow union."""
    return internal_footprint_holes(union_footprint(anchors, step_x=step_x, step_y=step_y))
