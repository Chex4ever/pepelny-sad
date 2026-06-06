"""Generator / Character mode toggle bar."""
from __future__ import annotations

from typing import Callable, Literal

import pygame

from src.characters.tuner_ui import COLOR_ACCENT, COLOR_BTN, COLOR_BTN_ACTIVE, COLOR_PANEL, COLOR_TEXT, Rect

EditorMode = Literal["generator", "character"]


class EditorModeBar:
    def __init__(self) -> None:
        self._hits: list[Rect] = []

    def handle_event(
        self,
        ev: pygame.event.Event,
        *,
        mode: EditorMode,
        on_toggle: Callable[[], None],
        on_set: Callable[[EditorMode], None] | None = None,
        mx: int,
        my: int,
        rect: Rect,
    ) -> bool:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_m:
            on_toggle()
            return True
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for i, hit in enumerate(self._hits):
                if hit.collide(mx, my):
                    target: EditorMode = "generator" if i == 0 else "character"
                    if on_set and target != mode:
                        on_set(target)
                    elif target != mode:
                        on_toggle()
                    return True
        return False

    def draw(
        self,
        surf: pygame.Surface,
        *,
        mode: EditorMode,
        rect: Rect,
        small: pygame.font.Font,
    ) -> None:
        pygame.draw.rect(surf, COLOR_PANEL, (rect.x, rect.y, rect.w, rect.h))
        self._hits = []
        for i, (label, m) in enumerate((("GEN", "generator"), ("CHAR", "character"))):
            r = Rect(rect.x + 4 + i * 58, rect.y + 2, 52, 18)
            self._hits.append(r)
            active = mode == m
            pygame.draw.rect(surf, COLOR_BTN_ACTIVE if active else COLOR_BTN, (r.x, r.y, r.w, r.h), border_radius=2)
            surf.blit(small.render(label, True, COLOR_ACCENT if active else COLOR_TEXT), (r.x + 6, r.y + 2))
        surf.blit(small.render("M", True, (120, 125, 145)), (rect.x + rect.w - 18, rect.y + 3))
