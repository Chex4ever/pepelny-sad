"""Build full dia_scale demo scenes."""
from __future__ import annotations

from src.prototype.dia_scale.constants import TREE_HEIGHT_TILES
from src.prototype.dia_scale.entity_gen import place_player
from src.prototype.dia_scale.forest_trees import generate_forest_trees
from src.prototype.dia_scale.meadow_gen import generate_meadow
from src.prototype.dia_scale.tessellation import stamp_origin
from src.prototype.dia_scale.tree_gen import generate_trees
from src.prototype.dia_scale.tree_voxel_gen import generate_voxel_tree, project_tree_to_solids
from src.prototype.dia_scale.world_grid import WorldGrid
from src.trees.instance import TreeInstanceSpec
from src.trees.adapters.voxel import spec_to_voxel_model
from src.trees.loader import load_species


def build_meadow_scene(
    *,
    seed: int,
    nx: int = 14,
    ny: int = 12,
    biome: str = "meadow",
    scatter_trees: bool = True,
    trees: bool | None = None,
    player: bool = True,
    forest_patch: str | None = "young_mixed",
    legacy_trees: bool = False,
) -> WorldGrid:
    if trees is not None:
        scatter_trees = trees
    grid = generate_meadow(seed=seed, nx=nx, ny=ny, biome=biome)
    if scatter_trees:
        if legacy_trees or forest_patch is None:
            generate_trees(grid, seed=seed, nx=nx, ny=ny)
        else:
            generate_forest_trees(grid, seed=seed, nx=nx, ny=ny, patch_id=forest_patch)
    if player:
        ptx, pty = nx // 2, ny // 2
        ox, oy = stamp_origin(ptx, pty)
        place_player(grid, feet_cx=ox + 1, feet_cy=oy + 1)
    return grid


def build_scene(**kwargs) -> WorldGrid:
    """Alias for meadow mode (backward compatible)."""
    return build_meadow_scene(**kwargs)


def build_tree_showcase(
    *,
    seed: int,
    nx: int = 8,
    ny: int = 8,
    tree_height: int = TREE_HEIGHT_TILES,
    species_id: str = "oak",
    age_years: float | None = None,
) -> tuple[WorldGrid, object]:
    grid = generate_meadow(seed=seed, nx=nx, ny=ny, biome="meadow")
    ptx, pty = nx // 2, ny // 2
    ox, oy = stamp_origin(ptx, pty)
    anchor_cx, anchor_cy = ox + 1, oy + 1
    species = load_species(species_id)
    age = age_years if age_years is not None else species.max_age_years * 0.55
    spec = TreeInstanceSpec(
        species_id=species_id,
        seed=seed,
        age_years=age,
        health=1.0,
        wx=anchor_cx,
        wy=anchor_cy,
    )
    model = spec_to_voxel_model(spec, anchor_x=anchor_cx, anchor_y=anchor_cy)
    for solid in project_tree_to_solids(model):
        grid.add_solid(solid)
    grid.meta["voxel_tree"] = {
        "height": model.max_z() + 1,
        "branches": model.branch_count,
        "voxels": len(model.voxels),
        "anchor": (anchor_cx, anchor_cy),
        "species_id": species_id,
        "age_years": age,
    }
    grid.meta["tree_model"] = model
    grid.meta["tree_spec"] = spec.to_dict()
    return grid, model


def build_character_showcase(
    *,
    seed: int,
    nx: int = 8,
    ny: int = 8,
    race_id: str = "human",
    age_years: float = 28,
    sex: str = "neutral",
    equipment: dict[str, str | None] | None = None,
    pose_id: str = "idle_s",
) -> tuple[WorldGrid, object, CharacterSpec]:
    from src.characters.bake import bake_voxel_model
    from src.characters.generate import generate_morphology
    from src.characters.spec import CharacterSpec

    grid = generate_meadow(seed=seed, nx=nx, ny=ny, biome="meadow", scatter_trees=False, player=False)
    ptx, pty = nx // 2, ny // 2
    ox, oy = stamp_origin(ptx, pty)
    anchor_cx, anchor_cy = ox + 1, oy + 1
    spec = CharacterSpec(
        race_id=race_id,
        seed=seed,
        age_years=age_years,
        sex=sex,
        equipment=equipment or {},
    )
    morph = generate_morphology(spec)
    model = bake_voxel_model(spec, pose_id=pose_id, anchor_x=anchor_cx, anchor_y=anchor_cy)
    place_player(grid, feet_cx=anchor_cx, feet_cy=anchor_cy, spec=spec, pose_id=pose_id)
    grid.meta["character_model"] = model
    grid.meta["character_spec"] = spec.to_dict()
    grid.meta["character_morph"] = {"height_m": morph.height_m, "race_id": morph.race_id}
    return grid, model, spec
