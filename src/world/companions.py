"""Spared companion spawning."""
from __future__ import annotations

COMPANION_SERVICES = {
    "whisper_companion": "mobile_forge",
    "sorrow_companion": "shard_ping",
}


def spawn_companion(world_state, enemy_id: str, enemies_data: dict):
    enemy = enemies_data.get(enemy_id, {})
    cid = enemy.get("companion_id")
    if cid and cid not in world_state.companions:
        world_state.companions.append(cid)
        world_state.spare_count += 1


def companion_pos_for_player(px: int, py: int) -> tuple[int, int]:
    return px - 1, py


def has_service(companions: list[str], service: str) -> bool:
    for cid in companions:
        if COMPANION_SERVICES.get(cid) == service:
            return True
    return False
