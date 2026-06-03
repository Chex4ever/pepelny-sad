"""Player inventory."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InvSlot:
    item_id: str | None = None
    count: int = 0


class Inventory:
    def __init__(self, capacity: int = 12):
        self.base_capacity = capacity
        self.slots: list[InvSlot] = [InvSlot() for _ in range(capacity)]

    @property
    def capacity(self) -> int:
        return len(self.slots)

    def set_capacity(self, n: int):
        while len(self.slots) < n:
            self.slots.append(InvSlot())
        if len(self.slots) > n:
            self.slots = self.slots[:n]

    def add(self, item_id: str, count: int = 1, stack_max: int = 99) -> int:
        remaining = count
        for slot in self.slots:
            if slot.item_id == item_id and slot.count < stack_max:
                space = stack_max - slot.count
                take = min(space, remaining)
                slot.count += take
                remaining -= take
                if remaining <= 0:
                    return 0
        while remaining > 0:
            empty = next((s for s in self.slots if s.item_id is None), None)
            if not empty:
                return remaining
            take = min(stack_max, remaining)
            empty.item_id = item_id
            empty.count = take
            remaining -= take
        return 0

    def remove(self, item_id: str, count: int = 1) -> bool:
        need = count
        for slot in self.slots:
            if slot.item_id == item_id:
                take = min(slot.count, need)
                slot.count -= take
                need -= take
                if slot.count <= 0:
                    slot.item_id = None
                    slot.count = 0
                if need <= 0:
                    return True
        return need <= 0

    def count(self, item_id: str) -> int:
        return sum(s.count for s in self.slots if s.item_id == item_id)

    def has(self, item_id: str, count: int = 1) -> bool:
        return self.count(item_id) >= count
