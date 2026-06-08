"""Level editor inspector (right panel)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from src.characters.tuner_ui import (
    COLOR_ACCENT,
    COLOR_BORDER,
    COLOR_BTN,
    COLOR_BTN_ACTIVE,
    COLOR_DIM,
    COLOR_PANEL,
    COLOR_TEXT,
    Rect,
)
from src.data.art_loader import load_biomes
from src.world.editor.editable_world import EditableWorld
from src.world.editor.inspect import inspect_diag_tile
from src.world.editor.state import LevelEditorState


@dataclass
class _Hit:
    kind: str
    rect: Rect


class LevelInspectorPanel:
    ROW_H = 18
    BTN_H = 22

    def __init__(self) -> None:
        self._biome_ids = sorted(load_biomes().keys())
        self._biome_idx = self._biome_ids.index("meadow") if "meadow" in self._biome_ids else 0
        self._hits: list[_Hit] = []

    @property
    def biome_id(self) -> str:
        return self._biome_ids[self._biome_idx]

    def cycle_biome(self, delta: int) -> None:
        self._biome_idx = (self._biome_idx + delta) % len(self._biome_ids)

    def handle_event(
        self,
        ev: pygame.event.Event,
        *,
        state: LevelEditorState,
        world: EditableWorld,
        on_change: Callable[[], None],
        mx: int,
        my: int,
        rect: Rect,
    ) -> bool:
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for hit in self._hits:
                if not hit.rect.collide(mx, my):
                    continue
                if hit.kind == "goto_template":
                    if state.selected_wx is not None and state.selected_wy is not None:
                        info = inspect_diag_tile(world, state.selected_wx, state.selected_wy)
                        state.focus_tile_in_palette(stencil=str(info["template_id"]))
                        on_change()
                    return True
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_LEFT, pygame.K_a):
                self.cycle_biome(-1)
                state.active_biome = self.biome_id
                on_change()
                return True
            if ev.key in (pygame.K_RIGHT, pygame.K_d):
                self.cycle_biome(1)
                state.active_biome = self.biome_id
                on_change()
                return True
        return rect.collide(mx, my)

    def draw(
        self,
        surf: pygame.Surface,
        *,
        state: LevelEditorState,
        world: EditableWorld,
        rect: Rect,
        font: pygame.font.Font,
        small: pygame.font.Font,
    ) -> None:
        self._hits.clear()
        pygame.draw.rect(surf, COLOR_PANEL, (rect.x, rect.y, rect.w, rect.h))
        pygame.draw.line(surf, COLOR_BORDER, (rect.x, rect.y), (rect.x, rect.y + rect.h))

        y = rect.y + 8
        surf.blit(font.render("Свойства", True, COLOR_ACCENT), (rect.x + 8, y))
        y += 24

        lines = [
            f"инструмент: {state.active_tool}",
            f"stencil: {state.active_stencil}",
            f"структура: {state.active_structure}",
            f"биом: {self.biome_id}  (←/→)",
            f"seed: {world.seed}",
            f"patch: {world.bounds.width}×{world.bounds.height} diag tiles",
            f"карта: {state.map_path or '(новая)'}",
        ]
        for line in lines:
            surf.blit(small.render(line, True, COLOR_TEXT), (rect.x + 8, y))
            y += self.ROW_H

        y += 8
        surf.blit(font.render("Тайл", True, COLOR_ACCENT), (rect.x + 8, y))
        y += 22

        if state.selected_wx is None or state.selected_wy is None:
            surf.blit(small.render("клик — выделить тайл", True, COLOR_DIM), (rect.x + 8, y))
            return

        info = inspect_diag_tile(world, state.selected_wx, state.selected_wy)
        tile_lines = [
            f"wx,wy = {info['wx']}, {info['wy']}",
            f"diag tx,ty = {info['tile_tx']}, {info['tile_ty']}",
            f"шаблон: {info['template_id']}",
            f"char = {info['char']!r}",
        ]
        for line in tile_lines:
            surf.blit(small.render(line, True, COLOR_TEXT), (rect.x + 8, y))
            y += self.ROW_H

        y += 6
        btn = Rect(rect.x + 8, y, rect.w - 16, self.BTN_H)
        self._hits.append(_Hit("goto_template", btn))
        active = state.active_stencil == info["template_id"]
        pygame.draw.rect(surf, COLOR_BTN_ACTIVE if active else COLOR_BTN, (btn.x, btn.y, btn.w, btn.h))
        surf.blit(
            small.render("Перейти к объекту в палитре", True, COLOR_TEXT),
            (btn.x + 4, btn.y + 3),
        )
        y += self.BTN_H + 8

        if info["anchors"]:
            surf.blit(small.render("структуры на тайле:", True, COLOR_DIM), (rect.x + 8, y))
            y += self.ROW_H
            for anchor in info["anchors"]:
                surf.blit(
                    small.render(f"  {anchor['structure_id']}", True, COLOR_TEXT),
                    (rect.x + 8, y),
                )
                y += self.ROW_H
