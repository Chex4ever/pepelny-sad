"""Craft station modal window."""
from __future__ import annotations

import pygame

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG
from src.data.art_loader import load_items, load_recipes
from src.progression.crafting import can_craft, craft, recipe_visible
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow


class CraftWindow(ModalWindow):
    name = "craft"

    def __init__(self):
        super().__init__("КРАФТ", x=28, y=8, w=44, h=26, visible=False)
        self.station = "forge"
        self.cursor = 0
        self.recipes: list[dict] = []

    def open_station(self, station: str) -> None:
        self.station = station
        titles = {"forge": "КУЗНЯ", "loom": "СТАНОК", "companion": "ШЁПОТ"}
        self.title = titles.get(station, "КРАФТ")
        self.cursor = 0
        self._refresh_list()
        self.show()

    def _refresh_list(self) -> None:
        all_r = load_recipes()
        self.recipes = [r for r in all_r if r.get("station") == self.station]

    def handle_keys(self, inp) -> bool:
        if not self.visible:
            return False
        if inp.pressed_escape():
            self.close()
            return True
        return False

    def draw_content(self, buf: ScreenBuffer) -> None:
        profile = getattr(self, "_profile", None)
        world_state = getattr(self, "_world_state", None)
        if profile is None or world_state is None:
            return
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
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
            buf.draw_text(cx + 1, cy + i, f"{name[:28]}", fg=fg, bg=COLOR_UI_BG)
        if visible:
            r = visible[min(self.cursor, len(visible) - 1)]
            buf.draw_text(cx + 1, cy + 12, "Ингредиенты:", fg=COLOR_TEXT, bg=COLOR_UI_BG)
            for j, ing in enumerate(r["ingredients"]):
                nm = items.get(ing["id"], {}).get("name", ing["id"])
                buf.draw_text(cx + 3, cy + 14 + j, f"{nm} x{ing['count']}", fg=COLOR_TEXT, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + ch - 1, "Enter-крафт  O-осмотр  Esc", fg=COLOR_TEXT, bg=COLOR_UI_BG)

    def handle_content_keys(self, inp, profile, world_state, examine, log, audio=None) -> bool:
        visible = [
            r
            for r in self.recipes
            if recipe_visible(r, world_state.discovered_recipes, world_state.scan_flags)
        ]
        if inp.nav_up_pressed():
            self.cursor = max(0, self.cursor - 1)
        if inp.nav_down_pressed():
            self.cursor = min(max(0, len(visible) - 1), self.cursor + 1)
        if inp.pressed(pygame.K_o) and visible:
            r = visible[min(self.cursor, len(visible) - 1)]
            examine.show(r["id"])
        if inp.pressed(pygame.K_RETURN) and visible:
            r = visible[min(self.cursor, len(visible) - 1)]
            result = craft(r["id"], profile.inventory, world_state.discovered_recipes, world_state.scan_flags)
            if result:
                log.add(f"Скрафчено: {load_items().get(result, {}).get('name', result)}")
                if audio:
                    audio.play_sfx("craft")
            else:
                log.add("Не хватает материалов.")
        return True

    def bind(self, profile, world_state) -> None:
        self._profile = profile
        self._world_state = world_state

    def draw(self, buf, profile=None, world_state=None, examine_panel=None):
        if profile is not None and world_state is not None:
            self.bind(profile, world_state)
        super().draw(buf)
