"""Lighting controls panel for character editor."""
from __future__ import annotations

from typing import Callable

import pygame

from src.characters.editor_lighting import EditorLighting
from src.characters.tuner_ui import COLOR_ACCENT, COLOR_BORDER, COLOR_DIM, COLOR_PANEL, COLOR_TEXT, Rect

SLIDER_W = 90


class EditorLightingPanel:
    ROW_H = 18

    def __init__(self) -> None:
        self._hits: list[tuple[str, Rect]] = []
        self._drag: str | None = None

    def handle_event(
        self,
        ev: pygame.event.Event,
        *,
        lighting: EditorLighting,
        on_change: Callable[[], None],
        mx: int,
        my: int,
        rect: Rect,
    ) -> bool:
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self._drag = None
            return False

        if ev.type == pygame.MOUSEMOTION and self._drag:
            for kind, hit in self._hits:
                if kind != self._drag:
                    continue
                t = max(0.0, min(1.0, (mx - hit.x) / max(1, hit.w)))
                if kind == "ambient":
                    lighting.ambient = t
                elif kind == "light":
                    lighting.light = t
                on_change()
                return True

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for kind, hit in self._hits:
                if hit.collide(mx, my):
                    self._drag = kind
                    if kind == "ambient":
                        lighting.ambient = max(0.0, min(1.0, (mx - hit.x) / max(1, hit.w)))
                    elif kind == "light":
                        lighting.light = max(0.0, min(1.0, (mx - hit.x) / max(1, hit.w)))
                    on_change()
                    return True
        return rect.collide(mx, my)

    def draw(
        self,
        surf: pygame.Surface,
        *,
        lighting: EditorLighting,
        rect: Rect,
        small: pygame.font.Font,
    ) -> None:
        self._hits.clear()
        pygame.draw.rect(surf, COLOR_PANEL, (rect.x, rect.y, rect.w, rect.h))
        pygame.draw.line(surf, COLOR_BORDER, (rect.x, rect.y), (rect.x + rect.w, rect.y))

        y = rect.y + 4
        surf.blit(small.render("Свет", True, COLOR_ACCENT), (rect.x + 6, y))
        y += self.ROW_H

        surf.blit(small.render("Shift+WS elev  AD orbit", True, COLOR_DIM), (rect.x + 6, y))
        surf.blit(small.render(lighting.sun_label(), True, COLOR_TEXT), (rect.x + 6, y + 10))
        y += self.ROW_H + 4

        for label, kind, val in (
            ("ambient", "ambient", lighting.ambient),
            ("light", "light", lighting.light),
        ):
            surf.blit(small.render(label, True, COLOR_DIM), (rect.x + 6, y + 2))
            sr = Rect(rect.x + 58, y + 4, SLIDER_W, 8)
            pygame.draw.rect(surf, (30, 34, 48), (sr.x, sr.y, sr.w, sr.h), border_radius=2)
            knob = sr.x + int(val * sr.w)
            pygame.draw.rect(surf, COLOR_ACCENT, (knob - 2, sr.y - 1, 4, sr.h + 2), border_radius=1)
            self._hits.append((kind, Rect(sr.x, sr.y - 3, sr.w, sr.h + 6)))
            surf.blit(small.render(f"{val:.2f}", True, COLOR_TEXT), (sr.x + sr.w + 4, y))
            y += self.ROW_H
