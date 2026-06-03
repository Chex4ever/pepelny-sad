"""Load JSON data and ASCII art."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache

from src import constants


def _data_dir() -> str:
    if constants.DATA_DIR is None:
        raise RuntimeError("init_paths() must be called before loading data")
    return constants.DATA_DIR


def _load_json(name: str):
    path = os.path.join(_data_dir(), name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_enemies():
    return _load_json("enemies.json")


@lru_cache(maxsize=1)
def load_items():
    return _load_json("items.json")


@lru_cache(maxsize=1)
def load_materials():
    return _load_json("materials.json")


@lru_cache(maxsize=1)
def load_recipes():
    return _load_json("recipes.json")


@lru_cache(maxsize=1)
def load_biomes():
    return _load_json("biomes.json")


@dataclass
class ArtEntry:
    art: list[str]
    examine_text: list[str]


@lru_cache(maxsize=128)
def load_art(art_id: str) -> ArtEntry:
    for sub in ("characters", "enemies", "items", "materials"):
        path = os.path.join(_data_dir(), "art", sub, f"{art_id}.txt")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                content = f.read()
            parts = content.split("---")
            art_lines = [ln.rstrip() for ln in parts[0].strip().splitlines() if ln.strip() or ln == ""]
            text_lines = []
            if len(parts) > 1:
                text_lines = [ln.strip() for ln in parts[1].strip().splitlines() if ln.strip()]
            return ArtEntry(art=art_lines[:12], examine_text=text_lines[:5])
    return ArtEntry(art=["  ?  ", " /|\\ ", " / \\ "], examine_text=[f"({art_id})"])
