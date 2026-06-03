"""Serialize / restore game state."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.progression.player_profile import PlayerProfile
from src.scenes.overworld.overworld_scene import OverworldScene
from src.world.world_map import WorldMap

if TYPE_CHECKING:
    from src.game import Game


class SaveService:
    @staticmethod
    def serialize(game: Game) -> dict:
        inv = [(s.item_id, s.count) for s in game.profile.inventory.slots]
        return {
            "world_seed": game.world_state.world_seed,
            "layer": game.world_state.layer,
            "spare_count": game.world_state.spare_count,
            "kill_count": game.world_state.kill_count,
            "companions": list(game.world_state.companions),
            "discovered_recipes": list(game.world_state.discovered_recipes),
            "scan_flags": list(game.world_state.scan_flags),
            "story_flags": list(game.world_state.story_flags),
            "turn_count": game.world_state.turn_count,
            "dungeon_entered": game.world_state.dungeon_entered,
            "boss_cleared": game.world_state.boss_cleared,
            "defeated_battles": list(game.world_state.defeated_battles),
            "dungeon_explored": list(game.world_map.dungeon_explored),
            "hp": game.profile.hp,
            "inventory": inv,
            "equipment": dict(game.profile.equipment.slots),
            "modules": list(game.profile.installed_modules),
            "player_pos": (
                (game.overworld.player.x, game.overworld.player.y) if game.overworld else (20, 24)
            ),
        }

    @staticmethod
    def restore(game: Game, data: dict) -> None:
        game.world_state.world_seed = data.get("world_seed", 42)
        game.world_state.layer = data.get("layer", "surface")
        game.world_state.spare_count = data.get("spare_count", 0)
        game.world_state.kill_count = data.get("kill_count", 0)
        game.world_state.companions = list(data.get("companions", []))
        game.world_state.discovered_recipes = set(data.get("discovered_recipes", []))
        game.world_state.scan_flags = set(data.get("scan_flags", []))
        game.world_state.story_flags = set(data.get("story_flags", []))
        game.world_state.turn_count = data.get("turn_count", 0)
        game.world_state.dungeon_entered = data.get("dungeon_entered", False)
        game.world_state.boss_cleared = data.get("boss_cleared", False)
        game.world_state.defeated_battles = set(tuple(x) for x in data.get("defeated_battles", []))
        game.world_map = WorldMap(game.world_state.world_seed)
        game.world_map.dungeon_explored = set(tuple(x) for x in data.get("dungeon_explored", []))
        game.profile = PlayerProfile()
        game.profile.hp = data.get("hp", 20)
        for i, (iid, cnt) in enumerate(data.get("inventory", [])):
            if iid and i < len(game.profile.inventory.slots):
                game.profile.inventory.slots[i].item_id = iid
                game.profile.inventory.slots[i].count = cnt
        for slot, iid in data.get("equipment", {}).items():
            game.profile.equipment.equip(slot, iid)
        game.profile.installed_modules = list(data.get("modules", []))
        game.profile.refresh_capacity()
        game.overworld = OverworldScene(game)
        px, py = data.get("player_pos", (20, 24))
        game.overworld.player.x, game.overworld.player.y = px, py
