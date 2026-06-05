"""Build tile stencils from parameters (trees by height)."""
from __future__ import annotations

from functools import lru_cache

from src.render.tile_stencil import Glyph, TileStencil


def _lines_to_glyphs(lines: list[str], fg: tuple, bg: tuple) -> TileStencil:
    glyphs: list[Glyph] = []
    height = len(lines)
    for row, line in enumerate(lines):
        dy = row - (height - 1)
        width = len(line)
        for col, ch in enumerate(line):
            if ch == " ":
                continue
            dx = col - (width - 1) // 2
            glyphs.append(Glyph(dx, dy, ch))
    return TileStencil(glyphs=glyphs, default_fg=fg, default_bg=bg)


@lru_cache(maxsize=256)
def procedural_tree_canopy(variant: int, height_bucket: int, radius: int) -> TileStencil:
    h = max(2, min(4, height_bucket // 2 + 1))
    rows: list[str] = []
    for level in range(h):
        width = 2 + min(level + radius, 6) * 2
        pad = max(0, 4 - level)
        ch = "T" if variant % 2 == 0 else "Y"
        if level == 0 and width >= 3:
            inner = ch * max(1, width - 2)
            core = (" " + inner + " ")[:width]
        else:
            core = (ch * width)[:width]
        rows.append(" " * pad + core)
    fg = (70, 110, 70) if variant < 3 else (90, 90, 85)
    bg = (20, 35, 20)
    return _lines_to_glyphs(rows, fg, bg)


@lru_cache(maxsize=32)
def procedural_tree_trunk(thick: bool) -> TileStencil:
    if thick:
        lines = [" | ", "| |", "| |", " | "]
    else:
        lines = [" | ", " | ", " | "]
    return _lines_to_glyphs(lines, (90, 70, 50), (30, 25, 20))
