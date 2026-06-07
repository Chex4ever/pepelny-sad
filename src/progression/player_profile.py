"""Player profile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.constants import DEFAULT_PLAYER_HEIGHT_M
from src.progression.combat_profile import CombatProfile, build_combat_profile
from src.progression.equipment import Equipment
from src.progression.inventory import Inventory
from src.progression.modules import module_inventory_bonus

if TYPE_CHECKING:
    from src.characters.bake import CharacterPoseSet
    from src.characters.spec import CharacterSpec


@dataclass
class PlayerProfile:
    hp: int = 20
    body_height_m: float = DEFAULT_PLAYER_HEIGHT_M
    inventory: Inventory = field(default_factory=lambda: Inventory(12))
    equipment: Equipment = field(default_factory=Equipment)
    installed_modules: list[str] = field(default_factory=list)
    appearance: CharacterSpec | None = None
    _pose_cache: CharacterPoseSet | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.appearance is None:
            from src.characters.appearance import default_appearance

            self.appearance = default_appearance()

    def refresh_capacity(self):
        bonus = module_inventory_bonus(self.installed_modules)
        self.inventory.set_capacity(12 + bonus)

    def combat_profile(self) -> CombatProfile:
        return build_combat_profile(self.equipment)

    def max_hp(self) -> int:
        return self.combat_profile().max_hp()

    def heal(self, amount: int):
        self.hp = min(self.max_hp(), self.hp + amount)

    def install_module(self, item_id: str) -> bool:
        if item_id in self.installed_modules or len(self.installed_modules) >= 4:
            return False
        self.installed_modules.append(item_id)
        self.refresh_capacity()
        return True

    def sync_appearance_equipment(self) -> None:
        from src.characters.appearance import invalidate_appearance

        if self.appearance is None:
            return
        eq = {slot: self.equipment.get(slot) for slot in self.equipment.slots if self.equipment.get(slot)}
        self.appearance = self.appearance.__class__(
            race_id=self.appearance.race_id,
            seed=self.appearance.seed,
            age_years=self.appearance.age_years,
            sex=self.appearance.sex,
            equipment=eq,
        )
        invalidate_appearance(self)
