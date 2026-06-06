"""Character sheet modal window — Diablo-style paper doll."""
from __future__ import annotations

import pygame

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, SCREEN_H, SCREEN_W
from src.data.art_loader import load_art, load_items
from src.progression.equipment import SLOTS
from src.world.tile_entities import resolve_inventory_item
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow

SLOT_LABELS = {
    "head": "голова",
    "amulet": "амулет",
    "chest": "грудь",
    "legs": "ноги",
    "feet": "ступни",
    "ring_l": "кольцо L",
    "ring_r": "кольцо R",
    "hand_l": "левая",
    "hand_r": "правая",
}

# (slot_name, x, y) relative to doll origin
SLOT_LAYOUT = [
    ("head", 12, 0),
    ("amulet", 12, 3),
    ("hand_l", 0, 8),
    ("chest", 12, 8),
    ("hand_r", 24, 8),
    ("ring_l", 0, 12),
    ("legs", 12, 12),
    ("ring_r", 24, 12),
    ("feet", 12, 16),
]

PORTRAIT_W = 22
PORTRAIT_LINES = 18


class CharacterSheetWindow(ModalWindow):
    name = "sheet"

    def __init__(self):
        w, h = 78, 40
        super().__init__("ЭЛИОН", x=(SCREEN_W - w) // 2, y=2, w=w, h=h, visible=False)
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
                    _, art_id = resolve_inventory_item(iid)
                    examine.show(art_id)
            else:
                slot = profile.inventory.slots[self.cursor]
                if slot.item_id:
                    _, art_id = resolve_inventory_item(slot.item_id)
                    examine.show(art_id)
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
                    data = load_items().get(slot.item_id)
                    if data and data.get("type") == "equipment":
                        eslot = data.get("slot", "hand_r")
                        profile.equipment.equip(eslot, slot.item_id)
                        profile.inventory.remove(slot.item_id, 1)
                        profile.sync_appearance_equipment()
                    elif data and data.get("type") == "module":
                        if profile.install_module(slot.item_id):
                            profile.inventory.remove(slot.item_id, 1)
        return True

    def _item_label(self, item_id: str | None, max_len: int = 8) -> str:
        if not item_id:
            return "—"
        name, _ = resolve_inventory_item(item_id)
        return name[:max_len]

    def _draw_slot(self, buf, cx, cy, slot, profile, selected: bool) -> None:
        iid = profile.equipment.get(slot)
        label = SLOT_LABELS.get(slot, slot)[:8]
        item = self._item_label(iid, 6)
        fg = COLOR_HIGHLIGHT if selected and self.mode == "equip" else COLOR_TEXT
        buf.draw_text(cx, cy, f"[{label}]", fg=fg, bg=COLOR_UI_BG)
        buf.draw_text(cx, cy + 1, item, fg=fg, bg=COLOR_UI_BG)

    def draw_content(self, buf: ScreenBuffer) -> None:
        profile = getattr(self, "_profile", None)
        if profile is None:
            return
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        items = load_items()
        buf.draw_text(cx + 1, cy, f"HP {profile.hp}/{profile.max_hp()}", fg=COLOR_HIGHLIGHT, bg=COLOR_UI_BG)

        doll_x = cx + 4
        doll_y = cy + 2
        entry = load_art("elion_portrait")
        for i, line in enumerate(entry.art[:PORTRAIT_LINES]):
            buf.draw_text(doll_x + 8, doll_y + 2 + i, line[:PORTRAIT_W], fg=COLOR_TEXT, bg=COLOR_UI_BG)

        for i, slot in enumerate(SLOTS):
            layout = next((entry for entry in SLOT_LAYOUT if entry[0] == slot), None)
            if not layout:
                continue
            _, sx, sy = layout
            selected = self.mode == "equip" and i == self.cursor
            self._draw_slot(buf, doll_x + sx, doll_y + sy, slot, profile, selected)

        inv_x = cx + 44
        inv_y = cy + 2
        buf.draw_text(inv_x, inv_y, "ИНВЕНТАРЬ", fg=COLOR_TEXT, bg=COLOR_UI_BG)
        for i, slot in enumerate(profile.inventory.slots[:8]):
            col, row = i % 4, i // 4
            bx, by = inv_x + col * 8, inv_y + 2 + row * 3
            if slot.item_id:
                nm = self._item_label(slot.item_id, 7)
                line = f"{nm}x{slot.count}"
            else:
                line = "· пусто"
            fg = COLOR_HIGHLIGHT if self.mode == "inventory" and i == self.cursor else COLOR_TEXT
            buf.draw_text(bx, by, line, fg=fg, bg=COLOR_UI_BG)

        buf.draw_text(cx + 1, cy + ch - 1, "Tab/Esc  O-осмотр  Enter-equip  ←→ режим", fg=COLOR_TEXT, bg=COLOR_UI_BG)

    def bind_profile(self, profile) -> None:
        self._profile = profile

    def draw(self, buf, profile=None):
        if profile is not None:
            self.bind_profile(profile)
        if not self.visible:
            return
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                buf.set_fog(x, y, level=1, alpha=140)
        super().draw(buf)
