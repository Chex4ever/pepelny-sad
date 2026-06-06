#!/usr/bin/env python3
"""Explain iso tile geometry: diamond footprint, bbox, ears, neighbors.

Run:
  python scripts/draw_tile_diagram.py
  python scripts/draw_tile_diagram.py --footprint compare --layout block --scale 3
  python scripts/draw_tile_diagram.py --footprint compact --layout single
"""
from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.constants import CELL_H, CELL_W, ISO_STEP_X, ISO_STEP_Y, init_paths
from src.render.fallout_footprint import (
    FALLOUT_ACTIVE_H,
    FALLOUT_BAND_H,
    FALLOUT_SKETCH_ROWS,
    FALLOUT_TILE_W,
    fallout_grid_metrics,
    fallout_tile_cells_local,
)
from src.render.iso_footprint import (
    FootprintMetrics,
    FootprintMode,
    bbox_ear_pixel_count,
    brick21_tile_cells,
    footprint_metrics,
    iso_diamond_geom,
    pixel_inside_footprint_diamond,
)
from src.render.iso_projector import IsoProjector
from src.render.tile_stencil import load_tile_stencil

_EAR_COLOR = (220, 80, 60, 160)
_STENCIL_FG = (100, 130, 90)
_STENCIL_BG = (30, 45, 30, 180)
_COMPACT_GRASS_ROW = ".."
_BRICK21_TILE_COLORS = (
    (50, 90, 55, 200),
    (45, 75, 95, 200),
    (85, 70, 45, 200),
    (70, 55, 90, 200),
)


def _brick21_label(wx: int, wy: int) -> tuple[str, str]:
    """Two identical glyphs per 2×1 tile (like aa, bb in the sketch)."""
    ch = chr(ord("a") + ((wx * 3 + wy * 5) % 26))
    return ch, ch


def _projector_for_mode(mode: FootprintMode) -> IsoProjector:
    if mode == "step11":
        return IsoProjector(step_x=1, step_y=1)
    return IsoProjector()


def _world_anchors(
    projector: IsoProjector,
    tiles: list[tuple[int, int]],
    *,
    focus_wx: int,
    focus_wy: int,
) -> list[tuple[int, int, int, int]]:
    """(wx, wy, anchor_cx, anchor_cy) per tile."""
    out: list[tuple[int, int, int, int]] = []
    for wx, wy in tiles:
        ax, ay = projector.world_to_screen(wx, wy, focus_wx=focus_wx, focus_wy=focus_wy)
        out.append((wx, wy, ax, ay))
    return out


def _layout_tiles(name: str) -> list[tuple[int, int]]:
    if name == "single":
        return [(10, 10)]
    if name == "pair":
        return [(10, 10), (11, 10)]
    if name == "cross":
        return [(10, 10), (11, 10), (10, 11), (9, 10), (10, 9)]
    if name == "block":
        return [(10, 10), (11, 10), (10, 11), (11, 11)]
    if name == "brick_sketch":
        return []  # char-grid demo, not world tiles
    if name == "fallout_sketch":
        return []
    raise ValueError(f"unknown layout {name!r}")


_BRICK_SKETCH_ROWS = (
    ("aa", "bb", "vv"),
    ("gg", "dd", "ee"),
    ("jj", "zz", "ii"),
    ("kk", "ll", "mm"),
)


def _diamond_verts(anchor_cx: int, anchor_cy: int, mode: FootprintMode) -> list[tuple[float, float]]:
    px, py, right, left, mid_y, top_y, *_ = iso_diamond_geom(anchor_cx, anchor_cy, mode=mode)
    return [(px, py), (right, mid_y), (px, top_y), (left, mid_y)]


def _collect_bounds(
    anchors: list[tuple[int, int, int, int]],
    mode: FootprintMode,
) -> tuple[float, float, float, float]:
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for *_rest, ax, ay in anchors:
        *_, bx0, by0, bx1, by1 = iso_diamond_geom(ax, ay, mode=mode)
        x0 = min(x0, bx0)
        y0 = min(y0, by0)
        x1 = max(x1, bx1)
        y1 = max(y1, by1)
    return x0, y0, x1, y1


def _blit_bbox_ears(
    layer: pygame.Surface,
    anchor_cx: int,
    anchor_cy: int,
    *,
    mode: FootprintMode,
    scale: int,
    sx: Callable[[float], int],
    sy: Callable[[float], int],
) -> None:
    """Paint ear pixels: geom bbox minus footprint diamond."""
    *_, x0, y0, x1, y1 = iso_diamond_geom(anchor_cx, anchor_cy, mode=mode)
    block = pygame.Surface((scale, scale), pygame.SRCALPHA)
    block.fill(_EAR_COLOR)
    ox = sx(x0)
    oy = sy(y0)
    for iy in range(int(y0), int(y1)):
        py = iy + 0.5
        for ix in range(int(x0), int(x1)):
            if pixel_inside_footprint_diamond(
                ix + 0.5, py, x0, y0, mode=mode, bounds_x1=x1, bounds_y1=y1
            ):
                continue
            layer.blit(block, (ox + (ix - int(x0)) * scale, oy + (iy - int(y0)) * scale))


def _blit_mock_stencil(
    layer: pygame.Surface,
    anchor_cx: int,
    anchor_cy: int,
    *,
    mode: FootprintMode,
    scale: int,
    sx: Callable[[float], int],
    sy: Callable[[float], int],
    font: pygame.font.Font,
) -> None:
    """Draw stencil mock on focus tile only (compact 2x1 or current grass.txt)."""
    cw = CELL_W * scale
    ch = CELL_H * scale

    def blit_glyph(cx: int, cy: int, ch_str: str) -> None:
        cell = pygame.Surface((cw, ch), pygame.SRCALPHA)
        cell.fill(_STENCIL_BG)
        text = font.render(ch_str, True, _STENCIL_FG)
        cell.blit(text, (0, 0))
        layer.blit(cell, (sx(cx * CELL_W), sy(cy * CELL_H)))

    if mode == "compact":
        blit_glyph(anchor_cx - 1, anchor_cy - 1, _COMPACT_GRASS_ROW[0])
        blit_glyph(anchor_cx, anchor_cy - 1, _COMPACT_GRASS_ROW[1])
        return

    if mode == "brick21":
        return

    grass = load_tile_stencil("grass")
    for g in grass.glyphs:
        blit_glyph(anchor_cx + g.dx, anchor_cy + g.dy, g.ch)


def _blit_brick21_tile(
    layer: pygame.Surface,
    wx: int,
    wy: int,
    anchor_cx: int,
    anchor_cy: int,
    *,
    scale: int,
    sx: Callable[[float], int],
    sy: Callable[[float], int],
    font: pygame.font.Font,
    tile_index: int,
) -> None:
    """Draw one staggered 2×1 char tile with paired glyphs."""
    cw = CELL_W * scale
    ch = CELL_H * scale
    cells = brick21_tile_cells(anchor_cx, anchor_cy)
    ch0, ch1 = _brick21_label(wx, wy)
    fill = _BRICK21_TILE_COLORS[tile_index % len(_BRICK21_TILE_COLORS)]
    for i, (cx, cy) in enumerate(cells):
        cell = pygame.Surface((cw, ch), pygame.SRCALPHA)
        cell.fill(fill)
        glyph = ch0 if i == 0 else ch1
        text = font.render(glyph, True, (230, 240, 220))
        cell.blit(text, (0, 0))
        layer.blit(cell, (sx(cx * CELL_W), sy(cy * CELL_H)))


def _mode_title(mode: FootprintMode) -> str:
    if mode == "current":
        return f"current ISO_STEP ({ISO_STEP_X},{ISO_STEP_Y})"
    if mode == "compact":
        return "compact 20x16 diamond (not brick layout)"
    if mode == "brick21":
        return "brick21: 2x1 char, staggered rows"
    return "step11 ISO_STEP (1,1)"


def _legend_entries(mode: FootprintMode, metrics: FootprintMetrics | None) -> list[tuple[str, tuple[int, int, int]]]:
    if mode == "brick21":
        return [
            (_mode_title(mode), (240, 240, 250)),
            ("Colored 2×1 pairs = one world tile (aa bb …)", (120, 200, 140)),
            ("Odd screen rows shift +1 char (_ gg dd …)", (200, 180, 80)),
            ("No diamond / no GPU ears — rect = tile", (160, 160, 180)),
            ("Yellow dot = iso anchor (right cell of pair)", (255, 255, 120)),
            (f"Grid cell = {CELL_W}x{CELL_H} px", (160, 160, 180)),
        ]

    m = metrics
    bbox_line = (
        f"Yellow = bbox {m.geom_bbox_px[0]}x{m.geom_bbox_px[1]} px "
        f"({m.geom_bbox_char[0]}x{m.geom_bbox_char[1]} char), ears {m.ear_percent:.0f}%"
        if m
        else "Yellow tint = bbox undercoat"
    )
    return [
        (_mode_title(mode), (240, 240, 250)),
        ("Green = iso diamond (footprint)", (120, 220, 140)),
        (bbox_line, (200, 180, 80)),
        ("Red = ear pixels (bbox outside diamond)", (220, 120, 100)),
        ("Cyan tint = stencil mock (focus tile)", (120, 200, 220)),
        ("Yellow dot = anchor (bottom tip)", (255, 255, 120)),
        (f"Grid cell = {CELL_W}x{CELL_H} px", (160, 160, 180)),
    ]


def _measure_legend(
    entries: list[tuple[str, tuple[int, int, int]]],
    font_title: pygame.font.Font,
    font_body: pygame.font.Font,
    pad_x: int,
    line_gap: int,
) -> tuple[int, int]:
    w = pad_x
    h = pad_x
    for i, (text, _color) in enumerate(entries):
        fnt = font_title if i == 0 else font_body
        surf = fnt.render(text, True, (255, 255, 255))
        w = max(w, surf.get_width() + 2 * pad_x)
        h += surf.get_height() + line_gap
    h += pad_x
    return w, h


def _render_brick_sketch_panel(*, scale: int, show_grid: bool) -> pygame.Surface:
    """Exact char-grid demo of the user's staggered 2×1 layout."""
    base_cx, base_cy = 48, 20
    margin = 24 * scale
    cols = 8
    rows = len(_BRICK_SKETCH_ROWS)
    pw = int(cols * CELL_W * scale + 2 * margin)
    ph = int(rows * CELL_H * scale + 2 * margin + 40 * scale)

    base = pygame.Surface((pw, ph))
    base.fill((24, 24, 32))
    layer = pygame.Surface((pw, ph), pygame.SRCALPHA)
    font = pygame.font.SysFont("consolas", max(10, 8 + scale))
    title = font.render("2x1 brick layout (your sketch)", True, (230, 230, 240))
    base.blit(title, (margin // 2, margin // 4))

    ox = margin
    oy = margin + title.get_height() + margin // 2

    def sx(x: float) -> int:
        return int(ox + x * scale)

    def sy(y: float) -> int:
        return int(oy + y * scale)

    if show_grid:
        for cx in range(cols + 1):
            x = sx(cx * CELL_W)
            pygame.draw.line(base, (40, 44, 56), (x, oy), (x, oy + rows * CELL_H * scale), 1)
        for cy in range(rows + 1):
            y = sy(cy * CELL_H)
            pygame.draw.line(base, (40, 44, 56), (ox, y), (ox + cols * CELL_W * scale, y), 1)

    cw = CELL_W * scale
    ch = CELL_H * scale
    for row_y, pairs in enumerate(_BRICK_SKETCH_ROWS):
        screen_cy = base_cy + row_y
        for i, pair in enumerate(pairs):
            cx0 = base_cx + 2 * i + (row_y % 2)
            fill = _BRICK21_TILE_COLORS[(row_y * 3 + i) % len(_BRICK21_TILE_COLORS)]
            for j, glyph in enumerate(pair):
                cx = cx0 + j
                cell = pygame.Surface((cw, ch), pygame.SRCALPHA)
                cell.fill(fill)
                text = font.render(glyph, True, (240, 245, 230))
                cell.blit(text, (0, 0))
                lx = sx((cx - base_cx) * CELL_W)
                ly = sy((screen_cy - base_cy) * CELL_H)
                layer.blit(cell, (lx, ly))
            x0 = sx((cx0 - base_cx) * CELL_W)
            y0 = sy((screen_cy - base_cy) * CELL_H)
            pygame.draw.rect(
                base,
                (200, 220, 100),
                pygame.Rect(x0, y0, 2 * cw, ch),
                max(1, scale // 2),
            )

    base.blit(layer, (0, 0))
    hint = font.render("odd rows: +1 char stagger  (_ gg dd …)", True, (160, 165, 180))
    base.blit(hint, (margin // 2, ph - hint.get_height() - margin // 4))
    return base


def _fallout_letter_color(ch: str) -> tuple[int, int, int, int]:
    i = max(0, ord(ch) - ord("a")) % 26
    return (45 + (i * 17) % 80, 70 + (i * 11) % 90, 45 + (i * 23) % 70, 220)


def _render_fallout_sketch_panel(*, scale: int, show_grid: bool) -> pygame.Surface:
    """Fallout-style 8×4 char macro bands (user reference sketch)."""
    rows = len(FALLOUT_SKETCH_ROWS)
    cols = max(len(r) for r in FALLOUT_SKETCH_ROWS)
    margin = 24 * scale
    legend_h = 110 * scale
    pw = int(cols * CELL_W * scale + 2 * margin)
    ph = int(rows * CELL_H * scale + 2 * margin + legend_h)

    base = pygame.Surface((pw, ph))
    base.fill((24, 24, 32))
    layer = pygame.Surface((pw, ph), pygame.SRCALPHA)
    font = pygame.font.SysFont("consolas", max(10, 8 + scale))
    font_sm = pygame.font.SysFont("consolas", max(8, 6 + scale))
    title = font.render("Fallout-style floor grid (8x4 char macro band)", True, (230, 230, 240))
    base.blit(title, (margin // 2, margin // 4))

    ox = margin
    oy = margin + title.get_height() + margin // 2

    def sx(x: float) -> int:
        return int(ox + x * scale)

    def sy(y: float) -> int:
        return int(oy + y * scale)

    cw = CELL_W * scale
    ch = CELL_H * scale
    local_diamond = set(fallout_tile_cells_local())

    # Macro band grid (8×4)
    macro_col = (80, 90, 110)
    for mx in range((cols + FALLOUT_TILE_W - 1) // FALLOUT_TILE_W + 1):
        x = sx(mx * FALLOUT_TILE_W * CELL_W)
        pygame.draw.line(base, macro_col, (x, oy), (x, oy + rows * CELL_H * scale), 1)
    for my in range((rows + FALLOUT_BAND_H - 1) // FALLOUT_BAND_H + 1):
        y = sy(my * FALLOUT_BAND_H * CELL_H)
        pygame.draw.line(base, macro_col, (ox, y), (ox + cols * CELL_W * scale, y), 1)

    if show_grid:
        for cx in range(cols + 1):
            x = sx(cx * CELL_W)
            pygame.draw.line(base, (40, 44, 56), (x, oy), (x, oy + rows * CELL_H * scale), 1)
        for cy in range(rows + 1):
            y = sy(cy * CELL_H)
            pygame.draw.line(base, (40, 44, 56), (ox, y), (ox + cols * CELL_W * scale, y), 1)

    # Glyphs from sketch
    for cy, row in enumerate(FALLOUT_SKETCH_ROWS):
        for cx, ch_g in enumerate(row):
            if ch_g == "_":
                continue
            cell = pygame.Surface((cw, ch), pygame.SRCALPHA)
            cell.fill(_fallout_letter_color(ch_g))
            text = font.render(ch_g, True, (245, 248, 240))
            cell.blit(text, (0, 0))
            layer.blit(cell, (sx(cx * CELL_W), sy(cy * CELL_H)))

    # Per-tile diamond outline + ear tint inside 8×3 bbox
    for my in range((rows + FALLOUT_BAND_H - 1) // FALLOUT_BAND_H):
        for mx in range((cols + FALLOUT_TILE_W - 1) // FALLOUT_TILE_W):
            bx = mx * FALLOUT_TILE_W
            by = my * FALLOUT_BAND_H
            if by + 2 >= rows:
                continue
            x0 = sx(bx * CELL_W)
            y0 = sy(by * CELL_H)
            pygame.draw.rect(
                base,
                (200, 180, 80),
                pygame.Rect(x0, y0, FALLOUT_TILE_W * cw, FALLOUT_ACTIVE_H * ch),
                max(1, scale // 2),
            )
            ear_block = pygame.Surface((cw, ch), pygame.SRCALPHA)
            ear_block.fill((220, 80, 60, 90))
            for dy in range(FALLOUT_ACTIVE_H):
                for dx in range(FALLOUT_TILE_W):
                    if (dx, dy) in local_diamond:
                        continue
                    layer.blit(ear_block, (x0 + dx * cw, y0 + dy * ch))
            verts = [
                (sx((bx + 4) * CELL_W), sy(by * CELL_H + ch * 0.5)),
                (sx(bx * CELL_W + cw * 0.5), sy((by + 1) * CELL_H)),
                (sx((bx + FALLOUT_TILE_W) * CELL_W - cw * 0.5), sy((by + 1) * CELL_H)),
                (sx((bx + 4) * CELL_W), sy((by + 3) * CELL_H - ch * 0.5)),
            ]
            pygame.draw.polygon(layer, (100, 210, 130, 200), verts, max(1, scale))

    base.blit(layer, (0, 0))

    m = fallout_grid_metrics()
    y = oy + rows * CELL_H * scale + margin // 2
    for line in (
        f"Pitch: {m.tile_pitch_char[0]}x{m.tile_pitch_char[1]} char  |  "
        f"tile bbox: {m.bbox_px[0]}x{m.bbox_px[1]} px ({FALLOUT_TILE_W}x{FALLOUT_ACTIVE_H} char)",
        f"Diamond fill: {m.active_cells_per_tile}/{m.bbox_cells_per_tile} cells  |  "
        f"ears in bbox: {m.ear_cells_in_bbox} ({m.ear_percent:.0f}%)",
        "rows 0-2 = one tile; row 3 = waist of next iso row (see dddd / jjjj bands)",
        "vs brick21 (2x1): Fallout tile ≈ 4x larger, classic iso diamond ASCII",
    ):
        base.blit(font_sm.render(line, True, (170, 175, 190)), (margin // 2, y))
        y += font_sm.get_height() + 2
    return base


def _render_panel(
    *,
    mode: FootprintMode,
    layout: str,
    show_grid: bool,
    show_labels: bool,
    scale: int,
    panel_w: int,
    panel_h: int,
    focus_wx: int,
    focus_wy: int,
    show_stencil: bool,
) -> tuple[pygame.Surface, FootprintMetrics]:
    projector = _projector_for_mode(mode)
    tiles = _layout_tiles(layout)
    anchors = _world_anchors(projector, tiles, focus_wx=focus_wx, focus_wy=focus_wy)

    bx0, by0, bx1, by1 = _collect_bounds(anchors, mode)
    content_w = bx1 - bx0
    content_h = by1 - by0

    margin = 20 * scale
    ox = bx0 - margin / scale
    oy = by0 - margin / scale

    def sx(x: float) -> int:
        return int((x - ox) * scale)

    def sy(y: float) -> int:
        return int((y - oy) * scale)

    def sdist(v: float) -> int:
        return max(1, int(v * scale))

    font_body = pygame.font.SysFont("consolas", 8 + scale)
    font_tag = pygame.font.SysFont("consolas", 7 + scale)
    font_stencil = pygame.font.SysFont("consolas", max(8, 6 + scale))

    focus_anchor: tuple[int, int] | None = None
    for wx, wy, ax, ay in anchors:
        if wx == focus_wx and wy == focus_wy:
            focus_anchor = (ax, ay)
            focus_ax, focus_ay = ax, ay
            break
    else:
        focus_ax = focus_ay = 0

    neighbor: tuple[int, int] | None = None
    for wx, wy, ax, ay in anchors:
        if (wx, wy) == (focus_wx + 1, focus_wy):
            neighbor = (ax, ay)
            break
    metrics = footprint_metrics(
        focus_ax,
        focus_ay,
        mode=mode,
        neighbor_anchor=neighbor,
        project_step_x=projector.step_x,
        project_step_y=projector.step_y,
    )

    diagram_w = int(content_w * scale + 2 * margin)
    diagram_h = int(content_h * scale + 2 * margin)
    pw = max(panel_w, diagram_w)
    ph = max(panel_h, diagram_h)

    base = pygame.Surface((pw, ph))
    base.fill((24, 24, 32))
    layer = pygame.Surface((pw, ph), pygame.SRCALPHA)

    if show_grid:
        cx_lo = int(bx0 // CELL_W) - 1
        cy_lo = int(by0 // CELL_H) - 1
        cx_hi = int(bx1 // CELL_W) + 2
        cy_hi = int(by1 // CELL_H) + 2
        grid_col = (40, 44, 56)
        for cx in range(cx_lo, cx_hi + 1):
            x = sx(cx * CELL_W)
            pygame.draw.line(base, grid_col, (x, 0), (x, ph), 1)
        for cy in range(cy_lo, cy_hi + 1):
            y = sy(cy * CELL_H)
            pygame.draw.line(base, grid_col, (0, y), (pw, y), 1)

    for tile_i, (wx, wy, ax, ay) in enumerate(anchors):
        *_, x0, y0, x1, y1 = iso_diamond_geom(ax, ay, mode=mode)
        if mode == "brick21":
            _blit_brick21_tile(
                layer,
                wx,
                wy,
                ax,
                ay,
                scale=scale,
                sx=sx,
                sy=sy,
                font=font_stencil,
                tile_index=tile_i,
            )
            continue
        bw, bh = int((x1 - x0) * scale), int((y1 - y0) * scale)
        if bw > 0 and bh > 0:
            bbox_s = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bbox_s.fill((240, 200, 60, 50))
            layer.blit(bbox_s, (sx(x0), sy(y0)))
        _blit_bbox_ears(layer, ax, ay, mode=mode, scale=scale, sx=sx, sy=sy)

    if show_stencil and focus_anchor is not None:
        fax, fay = focus_anchor
        _blit_mock_stencil(
            layer,
            fax,
            fay,
            mode=mode,
            scale=scale,
            sx=sx,
            sy=sy,
            font=font_stencil,
        )

    outline_w = max(1, scale)
    if mode != "brick21":
        for _wx, _wy, ax, ay in anchors:
            verts = [(sx(x), sy(y)) for x, y in _diamond_verts(ax, ay, mode)]
            pygame.draw.polygon(layer, (60, 160, 90, 170), verts)
            pygame.draw.polygon(layer, (120, 220, 140, 255), verts, outline_w)

    base.blit(layer, (0, 0))

    dot_r = max(2, scale + 1)
    for wx, wy, ax, ay in anchors:
        *_, x0, y0, x1, y1 = iso_diamond_geom(ax, ay, mode=mode)
        rect = pygame.Rect(sx(x0), sy(y0), sdist(x1 - x0), sdist(y1 - y0))
        if mode == "brick21":
            pygame.draw.rect(base, (200, 220, 120), rect, max(1, scale // 2))
        else:
            pygame.draw.rect(base, (200, 180, 80), rect, max(1, scale // 2))

        px, py, right, left, mid_y, top_y, *_ = iso_diamond_geom(ax, ay, mode=mode)
        tip = sx(px), sy(py)
        pygame.draw.circle(base, (255, 255, 80), tip, dot_r)
        pygame.draw.circle(base, (0, 0, 0), tip, dot_r, 1)

        if show_labels:
            label = font_body.render(f"({wx},{wy})", True, (230, 230, 240))
            lx = tip[0] - label.get_width() // 2
            ly = tip[1] + dot_r + 2
            if ly + label.get_height() < diagram_h:
                base.blit(label, (lx, ly))

        if show_labels and wx == focus_wx and wy == focus_wy and mode != "brick21":
            for name, pt in (
                ("tip", (px, py)),
                ("left", (left, mid_y)),
                ("right", (right, mid_y)),
                ("top", (px, top_y)),
            ):
                sp = sx(pt[0]), sy(pt[1])
                t = font_tag.render(name, True, (255, 220, 120))
                base.blit(t, (sp[0] + dot_r + 2, sp[1] - t.get_height() // 2))

    return base, metrics


def render_diagram(
    *,
    layout: str = "cross",
    show_grid: bool = True,
    show_labels: bool = True,
    scale: int = 3,
    footprint: FootprintMode | str = "current",
    show_stencil: bool = True,
) -> pygame.Surface:
    if scale < 1:
        raise ValueError("scale must be >= 1")

    focus_wx, focus_wy = 10, 10
    mode: FootprintMode
    if footprint == "compare":
        return render_comparison(
            layout=layout,
            show_grid=show_grid,
            show_labels=show_labels,
            scale=scale,
            show_stencil=show_stencil,
        )
    if footprint == "brick21" and layout == "brick_sketch":
        return _render_brick_sketch_panel(scale=scale, show_grid=show_grid)
    if layout == "fallout_sketch":
        return _render_fallout_sketch_panel(scale=scale, show_grid=show_grid)
    mode = footprint  # type: ignore[assignment]

    panel, metrics = _render_panel(
        mode=mode,
        layout=layout,
        show_grid=show_grid,
        show_labels=show_labels,
        scale=scale,
        panel_w=0,
        panel_h=0,
        focus_wx=focus_wx,
        focus_wy=focus_wy,
        show_stencil=show_stencil,
    )

    font_title = pygame.font.SysFont("consolas", 10 + scale)
    font_body = pygame.font.SysFont("consolas", 8 + scale)
    legend_entries = _legend_entries(mode, metrics)
    legend_pad = 10 * scale
    legend_gap = max(2, scale // 2)
    legend_w, legend_h = _measure_legend(
        legend_entries, font_title, font_body, legend_pad, legend_gap
    )

    margin = 20 * scale
    pw = max(panel.get_width(), legend_w)
    ph = panel.get_height() + legend_h + margin // 2
    out = pygame.Surface((pw, ph))
    out.fill((24, 24, 32))
    out.blit(panel, (0, 0))

    legend_y = panel.get_height() + legend_pad // 2
    pygame.draw.line(
        out,
        (60, 60, 70),
        (legend_pad, legend_y),
        (pw - legend_pad, legend_y),
        max(1, scale // 2),
    )
    y = legend_y + legend_pad // 2
    for i, (text, color) in enumerate(legend_entries):
        fnt = font_title if i == 0 else font_body
        surf = fnt.render(text, True, color)
        out.blit(surf, (legend_pad, y))
        y += surf.get_height() + legend_gap

    return out


def render_comparison(
    *,
    layout: str = "block",
    show_grid: bool = True,
    show_labels: bool = True,
    scale: int = 3,
    show_stencil: bool = True,
) -> pygame.Surface:
    """Side-by-side: current | brick21 | step11."""
    focus_wx, focus_wy = 10, 10
    modes: list[FootprintMode] = ["current", "brick21", "step11"]
    panels: list[pygame.Surface] = []
    all_metrics: list[FootprintMetrics] = []

    max_w = 0
    max_h = 0
    for mode in modes:
        panel, metrics = _render_panel(
            mode=mode,
            layout=layout,
            show_grid=show_grid,
            show_labels=show_labels and mode == "current",
            scale=scale,
            panel_w=max_w,
            panel_h=max_h,
            focus_wx=focus_wx,
            focus_wy=focus_wy,
            show_stencil=show_stencil,
        )
        panels.append(panel)
        all_metrics.append(metrics)
        max_w = max(max_w, panel.get_width())
        max_h = max(max_h, panel.get_height())

    gap = 8 * scale
    font_title = pygame.font.SysFont("consolas", 9 + scale)
    font_body = pygame.font.SysFont("consolas", 7 + scale)
    header_h = font_title.get_height() + gap // 2

    legend_pad = 10 * scale
    legend_gap = max(2, scale // 2)
    legend_blocks: list[list[tuple[str, tuple[int, int, int]]]] = [
        _legend_entries(m.mode, m) for m in all_metrics
    ]
    legend_w = legend_pad
    legend_h = legend_pad
    for entries in legend_blocks:
        lw, lh = _measure_legend(entries, font_title, font_body, legend_pad, legend_gap)
        legend_w = max(legend_w, lw)
        legend_h = max(legend_h, lh)

    total_w = 3 * max_w + 2 * gap
    content_h = header_h + max_h
    pw = max(total_w, legend_w)
    ph = content_h + legend_h + gap

    out = pygame.Surface((pw, ph))
    out.fill((24, 24, 32))

    for i, (panel, metrics) in enumerate(zip(panels, all_metrics, strict=True)):
        x0 = i * (max_w + gap)
        title = font_title.render(_mode_title(metrics.mode), True, (220, 220, 235))
        out.blit(title, (x0 + legend_pad // 2, 0))
        stats = font_body.render(
            f"bbox {metrics.geom_bbox_px[0]}x{metrics.geom_bbox_px[1]}  "
            f"ears {metrics.ear_percent:.0f}%  cells {metrics.footprint_cells}  "
            f"overlap {metrics.neighbor_overlap_cells}",
            True,
            (160, 165, 180),
        )
        out.blit(stats, (x0 + legend_pad // 2, title.get_height() + 2))
        out.blit(panel, (x0, header_h))

    legend_y = content_h + gap // 2
    pygame.draw.line(
        out,
        (60, 60, 70),
        (legend_pad, legend_y),
        (pw - legend_pad, legend_y),
        max(1, scale // 2),
    )
    y = legend_y + legend_pad // 2
    for entries in legend_blocks:
        for i, (text, color) in enumerate(entries):
            fnt = font_title if i == 0 else font_body
            surf = fnt.render(text, True, color)
            out.blit(surf, (legend_pad, y))
            y += surf.get_height() + legend_gap
        y += legend_gap

    return out


def print_footprint_metrics(
    anchor_cx: int,
    anchor_cy: int,
    *,
    neighbor_anchor: tuple[int, int] | None = None,
    project_step_x: int = ISO_STEP_X,
    project_step_y: int = ISO_STEP_Y,
) -> None:
    """Print metrics table for all footprint modes (stdout)."""
    print("Footprint comparison (focus tile anchor):")
    print(
        f"{'mode':<10} {'spacing':<12} {'vertex':<12} {'bbox':<12} "
        f"{'ears%':<8} {'cells':<6} {'overlap':<8}"
    )
    for mode in ("current", "compact", "step11", "brick21"):
        psx = 1 if mode == "step11" else project_step_x
        psy = 1 if mode == "step11" else project_step_y
        m = footprint_metrics(
            anchor_cx,
            anchor_cy,
            mode=mode,
            neighbor_anchor=neighbor_anchor,
            project_step_x=psx,
            project_step_y=psy,
        )
        print(
            f"{mode:<10} "
            f"{m.iso_spacing_px[0]}x{m.iso_spacing_px[1]:<7} "
            f"{m.vertex_aabb_px[0]}x{m.vertex_aabb_px[1]:<7} "
            f"{m.geom_bbox_px[0]}x{m.geom_bbox_px[1]:<7} "
            f"{m.ear_percent:5.1f}%  "
            f"{m.footprint_cells:<6} "
            f"{m.neighbor_overlap_cells!s:<8}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Draw iso tile diamond / bbox / ears diagram.")
    parser.add_argument(
        "--out",
        default=os.path.join(ROOT, "assets", "debug", "tile_diagram.png"),
        help="Output PNG path",
    )
    parser.add_argument(
        "--layout",
        choices=("single", "pair", "cross", "block", "brick_sketch", "fallout_sketch"),
        default="cross",
        help="Which world tiles to draw (default: cross around focus 10,10)",
    )
    parser.add_argument(
        "--footprint",
        choices=("current", "compact", "step11", "brick21", "compare"),
        default="current",
        help="Footprint: current | compact | brick21 (2x1 stagger) | step11 | compare",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=3,
        help="Pixel scale factor for diagram (default: 3)",
    )
    parser.add_argument("--no-grid", action="store_true", help="Hide char cell grid")
    parser.add_argument("--no-labels", action="store_true", help="Hide text labels")
    parser.add_argument("--no-stencil", action="store_true", help="Hide stencil mock on focus tile")
    args = parser.parse_args()

    init_paths(ROOT)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    try:
        if args.footprint == "compare":
            out_path = args.out
            if out_path.endswith(".png"):
                out_path = out_path.replace(".png", "_compare.png")
            else:
                out_path = out_path + "_compare.png"
        else:
            out_path = args.out

        projector = IsoProjector()
        focus_wx, focus_wy = 10, 10
        ax, ay = projector.world_to_screen(focus_wx, focus_wy, focus_wx=focus_wx, focus_wy=focus_wy)
        nax, nay = projector.world_to_screen(
            focus_wx + 1, focus_wy, focus_wx=focus_wx, focus_wy=focus_wy
        )
        print_footprint_metrics(ax, ay, neighbor_anchor=(nax, nay))
        if args.layout == "fallout_sketch":
            fm = fallout_grid_metrics()
            print(
                f"fallout: pitch {fm.tile_pitch_char[0]}x{fm.tile_pitch_char[1]} char, "
                f"bbox {fm.bbox_px[0]}x{fm.bbox_px[1]} px, "
                f"diamond {fm.active_cells_per_tile}/{fm.bbox_cells_per_tile} cells, "
                f"ears {fm.ear_percent:.0f}%"
            )

        surf = render_diagram(
            layout=args.layout if args.footprint != "compare" else "block",
            show_grid=not args.no_grid,
            show_labels=not args.no_labels,
            scale=max(1, args.scale),
            footprint=args.footprint,
            show_stencil=not args.no_stencil,
        )
        out_dir = os.path.dirname(os.path.abspath(out_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        pygame.image.save(surf, out_path)
        print(f"Wrote {out_path} ({surf.get_width()}x{surf.get_height()})")
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
