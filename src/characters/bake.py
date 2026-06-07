"""Bake voxel models and lazy pose sets (canonical + facing transform)."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from src.characters.adapters.voxel import morphology_to_voxels, voxel_build_config_from_tuning
from src.characters.equipment import EquipmentAttachment, resolve_attachments
from src.characters.generate import generate_morphology
from src.characters.loader import load_equipment_visuals
from src.characters.poses import (
    CANONICAL_POSE_KEYS,
    POSE_KEYS,
    apply_pose,
    canonical_pose_id,
    facing_from_pose,
    load_pose_delta,
    transform_voxels_xy,
)
from src.characters.spec import CharacterSpec
from src.characters.voxel_edits import VoxelEditLayer, apply_edits
from src.constants import TILES_PER_M_Z
from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel

if TYPE_CHECKING:
    from src.characters.tuning import TuningState


@dataclass
class CharacterPoseSet:
    spec: CharacterSpec
    canonical: dict[str, TreeVoxelModel] = field(default_factory=dict)
    edits: VoxelEditLayer | None = None
    _cache: dict[str, TreeVoxelModel] = field(default_factory=dict, repr=False)

    @property
    def poses(self) -> dict[str, TreeVoxelModel]:
        """Legacy access — builds all cached + canonical."""
        out = dict(self.canonical)
        out.update(self._cache)
        return out

    def invalidate_cache(self) -> None:
        self._cache.clear()

    def get(self, pose_id: str) -> TreeVoxelModel:
        if pose_id in self._cache:
            return self._cache[pose_id]
        if pose_id in self.canonical:
            return self.canonical[pose_id]
        canon_id = canonical_pose_id(pose_id)
        if canon_id not in self.canonical:
            raise KeyError(pose_id)
        base = self.canonical[canon_id]
        facing = facing_from_pose(pose_id)
        model = transform_model_facing(base, facing)
        self._cache[pose_id] = model
        return model

    def __len__(self) -> int:
        return len(self.canonical)


def transform_model_facing(model: TreeVoxelModel, facing: str) -> TreeVoxelModel:
    voxels = transform_voxels_xy(
        model.voxels,
        anchor_x=model.anchor_x,
        anchor_y=model.anchor_y,
        facing=facing,
    )
    return replace(model, voxels=voxels)


def _template_voxels(template_id: str) -> list[tuple[int, int, int, str]]:
    data = load_equipment_visuals()
    templates = data.get("voxel_templates", {})
    raw = templates.get(template_id, [])
    return [(int(v[0]), int(v[1]), int(v[2]), str(v[3])) for v in raw]


def merge_voxels(
    body: dict[tuple[int, int, int], str],
    attachments: list[EquipmentAttachment],
    morph,
    *,
    pose_id: str = "idle_s",
) -> dict[tuple[int, int, int], str]:
    from src.characters.adapters.voxel import _m_to_tiles_xy, _m_to_tiles_z

    posed = apply_pose(morph, pose_id)
    delta = load_pose_delta(pose_id)
    out = dict(body)

    slot_order = {"legs": 0, "chest": 1, "head": 2, "amulet": 3, "hand_l": 4, "hand_r": 5}
    sorted_attach = sorted(attachments, key=lambda a: slot_order.get(a.slot, 9))

    for att in sorted_attach:
        for kind in att.occlusion_mask:
            to_remove = [k for k, v in out.items() if v == kind]
            for k in to_remove:
                del out[k]

        anchors = [att.anchor]
        if att.anchor_secondary:
            anchors.append(att.anchor_secondary)

        for anchor_name in anchors:
            if anchor_name not in posed.anchors:
                continue
            ap = posed.anchors[anchor_name]
            ax = int(round(_m_to_tiles_xy(ap.x)))
            ay = int(round(_m_to_tiles_xy(ap.y)))
            az = int(round(_m_to_tiles_z(ap.z)))
            if anchor_name == "leg_l":
                az += int(round(delta.leg_l_z * TILES_PER_M_Z))
            elif anchor_name == "leg_r":
                az += int(round(delta.leg_r_z * TILES_PER_M_Z))

            for dx, dy, dz, _tk in _template_voxels(att.voxel_template):
                pos = (ax + dx, ay + dy, az + dz)
                out[pos] = att.kind

    return out


def _bake_single_pose(
    morph,
    *,
    pose_id: str,
    anchor_x: int,
    anchor_y: int,
    vcfg,
    attachments: list[EquipmentAttachment],
    edits: VoxelEditLayer | None,
) -> TreeVoxelModel:
    model = morphology_to_voxels(
        morph, anchor_x=anchor_x, anchor_y=anchor_y, pose_id=pose_id, voxel_config=vcfg,
    )
    if attachments:
        model.voxels = merge_voxels(model.voxels, attachments, morph, pose_id=pose_id)
    if edits:
        model.voxels = apply_edits(model.voxels, edits)
    return model


def bake_voxel_model(
    spec: CharacterSpec,
    *,
    pose_id: str = "idle_s",
    anchor_x: int = 0,
    anchor_y: int = 0,
    tuning: TuningState | None = None,
    edits: VoxelEditLayer | None = None,
) -> TreeVoxelModel:
    morph = generate_morphology(spec, tuning=tuning)
    vcfg = voxel_build_config_from_tuning(tuning)
    attachments = resolve_attachments(spec.equipment)
    canon = canonical_pose_id(pose_id)
    model = _bake_single_pose(
        morph, pose_id=canon, anchor_x=anchor_x, anchor_y=anchor_y,
        vcfg=vcfg, attachments=attachments, edits=edits,
    )
    facing = facing_from_pose(pose_id)
    if facing != facing_from_pose(canon):
        model = transform_model_facing(model, facing)
    return model


def bake_pose_set(
    spec: CharacterSpec,
    *,
    anchor_x: int = 0,
    anchor_y: int = 0,
    tuning: TuningState | None = None,
    edits: VoxelEditLayer | None = None,
) -> CharacterPoseSet:
    morph = generate_morphology(spec, tuning=tuning)
    vcfg = voxel_build_config_from_tuning(tuning)
    attachments = resolve_attachments(spec.equipment)
    pose_set = CharacterPoseSet(spec=spec, edits=edits)
    for pose_id in CANONICAL_POSE_KEYS:
        model = _bake_single_pose(
            morph, pose_id=pose_id, anchor_x=anchor_x, anchor_y=anchor_y,
            vcfg=vcfg, attachments=attachments, edits=edits,
        )
        pose_set.canonical[pose_id] = model
    return pose_set


def bake_pose_set_legacy_full(
    spec: CharacterSpec,
    *,
    anchor_x: int = 0,
    anchor_y: int = 0,
    tuning: TuningState | None = None,
) -> dict[str, TreeVoxelModel]:
    """Full per-pose bake (compatibility / tests)."""
    morph = generate_morphology(spec, tuning=tuning)
    vcfg = voxel_build_config_from_tuning(tuning)
    attachments = resolve_attachments(spec.equipment)
    out: dict[str, TreeVoxelModel] = {}
    for pose_id in POSE_KEYS:
        model = morphology_to_voxels(
            morph, anchor_x=anchor_x, anchor_y=anchor_y, pose_id=pose_id, voxel_config=vcfg,
        )
        if attachments:
            model.voxels = merge_voxels(model.voxels, attachments, morph, pose_id=pose_id)
        out[pose_id] = model
    return out
