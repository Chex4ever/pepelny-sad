"""Scatter species-aware voxel trees via forest patch presets."""
from __future__ import annotations

from src.prototype.dia_scale.tessellation import stamp_origin
from src.prototype.dia_scale.tree_voxel_gen import project_tree_to_solids
from src.prototype.dia_scale.world_grid import WorldGrid
from src.trees.adapters.voxel import spec_to_voxel_model
from src.trees.forest_placer import place_forest_multi


def generate_forest_trees(
    grid: WorldGrid,
    *,
    seed: int,
    nx: int,
    ny: int,
    patch_id: str = "young_mixed",
    max_trees: int | None = None,
) -> WorldGrid:
    placements = place_forest_multi(
        patch_id, nx=nx, ny=ny, world_seed=seed, max_trees=max_trees
    )
    species_counts: dict[str, int] = {}
    for placement in placements:
        ox, oy = stamp_origin(placement.wx, placement.wy)
        ax, ay = ox + 1, oy + 1
        model = spec_to_voxel_model(placement.instance, anchor_x=ax, anchor_y=ay)
        for solid in project_tree_to_solids(model):
            grid.add_solid(solid)
        sid = placement.instance.species_id
        species_counts[sid] = species_counts.get(sid, 0) + 1

    grid.meta["forest_patch"] = patch_id
    grid.meta["tree_count"] = len(placements)
    grid.meta["species_counts"] = species_counts
    return grid
