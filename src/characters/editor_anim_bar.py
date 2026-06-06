"""Bottom animation control bar for character editor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pygame

from src.characters.anim import AnimPlayer
from src.characters.poses import FACINGS_8
from src.characters.tuner_ui import COLOR_ACCENT, COLOR_BTN, COLOR_BORDER, COLOR_DIM, COLOR_PANEL, COLOR_TEXT, Rect, _draw_btn

WALK_SPEED_MIN = 0.15
WALK_SPEED_MAX = 1.2
SPEED_SLIDER_W = 120


@dataclass
class HitTarget:
    kind: str
    rect: Rect
    meta: object = None


class EditorAnimBar:
    def __init__(self) -> None:
        self._hits: list[HitTarget] = []
        self._speed_drag = False
        self._speed_rect: Rect | None = None

    def handle_event(
        self,
        ev: pygame.event.Event,
        *,
        anim: AnimPlayer,
        on_change: Callable[[], None],
        mx: int,
        my: int,
        rect: Rect,
    ) -> bool:
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self._speed_drag:
                self._speed_drag = False
                return True

        if ev.type == pygame.MOUSEMOTION and self._speed_drag and self._speed_rect:
            self._apply_speed(mx, anim, on_change, self._speed_rect)
            return True

        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
            anim.toggle_pause()
            return True

        if not rect.collide(mx, my) and ev.type not in (pygame.KEYDOWN,):
            return False

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for hit in self._hits:
                if not hit.rect.collide(mx, my):
                    continue
                if hit.kind == "play_pause":
                    anim.toggle_pause()
                    return True
                if hit.kind == "walk_toggle":
                    anim.set_walking(not anim.walking)
                    if anim.walking:
                        anim.manual_phase = 0
                    on_change()
                    return True
                if hit.kind == "phase_prev":
                    anim.set_manual_phase((anim.walk_phase() - 1) % 3)
                    anim.paused = True
                    on_change()
                    return True
                if hit.kind == "phase_next":
                    anim.set_manual_phase((anim.walk_phase() + 1) % 3)
                    anim.paused = True
                    on_change()
                    return True
                if hit.kind == "facing":
                    anim.set_facing(str(hit.meta))
                    on_change()
                    return True
                if hit.kind == "speed_slider":
                    self._speed_drag = True
                    self._apply_speed(mx, anim, on_change, hit.rect)
                    return True

        return rect.collide(mx, my)

    def _apply_speed(self, mx: int, anim: AnimPlayer, on_change: Callable[[], None], rect: Rect) -> None:
        t = max(0.0, min(1.0, (mx - rect.x) / max(1, rect.w)))
        speed = WALK_SPEED_MIN + t * (WALK_SPEED_MAX - WALK_SPEED_MIN)
        if abs(anim.walk_period_s - speed) > 0.005:
            anim.walk_period_s = speed
            on_change()

    def draw(
        self,
        surf: pygame.Surface,
        *,
        anim: AnimPlayer,
        rect: Rect,
        font: pygame.font.Font,
        small: pygame.font.Font,
    ) -> None:
        self._hits.clear()
        pygame.draw.rect(surf, COLOR_PANEL, (rect.x, rect.y, rect.w, rect.h))
        pygame.draw.line(surf, COLOR_BORDER, (rect.x, rect.y + rect.h - 1), (rect.x + rect.w, rect.y + rect.h - 1))

        y = rect.y + 8
        x = rect.x + 8

        pause_lbl = "▶" if anim.paused else "⏸"
        r_pp = Rect(x, y, 28, 24)
        _draw_btn(surf, r_pp, pause_lbl, small, active=anim.paused)
        self._hits.append(HitTarget("play_pause", r_pp))
        x += 34

        walk_lbl = "WALK" if anim.walking else "IDLE"
        r_wk = Rect(x, y, 44, 24)
        _draw_btn(surf, r_wk, walk_lbl, small, active=anim.walking)
        self._hits.append(HitTarget("walk_toggle", r_wk))
        x += 50

        r_prev = Rect(x, y, 24, 24)
        r_next = Rect(x + 28, y, 24, 24)
        _draw_btn(surf, r_prev, "◀", small)
        _draw_btn(surf, r_next, "▶", small)
        self._hits.append(HitTarget("phase_prev", r_prev))
        self._hits.append(HitTarget("phase_next", r_next))
        phase = anim.walk_phase()
        surf.blit(small.render(f"phase {phase}/2", True, COLOR_TEXT), (x + 58, y + 5))
        x += 130

        surf.blit(small.render("speed", True, COLOR_DIM), (x, y + 5))
        slider = Rect(x + 42, y + 8, SPEED_SLIDER_W, 10)
        self._speed_rect = slider
        pygame.draw.rect(surf, (30, 34, 48), (slider.x, slider.y, slider.w, slider.h), border_radius=3)
        t = (anim.walk_period_s - WALK_SPEED_MIN) / (WALK_SPEED_MAX - WALK_SPEED_MIN)
        knob = slider.x + int(max(0.0, min(1.0, t)) * slider.w)
        pygame.draw.rect(surf, COLOR_ACCENT, (knob - 3, slider.y - 1, 6, slider.h + 2), border_radius=2)
        self._hits.append(HitTarget("speed_slider", Rect(slider.x, slider.y - 4, slider.w, slider.h + 8)))
        surf.blit(small.render(f"{anim.walk_period_s:.2f}s", True, COLOR_TEXT), (slider.x + slider.w + 6, y + 4))
        x += 42 + SPEED_SLIDER_W + 50

        surf.blit(small.render("facing", True, COLOR_DIM), (x, y + 5))
        fx = x + 44
        for f in FACINGS_8:
            r = Rect(fx, y, 28, 24)
            active = anim.facing == f
            _draw_btn(surf, r, f.upper(), small, active=active)
            self._hits.append(HitTarget("facing", r, meta=f))
            fx += 30

        hint = "Space=pause Z/X=facing A/S=frame LMB/RMB=edit"
        surf.blit(small.render(hint, True, COLOR_DIM), (rect.x + rect.w - 260, y + 6))
