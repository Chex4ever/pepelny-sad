"""Map world tiles and biomes to footstep surface ids."""
from __future__ import annotations

from src.world.chunk import Chunk

TILE_OVERRIDE = {
    ".": "grass",
    ",": "dirt",
    ":": "gravel",
    "+": "stone",
    "=": "road",
    "~": "wood",
    "&": "wood",
    "#": "stone",
    "l": "stone",
    "i": "stone",
    ">": "stone",
    "<": "stone",
}

BIOME_SURFACE = {
    "meadow": "grass",
    "ashen_forest": "dirt",
    "ridge": "gravel",
    "ruins_edge": "stone",
}


def resolve_footstep(wx: int, wy: int, layer: str, world_map) -> str:
    ch, _, _ = world_map.get_tile(wx, wy, layer)
    if ch in TILE_OVERRIDE:
        return TILE_OVERRIDE[ch]
    if layer == "dungeon":
        return "stone"
    cx, cy, _, _ = world_map.world_to_chunk(wx, wy)
    chunk = world_map.chunks.get((cx, cy))
    if chunk is None:
        return "grass"
    return BIOME_SURFACE.get(chunk.biome, "grass")
