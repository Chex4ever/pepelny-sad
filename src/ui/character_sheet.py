"""Character sheet UI."""
from __future__ import annotations

import pygame

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, COLOR_UI_BORDER
from src.data.art_loader import load_items
from src.progression.equipment import SLOTS
from src.render.screen_buffer import ScreenBuffer


class CharacterSheet:
    def __init__(self):
        self.open = False
        self.cursor = 0
        self.mode = "equip"  # equip | inventory

    def draw(self, buf: ScreenBuffer, profile):
        if not self.open:
            return
        w, h = 50, 30
        x, y = 5, 5
        buf.draw_box(x, y, w, h, "ЭЛИОН", fg=COLOR_UI_BORDER, bg=COLOR_UI_BG)
        buf.draw_text(x + 2, y + 2, f"HP {profile.hp}/{profile.max_hp()}", fg=COLOR_HIGHLIGHT)
        buf.draw_text(x + 2, y + 4, "Экипировка:", fg=COLOR_TEXT)
        items = load_items()
        for i, slot in enumerate(SLOTS):
            iid = profile.equipment.get(slot)
            name = items.get(iid, {}).get("name", "—") if iid else "—"
            fg = COLOR_HIGHLIGHT if self.mode == "equip" and i == self.cursor else COLOR_TEXT
            buf.draw_text(x + 4, y + 6 + i, f"{slot:8} {name[:20]}", fg=fg)
        buf.draw_text(x + 2, y + 17, "Инвентарь:", fg=COLOR_TEXT)
        for i, slot in enumerate(profile.inventory.slots[:8]):
            if slot.item_id:
                nm = items.get(slot.item_id, {}).get("name", slot.item_id)
                line = f"{nm} x{slot.count}"
            else:
                line = "—"
            fg = COLOR_HIGHLIGHT if self.mode == "inventory" and i == self.cursor else COLOR_TEXT
            buf.draw_text(x + 4, y + 19 + i, line[:30], fg=fg)
        buf.draw_text(x + 2, y + h - 2, "Tab/Esc  O-осмотр  Enter-equip", fg=COLOR_TEXT)

    def handle_input(self, inp, profile, examine_panel) -> bool:
        if not self.open:
            return False
        if inp.pressed(pygame.K_TAB) or inp.pressed(pygame.K_ESCAPE):
            self.open = False
            return True
        if inp.pressed(pygame.K_o):
            if self.mode == "equip":
                iid = profile.equipment.get(SLOTS[self.cursor])
                if iid:
                    examine_panel.show(load_items().get(iid, {}).get("art_id", iid))
            else:
                slot = profile.inventory.slots[self.cursor]
                if slot.item_id:
                    examine_panel.show(slot.item_id)
            return True
        if inp.any_pressed(pygame.K_UP, pygame.K_w):
            self.cursor = max(0, self.cursor - 1)
        if inp.any_pressed(pygame.K_DOWN, pygame.K_s):
            max_c = len(SLOTS) - 1 if self.mode == "equip" else 7
            self.cursor = min(max_c, self.cursor + 1)
        if inp.pressed(pygame.K_LEFT) or inp.pressed(pygame.K_a):
            self.mode = "equip"
            self.cursor = 0
        if inp.pressed(pygame.K_RIGHT) or inp.pressed(pygame.K_d):
            self.mode = "inventory"
            self.cursor = 0
        if inp.pressed(pygame.K_RETURN):
            if self.mode == "inventory":
                slot = profile.inventory.slots[self.cursor]
                if slot.item_id:
                    data = load_items().get(slot.item_id, {})
                    if data.get("type") == "equipment":
                        eslot = data.get("slot", "hand_r")
                        profile.equipment.equip(eslot, slot.item_id)
                        profile.inventory.remove(slot.item_id, 1)
                    elif data.get("type") == "module":
                        if profile.install_module(slot.item_id):
                            profile.inventory.remove(slot.item_id, 1)
        return True
