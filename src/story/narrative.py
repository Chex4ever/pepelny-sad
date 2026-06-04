"""Narrative flags and endings."""
from __future__ import annotations

from src.i18n import t, t_list


def get_ending(ending_id: str) -> dict:
    return {
        "title": t(f"ending.{ending_id}.title"),
        "lines": t_list(f"ending.{ending_id}.lines"),
    }


class _EndingsAccessor:
    def __getitem__(self, item: str) -> dict:
        return get_ending(item)


ENDINGS = _EndingsAccessor()


def pick_ending(world_state, battle_result: str) -> str:
    if battle_result == "spare" and world_state.spare_count >= 1:
        return "mercy"
    return "kill"
