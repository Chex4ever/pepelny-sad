#!/usr/bin/env python3
"""Compare 2a (@@_/_@@) tessellation layouts: diagonal iso vs horizontal brick rows.

User sketches (horizontal, monitor axes):

  Pattern A — brick band (ASCII shorthand):
    aabb_
    -aabb
    ccdd_
    _ccdd
  => pitch x=2, band y=2; even bands ox=tx*2, odd bands ox=tx*2+1

  Pattern B — gap-free horizontal brick (same letters, vy=1 stagger):
    ox = tx*2 + (ty%2), oy = ty

  Pattern C — diagonal iso rows (ASCII wedge):
    __bb / aabbdd / _aaccdd / ____cc
  => world (wx,wy) tip at (wx-wy, wx+wy)

Run:
  python scripts/compare_2a_lattice.py
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Callable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.constants import init_paths

ISO32_PREVIEW = ("@@_", "_@@")
ISO32_CELLS: frozenset[tuple[int, int]] = frozenset(
    (x, y)
    for y, row in enumerate(ISO32_PREVIEW)
    for x, ch in enumerate(row)
    if ch == "@"
)
ISO32_TW = 3
ISO32_TH = 2
ISO32_TIP = (1, 1)


@dataclass(frozen=True)
class LayoutSpec:
    key: str
    title: str
    subtitle: str
    ascii_sketch: tuple[str, ...]


LAYOUTS: tuple[LayoutSpec, ...] = (
    LayoutSpec(
        "diag",
        "C) Diagonal iso (world 1,1)",
        "tip (wx-wy, wx+wy); shared seams, many bbox holes",
        ("__bb", "aabbdd", "_aaccdd", "____cc"),
    ),
    LayoutSpec(
        "horiz_band",
        "A) Horizontal band pitch 2x2",
        "aabb_ / -aabb — pitch 2x2; ears at band corners (4 holes per 2x2 patch)",
        ("aabb_", "-aabb", "ccdd_", "_ccdd"),
    ),
    LayoutSpec(
        "horiz_brick",
        "B) Horizontal brick pitch 2x1",
        "same stamp, vy=1 stagger — interior gap-free (seams OK)",
        ("aabb_", "-aabb", "ccdd_", "_ccdd"),
    ),
)


@dataclass(frozen=True)
class LatticeStats:
    name: str
    tiles: int
    blits: int
    gaps: int
    seams: int
    coverage_pct: float
    internal_gaps: int


def _tip_to_top_left(ax: int, ay: int) -> tuple[int, int]:
    return ax - ISO32_TIP[0], ay - ISO32_TIP[1]


def _origins_diag(n: int) -> list[tuple[int, int, int, int]]:
    out: list[tuple[int, int, int, int]] = []
    for wy in range(n):
        for wx in range(n):
            ax, ay = wx - wy, wx + wy
            ox, oy = _tip_to_top_left(ax, ay)
            out.append((wx, wy, ox, oy))
    return out


def _origins_horiz_band(nx: int, ny: int) -> list[tuple[int, int, int, int]]:
    """Pattern A: aabb_ / ccdd_ bands — ox=tx*2, oy=ty*2 (no band stagger).

    Leading '-' / '_' in ASCII is the diamond ear, not an extra origin shift.
    """
    out: list[tuple[int, int, int, int]] = []
    for ty in range(ny):
        for tx in range(nx):
            ox = tx * 2
            oy = ty * 2
            out.append((tx, ty, ox, oy))
    return out


def _origins_horiz_brick(nx: int, ny: int) -> list[tuple[int, int, int, int]]:
    """Pattern B: gap-free interior — ox=tx*2+(ty%2), oy=ty."""
    out: list[tuple[int, int, int, int]] = []
    for ty in range(ny):
        for tx in range(nx):
            ox = tx * 2 + (ty % 2)
            oy = ty
            out.append((tx, ty, ox, oy))
    return out


def _origin_fn(key: str) -> Callable[[int, int], list[tuple[int, int, int, int]]]:
    if key == "diag":
        return lambda nx, ny: _origins_diag(max(nx, ny))
    if key == "horiz_band":
        return _origins_horiz_band
    if key == "horiz_brick":
        return _origins_horiz_brick
    raise ValueError(key)


def _build_counts(origins: list[tuple[int, int, int, int]]) -> Counter:
    counts: Counter = Counter()
    for *_ids, ox, oy in origins:
        for dx, dy in ISO32_CELLS:
            counts[(ox + dx, oy + dy)] += 1
    return counts


def _bbox(counts: Counter) -> tuple[int, int, int, int]:
    xs = [k[0] for k in counts]
    ys = [k[1] for k in counts]
    return min(xs), min(ys), max(xs), max(ys)


def _analyze(name: str, origins: list[tuple[int, int, int, int]]) -> tuple[LatticeStats, Counter]:
    counts = _build_counts(origins)
    min_x, min_y, max_x, max_y = _bbox(counts)
    gaps = 0
    internal_gaps = 0
    seams = sum(1 for v in counts.values() if v > 1)
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            if counts[(x, y)] == 0:
                gaps += 1
                if min_x + 1 <= x <= max_x - 1 and min_y + 1 <= y <= max_y - 1:
                    internal_gaps += 1
    bbox_cells = (max_x - min_x + 1) * (max_y - min_y + 1)
    return (
        LatticeStats(
            name=name,
            tiles=len(origins),
            blits=sum(counts.values()),
            gaps=gaps,
            seams=seams,
            coverage_pct=100.0 * (bbox_cells - gaps) / bbox_cells if bbox_cells else 0.0,
            internal_gaps=internal_gaps,
        ),
        counts,
    )


def _draw_panel(
    *,
    spec: LayoutSpec,
    origins: list[tuple[int, int, int, int]],
    counts: Counter,
    stats: LatticeStats,
    cell_w: int,
    cell_h: int,
    scale: int,
) -> pygame.Surface:
    min_x, min_y, max_x, max_y = _bbox(counts)
    cw, ch = cell_w * scale, cell_h * scale
    pad = 10 * scale
    font_title = pygame.font.SysFont("consolas", 8 + scale)
    font_sm = pygame.font.SysFont("consolas", 6 + scale)
    font_cell = pygame.font.SysFont("consolas", max(6, cell_h * scale - 4))

    grid_w = (max_x - min_x + 1) * cw
    grid_h = (max_y - min_y + 1) * ch
    sketch_h = len(spec.ascii_sketch) * (font_sm.get_height() + 1) + 4
    title_h = font_title.get_height() + font_sm.get_height() + sketch_h + 8
    stats_h = font_sm.get_height() * 3 + 8
    pw = pad * 2 + grid_w
    ph = pad + title_h + grid_h + pad + stats_h

    surf = pygame.Surface((pw, ph))
    surf.fill((22, 24, 32))

    y = pad
    surf.blit(font_title.render(spec.title, True, (230, 235, 245)), (pad, y))
    y += font_title.get_height() + 2
    surf.blit(font_sm.render(spec.subtitle, True, (150, 160, 175)), (pad, y))
    y += font_sm.get_height() + 4
    for line in spec.ascii_sketch:
        surf.blit(font_sm.render(line, True, (120, 200, 140)), (pad, y))
        y += font_sm.get_height() + 1
    y += 4

    grid_ox, grid_oy = pad, y

    def px(cx: int) -> int:
        return grid_ox + (cx - min_x) * cw

    def py(cy: int) -> int:
        return grid_oy + (cy - min_y) * ch

    for cx in range(min_x, max_x + 2):
        x = px(cx)
        pygame.draw.line(surf, (45, 50, 62), (x, grid_oy), (x, grid_oy + grid_h), 1)
    for cy in range(min_y, max_y + 2):
        yy = py(cy)
        pygame.draw.line(surf, (45, 50, 62), (grid_ox, yy), (grid_ox + grid_w, yy), 1)

    gap_s = pygame.Surface((cw, ch), pygame.SRCALPHA)
    gap_s.fill((220, 55, 55, 190))
    seam_s = pygame.Surface((cw, ch), pygame.SRCALPHA)
    seam_s.fill((45, 160, 95, 210))
    fill_s = pygame.Surface((cw, ch), pygame.SRCALPHA)
    fill_s.fill((70, 110, 150, 220))

    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            n = counts[(x, y)]
            if n == 0:
                surf.blit(gap_s, (px(x), py(y)))
            elif n > 1:
                surf.blit(seam_s, (px(x), py(y)))
                t = font_cell.render("@", True, (12, 40, 24))
                surf.blit(t, (px(x), py(y)))
            else:
                surf.blit(fill_s, (px(x), py(y)))
                t = font_cell.render("@", True, (235, 240, 250))
                surf.blit(t, (px(x), py(y)))

    for tx, ty, ox, oy in origins:
        pygame.draw.rect(
            surf,
            (200, 180, 80),
            pygame.Rect(px(ox), py(oy), ISO32_TW * cw, ISO32_TH * ch),
            max(1, scale // 2),
        )

    y = grid_oy + grid_h + pad // 2
    for line in (
        f"tiles={stats.tiles} blits={stats.blits} gaps={stats.gaps} "
        f"(internal {stats.internal_gaps}) seams={stats.seams}",
        f"cover={stats.coverage_pct:.0f}%  red=hole green=shared seam",
    ):
        surf.blit(font_sm.render(line, True, (165, 170, 185)), (pad, y))
        y += font_sm.get_height() + 2
    return surf


def _draw_mini_patch(
    *,
    spec: LayoutSpec,
    origins: list[tuple[int, int, int, int]],
    counts: Counter,
    cell_w: int,
    cell_h: int,
    scale: int,
) -> pygame.Surface:
    """2x2 tile patch matching user ASCII scale."""
    min_x, min_y, max_x, max_y = _bbox(counts)
    cw, ch = cell_w * scale, cell_h * scale
    font = pygame.font.SysFont("consolas", 6 + scale)
    pad = 6 * scale
    pw = pad * 2 + (max_x - min_x + 1) * cw
    ph = pad + font.get_height() + 4 + (max_y - min_y + 1) * ch + pad
    s = pygame.Surface((pw, ph))
    s.fill((28, 30, 40))
    s.blit(font.render(spec.key, True, (190, 195, 210)), (pad, pad))
    y0 = pad + font.get_height() + 4

    def px(cx: int) -> int:
        return pad + (cx - min_x) * cw

    def py(cy: int) -> int:
        return y0 + (cy - min_y) * ch

    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            n = counts[(x, y)]
            col = (220, 55, 55) if n == 0 else ((45, 160, 95) if n > 1 else (70, 110, 150))
            pygame.draw.rect(s, col, pygame.Rect(px(x), py(y), cw, ch))
            chs = "." if n == 0 else "@"
            s.blit(font.render(chs, True, (240, 245, 250)), (px(x), py(y)))
    return s


def render_row(*, cell_w: int, cell_h: int, scale: int, nx: int, ny: int) -> pygame.Surface:
    panels: list[pygame.Surface] = []
    minis: list[pygame.Surface] = []
    pad = 10 * scale
    font_hdr = pygame.font.SysFont("consolas", 10 + scale)

    for spec in LAYOUTS:
        origins = _origin_fn(spec.key)(nx, ny)
        stats, counts = _analyze(spec.key, origins)
        panels.append(
            _draw_panel(
                spec=spec,
                origins=origins,
                counts=counts,
                stats=stats,
                cell_w=cell_w,
                cell_h=cell_h,
                scale=scale,
            )
        )
        mini_origins = _origin_fn(spec.key)(2, 2)
        mini_counts = _build_counts(mini_origins)
        minis.append(
            _draw_mini_patch(
                spec=spec,
                origins=mini_origins,
                counts=mini_counts,
                cell_w=cell_w,
                cell_h=cell_h,
                scale=max(2, scale),
            )
        )

    hdr = font_hdr.render(
        f"2a @@_/ _@@ — diagonal vs horizontal stitch  [{cell_w}x{cell_h} px/char]",
        True,
        (240, 242, 250),
    )
    row_w = sum(p.get_width() for p in panels) + pad * (len(panels) - 1)
    row_h = max(p.get_height() for p in panels)
    mini_w = sum(m.get_width() for m in minis) + pad * (len(minis) - 1)
    mini_h = max(m.get_height() for m in minis)
    lbl = pygame.font.SysFont("consolas", 7 + scale).render(
        "Mini 2x2 patch (same ASCII scale as your sketches)",
        True,
        (170, 175, 190),
    )
    pw = pad * 2 + max(row_w, mini_w)
    ph = pad + hdr.get_height() + pad + row_h + pad + lbl.get_height() + 4 + mini_h + pad
    out = pygame.Surface((pw, ph))
    out.fill((16, 18, 26))
    out.blit(hdr, (pad, pad))
    y = pad + hdr.get_height() + pad
    x = pad
    for p in panels:
        out.blit(p, (x, y))
        x += p.get_width() + pad
    y += row_h + pad
    out.blit(lbl, (pad, y))
    y += lbl.get_height() + 4
    x = pad
    for m in minis:
        out.blit(m, (x, y))
        x += m.get_width() + pad
    return out


def render_dual(*, scale: int, nx: int, ny: int) -> pygame.Surface:
    top = render_row(cell_w=5, cell_h=8, scale=scale, nx=nx, ny=ny)
    bot = render_row(cell_w=10, cell_h=16, scale=max(1, scale // 2), nx=nx, ny=ny)
    gap = 8 * scale
    out = pygame.Surface((max(top.get_width(), bot.get_width()), top.get_height() + gap + bot.get_height()))
    out.fill((16, 18, 26))
    out.blit(top, (0, 0))
    out.blit(bot, (0, top.get_height() + gap))
    return out


def print_stats(nx: int, ny: int) -> None:
    print(f"2a layouts ({nx}x{ny} tiles), stamp {ISO32_PREVIEW[0]} / {ISO32_PREVIEW[1]}")
    print(f"{'key':<14} {'gaps':>5} {'internal':>8} {'seams':>6} {'cover':>6}")
    for spec in LAYOUTS:
        stats, _ = _analyze(spec.key, _origin_fn(spec.key)(nx, ny))
        print(
            f"{spec.key:<14} {stats.gaps:5} {stats.internal_gaps:8} "
            f"{stats.seams:6} {stats.coverage_pct:5.0f}%"
        )
    print()
    print("horiz_brick: ox=tx*2+(ty%2), oy=ty  — removes interior holes")
    print("horiz_band:  ox=tx*2, oy=ty*2 — aabb_/ccdd_ sketch; diamond ears between bands")
    print("diag:        iso world step — seams + many internal holes in bbox")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare 2a diagonal vs horizontal tessellation.")
    parser.add_argument(
        "--out",
        default=os.path.join(ROOT, "assets", "debug", "tile_2a_lattice_compare.png"),
    )
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--nx", type=int, default=7)
    parser.add_argument("--ny", type=int, default=7)
    args = parser.parse_args()

    init_paths(ROOT)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    try:
        print_stats(args.nx, args.ny)
        surf = render_dual(scale=max(1, args.scale), nx=args.nx, ny=args.ny)
        out_dir = os.path.dirname(os.path.abspath(args.out))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        pygame.image.save(surf, args.out)
        print(f"Wrote {args.out} ({surf.get_width()}x{surf.get_height()})")
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
