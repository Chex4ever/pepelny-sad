"""Player profile."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.progression.combat_profile import CombatProfile, build_combat_profile
from src.progression.equipment import Equipment
from src.progression.inventory import Inventory
from src.progression.modules import module_inventory_bonus


@dataclass
class PlayerProfile:
    hp: int = 20
    inventory: Inventory = field(default_factory=lambda: Inventory(12))
    equipment: Equipment = field(default_factory=Equipment)
    installed_modules: list[str] = field(default_factory=list)

    def refresh_capacity(self):
        bonus = module_inventory_bonus(self.installed_modules)
        self.inventory.set_capacity(12 + bonus)

    def combat_profile(self) -> CombatProfile:
        return build_combat_profile(self.equipment)

    def max_hp(self) -> int:
        return self.combat_profile().max_hp

    def heal(self, amount: int):
        self.hp = min(self.max_hp(), self.hp + amount)

    def install_module(self, item_id: str) -> bool:
        if item_id in self.installed_modules or len(self.installed_modules) >= 4:
            return False
        self.installed_modules.append(item_id)
        self.refresh_capacity()
        return True
