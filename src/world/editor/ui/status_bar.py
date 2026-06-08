"""Level editor bottom status bar."""
from __future__ import annotations

import pygame

from src.characters.tuner_ui import COLOR_BORDER, COLOR_DIM, COLOR_PANEL, COLOR_TEXT, Rect


class LevelStatusBar:
    def draw(
        self,
        surf: pygame.Surface,
        *,
        rect: Rect,
        lines: list[str],
        small: pygame.font.Font,
    ) -> None:
        pygame.draw.rect(surf, COLOR_PANEL, (rect.x, rect.y, rect.w, rect.h))
        pygame.draw.line(surf, COLOR_BORDER, (rect.x, rect.y), (rect.x + rect.w, rect.y))
        x = rect.x + 8
        y = rect.y + 8
        for line in lines[:3]:
            surf.blit(small.render(line, True, COLOR_TEXT), (x, y))
            y += 16
        if len(lines) > 3:
            surf.blit(small.render(lines[3], True, COLOR_DIM), (rect.x + 8, rect.y + rect.h - 20))
