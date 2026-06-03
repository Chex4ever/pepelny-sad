"""Render ScreenBuffer to pygame surface."""
from __future__ import annotations

import pygame

from src.constants import CELL_H, CELL_W, COLOR_BG


class AsciiRenderer:
    def __init__(self, screen: pygame.Surface, char_w=CELL_W, char_h=CELL_H):
        self.screen = screen
        self.char_w = char_w
        self.char_h = char_h
        self.font = pygame.font.SysFont("consolas,courier,cascadiamono", char_h)
        if self.font is None:
            self.font = pygame.font.Font(None, char_h + 4)

    def draw(self, buffer):
        self.screen.fill(COLOR_BG)
        w, h = buffer.width, buffer.height
        for y in range(h):
            for x in range(w):
                i = y * w + x
                ch = buffer.chars[i]
                if ch == " ":
                    continue
                fg = buffer.fg[i]
                bg = buffer.bg[i]
                light = buffer.light[i]
                fg = tuple(max(0, min(255, int(c * light))) for c in fg)
                bg = tuple(max(0, min(255, int(c * light))) for c in bg)
                surf = self.font.render(ch, True, fg, bg)
                self.screen.blit(surf, (x * self.char_w, y * self.char_h))
        pygame.display.flip()
