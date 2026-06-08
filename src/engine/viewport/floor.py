"""Draw packed floor glyphs onto a pygame surface."""
from __future__ import annotations

from typing import Callable, Protocol

import pygame

from src.engine.floor import FloorGlyphCell, floor_packed_draw_map
from src.engine.projection.packed import layout_cell_to_screen


class BrightnessFn(Protocol):
    def __call__(self, cx: float, cy: float, z: float) -> float: ...


class ShadeFn(Protocol):
    def __call__(
        self,
        fg: tuple[int, int, int],
        bg: tuple[int, int, int],
        brightness: float,
    ) -> tuple[tuple[int, int, int], tuple[int, int, int]]: ...


def draw_packed_floor_map(
    surf: pygame.Surface,
    draw_map: dict[tuple[int, int], FloorGlyphCell],
    *,
    ox: int,
    oy: int,
    cell_w: int,
    cell_h: int,
    font: pygame.font.Font,
    brightness_at: BrightnessFn | None = None,
    shade_from_brightness: ShadeFn | None = None,
    floor_shadow: set[tuple[int, int]] | None = None,
) -> None:
    """Draw pre-built packed layout map."""
    shadow = floor_shadow or set()
    for (col, row), cell in draw_map.items():
        lu, lv = layout_cell_to_screen(col, row)
        px = ox + lu * cell_w
        py = oy + lv * cell_h
        if brightness_at and shade_from_brightness:
            b = brightness_at(float(cell.cx), float(cell.cy), 0.0)
            if (cell.cx, cell.cy) in shadow:
                b *= 0.55
            fg, bg = shade_from_brightness(cell.fg, cell.bg, b)
        else:
            fg, bg = cell.fg, cell.bg
        rect = pygame.Rect(px, py, cell_w, cell_h)
        pygame.draw.rect(surf, bg, rect)
        if cell_w >= 4 and cell_h >= 6 and cell.ch.strip():
            surf.blit(font.render(cell.ch, True, fg), (px, py))


def draw_packed_floor(
    surf: pygame.Surface,
    *,
    feet_cx: int,
    feet_cy: int,
    ox: int,
    oy: int,
    cell_w: int,
    cell_h: int,
    font: pygame.font.Font,
    floor_seed: int = 0,
    brightness_at: BrightnessFn | None = None,
    shade_from_brightness: ShadeFn | None = None,
    floor_shadow: set[tuple[int, int]] | None = None,
) -> None:
    draw_map = floor_packed_draw_map(feet_cx, feet_cy, seed=floor_seed)
    shadow = floor_shadow or set()
    for (col, row), cell in draw_map.items():
        lu, lv = layout_cell_to_screen(col, row)
        px = ox + lu * cell_w
        py = oy + lv * cell_h
        if brightness_at and shade_from_brightness:
            b = brightness_at(float(cell.cx), float(cell.cy), 0.0)
            if (cell.cx, cell.cy) in shadow:
                b *= 0.55
            fg, bg = shade_from_brightness(cell.fg, cell.bg, b)
        else:
            fg, bg = cell.fg, cell.bg
        rect = pygame.Rect(px, py, cell_w, cell_h)
        pygame.draw.rect(surf, bg, rect)
        if cell_w >= 4 and cell_h >= 6 and cell.ch.strip():
            surf.blit(font.render(cell.ch, True, fg), (px, py))
