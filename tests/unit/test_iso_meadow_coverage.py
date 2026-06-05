"""Iso meadow must not leave screen holes between grass tile footprints."""
from __future__ import annotations

from src.constants import ISO_ORIGIN_X, ISO_ORIGIN_Y, ISO_STEP_X, ISO_STEP_Y
from src.constants import CELL_H, CELL_W
from src.render.iso_footprint import (
    internal_footprint_holes,
    iso_footprint_cells,
    iso_footprint_pixel_rect,
    union_footprint,
)
from src.render.iso_projector import IsoProjector
from src.render.screen_buffer import ScreenBuffer
from src.render.tile_stencil import load_tile_stencil, stamp


def _meadow_anchors(
    wx0: int,
    wy0: int,
    w: int,
    h: int,
    *,
    focus_wx: int,
    focus_wy: int,
) -> list[tuple[int, int]]:
    p = IsoProjector(origin_x=ISO_ORIGIN_X, origin_y=ISO_ORIGIN_Y)
    anchors: list[tuple[int, int]] = []
    for wx in range(wx0, wx0 + w):
        for wy in range(wy0, wy0 + h):
            ax, ay = p.world_to_screen(wx, wy, focus_wx=focus_wx, focus_wy=focus_wy)
            anchors.append((ax, ay))
    return anchors


def test_gpu_footprint_pixel_rect_covers_all_cells():
    ax, ay = 50, 20
    cells = iso_footprint_cells(ax, ay)
    x0, y0, x1, y1 = iso_footprint_pixel_rect(ax, ay)
    for cx, cy in cells:
        px, py = cx * CELL_W, cy * CELL_H
        assert x0 <= px and px + CELL_W <= x1 + 0.01
        assert y0 <= py and py + CELL_H <= y1 + 0.01


def test_iso_footprint_covers_full_diamond():
    cells = iso_footprint_cells(50, 20, step_x=ISO_STEP_X, step_y=ISO_STEP_Y)
    assert len(cells) >= 8
    assert (50, 20) in cells
    assert (49, 21) in cells and (51, 21) in cells


def test_adjacent_tiles_share_footprint():
    p = IsoProjector(origin_x=ISO_ORIGIN_X, origin_y=ISO_ORIGIN_Y)
    focus_wx, focus_wy = 6, 6
    a = set(
        iso_footprint_cells(
            *p.world_to_screen(5, 6, focus_wx=focus_wx, focus_wy=focus_wy)
        )
    )
    b = set(
        iso_footprint_cells(
            *p.world_to_screen(6, 6, focus_wx=focus_wx, focus_wy=focus_wy)
        )
    )
    assert len(a & b) >= 2


def test_meadow_12x12_no_internal_holes():
    wx0, wy0, mw, mh = 0, 0, 12, 12
    focus_wx, focus_wy = wx0 + mw // 2, wy0 + mh // 2
    anchors = _meadow_anchors(wx0, wy0, mw, mh, focus_wx=focus_wx, focus_wy=focus_wy)
    covered = union_footprint(anchors, step_x=ISO_STEP_X, step_y=ISO_STEP_Y)
    holes = internal_footprint_holes(covered)
    assert holes == [], f"internal holes {holes[:20]}"
    assert len(covered) >= mw * mh * 4


def test_meadow_stamp_fills_buffer_cells():
    wx0, wy0, mw, mh = 5, 5, 10, 10
    focus_wx, focus_wy = wx0 + mw // 2, wy0 + mh // 2
    p = IsoProjector(origin_x=ISO_ORIGIN_X, origin_y=ISO_ORIGIN_Y)
    buf = ScreenBuffer(100, 50)
    buf.clear()
    grass = load_tile_stencil("grass")
    fg, bg = (100, 130, 90), (30, 45, 30)
    covered: set[tuple[int, int]] = set()
    for wx in range(wx0, wx0 + mw):
        for wy in range(wy0, wy0 + mh):
            ax, ay = p.world_to_screen(wx, wy, focus_wx=focus_wx, focus_wy=focus_wy)
            stamp(buf, ax, ay, grass, fg=fg, bg=bg, fill_iso_footprint=True)
            stamp(buf, ax, ay, grass, fg=fg, bg=bg, fill_iso_footprint=False)
            for cx, cy in iso_footprint_cells(ax, ay):
                if buf.in_bounds(cx, cy) and buf.chars[buf._idx(cx, cy)] != " ":
                    covered.add((cx, cy))
    covered_union = union_footprint(
        _meadow_anchors(wx0, wy0, mw, mh, focus_wx=focus_wx, focus_wy=focus_wy)
    )
    holes = internal_footprint_holes(covered)
    unstamped = [c for c in holes if c not in covered]
    assert unstamped == [], f"internal holes {unstamped[:15]}"
