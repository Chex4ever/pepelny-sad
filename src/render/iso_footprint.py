"""Screen-cell coverage for one 2:1 isometric ground tile."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.constants import CELL_H, CELL_W, ISO_STEP_X, ISO_STEP_Y

FootprintMode = Literal["current", "compact", "step11", "brick21"]


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


def footprint_diamond_steps(mode: FootprintMode) -> tuple[int, int]:
    """Diamond step_x/step_y for experimental footprint modes (prototype only)."""
    if mode in ("step11", "compact"):
        return 1, 1
    if mode == "brick21":
        return 1, 1
    return ISO_STEP_X, ISO_STEP_Y


def brick21_tile_cells(anchor_cx: int, anchor_cy: int) -> list[tuple[int, int]]:
    """2×1 char tile on staggered rows (odd cy shifted +1 char).

    Pattern (each pair = one tile, `_` = half-char stagger on odd rows):
      aa bb vv
      _ gg dd ee
      jj zz ii
      _ kk ll mm
    """
    cy = anchor_cy
    cx1 = anchor_cx
    cx0 = cx1 - 1
    if cy % 2 == 1 and cx0 % 2 == 0:
        cx0 += 1
        cx1 += 1
    return [(cx0, cy), (cx1, cy)]


def brick21_tile_pixel_rect(anchor_cx: int, anchor_cy: int) -> tuple[float, float, float, float]:
    """Axis-aligned 2×1 char rect for a brick21 tile (no diamond ears)."""
    cells = brick21_tile_cells(anchor_cx, anchor_cy)
    cx0 = min(c[0] for c in cells)
    cy = cells[0][1]
    return (
        float(cx0 * CELL_W),
        float(cy * CELL_H),
        float((cx0 + 2) * CELL_W),
        float((cy + 1) * CELL_H),
    )


def iso_diamond_geom(
    anchor_cx: int,
    anchor_cy: int,
    *,
    mode: FootprintMode = "current",
) -> tuple[float, float, float, float, float, float, float, float, float, float]:
    """Diamond corners + footprint AABB (prototype-aware; production uses iso_renderer._diamond_geom).

    Returns: px, py, right, left, mid_y, top_y, x0, y0, x1, y1
    """
    if mode == "compact":
        px = float(anchor_cx * CELL_W)
        py = float(anchor_cy * CELL_H)
        x0 = float((anchor_cx - 1) * CELL_W)
        y0 = float((anchor_cy - 1) * CELL_H)
        x1 = float((anchor_cx + 1) * CELL_W)
        y1 = py
        right = x1
        left = x0
        mid_y = y0 + (y1 - y0) * 0.5
        top_y = y0
        return px, py, right, left, mid_y, top_y, x0, y0, x1, y1

    if mode == "brick21":
        x0, y0, x1, y1 = brick21_tile_pixel_rect(anchor_cx, anchor_cy)
        px = x0 + (x1 - x0) * 0.5
        py = y1
        right = x1
        left = x0
        mid_y = y0 + (y1 - y0) * 0.5
        top_y = y0
        return px, py, right, left, mid_y, top_y, x0, y0, x1, y1

    step_x, step_y = footprint_diamond_steps(mode)
    px = float(anchor_cx * CELL_W)
    py = float(anchor_cy * CELL_H)
    x0 = float((anchor_cx - step_x) * CELL_W)
    y0 = float((anchor_cy - step_y) * CELL_H)
    x1 = float((anchor_cx + step_x + 1) * CELL_W)
    y1 = float((anchor_cy + 2 * step_y + 1) * CELL_H)
    right = float((anchor_cx + step_x) * CELL_W)
    left = float((anchor_cx - step_x) * CELL_W)
    mid_y = float((anchor_cy + step_y) * CELL_H)
    top_y = float((anchor_cy + 2 * step_y) * CELL_H)
    return px, py, right, left, mid_y, top_y, x0, y0, x1, y1


def pixel_inside_footprint_diamond(
    px: float,
    py: float,
    bounds_x0: float,
    bounds_y0: float,
    *,
    mode: FootprintMode = "current",
    bounds_x1: float | None = None,
    bounds_y1: float | None = None,
) -> bool:
    """Footprint diamond hit test (matches iso_diamond_geom for the given mode)."""
    if mode == "compact":
        x1 = bounds_x0 + 2 * CELL_W if bounds_x1 is None else bounds_x1
        y1 = bounds_y0 + CELL_H if bounds_y1 is None else bounds_y1
        verts = [
            (bounds_x0 + CELL_W, y1),
            (x1, bounds_y0 + CELL_H * 0.5),
            (bounds_x0 + CELL_W, bounds_y0),
            (bounds_x0, bounds_y0 + CELL_H * 0.5),
        ]
        return _point_in_polygon(px, py, verts)

    if mode == "brick21":
        x1 = bounds_x0 + 2 * CELL_W if bounds_x1 is None else bounds_x1
        y1 = bounds_y0 + CELL_H if bounds_y1 is None else bounds_y1
        return bounds_x0 <= px < x1 and bounds_y0 <= py < y1

    step_x, step_y = footprint_diamond_steps(mode)
    return pixel_inside_iso_diamond(
        px, py, bounds_x0, bounds_y0, step_x=step_x, step_y=step_y
    )


def bbox_ear_pixel_count(
    anchor_cx: int,
    anchor_cy: int,
    *,
    mode: FootprintMode = "current",
) -> int:
    """Pixels inside geom bbox but outside the footprint diamond."""
    *_, x0, y0, x1, y1 = iso_diamond_geom(anchor_cx, anchor_cy, mode=mode)
    count = 0
    for iy in range(int(y0), int(y1)):
        for ix in range(int(x0), int(x1)):
            if not pixel_inside_footprint_diamond(
                ix + 0.5, iy + 0.5, x0, y0, mode=mode, bounds_x1=x1, bounds_y1=y1
            ):
                count += 1
    return count


@dataclass(frozen=True)
class FootprintMetrics:
    mode: FootprintMode
    iso_spacing_px: tuple[int, int]
    vertex_aabb_px: tuple[int, int]
    geom_bbox_px: tuple[int, int]
    geom_bbox_char: tuple[int, int]
    footprint_cells: int
    diamond_px: int
    ear_px: int
    neighbor_overlap_cells: int | None = None

    @property
    def ear_percent(self) -> float:
        total = self.diamond_px + self.ear_px
        if total == 0:
            return 0.0
        return 100.0 * self.ear_px / total


def footprint_metrics(
    anchor_cx: int,
    anchor_cy: int,
    *,
    mode: FootprintMode = "current",
    neighbor_anchor: tuple[int, int] | None = None,
    project_step_x: int = ISO_STEP_X,
    project_step_y: int = ISO_STEP_Y,
) -> FootprintMetrics:
    """Summary stats for diagram / prototype comparison."""
    if mode == "brick21":
        x0, y0, x1, y1 = brick21_tile_pixel_rect(anchor_cx, anchor_cy)
        cells = brick21_tile_cells(anchor_cx, anchor_cy)
        tile_px = int((x1 - x0) * (y1 - y0))
        overlap: int | None = None
        if neighbor_anchor is not None:
            ncells = set(brick21_tile_cells(*neighbor_anchor))
            overlap = len(set(cells) & ncells)
        bw = int(x1 - x0)
        bh = int(y1 - y0)
        return FootprintMetrics(
            mode=mode,
            iso_spacing_px=(project_step_x * CELL_W, project_step_y * CELL_H),
            vertex_aabb_px=(bw, bh),
            geom_bbox_px=(bw, bh),
            geom_bbox_char=(2, 1),
            footprint_cells=len(cells),
            diamond_px=tile_px,
            ear_px=0,
            neighbor_overlap_cells=overlap,
        )

    px, py, right, left, mid_y, top_y, x0, y0, x1, y1 = iso_diamond_geom(
        anchor_cx, anchor_cy, mode=mode
    )
    verts = [(px, py), (right, mid_y), (left, mid_y), (px, top_y)]
    vx0 = int(min(v[0] for v in verts))
    vx1 = int(max(v[0] for v in verts))
    vy0 = int(min(v[1] for v in verts))
    vy1 = int(max(v[1] for v in verts))
    step_x, step_y = footprint_diamond_steps(mode)
    cells = iso_footprint_cells(anchor_cx, anchor_cy, step_x=step_x, step_y=step_y)
    if mode == "compact":
        cells = [
            (anchor_cx - 1, anchor_cy - 1),
            (anchor_cx, anchor_cy - 1),
        ]
    elif mode == "brick21":
        cells = brick21_tile_cells(anchor_cx, anchor_cy)
    diamond_px = 0
    ear_px = 0
    for iy in range(int(y0), int(y1)):
        for ix in range(int(x0), int(x1)):
            if pixel_inside_footprint_diamond(
                ix + 0.5, iy + 0.5, x0, y0, mode=mode, bounds_x1=x1, bounds_y1=y1
            ):
                diamond_px += 1
            else:
                ear_px += 1
    overlap: int | None = None
    if neighbor_anchor is not None:
        nax, nay = neighbor_anchor
        nstep_x, nstep_y = footprint_diamond_steps(mode)
        ncells = set(iso_footprint_cells(nax, nay, step_x=nstep_x, step_y=nstep_y))
        if mode == "compact":
            ncells = {(nax - 1, nay - 1), (nax, nay - 1)}
        elif mode == "brick21":
            ncells = set(brick21_tile_cells(nax, nay))
        overlap = len(set(cells) & ncells)
    bw = int(x1 - x0)
    bh = int(y1 - y0)
    return FootprintMetrics(
        mode=mode,
        iso_spacing_px=(project_step_x * CELL_W, project_step_y * CELL_H),
        vertex_aabb_px=(vx1 - vx0, vy1 - vy0),
        geom_bbox_px=(bw, bh),
        geom_bbox_char=(bw // CELL_W, bh // CELL_H),
        footprint_cells=len(cells),
        diamond_px=diamond_px,
        ear_px=ear_px,
        neighbor_overlap_cells=overlap,
    )
