"""Fast column + floor shading for editor iso preview."""
from __future__ import annotations


def _clamp(v: int) -> int:
    return max(0, min(255, v))


def shade_color(fg: tuple[int, int, int], bg: tuple[int, int, int], factor: float) -> tuple[tuple, tuple]:
    """Darken colors; factor 0=no change, 1=black."""
    f = max(0.0, min(1.0, factor))
    nf = 1.0 - f
    nfg = (_clamp(int(fg[0] * nf)), _clamp(int(fg[1] * nf)), _clamp(int(fg[2] * nf)))
    nbg = (_clamp(int(bg[0] * nf)), _clamp(int(bg[1] * nf)), _clamp(int(bg[2] * nf)))
    return nfg, nbg


def build_column_depth(voxels: dict[tuple[int, int, int], str]) -> dict[tuple[int, int, int], int]:
    """For each voxel, count voxels above in same (x,y) column."""
    columns: dict[tuple[int, int], list[int]] = {}
    for (x, y, z), _k in voxels.items():
        columns.setdefault((x, y), []).append(z)
    depth_map: dict[tuple[int, int, int], int] = {}
    for (x, y), zs in columns.items():
        zs_sorted = sorted(zs)
        for i, z in enumerate(zs_sorted):
            depth_map[(x, y, z)] = len(zs_sorted) - 1 - i
    return depth_map


def build_floor_shadow(
    voxels: dict[tuple[int, int, int], str],
    floor_z: int,
) -> set[tuple[int, int]]:
    """XY cells with any voxel above floor."""
    shadow: set[tuple[int, int]] = set()
    for (x, y, z), _k in voxels.items():
        if z >= floor_z:
            shadow.add((x, y))
    return shadow


def shade_factor_for_voxel(
    pos: tuple[int, int, int],
    kind: str,
    *,
    column_depth: dict[tuple[int, int, int], int],
    voxels: dict[tuple[int, int, int], str],
    max_column_shade: float = 0.35,
) -> float:
    above = column_depth.get(pos, 0)
    col = min(max_column_shade, above * 0.08)
    x, y, z = pos
    under = (x, y, z - 1)
    vol = 0.1 if under in voxels and voxels[under] == kind else 0.0
    return col + vol
