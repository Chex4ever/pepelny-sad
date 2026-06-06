"""Voxel selection, create, move for character editor."""
from __future__ import annotations

from src.characters.poses import FACINGS_8
from src.characters.voxel_edits import VoxelEditLayer
from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel

from src.characters.editor_diagnostics import compute_floor_z

VoxelPos = tuple[int, int, int]


def facing_index(facing: str) -> int:
    try:
        return FACINGS_8.index(facing)
    except ValueError:
        return FACINGS_8.index("s")


def rotate_facing(facing: str, delta: int) -> str:
    i = (facing_index(facing) + delta) % len(FACINGS_8)
    return FACINGS_8[i]


def voxel_at(model: TreeVoxelModel, edits: VoxelEditLayer, pos: VoxelPos) -> str | None:
    if pos in edits.removals:
        return None
    if pos in edits.additions:
        return edits.additions[pos]
    return model.voxels.get(pos)


def merged_voxels(model: TreeVoxelModel, edits: VoxelEditLayer) -> dict[VoxelPos, str]:
    out = dict(model.voxels)
    for p in edits.removals:
        out.pop(p, None)
    out.update(edits.additions)
    return out


def move_voxel_in_edits(
    edits: VoxelEditLayer,
    model: TreeVoxelModel,
    old: VoxelPos,
    new: VoxelPos,
) -> bool:
    if old == new:
        return True
    kind = voxel_at(model, edits, old)
    if kind is None:
        return False
    edits.remove(*old)
    edits.add(*new, kind)
    return True


def delete_voxel(edits: VoxelEditLayer, model: TreeVoxelModel, pos: VoxelPos) -> None:
    if pos in edits.additions:
        edits.remove(*pos)
    elif pos in model.voxels:
        edits.remove(*pos)


def create_voxel(
    edits: VoxelEditLayer,
    pos: VoxelPos,
    kind: str,
) -> None:
    edits.add(*pos, kind)


def default_create_pos(
    model: TreeVoxelModel,
    edits: VoxelEditLayer,
    *,
    selected: VoxelPos | None,
    anchor_x: int,
    anchor_y: int,
) -> VoxelPos:
    merged = merged_voxels(model, edits)
    floor_z = compute_floor_z(merged)
    if selected is not None:
        return (anchor_x, anchor_y, selected[2])
    if merged:
        min_z = min(z for (_x, _y, z) in merged)
        return (anchor_x, anchor_y, max(floor_z, min_z))
    return (anchor_x, anchor_y, floor_z + 1)


def arrow_delta(key: int, facing: str) -> tuple[int, int, int] | None:
    """Map pygame key + facing to model-space delta. ↑↓=Y, ←→=X."""
    import pygame

    # Screen-relative axes from facing (forward = facing direction in XY).
    fwd_map = {
        "n": (0, -1), "ne": (1, -1), "e": (1, 0), "se": (1, 1),
        "s": (0, 1), "sw": (-1, 1), "w": (-1, 0), "nw": (-1, -1),
    }
    fx, fy = fwd_map.get(facing, (0, 1))
    # right = rotate forward 90° cw in grid: (fy, -fx) simplified to cardinals
    rx, ry = fy, -fx if fx else (1 if fy >= 0 else -1)

    if key == pygame.K_LEFT:
        return (-rx, -ry, 0)
    if key == pygame.K_RIGHT:
        return (rx, ry, 0)
    if key == pygame.K_UP:
        return (fx, fy, 0)
    if key == pygame.K_DOWN:
        return (-fx, -fy, 0)
    if key == pygame.K_PAGEUP:
        return (0, 0, 1)
    if key == pygame.K_PAGEDOWN:
        return (0, 0, -1)
    return None
