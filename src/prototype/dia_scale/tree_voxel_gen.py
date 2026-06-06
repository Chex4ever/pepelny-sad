"""Procedural voxel tree generator for dia_scale (tile-unit 3D grid)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.prototype.dia_scale.constants import (
    TREE_HEIGHT_TILES,
    VOXEL_BRANCH,
    VOXEL_LEAF,
    VOXEL_TRUNK,
)


@dataclass
class TreeVoxelModel:
    seed: int
    height_tiles: int
    anchor_x: int = 0
    anchor_y: int = 0
    voxels: dict[tuple[int, int, int], str] = field(default_factory=dict)
    branch_count: int = 0
    trunk_volume: int = 0

    def max_z(self) -> int:
        if not self.voxels:
            return 0
        return max(vz for _x, _y, vz in self.voxels)

    def kind_counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for k in self.voxels.values():
            out[k] = out.get(k, 0) + 1
        return out

    def trunk_width_at_z(self, z: int) -> int:
        xs = [x for x, _y, vz in self.voxels if vz == z and self.voxels[(x, _y, vz)] == VOXEL_TRUNK]
        if not xs:
            return 0
        return max(xs) - min(xs) + 1


def _write_voxel(voxels: dict[tuple[int, int, int], str], pos: tuple[int, int, int], kind: str) -> None:
    """Branches/leaves must not erase the trunk core."""
    if kind != VOXEL_TRUNK and voxels.get(pos) == VOXEL_TRUNK:
        return
    voxels[pos] = kind


def _fill_sphere(
    voxels: dict[tuple[int, int, int], str],
    cx: float,
    cy: float,
    cz: float,
    r: float,
    kind: str,
) -> None:
    ri = int(math.ceil(r))
    for dx in range(-ri, ri + 1):
        for dy in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                if dx * dx + dy * dy + dz * dz <= r * r + 0.5:
                    _write_voxel(
                        voxels,
                        (int(round(cx + dx)), int(round(cy + dy)), int(round(cz + dz))),
                        kind,
                    )


def _fill_cylinder(
    voxels: dict[tuple[int, int, int], str],
    x0: float,
    y0: float,
    z0: float,
    x1: float,
    y1: float,
    z1: float,
    radius: float,
    kind: str,
) -> None:
    steps = max(int(math.ceil(math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2))) + 1, 2)
    for i in range(steps + 1):
        t = i / steps
        cx = x0 + (x1 - x0) * t
        cy = y0 + (y1 - y0) * t
        cz = z0 + (z1 - z0) * t
        _fill_sphere(voxels, cx, cy, cz, radius, kind)


def generate_voxel_tree(
    *,
    seed: int,
    height_tiles: int = TREE_HEIGHT_TILES,
    anchor_x: int = 0,
    anchor_y: int = 0,
    species_id: str = "oak",
    age_years: float | None = None,
) -> TreeVoxelModel:
    """Generate voxel tree via species-aware morphology pipeline."""
    from src.trees.instance import TreeInstanceSpec
    from src.trees.adapters.voxel import spec_to_voxel_model
    from src.trees.loader import load_species

    species = load_species(species_id)
    age = age_years if age_years is not None else species.max_age_years * 0.55
    spec = TreeInstanceSpec(
        species_id=species_id,
        seed=seed,
        age_years=age,
        health=1.0,
        wx=anchor_x,
        wy=anchor_y,
    )
    return spec_to_voxel_model(spec, anchor_x=anchor_x, anchor_y=anchor_y)


def _solids_from_columns(columns: dict[tuple[int, int], tuple[int, str]]) -> list:
    from src.prototype.dia_scale.constants import (
        COLOR_BRANCH_BG,
        COLOR_BRANCH_FG,
        COLOR_CANOPY_BG,
        COLOR_CANOPY_FG,
        COLOR_TRUNK_BG,
        COLOR_TRUNK_FG,
    )
    from src.prototype.dia_scale.world_grid import GridSolid

    style = {
        VOXEL_TRUNK: (COLOR_TRUNK_FG, COLOR_TRUNK_BG, "T"),
        VOXEL_BRANCH: (COLOR_BRANCH_FG, COLOR_BRANCH_BG, "|"),
        VOXEL_LEAF: (COLOR_CANOPY_FG, COLOR_CANOPY_BG, "Y"),
    }
    solids: list[GridSolid] = []
    for (cx, cy), (z, kind) in columns.items():
        fg, bg, ch = style.get(kind, ((200, 200, 200), (30, 30, 30), "?"))
        solids.append(
            GridSolid(
                cx=cx,
                cy=cy,
                z_min=float(z),
                z_max=float(z + 1),
                stencil_id=f"voxel_{kind}",
                fg=fg,
                bg=bg,
                ch=ch,
                kind=kind,
            )
        )
    return solids


def project_tree_to_solids(model: TreeVoxelModel):
    """Top-down column projection for char-grid overlay."""
    columns: dict[tuple[int, int], tuple[int, str]] = {}
    for (x, y, z), kind in model.voxels.items():
        prev = columns.get((x, y))
        if prev is None or z >= prev[0]:
            columns[(x, y)] = (z, kind)
    return _solids_from_columns(columns)


def project_tree_at_z(model: TreeVoxelModel, z0: int) -> list:
    """Axial XY slice: one solid per voxel at Z=z0 (for top-down cut plane)."""
    columns: dict[tuple[int, int], tuple[int, str]] = {}
    for (x, y, z), kind in model.voxels.items():
        if z != z0:
            continue
        columns[(x, y)] = (z, kind)
    return _solids_from_columns(columns)


def project_tree_up_to_z(model: TreeVoxelModel, z_max: int) -> list:
    """Top-down max projection using voxels with Z <= z_max (rear cull above cut)."""
    columns: dict[tuple[int, int], tuple[int, str]] = {}
    for (x, y, z), kind in model.voxels.items():
        if z > z_max:
            continue
        prev = columns.get((x, y))
        if prev is None or z >= prev[0]:
            columns[(x, y)] = (z, kind)
    return _solids_from_columns(columns)
