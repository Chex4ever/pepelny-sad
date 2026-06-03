"""Character sheet modal window."""
from __future__ import annotations

import pygame

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG
from src.data.art_loader import load_items
from src.progression.equipment import SLOTS
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow


class CharacterSheetWindow(ModalWindow):
    name = "sheet"

    def __init__(self):
        super().__init__("ЭЛИОН", x=5, y=5, w=50, h=30, visible=False)
        self.cursor = 0
        self.mode = "equip"

    def handle_keys(self, inp) -> bool:
        if not self.visible:
            return False
        if inp.pressed_tab() or inp.pressed_escape():
            self.close()
            return True
        return False

    def handle_content_keys(self, inp, profile, examine) -> bool:
        if inp.pressed(pygame.K_o):
            if self.mode == "equip":
                iid = profile.equipment.get(SLOTS[self.cursor])
                if iid:
                    examine.show(load_items().get(iid, {}).get("art_id", iid))
            else:
                slot = profile.inventory.slots[self.cursor]
                if slot.item_id:
                    examine.show(slot.item_id)
            return True
        if inp.nav_up_pressed():
            self.cursor = max(0, self.cursor - 1)
        if inp.nav_down_pressed():
            max_c = len(SLOTS) - 1 if self.mode == "equip" else 7
            self.cursor = min(max_c, self.cursor + 1)
        if inp.nav_left_pressed():
            self.mode = "equip"
            self.cursor = 0
        if inp.nav_right_pressed():
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

    def draw_content(self, buf: ScreenBuffer) -> None:
        profile = getattr(self, "_profile", None)
        if profile is None:
            return
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        items = load_items()
        buf.draw_text(cx + 1, cy, f"HP {profile.hp}/{profile.max_hp()}", fg=COLOR_HIGHLIGHT, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + 2, "Экипировка:", fg=COLOR_TEXT, bg=COLOR_UI_BG)
        for i, slot in enumerate(SLOTS):
            iid = profile.equipment.get(slot)
            name = items.get(iid, {}).get("name", "—") if iid else "—"
            fg = COLOR_HIGHLIGHT if self.mode == "equip" and i == self.cursor else COLOR_TEXT
            buf.draw_text(cx + 3, cy + 4 + i, f"{slot:8} {name[:20]}", fg=fg, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + 15, "Инвентарь:", fg=COLOR_TEXT, bg=COLOR_UI_BG)
        for i, slot in enumerate(profile.inventory.slots[:8]):
            if slot.item_id:
                nm = items.get(slot.item_id, {}).get("name", slot.item_id)
                line = f"{nm} x{slot.count}"
            else:
                line = "—"
            fg = COLOR_HIGHLIGHT if self.mode == "inventory" and i == self.cursor else COLOR_TEXT
            buf.draw_text(cx + 3, cy + 17 + i, line[:30], fg=fg, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + ch - 1, "Tab/Esc  O-осмотр  Enter-equip", fg=COLOR_TEXT, bg=COLOR_UI_BG)

    def handle_input(self, inp, profile, examine_panel) -> bool:
        if not self.visible:
            return False
        if self.handle_keys(inp):
            return True
        self.handle_content_keys(inp, profile, examine_panel)
        return True

    def bind_profile(self, profile) -> None:
        self._profile = profile

    def draw(self, buf, profile=None):
        if profile is not None:
            self.bind_profile(profile)
        super().draw(buf)
