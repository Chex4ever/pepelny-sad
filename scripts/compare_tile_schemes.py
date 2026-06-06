#!/usr/bin/env python3
"""Compare floor tile stamp schemes at 5x8 and 10x16 char sizes.

Run:
  python scripts/compare_tile_schemes.py
  python scripts/compare_tile_schemes.py --out assets/debug/tile_schemes_compare.png
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.constants import MAP_VIEW_H, MAP_VIEW_W, init_paths
from src.render.fallout_footprint import fallout_tile_cells_local
from src.render.iso_footprint import iso_footprint_cells

VIEW_CHARS_W = MAP_VIEW_W
VIEW_CHARS_H = MAP_VIEW_H

# Relative (dx, dy) filled cells; anchor at stamp origin (0,0) top-left of tight bbox unless noted.


@dataclass(frozen=True)
class TileScheme:
    id: str
    title: str
    cells: frozenset[tuple[int, int]]
    # Optional ASCII preview rows (for label); '@' = fill
    preview: tuple[str, ...] = ()
    note: str = ""


def _cells_from_preview(rows: tuple[str, ...], ch: str = "@") -> frozenset[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == ch:
                out.add((x, y))
    return frozenset(out)


def _current_iso_cells() -> frozenset[tuple[int, int]]:
    anchor = (50, 22)
    return frozenset(
        (cx - anchor[0], cy - anchor[1]) for cx, cy in iso_footprint_cells(*anchor)
    )


def _schemes() -> list[TileScheme]:
    fallout_prev = (
        "__@@@@__",
        "@@@@@@@@",
        "__@@@@__",
    )
    iso32_prev = ("@@_", "_@@")
    return [
        TileScheme(
            "1a",
            "Fallout 8x3",
            frozenset(fallout_tile_cells_local()),
            fallout_prev,
            "hex / Fallout floor romb",
        ),
        TileScheme(
            "2a",
            "Iso square 3x2",
            _cells_from_preview(iso32_prev),
            iso32_prev,
            "square-grid iso diamond",
        ),
        TileScheme(
            "2b",
            "Current iso (ISO_STEP)",
            _current_iso_cells(),
            (),
            "10 char cells, 4x3 tight; old GPU 5x4 bbox",
        ),
        TileScheme(
            "3a",
            "Brick 2x1",
            frozenset({(0, 0), (1, 0)}),
            ("@@",),
            "stagger rows +1 char",
        ),
        TileScheme(
            "3b",
            "Plain 1x1",
            frozenset({(0, 0)}),
            ("@",),
            "top-down cell",
        ),
        TileScheme(
            "2c",
            "GPU bbox (old 2b)",
            _current_iso_cells(),
            (),
            "same shape; yellow = rect 5x4 ears if filled",
        ),
    ]


@dataclass(frozen=True)
class SchemeMetrics:
    scheme_id: str
    cell_w: int
    cell_h: int
    blits_per_stamp: int
    tight_w: int
    tight_h: int
    tight_px_w: int
    tight_px_h: int
    rect_w: int
    rect_h: int
    rect_px_w: int
    rect_px_h: int
    ear_cells: int
    meadow_5x5_blits: int
    meadow_5x5_px: int
    view_stamps_x: int
    view_stamps_y: int
    view_blits: int
    view_px_w: int
    view_px_h: int


def _tight_bounds(cells: frozenset[tuple[int, int]]) -> tuple[int, int, int, int]:
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def _metrics(scheme: TileScheme, cell_w: int, cell_h: int) -> SchemeMetrics:
    x0, y0, x1, y1 = _tight_bounds(scheme.cells)
    tw, th = x1 - x0, y1 - y0
    rect_cells = tw * th
    ear = rect_cells - len(scheme.cells)
    # Meadow: 5x5 stamps on pitch = tight size (touching tiles)
    pitch_x, pitch_y = tw, th
    nx = ny = 5
    meadow_blits = len(scheme.cells) * nx * ny
    meadow_px = (nx * pitch_x * cell_w) * (ny * pitch_y * cell_h)
    sx = max(1, VIEW_CHARS_W // pitch_x)
    sy = max(1, VIEW_CHARS_H // pitch_y)
    view_blits = len(scheme.cells) * sx * sy
    view_px_w = VIEW_CHARS_W * cell_w
    view_px_h = VIEW_CHARS_H * cell_h
    return SchemeMetrics(
        scheme_id=scheme.id,
        cell_w=cell_w,
        cell_h=cell_h,
        blits_per_stamp=len(scheme.cells),
        tight_w=tw,
        tight_h=th,
        tight_px_w=tw * cell_w,
        tight_px_h=th * cell_h,
        rect_w=tw,
        rect_h=th,
        rect_px_w=tw * cell_w,
        rect_px_h=th * cell_h,
        ear_cells=ear,
        meadow_5x5_blits=meadow_blits,
        meadow_5x5_px=meadow_px,
        view_stamps_x=sx,
        view_stamps_y=sy,
        view_blits=view_blits,
        view_px_w=view_px_w,
        view_px_h=view_px_h,
    )


def _gpu_bbox_cells_2b() -> frozenset[tuple[int, int]]:
    """5x4 char geom bbox relative to current iso anchor region."""
    out: set[tuple[int, int]] = set()
    for dx in range(-2, 3):
        for dy in range(-1, 3):
            out.add((dx, dy))
    return frozenset(out)


def _scheme_color(sid: str) -> tuple[int, int, int, int]:
    palette = {
        "1a": (70, 120, 80, 230),
        "2a": (80, 100, 140, 230),
        "2b": (120, 90, 70, 230),
        "3a": (90, 75, 110, 230),
        "3b": (60, 60, 70, 230),
        "2c": (120, 90, 70, 120),
    }
    return palette.get(sid, (100, 100, 100, 230))


def _draw_stamp_mosaic(
    surf: pygame.Surface,
    ox: int,
    oy: int,
    scheme: TileScheme,
    *,
    cell_w: int,
    cell_h: int,
    scale: int,
    tiles_x: int = 3,
    tiles_y: int = 2,
    show_gpu_ears: bool = False,
) -> None:
    x0, y0, x1, y1 = _tight_bounds(scheme.cells)
    tw, th = x1 - x0, y1 - y0
    cw, ch = cell_w * scale, cell_h * scale
    font = pygame.font.SysFont("consolas", max(6, cell_h * scale - 2))
    fill = _scheme_color(scheme.id)

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            base_x = ox + tx * tw * cw
            base_y = oy + ty * th * ch
            if show_gpu_ears:
                ears = _gpu_bbox_cells_2b()
                ear_s = pygame.Surface((cw, ch), pygame.SRCALPHA)
                ear_s.fill((220, 80, 60, 100))
                for (dx, dy) in ears:
                    if (dx, dy) in scheme.cells:
                        continue
                    px = base_x + (dx - x0) * cw
                    py = base_y + (dy - y0) * ch
                    surf.blit(ear_s, (px, py))
                pygame.draw.rect(
                    surf,
                    (200, 180, 80),
                    pygame.Rect(base_x, base_y, tw * cw, th * ch),
                    max(1, scale),
                )
            for (dx, dy) in scheme.cells:
                cell = pygame.Surface((cw, ch), pygame.SRCALPHA)
                cell.fill(fill)
                ch_str = "@" if not scheme.preview else _preview_char(scheme, dx - x0, dy - y0)
                text = font.render(ch_str, True, (240, 245, 235))
                cell.blit(text, (0, 0))
                surf.blit(cell, (base_x + (dx - x0) * cw, base_y + (dy - y0) * ch))
            pygame.draw.rect(
                surf,
                (120, 130, 150),
                pygame.Rect(base_x, base_y, tw * cw, th * ch),
                max(1, scale // 2),
            )


def _preview_char(scheme: TileScheme, lx: int, ly: int) -> str:
    if not scheme.preview:
        return "@"
    if ly < len(scheme.preview) and lx < len(scheme.preview[ly]):
        c = scheme.preview[ly][lx]
        return c if c != " " else "@"
    return "@"


def _draw_single_stamp(
    surf: pygame.Surface,
    ox: int,
    oy: int,
    scheme: TileScheme,
    *,
    cell_w: int,
    cell_h: int,
    scale: int,
) -> None:
    _draw_stamp_mosaic(
        surf, ox, oy, scheme, cell_w=cell_w, cell_h=cell_h, scale=scale, tiles_x=1, tiles_y=1
    )


def render_comparison(*, scale: int = 2) -> pygame.Surface:
    schemes = _schemes()
    cell_sizes = ((5, 8, "5x8"), (10, 16, "10x16"))
    font_title = pygame.font.SysFont("consolas", 12 + scale)
    font_body = pygame.font.SysFont("consolas", 8 + scale)
    font_sm = pygame.font.SysFont("consolas", 7 + scale)

    pad = 12 * scale
    col_w = 220 * scale
    row_h = 130 * scale
    table_h = 28 * scale + len(schemes) * (font_sm.get_height() + 4)
    pw = pad * 2 + len(cell_sizes) * col_w + (len(cell_sizes) - 1) * pad
    ph = pad + font_title.get_height() + pad + len(schemes) * row_h + table_h + pad

    out = pygame.Surface((pw, ph))
    out.fill((20, 22, 30))

    title = font_title.render("Tile schemes: filled cells only (no bbox undercoat)", True, (235, 235, 245))
    out.blit(title, (pad, pad))
    y0 = pad + title.get_height() + pad

    for row_i, scheme in enumerate(schemes):
        row_y = y0 + row_i * row_h
        label = font_body.render(f"{scheme.id}) {scheme.title}", True, (220, 225, 235))
        out.blit(label, (pad, row_y))
        sub = font_sm.render(scheme.note, True, (150, 155, 170))
        out.blit(sub, (pad, row_y + label.get_height() + 2))

        for col_i, (cw, ch, size_label) in enumerate(cell_sizes):
            col_x = pad + col_i * (col_w + pad)
            hdr = font_sm.render(size_label, True, (180, 185, 200))
            out.blit(hdr, (col_x, row_y))
            mosaic_y = row_y + hdr.get_height() + 4
            show_ears = scheme.id == "2c"
            _draw_stamp_mosaic(
                out,
                col_x,
                mosaic_y,
                scheme,
                cell_w=cw,
                cell_h=ch,
                scale=scale,
                tiles_x=3 if scheme.id != "3b" else 4,
                tiles_y=2,
                show_gpu_ears=show_ears,
            )
            m = _metrics(scheme, cw, ch)
            info = font_sm.render(
                f"blit/stamp={m.blits_per_stamp}  tight={m.tight_px_w}x{m.tight_px_h}px",
                True,
                (160, 165, 180),
            )
            out.blit(info, (col_x, mosaic_y + 2 * m.tight_px_h * scale + 4))

    # Table
    ty = y0 + len(schemes) * row_h + pad // 2
    pygame.draw.line(out, (60, 65, 80), (pad, ty), (pw - pad, ty), 1)
    ty += pad // 2
    hdr = font_body.render("Metrics (per stamp / 5x5 meadow patch)", True, (200, 205, 220))
    out.blit(hdr, (pad, ty))
    ty += hdr.get_height() + 6

    for size_i, (cw, ch, size_label) in enumerate(cell_sizes):
        lines = [
            f"[{size_label}] id blit/stamp tight_px ear view_blits view_px({VIEW_CHARS_W}x{VIEW_CHARS_H}ch)",
        ]
        for scheme in schemes:
            m = _metrics(scheme, cw, ch)
            ear = m.ear_cells if scheme.id != "2c" else len(_gpu_bbox_cells_2b()) - m.blits_per_stamp
            lines.append(
                f"  {scheme.id:3} {m.blits_per_stamp:4} {m.tight_px_w:3}x{m.tight_px_h:<3} {ear:3} "
                f"{m.view_blits:5} {m.view_px_w}x{m.view_px_h}"
            )
        lines.append("  ear=rect-fill waste; view_blits=stamps covering 100x44 char viewport")
        for line in lines:
            out.blit(font_sm.render(line, True, (170, 175, 190)), (pad, ty))
            ty += font_sm.get_height() + 2
        ty += 6

    return out


def print_metrics_table() -> None:
    schemes = _schemes()
    print("Tile scheme comparison (filled cells only rendering)")
    print()
    for cw, ch, label in ((5, 8, "5x8"), (10, 16, "10x16")):
        print(f"=== CELL {label} ({cw}x{ch} px) ===")
        print(
            f"{'id':<4} {'title':<22} {'blit':>5} {'tight':>7} {'stamp px':>10} "
            f"{'ear':>4} {'view blits':>10} {'view px':>12} {'stamps':>8}"
        )
        for s in schemes:
            m = _metrics(s, cw, ch)
            ear = m.ear_cells
            if s.id == "2c":
                ear = len(_gpu_bbox_cells_2b()) - m.blits_per_stamp
            print(
                f"{s.id:<4} {s.title:<22} {m.blits_per_stamp:5} "
                f"{m.tight_w}x{m.tight_h} {m.tight_px_w:4}x{m.tight_px_h:<4} "
                f"{ear:4} {m.view_blits:10} {m.view_px_w:4}x{m.view_px_h:<4} "
                f"{m.view_stamps_x}x{m.view_stamps_y}"
            )
        print(f"  viewport = {VIEW_CHARS_W}x{VIEW_CHARS_H} char cells (MAP_VIEW); filled cells only")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare 6 floor tile stamp schemes.")
    parser.add_argument(
        "--out",
        default=os.path.join(ROOT, "assets", "debug", "tile_schemes_compare.png"),
    )
    parser.add_argument("--scale", type=int, default=2, help="Pixel scale (default 2)")
    args = parser.parse_args()

    init_paths(ROOT)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    try:
        print_metrics_table()
        surf = render_comparison(scale=max(1, args.scale))
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
