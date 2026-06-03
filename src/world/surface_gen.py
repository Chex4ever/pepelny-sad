"""Surface chunk generation."""
from __future__ import annotations

import random

from src.constants import CHUNK_SIZE, WORLD_RADIUS_CHUNKS
from src.data.art_loader import load_biomes
from src.world.chunk import Chunk
from src.world.noise import ValueNoise2D


def _biome_for(h: float, m: float) -> str:
    if h > 0.72:
        return "ridge"
    if m > 0.62:
        return "ashen_forest"
    if h < 0.35:
        return "ruins_edge"
    return "meadow"


def generate_chunk(cx: int, cy: int, seed: int) -> Chunk:
    chunk = Chunk(cx, cy)
    if abs(cx) > WORLD_RADIUS_CHUNKS or abs(cy) > WORLD_RADIUS_CHUNKS:
        for ly in range(CHUNK_SIZE):
            for lx in range(CHUNK_SIZE):
                chunk.set(lx, ly, "░", fg=(60, 60, 70), bg=(15, 15, 20))
        return chunk

    noise = ValueNoise2D(seed + cx * 991 + cy * 997)
    biomes = load_biomes()
    rng = random.Random(seed ^ (cx << 16) ^ cy)

    for ly in range(CHUNK_SIZE):
        for lx in range(CHUNK_SIZE):
            wx = cx * CHUNK_SIZE + lx
            wy = cy * CHUNK_SIZE + ly
            h = noise.noise(wx * 0.02, wy * 0.02)
            m = noise.noise(wx * 0.03 + 50, wy * 0.03 + 50)
            biome_id = _biome_for(h, m)
            biome = biomes[biome_id]
            chunk.biome = biome_id
            chunk.set(lx, ly, biome["floor"], fg=tuple(biome["fg"]), bg=tuple(biome["bg"]))
            roll = rng.random()
            if roll < biome.get("tree_chance", 0):
                chunk.set(lx, ly, "T", fg=(80, 100, 70), bg=tuple(biome["bg"]))
            elif roll < biome.get("herb_chance", 0) + biome.get("tree_chance", 0):
                chunk.set(lx, ly, "o", fg=(140, 160, 100), bg=tuple(biome["bg"]))
            elif roll < biome.get("fiber_chance", 0) + biome.get("herb_chance", 0) + biome.get("tree_chance", 0):
                chunk.set(lx, ly, "+", fg=(120, 110, 90), bg=tuple(biome["bg"]))
            elif roll < biome.get("shard_chance", 0) + biome.get("fiber_chance", 0) + biome.get("herb_chance", 0):
                chunk.set(lx, ly, "*", fg=(200, 200, 255), bg=tuple(biome["bg"]))

    if chunk.biome == "ashen_forest":
        if rng.random() < 0.35:
            lx, ly = rng.randint(4, CHUNK_SIZE - 5), rng.randint(4, CHUNK_SIZE - 5)
            chunk.set(lx, ly, "!", fg=(255, 120, 120), bg=(40, 20, 20))

    return chunk
