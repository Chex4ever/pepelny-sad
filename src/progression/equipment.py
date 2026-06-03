"""Equipment slots."""
from __future__ import annotations

SLOTS = ["head", "amulet", "chest", "legs", "feet", "ring_l", "ring_r", "hand_l", "hand_r"]


class Equipment:
    def __init__(self):
        self.slots: dict[str, str | None] = {s: None for s in SLOTS}

    def equip(self, slot: str, item_id: str | None):
        if slot in self.slots:
            self.slots[slot] = item_id

    def get(self, slot: str) -> str | None:
        return self.slots.get(slot)

    def all_items(self) -> list[str]:
        return [i for i in self.slots.values() if i]
