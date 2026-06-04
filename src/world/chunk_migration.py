"""Migrate legacy single-char tiles to volumetric structures."""
from __future__ import annotations

from src.constants import CHUNK_SIZE
from src.data.art_loader import load_biomes
from src.world.tree_generator import place_tree_anchor


def migrate_legacy_tree_tiles(chunk, seed: int, world_map=None) -> int:
    """Replace floor char T with grass floor + tree anchor. Returns count migrated."""
    biomes = load_biomes()
    count = 0
    for ly in range(CHUNK_SIZE):
        for lx in range(CHUNK_SIZE):
            i = chunk.idx(lx, ly)
            if chunk.tiles[i] != "T":
                continue
            wx = chunk.cx * CHUNK_SIZE + lx
            wy = chunk.cy * CHUNK_SIZE + ly
            biome_id = chunk.dominant_biome
            biome = biomes.get(biome_id, biomes["meadow"])
            fg, bg = chunk.fg[i], chunk.bg[i]
            stencil = chunk.floor_stencils[i] if chunk.floor_stencils[i] != "tree" else "grass"
            chunk.set_floor(lx, ly, ".", fg=fg, bg=bg, stencil_id=stencil)
            chunk.cell_solids[i] = []
            place_tree_anchor(chunk, wx, wy, biome, seed, world_map=world_map)
            count += 1
    return count
