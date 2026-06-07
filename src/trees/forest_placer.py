"""Place trees on a tile grid using forest patch presets."""
from __future__ import annotations

import random
from dataclasses import dataclass

from src.trees.instance import TreeInstanceSpec, roll_tree_instance
from src.trees.loader import load_forest_patch
from src.trees.species import ForestPatchDef


@dataclass(frozen=True)
class ForestPlacement:
    wx: int
    wy: int
    instance: TreeInstanceSpec
    patch_id: str


def place_forest(
    patch_id: str,
    *,
    nx: int,
    ny: int,
    world_seed: int,
) -> list[ForestPlacement]:
    patch = load_forest_patch(patch_id)
    rng = random.Random(world_seed ^ 0xF0EE57)
    placements: list[ForestPlacement] = []

    cluster_centers: list[tuple[int, int]] = []
    n_clusters = max(1, int((nx * ny) ** 0.5 * patch.density * 0.35))
    for _ in range(n_clusters):
        cluster_centers.append((rng.randint(0, nx - 1), rng.randint(0, ny - 1)))

    for tx in range(nx):
        for ty in range(ny):
            tile_rng = random.Random(world_seed ^ (tx * 977 + ty * 131))
            local_density = patch.density
            for cx, cy in cluster_centers:
                dist = abs(tx - cx) + abs(ty - cy)
                if dist <= patch.cluster_radius:
                    local_density = min(0.95, local_density * (1.4 - dist / (patch.cluster_radius + 1)))
            if tile_rng.random() >= local_density:
                continue
            inst = roll_tree_instance(patch, world_seed=world_seed, wx=tx, wy=ty)
            placements.append(ForestPlacement(wx=tx, wy=ty, instance=inst, patch_id=patch_id))

    return placements


def place_forest_multi(
    patch_id: str,
    *,
    nx: int,
    ny: int,
    world_seed: int,
    max_trees: int | None = None,
) -> list[ForestPlacement]:
    out = place_forest(patch_id, nx=nx, ny=ny, world_seed=world_seed)
    if max_trees is not None and len(out) > max_trees:
        rng = random.Random(world_seed)
        rng.shuffle(out)
        return out[:max_trees]
    return out
