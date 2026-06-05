"""Regression: bake_all_tree_solids must not mutate chunks during iteration."""
from __future__ import annotations

from src.world.surface_gen import generate_chunk_isolated
from src.world.tree_generator import tree_anchor
from src.world.world_fields import init_world_fields
from src.world.world_map import WorldMap


def test_bake_all_tree_solids_cross_chunk_tree():
    seed = 4242
    init_world_fields(seed)
    wm = WorldMap.__new__(WorldMap)
    wm.seed = seed
    wm.perf_stats = None
    wm._column_cache = None
    wm.chunks = {}
    wm.dungeon_tiles = {}
    wm.dungeon_explored = set()
    wm._landmarks_applied = False
    wm._chunk_gen_queue = []
    wm._chunks_per_frame = 2

    chunk = generate_chunk_isolated(0, 0, seed)
    biome = {"id": "meadow", "tree_density": 0.5}
    anchor = tree_anchor(60, 60, biome, seed)
    chunk.structure_anchors.append(anchor)
    wm.chunks[(0, 0)] = chunk

    wm.bake_all_tree_solids()
    assert len(wm.chunks) >= 1
