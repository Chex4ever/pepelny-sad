"""Project character voxels to dia_scale GridEntity."""
from __future__ import annotations

from src.characters.loader import load_palette
from src.prototype.dia_scale.constants import COLOR_PLAYER_BG, COLOR_PLAYER_FG
from src.prototype.dia_scale.world_grid import GridEntity, WorldGrid
from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel

_KIND_TO_PALETTE = {
    "skin": "skin",
    "skin_ghost": "skin",
    "body_head": "body_head",
    "body_torso": "body_torso",
    "body_arm_l": "body_arm_l",
    "body_arm_r": "body_arm_r",
    "body_leg_l": "body_leg_l",
    "body_leg_r": "body_leg_r",
    "hair": "hair",
    "scalp": "scalp",
    "eye": "eye",
    "feature": "feature_stone",
    "weapon": "metal_steel",
    "armor_chest": "armor_ash",
    "armor_legs": "armor_root",
    "armor_head": "armor_ash",
    "lantern": "lantern_glow",
    "amulet": "amulet_star",
}


def _colors_for_kind(kind: str, morph_palette: dict[str, str] | None = None):
    pal = load_palette()
    if morph_palette:
        if kind in ("skin", "skin_ghost", "body_head", "body_torso", "scalp"):
            if kind == "body_head":
                key = "body_head"
            elif kind == "body_torso":
                key = "body_torso"
            elif kind in ("skin", "skin_ghost", "scalp"):
                key = morph_palette.get("skin", "skin_fair")
            else:
                key = morph_palette.get("skin", "skin_fair")
        elif kind == "hair":
            key = morph_palette.get("hair", "hair_brown")
        elif kind == "eye":
            key = morph_palette.get("eye", "eye_brown")
        elif kind.startswith("body_"):
            key = kind
        else:
            key = _KIND_TO_PALETTE.get(kind, "metal_steel")
    else:
        key = _KIND_TO_PALETTE.get(kind, "skin_fair")
    entry = pal.get(key, {"fg": [200, 200, 200], "bg": [30, 30, 30]})
    fg = tuple(entry["fg"])
    bg = tuple(entry["bg"])
    return fg, bg


def model_to_grid_entity(
    model: TreeVoxelModel,
    *,
    entity_id: str = "player",
    feet_cx: int,
    feet_cy: int,
    morph_palette: dict[str, str] | None = None,
    z_sort: float = 0.55,
) -> GridEntity:
    if not model.voxels:
        return GridEntity(entity_id=entity_id, feet_cx=feet_cx, feet_cy=feet_cy, cells=[], z_sort=z_sort)

    min_z = min(z for _x, _y, z in model.voxels)

    cells: list[tuple[int, int, str, tuple, tuple]] = []
    for (x, y, z), kind in model.voxels.items():
        cx = feet_cx + (x - model.anchor_x)
        cy = feet_cy + (y - model.anchor_y) - (z - min_z)
        fg, bg = _colors_for_kind(kind, morph_palette)
        if kind in ("skin", "skin_ghost", "scalp"):
            ch = "@"
        elif kind == "hair":
            ch = "~"
        elif kind == "eye":
            ch = "o"
        elif "armor" in kind:
            ch = "#"
        elif kind == "weapon":
            ch = "/"
        else:
            ch = "|"
        cells.append((cx, cy, ch, fg, bg))

    return GridEntity(
        entity_id=entity_id,
        feet_cx=feet_cx,
        feet_cy=feet_cy,
        cells=cells,
        z_sort=z_sort,
    )


def place_character(
    grid: WorldGrid,
    model: TreeVoxelModel,
    *,
    feet_cx: int,
    feet_cy: int,
    morph_palette: dict[str, str] | None = None,
) -> GridEntity:
    entity = model_to_grid_entity(
        model,
        feet_cx=feet_cx,
        feet_cy=feet_cy,
        morph_palette=morph_palette,
    )
    grid.add_entity(entity)
    return entity
