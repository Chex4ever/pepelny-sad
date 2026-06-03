"""Combat stats from equipment."""
from __future__ import annotations

from dataclasses import dataclass

from src.data.art_loader import load_items
from src.progression.equipment import Equipment


@dataclass
class CombatProfile:
    max_hp: int = 20
    armor: int = 0
    fight_damage: int = 4
    fight_mode: str = "blade"
    box_shape: str = "normal"
    soul_dash: bool = False
    lantern: bool = False
    extra_act: str | None = None


def build_combat_profile(equipment: Equipment) -> CombatProfile:
    profile = CombatProfile()
    items = load_items()
    for item_id in equipment.all_items():
        data = items.get(item_id, {})
        profile.max_hp += data.get("max_hp", 0)
        profile.armor += data.get("armor", 0)
        profile.fight_damage += data.get("fight_damage", 0)
        traits = data.get("combat_traits", {})
        if "fight_mode" in traits:
            profile.fight_mode = traits["fight_mode"]
        if "box_shape" in traits:
            profile.box_shape = traits["box_shape"]
        if traits.get("soul_dash"):
            profile.soul_dash = True
        if traits.get("lantern"):
            profile.lantern = True
        if "extra_act" in traits:
            profile.extra_act = traits["extra_act"]
    return profile
