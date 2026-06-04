"""Floor variants, grass overlays, bushes."""
from __future__ import annotations

import random

from src.data.art_loader import load_biomes
from src.world.column import Solid
from src.world.structures import place_structure
from src.world.world_fields import detail_noise


def _tile_rng(seed: int, wx: int, wy: int) -> random.Random:
    return random.Random(seed ^ (wx * 1013904223) ^ (wy * 1664525))


def pick_floor_stencil(biome_id: str, wx: int, wy: int, seed: int) -> str:
    biome = load_biomes()[biome_id]
    variants = biome.get("floor_variants") or [biome.get("stencil_id", "grass")]
    d = detail_noise(wx, wy)
    idx = int(d * len(variants)) % len(variants)
    return variants[idx]


def maybe_grass_overlay(biome: dict, wx: int, wy: int, seed: int) -> Solid | None:
    variants = biome.get("grass_overlay_variants")
    if not variants:
        return None
    rng = _tile_rng(seed, wx, wy)
    if rng.random() > biome.get("grass_overlay_chance", 0.12):
        return None
    vid = variants[int(detail_noise(wx, wy + 99) * len(variants)) % len(variants)]
    return Solid(
        0.02,
        0.18,
        blocks_movement=False,
        stencil_id=vid,
    )


def maybe_bush(world_map, biome: dict, wx: int, wy: int, seed: int) -> None:
    variants = biome.get("bush_variants")
    if not variants:
        return
    rng = _tile_rng(seed, wx, wy)
    if rng.random() > biome.get("bush_chance", 0.04):
        return
    sid = variants[rng.randint(0, len(variants) - 1)]
    place_structure(world_map, sid, wx, wy)
