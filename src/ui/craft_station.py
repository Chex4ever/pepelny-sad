"""Craft station UI."""
from __future__ import annotations

import pygame

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, COLOR_UI_BORDER
from src.data.art_loader import load_items, load_recipes
from src.progression.crafting import can_craft, craft, recipe_visible
from src.render.screen_buffer import ScreenBuffer


class CraftStation:
    def __init__(self):
        self.open = False
        self.station = "forge"
        self.cursor = 0
        self.recipes: list[dict] = []

    def open_station(self, station: str):
        self.station = station
        self.open = True
        self.cursor = 0
        self._refresh_list()

    def _refresh_list(self):
        all_r = load_recipes()
        self.recipes = [r for r in all_r if r.get("station") == self.station]

    def draw(self, buf: ScreenBuffer, profile, world_state, examine_panel):
        if not self.open:
            return
        w, h = 44, 26
        x, y = 28, 8
        title = {"forge": "КУЗНЯ", "loom": "СТАНОК", "companion": "ШЁПОТ"}.get(self.station, "КРАФТ")
        buf.draw_box(x, y, w, h, title, fg=COLOR_UI_BORDER, bg=COLOR_UI_BG)
        items = load_items()
        visible = [
            r
            for r in self.recipes
            if recipe_visible(r, world_state.discovered_recipes, world_state.scan_flags)
        ]
        for i, recipe in enumerate(visible[:10]):
            ok = can_craft(recipe["id"], profile.inventory, world_state.discovered_recipes, world_state.scan_flags)
            name = items.get(recipe["id"], {}).get("name", recipe["id"])
            fg = COLOR_HIGHLIGHT if i == self.cursor else (COLOR_TEXT if ok else (100, 100, 100))
            buf.draw_text(x + 2, y + 2 + i, f"{name[:28]}", fg=fg)
        if visible:
            r = visible[min(self.cursor, len(visible) - 1)]
            buf.draw_text(x + 2, y + 14, "Ингредиенты:", fg=COLOR_TEXT)
            for j, ing in enumerate(r["ingredients"]):
                nm = items.get(ing["id"], {}).get("name", ing["id"])
                buf.draw_text(x + 4, y + 16 + j, f"{nm} x{ing['count']}", fg=COLOR_TEXT)
        buf.draw_text(x + 2, y + h - 2, "Enter-крафт  O-осмотр  Esc", fg=COLOR_TEXT)

    def handle_input(self, inp, profile, world_state, examine_panel, log) -> bool:
        if not self.open:
            return False
        if inp.pressed(pygame.K_ESCAPE):
            self.open = False
            return True
        visible = [
            r
            for r in self.recipes
            if recipe_visible(r, world_state.discovered_recipes, world_state.scan_flags)
        ]
        if inp.any_pressed(pygame.K_UP, pygame.K_w):
            self.cursor = max(0, self.cursor - 1)
        if inp.any_pressed(pygame.K_DOWN, pygame.K_s):
            self.cursor = min(max(0, len(visible) - 1), self.cursor + 1)
        if inp.pressed(pygame.K_o) and visible:
            r = visible[min(self.cursor, len(visible) - 1)]
            examine_panel.show(r["id"])
        if inp.pressed(pygame.K_RETURN) and visible:
            r = visible[min(self.cursor, len(visible) - 1)]
            result = craft(r["id"], profile.inventory, world_state.discovered_recipes, world_state.scan_flags)
            if result:
                log.add(f"Скрафчено: {load_items().get(result, {}).get('name', result)}")
            else:
                log.add("Не хватает материалов.")
        return True
