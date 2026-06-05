"""Global world state."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorldState:
    world_seed: int = 42
    layer: str = "surface"  # surface | dungeon
    spare_count: int = 0
    kill_count: int = 0
    companions: list[str] = field(default_factory=list)
    discovered_recipes: set = field(default_factory=set)
    scan_flags: set = field(default_factory=set)
    story_flags: set = field(default_factory=set)
    dungeon_graph: dict | None = None
    dungeon_entered: bool = False
    boss_cleared: bool = False
    turn_count: int = 0
    world_time_s: float = 0.0
    checkpoint: dict | None = None
    defeated_battles: set = field(default_factory=set)
    tutorial_step: int = 0

    def add_discovered_recipe(self, recipe_id: str):
        self.discovered_recipes.add(recipe_id)
