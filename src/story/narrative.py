"""Narrative flags and endings."""
from __future__ import annotations

ENDINGS = {
    "mercy": {
        "title": "Пепельный Рассвет",
        "lines": [
            "Элион отпускает искру Лиры.",
            "Пепел оседает мягко, как первый снег.",
            "На серой траве — зелёный росток.",
        ],
    },
    "kill": {
        "title": "Осколок в ладони",
        "lines": [
            "Элион забирает память силой.",
            "Сад молчит. Звёзды не возвращаются.",
            "Но он идёт дальше — один.",
        ],
    },
}


def pick_ending(world_state, battle_result: str) -> str:
    if battle_result == "spare" and world_state.spare_count >= 1:
        return "mercy"
    return "kill"
