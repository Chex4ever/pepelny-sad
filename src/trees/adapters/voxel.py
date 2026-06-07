"""Convert TreeMorphology to dia_scale voxel model."""
from __future__ import annotations

from src.constants import TILES_PER_M_XY, TILES_PER_M_Z
from src.prototype.dia_scale.constants import VOXEL_BRANCH, VOXEL_LEAF, VOXEL_TRUNK
from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel, _fill_cylinder, _fill_sphere
from src.trees.loader import load_species
from src.trees.morphology import TreeMorphology


def _m_to_tiles_xy(m: float) -> float:
    return m * TILES_PER_M_XY


def _m_to_tiles_z(m: float) -> float:
    return m * TILES_PER_M_Z


def _branch_kind_to_voxel(kind: str) -> str:
    if kind in ("trunk", "bark_only"):
        return VOXEL_TRUNK
    return VOXEL_BRANCH


def morphology_to_voxels(
    morph: TreeMorphology,
    *,
    anchor_x: int = 0,
    anchor_y: int = 0,
) -> TreeVoxelModel:
    voxels: dict[tuple[int, int, int], str] = {}
    height_tiles = max(1, int(round(_m_to_tiles_z(morph.height_m))))

    model = TreeVoxelModel(
        seed=morph.seed,
        height_tiles=height_tiles,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
        voxels=voxels,
    )

    if not morph.trunk_segments:
        return model

    ax = float(anchor_x) + _m_to_tiles_xy(morph.lean_x)
    ay = float(anchor_y) + _m_to_tiles_xy(morph.lean_y)

    prev_z = 0.0
    prev_r = morph.trunk_segments[0].radius_m
    for ring in morph.trunk_segments[1:]:
        z0 = _m_to_tiles_z(prev_z)
        z1 = _m_to_tiles_z(ring.z_m)
        r0 = _m_to_tiles_xy(prev_r)
        r1 = _m_to_tiles_xy(ring.radius_m)
        steps = max(2, int(z1 - z0))
        for i in range(steps):
            t = i / steps
            z = z0 + (z1 - z0) * t
            r = r0 + (r1 - r0) * t
            _fill_sphere(voxels, ax, ay, z, max(0.5, r), VOXEL_TRUNK)
        prev_z = ring.z_m
        prev_r = ring.radius_m

    for seg in morph.branches:
        kind = _branch_kind_to_voxel(seg.kind)
        _fill_cylinder(
            voxels,
            ax + _m_to_tiles_xy(seg.x0),
            ay + _m_to_tiles_xy(seg.y0),
            _m_to_tiles_z(seg.z0),
            ax + _m_to_tiles_xy(seg.x1),
            ay + _m_to_tiles_xy(seg.y1),
            _m_to_tiles_z(seg.z1),
            max(0.4, _m_to_tiles_xy(seg.radius_m)),
            kind,
        )

    for blob in morph.foliage_clusters:
        if not blob.has_leaves:
            continue
        _fill_sphere(
            voxels,
            ax + _m_to_tiles_xy(blob.x),
            ay + _m_to_tiles_xy(blob.y),
            _m_to_tiles_z(blob.z),
            max(0.8, _m_to_tiles_xy(blob.radius_m)),
            VOXEL_LEAF,
        )

    model.trunk_volume = sum(1 for k in voxels.values() if k == VOXEL_TRUNK)
    model.branch_count = sum(1 for k in voxels.values() if k == VOXEL_BRANCH)
    return model


def spec_to_voxel_model(spec, *, anchor_x: int = 0, anchor_y: int = 0) -> TreeVoxelModel:
    from src.trees.generate import generate_morphology

    morph = generate_morphology(spec)
    return morphology_to_voxels(morph, anchor_x=anchor_x, anchor_y=anchor_y)
