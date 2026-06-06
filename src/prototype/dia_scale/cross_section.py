"""Cross-section slices through voxel tree models."""
from __future__ import annotations

from dataclasses import dataclass

from src.prototype.dia_scale.constants import (
    VOXEL_BRANCH,
    VOXEL_LEAF,
    VOXEL_TRUNK,
)
from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel


@dataclass(frozen=True)
class SectionCell:
    ch: str
    kind: str


@dataclass
class SectionGrid:
    """2D slice: horizontal axis = lateral offset, vertical axis = Z (0 at bottom)."""
    plane: str
    plane_coord: int
    min_h: int
    max_h: int
    min_z: int
    max_z: int
    cells: dict[tuple[int, int], SectionCell]

    def get(self, h: int, z: int) -> SectionCell | None:
        return self.cells.get((h, z))


_KIND_CHAR = {
    VOXEL_TRUNK: "T",
    VOXEL_BRANCH: "|",
    VOXEL_LEAF: "Y",
}


def slice_yz(model: TreeVoxelModel, x0: int) -> SectionGrid:
    """Plane X=x0: horizontal = Y offset from anchor, vertical = Z."""
    cells: dict[tuple[int, int], SectionCell] = {}
    ax, ay = model.anchor_x, model.anchor_y
    for (x, y, z), kind in model.voxels.items():
        if x != x0:
            continue
        h = y - ay
        cells[(h, z)] = SectionCell(ch=_KIND_CHAR.get(kind, "#"), kind=kind)
    return _finalize("yz", x0, cells)


def slice_xz(model: TreeVoxelModel, y0: int) -> SectionGrid:
    """Plane Y=y0: horizontal = X offset from anchor, vertical = Z."""
    cells: dict[tuple[int, int], SectionCell] = {}
    ax, ay = model.anchor_x, model.anchor_y
    for (x, y, z), kind in model.voxels.items():
        if y != y0:
            continue
        h = x - ax
        cells[(h, z)] = SectionCell(ch=_KIND_CHAR.get(kind, "#"), kind=kind)
    return _finalize("xz", y0, cells)


def project_yz(model: TreeVoxelModel) -> SectionGrid:
    """YZ elevation: max-X projection (all voxels collapsed onto YZ)."""
    cells: dict[tuple[int, int], SectionCell] = {}
    ax, ay = model.anchor_x, model.anchor_y
    best: dict[tuple[int, int], tuple[int, str]] = {}
    for (x, y, z), kind in model.voxels.items():
        key = (y - ay, z)
        prev = best.get(key)
        if prev is None or x >= prev[0]:
            best[key] = (x, kind)
    for (h, z), (_x, kind) in best.items():
        cells[(h, z)] = SectionCell(ch=_KIND_CHAR.get(kind, "#"), kind=kind)
    return _finalize("yz", ax, cells)


def project_xz(model: TreeVoxelModel) -> SectionGrid:
    """XZ elevation: max-Y projection (all voxels collapsed onto XZ)."""
    cells: dict[tuple[int, int], SectionCell] = {}
    ax, ay = model.anchor_x, model.anchor_y
    best: dict[tuple[int, int], tuple[int, str]] = {}
    for (x, y, z), kind in model.voxels.items():
        key = (x - ax, z)
        prev = best.get(key)
        if prev is None or y >= prev[0]:
            best[key] = (y, kind)
    for (h, z), (_y, kind) in best.items():
        cells[(h, z)] = SectionCell(ch=_KIND_CHAR.get(kind, "#"), kind=kind)
    return _finalize("xz", ay, cells)


def _finalize(plane: str, coord: int, cells: dict[tuple[int, int], SectionCell]) -> SectionGrid:
    if not cells:
        from src.prototype.dia_scale.constants import TREE_HEIGHT_TILES

        return SectionGrid(plane, coord, -1, 1, 0, TREE_HEIGHT_TILES, {})
    hs = [k[0] for k in cells]
    zs = [k[1] for k in cells]
    return SectionGrid(
        plane=plane,
        plane_coord=coord,
        min_h=min(hs),
        max_h=max(hs),
        min_z=min(zs),
        max_z=max(zs),
        cells=cells,
    )


def section_kinds(section: SectionGrid) -> set[str]:
    return {c.kind for c in section.cells.values()}


def section_plane_world_line(
    plane: str,
    coord: int,
    *,
    focus_cx: int,
    focus_cy: int,
    span: int = 512,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Top-down XY line endpoints for a YZ (X=const) or XZ (Y=const) cut."""
    if plane == "yz":
        return (coord, focus_cy - span), (coord, focus_cy + span)
    return (focus_cx - span, coord), (focus_cx + span, coord)


def scroll_section_coord(plane: str, coord: int, delta: int) -> int:
    """Wheel step along the axis normal to the right-panel section."""
    return coord + delta
