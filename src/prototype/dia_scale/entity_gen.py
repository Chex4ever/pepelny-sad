"""Player / object sprites for dia_scale prototype."""
from __future__ import annotations

from src.characters.adapters.grid_entity import place_character
from src.characters.appearance import default_appearance
from src.characters.bake import bake_voxel_model
from src.characters.generate import generate_morphology
from src.characters.spec import CharacterSpec
from src.prototype.dia_scale.world_grid import GridEntity, WorldGrid


def player_sprite_rows(spec: CharacterSpec | None = None) -> tuple[str, ...]:
    """Build ASCII rows from generated voxel model (top row first)."""
    appearance = spec or default_appearance()
    model = bake_voxel_model(appearance, anchor_x=0, anchor_y=0)
    if not model.voxels:
        return (" @ ", "/|\\", "/ \\")

    min_x = min(x for x, _y, _z in model.voxels)
    max_x = max(x for x, _y, _z in model.voxels)
    min_y = min(y for _x, y, _z in model.voxels)
    max_y = max(y for _x, y, _z in model.voxels)
    min_z = min(z for _x, _y, z in model.voxels)
    max_z = max(z for _x, _y, z in model.voxels)

    grid: dict[tuple[int, int], str] = {}
    for (x, y, z), kind in model.voxels.items():
        row = max_z - z
        col = x - min_x
        ch = "@" if kind in ("skin", "skin_ghost", "scalp") else "|"
        grid[(row, col)] = ch

    width = max_x - min_x + 1
    height = max_z - min_z + 1
    rows: list[str] = []
    for row in range(height):
        line = "".join(grid.get((row, col), " ") for col in range(width))
        rows.append(line)
    return tuple(rows)


def place_player(
    grid: WorldGrid,
    *,
    feet_cx: int,
    feet_cy: int,
    spec: CharacterSpec | None = None,
    pose_id: str = "idle_s",
) -> GridEntity:
    appearance = spec or default_appearance()
    morph = generate_morphology(appearance)
    model = bake_voxel_model(
        appearance,
        pose_id=pose_id,
        anchor_x=feet_cx,
        anchor_y=feet_cy,
    )
    return place_character(
        grid,
        model,
        feet_cx=feet_cx,
        feet_cy=feet_cy,
        morph_palette=morph.palette,
    )


def player_footprint_cells(feet_cx: int, feet_cy: int, spec: CharacterSpec | None = None) -> set[tuple[int, int]]:
    appearance = spec or default_appearance()
    model = bake_voxel_model(appearance, anchor_x=feet_cx, anchor_y=feet_cy)
    out: set[tuple[int, int]] = set()
    min_z = min((z for _x, _y, z in model.voxels), default=0)
    for (x, y, z), _kind in model.voxels.items():
        cx = feet_cx + (x - model.anchor_x)
        cy = feet_cy + (y - model.anchor_y) - (z - min_z)
        out.add((cx, cy))
    return out
