"""Voice / speaker mapping for typewriter dialogue blips."""
from __future__ import annotations

import json
import os

from src.constants import DATA_DIR

_CACHE: dict | None = None


def _load() -> dict:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    path = os.path.join(DATA_DIR or "", "story", "voices.json")
    if not os.path.isfile(path):
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "voices.json")
    with open(path, encoding="utf-8") as f:
        _CACHE = json.load(f)
    return _CACHE


def default_voice() -> str:
    return _load().get("default_voice", "default")


def intro_voice() -> str:
    return _load().get("intro_voice", "elion")


def voice_for_dialogue(dialogue_id: str) -> str:
    voices = _load().get("dialogue_voices", {})
    return voices.get(dialogue_id, default_voice())
