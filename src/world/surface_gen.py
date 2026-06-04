"""Surface chunk generation."""
from __future__ import annotations

import random

from src.constants import CHUNK_SIZE, WORLD_RADIUS_CHUNKS
from src.data.art_loader import load_biomes
from src.world.biome_blend import blended_chance, blended_floor, sample_climate
from src.world.chunk import Chunk
from src.world.column import Solid
from src.world.surface_detail import maybe_bush, maybe_grass_overlay, pick_floor_stencil
from src.world.tree_generator import place_tree_anchor
from src.world.world_fields import init_world_fields

_tree_mask: set[tuple[int, int]] = set()


def _tree_suppressed(wx: int, wy: int) -> bool:
    return (wx, wy) in _tree_mask


def _mark_tree_area(wx: int, wy: int, radius: int = 2) -> None:
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            _tree_mask.add((wx + dx, wy + dy))


def sample_surface(world_map, wx: int, wy: int, seed: int, rng: random.Random) -> None:
    primary, secondary, blend, _weights = sample_climate(wx, wy)
    floor, fg, bg, _stencil = blended_floor(primary, secondary, blend)
    biome = load_biomes()[primary]
    stencil_id = pick_floor_stencil(primary, wx, wy, seed)

    cx, cy, lx, ly = world_map.world_to_chunk(wx, wy)
    chunk = world_map.chunks[(cx, cy)]
    chunk.set_floor(lx, ly, floor, fg=fg, bg=bg, stencil_id=stencil_id)
    chunk.biome_counts[primary] += 1

    overlay = maybe_grass_overlay(biome, wx, wy, seed)
    if overlay:
        chunk.add_solid(lx, ly, overlay)

    tree_chance = blended_chance(primary, secondary, blend, "tree_chance")
    if tree_chance > 0 and not _tree_suppressed(wx, wy) and rng.random() < tree_chance:
        place_tree_anchor(chunk, wx, wy, biome, seed, world_map=world_map)
        _mark_tree_area(wx, wy)
    elif rng.random() < blended_chance(primary, secondary, blend, "herb_chance"):
        chunk.add_solid(lx, ly, Solid(0.05, 0.15, blocks_movement=False, stencil_id="herb"))
    elif rng.random() < blended_chance(primary, secondary, blend, "fiber_chance"):
        chunk.set(lx, ly, "+", fg=fg, bg=bg)
    elif rng.random() < blended_chance(primary, secondary, blend, "shard_chance"):
        chunk.add_solid(lx, ly, Solid(0.1, 0.25, blocks_movement=False, stencil_id="shard"))

    maybe_bush(world_map, biome, wx, wy, seed)


def generate_chunk(cx: int, cy: int, seed: int, world_map=None) -> Chunk:
    global _tree_mask
    if cx == 0 and cy == 0:
        _tree_mask = set()
    init_world_fields(seed)

    chunk = Chunk(cx, cy)
    if abs(cx) > WORLD_RADIUS_CHUNKS or abs(cy) > WORLD_RADIUS_CHUNKS:
        for ly in range(CHUNK_SIZE):
            for lx in range(CHUNK_SIZE):
                chunk.set_floor(lx, ly, "░", fg=(60, 60, 70), bg=(15, 15, 20), stencil_id="wall")
        return chunk

    rng = random.Random(seed ^ (cx << 16) ^ cy)

    if world_map is not None:
        world_map.chunks[(cx, cy)] = chunk
        for ly in range(CHUNK_SIZE):
            for lx in range(CHUNK_SIZE):
                wx = cx * CHUNK_SIZE + lx
                wy = cy * CHUNK_SIZE + ly
                sample_surface(world_map, wx, wy, seed, rng)
    else:
        for ly in range(CHUNK_SIZE):
            for lx in range(CHUNK_SIZE):
                wx = cx * CHUNK_SIZE + lx
                wy = cy * CHUNK_SIZE + ly
                primary, secondary, blend, _ = sample_climate(wx, wy)
                floor, fg, bg, _ = blended_floor(primary, secondary, blend)
                stencil_id = pick_floor_stencil(primary, wx, wy, seed)
                chunk.set_floor(lx, ly, floor, fg=fg, bg=bg, stencil_id=stencil_id)
                chunk.biome_counts[primary] += 1

    if chunk.dominant_biome == "ashen_forest":
        if rng.random() < 0.35:
            lx, ly = rng.randint(4, CHUNK_SIZE - 5), rng.randint(4, CHUNK_SIZE - 5)
            chunk.set_floor(lx, ly, "!", fg=(255, 120, 120), bg=(40, 20, 20))

    return chunk
