"""Level editor palette tree (left panel)."""
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
from src.world.editor.state import LevelEditorState
from src.world.structures import load_structures


@dataclass
class _PaletteItem:
    item_id: str
    label: str
    kind: str


@dataclass
class _PaletteFolder:
    folder_id: str
    label: str
    items: tuple[_PaletteItem, ...]


@dataclass
class _Hit:
    kind: str
    rect: Rect
    folder_id: str | None = None
    item_id: str | None = None
    item_kind: str | None = None


def _build_palette() -> tuple[_PaletteFolder, ...]:
    structures = load_structures()
    biomes = load_biomes()
    floor_stencils: set[str] = set()
    for bid, b in biomes.items():
        floor_stencils.add(b.get("floor_stencil", "grass"))
        floor_stencils.add(f"floor_{bid}")
    floor_stencils.update({"grass", "grass_dense", "grass_sparse", "meadow", "road", "dirt"})

    return (
        _PaletteFolder(
            "tools",
            "Инструменты",
            (
                _PaletteItem("select", "Выделение", "tool"),
                _PaletteItem("paint", "Кисть", "tool"),
                _PaletteItem("erase", "Ластик", "tool"),
                _PaletteItem("road", "Дорога", "tool"),
            ),
        ),
        _PaletteFolder(
            "floor",
            "Пол",
            tuple(
                _PaletteItem(s, s, "stencil")
                for s in sorted(floor_stencils)
            ),
        ),
        _PaletteFolder(
            "structures",
            "Структуры",
            tuple(
                _PaletteItem(sid, sid.replace("_", " "), "structure")
                for sid in sorted(structures.keys())
            ),
        ),
        _PaletteFolder(
            "vegetation",
            "Растительность",
            (
                _PaletteItem("tree", "Дерево", "vegetation"),
            ),
        ),
        _PaletteFolder(
            "generators",
            "Генераторы",
            (
                _PaletteItem("gen_biome", "Заливка биома", "generator"),
                _PaletteItem("gen_trees", "Деревья (scatter)", "generator"),
                _PaletteItem("gen_bushes", "Кусты (scatter)", "generator"),
                _PaletteItem("gen_clearing", "Поляна 3×3", "generator"),
            ),
        ),
    )


class LevelPaletteTree:
    ROW_H = 22
    FOLDER_H = 24

    def __init__(self) -> None:
        self._folders = _build_palette()
        self._hits: list[_Hit] = []

    def handle_event(
        self,
        ev: pygame.event.Event,
        *,
        state: LevelEditorState,
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
            if hit.kind == "folder" and hit.folder_id:
                state.toggle_folder(hit.folder_id)
                return True
            if hit.kind == "item" and hit.item_id and hit.item_kind:
                state.apply_palette_item(hit.item_id, hit.item_kind)
                on_change()
                return True
        return rect.collide(mx, my)

    def draw(
        self,
        surf: pygame.Surface,
        *,
        state: LevelEditorState,
        rect: Rect,
        font: pygame.font.Font,
        small: pygame.font.Font,
    ) -> None:
        self._hits.clear()
        pygame.draw.rect(surf, COLOR_PANEL, (rect.x, rect.y, rect.w, rect.h))
        pygame.draw.line(
            surf, COLOR_BORDER, (rect.x + rect.w - 1, rect.y), (rect.x + rect.w - 1, rect.y + rect.h)
        )

        y = rect.y + 6
        surf.blit(font.render("Палитра", True, COLOR_ACCENT), (rect.x + 6, y))
        y += 22

        for folder in self._folders:
            expanded = folder.folder_id in state.expanded_folders
            arrow = "▼" if expanded else "▶"
            folder_rect = Rect(rect.x + 4, y, rect.w - 8, self.FOLDER_H)
            self._hits.append(_Hit("folder", folder_rect, folder_id=folder.folder_id))
            pygame.draw.rect(surf, COLOR_BTN, (folder_rect.x, folder_rect.y, folder_rect.w, folder_rect.h))
            surf.blit(
                small.render(f"{arrow} {folder.label}", True, COLOR_TEXT),
                (folder_rect.x + 4, folder_rect.y + 4),
            )
            y += self.FOLDER_H

            if not expanded:
                continue
            for item in folder.items:
                item_rect = Rect(rect.x + 12, y, rect.w - 16, self.ROW_H)
                active = (
                    (item.kind == "tool" and state.active_tool == item.item_id)
                    or (item.kind == "stencil" and state.active_stencil == item.item_id)
                    or (item.kind == "structure" and state.active_structure == item.item_id)
                    or (item.kind in ("vegetation", "generator") and state.active_tool == item.item_id)
                )
                self._hits.append(
                    _Hit(
                        "item",
                        item_rect,
                        item_id=item.item_id,
                        item_kind=item.kind,
                    )
                )
                bg = COLOR_BTN_ACTIVE if active else (40, 44, 58)
                pygame.draw.rect(surf, bg, (item_rect.x, item_rect.y, item_rect.w, item_rect.h))
                surf.blit(small.render(f"  {item.label}", True, COLOR_TEXT), (item_rect.x + 4, item_rect.y + 3))
                y += self.ROW_H
            y += 4

        if y < rect.y + rect.h - 40:
            surf.blit(small.render("инструмент", True, COLOR_DIM), (rect.x + 6, rect.y + rect.h - 32))
            surf.blit(
                small.render(state.active_tool, True, COLOR_TEXT),
                (rect.x + 6, rect.y + rect.h - 18),
            )
