"""Render ScreenBuffer to pygame surface with RGBA blending."""
from __future__ import annotations

import pygame

from src.constants import CELL_H, CELL_W, COLOR_BG
from src.render.screen_buffer import FOG_EXPLORED, FOG_UNEXPLORED


class AsciiRenderer:
    def __init__(self, screen: pygame.Surface, char_w=CELL_W, char_h=CELL_H):
        self.screen = screen
        self.char_w = char_w
        self.char_h = char_h
        self.font = pygame.font.SysFont("consolas,courier,cascadiamono", char_h)
        if self.font is None:
            self.font = pygame.font.Font(None, char_h + 4)
        self._cell = pygame.Surface((char_w, char_h), pygame.SRCALPHA)
        self._overlay = pygame.Surface((char_w, char_h), pygame.SRCALPHA)
        self._glyph_cache: dict[tuple, pygame.Surface] = {}

    def _tint(self, rgb: tuple[int, int, int], light: float) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(c * light))) for c in rgb)

    def _glyph(self, ch: str, fg: tuple[int, int, int], fg_a: int) -> pygame.Surface:
        key = (ch, fg, fg_a)
        surf = self._glyph_cache.get(key)
        if surf is None:
            surf = self.font.render(ch, True, (*fg, fg_a))
            self._glyph_cache[key] = surf
            if len(self._glyph_cache) > 4096:
                self._glyph_cache.clear()
        return surf

    def draw(self, buffer, global_alpha: int = 255):
        self.screen.fill(COLOR_BG)
        w, h = buffer.width, buffer.height
        for y in range(h):
            for x in range(w):
                i = y * w + x
                ch = buffer.chars[i]
                light = buffer.light[i]
                bg = self._tint(buffer.bg[i], light)
                bg_a = buffer.bg_a[i]
                px, py = x * self.char_w, y * self.char_h

                if ch == " " and buffer.fog[i] == 0 and bg_a >= 250:
                    continue

                if bg_a > 0:
                    self._cell.fill((*bg, min(255, int(bg_a * global_alpha / 255))))
                    self.screen.blit(self._cell, (px, py))

                if ch != " ":
                    fg = self._tint(buffer.fg[i], light)
                    fg_a = min(255, int(buffer.fg_a[i] * global_alpha / 255))
                    if fg_a > 0:
                        self.screen.blit(self._glyph(ch, fg, fg_a), (px, py))

                fog = buffer.fog[i]
                if fog != 0:
                    alpha = buffer.fog_a[i] if buffer.fog_a[i] else (220 if fog == FOG_UNEXPLORED else 80)
                    alpha = min(255, int(alpha * global_alpha / 255))
                    self._overlay.fill((0, 0, 0, alpha))
                    self.screen.blit(self._overlay, (px, py))

        pygame.display.flip()
