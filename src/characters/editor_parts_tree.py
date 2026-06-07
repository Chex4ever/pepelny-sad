"""Left panel: body part hierarchy with visibility modes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from src.characters.editor_state import EditorState
from src.characters.limb_legend import kind_color
from src.characters.voxel_kinds import kind_glyph
from src.characters.tuner_ui import COLOR_ACCENT, COLOR_BTN, COLOR_BTN_ACTIVE, COLOR_BORDER, COLOR_DIM, COLOR_PANEL, COLOR_TEXT, Rect

PART_TREE: tuple[tuple[str, str], ...] = (
    ("body_head", "голова"),
    ("body_torso", "торс"),
    ("body_arm_l", "рука L"),
    ("body_arm_r", "рука R"),
    ("body_leg_l", "нога L"),
    ("body_leg_r", "нога R"),
    ("hair", "волосы"),
    ("eye", "глаза"),
    ("feature", "детали"),
    ("weapon", "оружие"),
    ("armor_head", "шлем"),
    ("armor_chest", "броня"),
    ("armor_legs", "поножи"),
)


@dataclass
class _Hit:
    kind: str
    rect: Rect
    meta: object = None


class EditorPartsTree:
    ROW_H = 22

    def __init__(self) -> None:
        self._hits: list[_Hit] = []

    def handle_event(
        self,
        ev: pygame.event.Event,
        *,
        state: EditorState,
        on_change: Callable[[], None],
        mx: int,
        my: int,
        rect: Rect,
    ) -> bool:
        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return False
        for hit in self._hits:
            if not hit.rect.collide(mx, my):
                continue
            if hit.kind == "part":
                state.selected_kind = str(hit.meta)
                on_change()
                return True
            if hit.kind == "vis_all":
                state.visibility_mode = "all"
                on_change()
                return True
            if hit.kind == "vis_solo":
                state.visibility_mode = "solo"
                on_change()
                return True
            if hit.kind == "vis_hide":
                state.visibility_mode = "hide"
                on_change()
                return True
            if hit.kind == "clear_edits":
                state.clear_edits()
                on_change()
                return True
        return rect.collide(mx, my)

    def draw(
        self,
        surf: pygame.Surface,
        *,
        state: EditorState,
        rect: Rect,
        font: pygame.font.Font,
        small: pygame.font.Font,
    ) -> None:
        self._hits.clear()
        pygame.draw.rect(surf, COLOR_PANEL, (rect.x, rect.y, rect.w, rect.h))
        pygame.draw.line(surf, COLOR_BORDER, (rect.x + rect.w - 1, rect.y), (rect.x + rect.w - 1, rect.y + rect.h))

        y = rect.y + 6
        surf.blit(font.render("Части", True, COLOR_ACCENT), (rect.x + 6, y))
        y += 20

        for mode, label, kind in (
            ("all", "All", "vis_all"),
            ("solo", "Solo", "vis_solo"),
            ("hide", "Hide", "vis_hide"),
        ):
            r = Rect(rect.x + 6 + (0 if mode == "all" else 48 if mode == "solo" else 96), y, 44, 18)
            active = state.visibility_mode == mode  # type: ignore[comparison-overlap]
            pygame.draw.rect(surf, COLOR_BTN_ACTIVE if active else COLOR_BTN, (r.x, r.y, r.w, r.h), border_radius=2)
            surf.blit(small.render(label, True, COLOR_TEXT), (r.x + 6, r.y + 2))
            self._hits.append(_Hit(kind, r))
        y += 24

        for kind, label in PART_TREE:
            r = Rect(rect.x + 4, y, rect.w - 8, self.ROW_H)
            selected = state.selected_kind == kind
            fg, bg = kind_color(kind)
            sw = 14
            pygame.draw.rect(surf, bg if selected else (28, 32, 42), (r.x, r.y, r.w, r.h), border_radius=2)
            if selected:
                pygame.draw.rect(surf, COLOR_ACCENT, (r.x, r.y, r.w, r.h), 1, border_radius=2)
            pygame.draw.rect(surf, bg, (r.x + 4, r.y + 4, sw, sw - 2))
            glyph = kind_glyph(kind)
            surf.blit(small.render(glyph, True, fg), (r.x + 7, r.y + 3))
            surf.blit(small.render(label[:14], True, COLOR_TEXT if not selected else COLOR_ACCENT), (r.x + 22, r.y + 4))
            self._hits.append(_Hit("part", r, meta=kind))
            y += self.ROW_H + 1

        r_clr = Rect(rect.x + 6, rect.y + rect.h - 28, rect.w - 12, 22)
        pygame.draw.rect(surf, COLOR_BTN, (r_clr.x, r_clr.y, r_clr.w, r_clr.h), border_radius=2)
        surf.blit(small.render("Clear edits", True, COLOR_DIM), (r_clr.x + 4, r_clr.y + 4))
        self._hits.append(_Hit("clear_edits", r_clr))
