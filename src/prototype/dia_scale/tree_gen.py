"""Trees and bushes on dia_scale char grid."""
from __future__ import annotations

import random

from src.prototype.dia_scale.constants import (
    TILE_Z_M,
    COLOR_BUSH_BG,
    COLOR_BUSH_FG,
    COLOR_CANOPY_BG,
    COLOR_CANOPY_FG,
    COLOR_TRUNK_BG,
    COLOR_TRUNK_FG,
)
from src.prototype.dia_scale.tessellation import stamp_origin
from src.prototype.dia_scale.world_grid import GridSolid, WorldGrid
from src.world.tree_generator import build_tree_solids, roll_tree_params


def _tile_center_char(tx: int, ty: int) -> tuple[int, int]:
    ox, oy = stamp_origin(tx, ty)
    return ox + 1, oy + 1


def _meters_to_char_z(z_m: float) -> float:
    return z_m / TILE_Z_M


def _solid_kind(stencil_id: str | None) -> str:
    sid = stencil_id or ""
    if "trunk" in sid:
        return "trunk"
    if "canopy" in sid:
        return "canopy"
    if "bush" in sid:
        return "bush"
    return "solid"


def _colors_for_kind(kind: str) -> tuple[tuple[int, int, int], tuple[int, int, int], str]:
    if kind == "trunk":
        return COLOR_TRUNK_FG, COLOR_TRUNK_BG, "T"
    if kind == "canopy":
        return COLOR_CANOPY_FG, COLOR_CANOPY_BG, "Y"
    if kind == "bush":
        return COLOR_BUSH_FG, COLOR_BUSH_BG, "o"
    return (180, 180, 180), (30, 30, 30), "?"


def _place_tree_at(
    grid: WorldGrid,
    *,
    anchor_cx: int,
    anchor_cy: int,
    seed: int,
    wx: int,
    wy: int,
    biome: dict,
) -> None:
    params = roll_tree_params(biome, seed, wx, wy)
    for dx, dy, solid in build_tree_solids(params):
        cx = anchor_cx + dx
        cy = anchor_cy + dy
        kind = _solid_kind(solid.stencil_id)
        fg, bg, ch = _colors_for_kind(kind)
        grid.add_solid(
            GridSolid(
                cx=cx,
                cy=cy,
                z_min=_meters_to_char_z(solid.z_min),
                z_max=_meters_to_char_z(solid.z_max),
                stencil_id=solid.stencil_id or kind,
                fg=fg,
                bg=bg,
                ch=ch,
                kind=kind,
            )
        )


def _place_bush_at(grid: WorldGrid, *, cx: int, cy: int, structure_id: str) -> None:
    from src.world.structures import _solids_from_template

    for dx, dy, solid in _solids_from_template(structure_id):
        kind = _solid_kind(solid.stencil_id or structure_id)
        fg, bg, ch = _colors_for_kind(kind)
        grid.add_solid(
            GridSolid(
                cx=cx + dx,
                cy=cy + dy,
                z_min=_meters_to_char_z(solid.z_min),
                z_max=_meters_to_char_z(solid.z_max),
                stencil_id=solid.stencil_id or structure_id,
                fg=fg,
                bg=bg,
                ch=ch,
                kind=kind,
            )
        )


def generate_trees(
    grid: WorldGrid,
    *,
    seed: int,
    nx: int,
    ny: int,
    tree_density: float = 0.12,
    bush_density: float = 0.08,
    biome: dict | None = None,
) -> WorldGrid:
    """Scatter trees/bushes on floor tile grid; skips occupied anchors."""
    biome = biome or {"tree_height_m": [4.0, 8.0]}
    rng = random.Random(seed ^ 0x7EED00)
    occupied: set[tuple[int, int]] = set()
    for tx in range(nx):
        for ty in range(ny):
            cx, cy = _tile_center_char(tx, ty)
            if not grid.has_floor(cx, cy):
                continue
            roll = rng.random()
            if roll < tree_density:
                _place_tree_at(
                    grid,
                    anchor_cx=cx,
                    anchor_cy=cy,
                    seed=seed,
                    wx=tx,
                    wy=ty,
                    biome=biome,
                )
                occupied.add((cx, cy))
            elif roll < tree_density + bush_density:
                bush_id = "bush_heather" if rng.random() < 0.5 else "bush_low"
                _place_bush_at(grid, cx=cx, cy=cy, structure_id=bush_id)
                occupied.add((cx, cy))
    grid.meta["tree_count"] = sum(1 for s in grid.solids if s.kind == "trunk")
    grid.meta["bush_count"] = sum(1 for s in grid.solids if s.kind == "bush")
    return grid
