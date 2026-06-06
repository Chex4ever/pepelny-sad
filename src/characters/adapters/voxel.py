"""Convert CharacterMorphology to dia_scale voxel model."""
from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace

from src.characters.loader import load_hair_styles, load_race
from src.characters.morphology import CharacterMorphology
from src.characters.poses import load_pose_delta
from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel, _fill_cylinder, _fill_sphere

VOXEL_SKIN = "skin"
VOXEL_SKIN_GHOST = "skin_ghost"
VOXEL_HAIR = "hair"
VOXEL_SCALP = "scalp"
VOXEL_EYE = "eye"
VOXEL_FEATURE = "feature"
BODY_HEAD = "body_head"
BODY_TORSO = "body_torso"
BODY_ARM_L = "body_arm_l"
BODY_ARM_R = "body_arm_r"
BODY_LEG_L = "body_leg_l"
BODY_LEG_R = "body_leg_r"

# Legacy module-level aliases (default config)
TILES_PER_M_XY = 5
TILES_PER_M_Z = 10


@dataclass(frozen=True)
class VoxelBuildConfig:
    tiles_per_m_xy: float = 5.0
    tiles_per_m_z: float = 10.0
    min_rxy_arm: float = 0.56
    min_rxy_leg: float = 0.66
    min_rxy_torso: float = 0.88
    min_rxy_head: float = 1.12
    min_rz: float = 0.5
    torso_steps: int = 10


DEFAULT_VOXEL_BUILD_CONFIG = VoxelBuildConfig()
_active_voxel_config = DEFAULT_VOXEL_BUILD_CONFIG


def voxel_build_config_from_tuning(tuning) -> VoxelBuildConfig:
    if tuning is None:
        return DEFAULT_VOXEL_BUILD_CONFIG
    kw: dict = {}
    for f in fields(VoxelBuildConfig):
        path = f"voxel.{f.name}"
        if hasattr(tuning, "is_locked") and tuning.is_locked(path):
            val = tuning.get(path)
            kw[f.name] = int(val) if f.name == "torso_steps" else float(val)
    return replace(DEFAULT_VOXEL_BUILD_CONFIG, **kw) if kw else DEFAULT_VOXEL_BUILD_CONFIG


def _cfg() -> VoxelBuildConfig:
    return _active_voxel_config


def _m_to_tiles_xy(m: float) -> float:
    return m * _cfg().tiles_per_m_xy


def _m_to_tiles_z(m: float) -> float:
    return m * _cfg().tiles_per_m_z


def _rxy(m: float) -> float:
    return max(0.9, _m_to_tiles_xy(m))


def _rxy_arm(m: float) -> float:
    return max(_cfg().min_rxy_arm, _m_to_tiles_xy(m))


def _rxy_leg(m: float) -> float:
    return max(_cfg().min_rxy_leg, _m_to_tiles_xy(m))


def _rxy_torso(m: float) -> float:
    return max(_cfg().min_rxy_torso, _m_to_tiles_xy(m))


def _rxy_head(m: float) -> float:
    return max(_cfg().min_rxy_head, _m_to_tiles_xy(m))


def _rz(m: float) -> float:
    return max(_cfg().min_rz, _m_to_tiles_z(m))


def _skin_kind(morph: CharacterMorphology) -> str:
    return morph.palette.get("skin_kind", VOXEL_SKIN)


def _fill_ellipsoid(
    voxels: dict,
    cx: float,
    cy: float,
    cz: float,
    rx: float,
    ry: float,
    rz: float,
    kind: str,
) -> None:
    """World-correct ellipsoid: rx/ry in XY tiles, rz in Z tiles."""
    ri = max(int(math.ceil(max(rx, ry, rz))), 1)
    for dx in range(-ri, ri + 1):
        for dy in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                if rx <= 0 or ry <= 0 or rz <= 0:
                    continue
                if (dx / rx) ** 2 + (dy / ry) ** 2 + (dz / rz) ** 2 <= 1.0 + 0.08:
                    voxels[(int(round(cx + dx)), int(round(cy + dy)), int(round(cz + dz)))] = kind


def _joint_xyz(morph: CharacterMorphology, name: str, ax0: float, ay0: float) -> tuple[float, float, float]:
    j = morph.joints[name]
    return ax0 + _m_to_tiles_xy(j.x), ay0 + _m_to_tiles_xy(j.y), _m_to_tiles_z(j.z)


def _apply_pose_to_joints(morph: CharacterMorphology, pose_id: str) -> dict[str, tuple[float, float, float]]:
    from src.characters.poses import apply_pose_delta_to_point, facing_from_pose, load_pose_delta

    delta = load_pose_delta(pose_id)
    facing = facing_from_pose(pose_id)
    out: dict[str, tuple[float, float, float]] = {}
    for name, j in morph.joints.items():
        out[name] = apply_pose_delta_to_point(name, j.x, j.y, j.z, delta, facing)
    return out


def _build_body_voxels(
    morph: CharacterMorphology,
    *,
    ax0: float,
    ay0: float,
    pose_id: str = "idle_s",
) -> dict[tuple[int, int, int], str]:
    p = morph.proportions
    if p is None:
        return {}

    skin = _skin_kind(morph)
    posed = _apply_pose_to_joints(morph, pose_id)
    voxels: dict[tuple[int, int, int], str] = {}
    torso_kind = BODY_TORSO if skin == VOXEL_SKIN else "skin_ghost"

    def jv(name: str) -> tuple[float, float, float]:
        x, y, z = posed[name]
        return ax0 + _m_to_tiles_xy(x), ay0 + _m_to_tiles_xy(y), _m_to_tiles_z(z)

    # Feet
    for side, foot_kind in (("ankle_l", BODY_LEG_L), ("ankle_r", BODY_LEG_R)):
        x, y, z = jv(side)
        _fill_ellipsoid(voxels, x, y, z, _rxy_leg(p.foot_r), _rxy_leg(p.foot_r * 1.4), _rz(p.foot_h * 0.4), foot_kind)

    # Legs: hip → knee → ankle
    for prefix, leg_kind in (("l", BODY_LEG_L), ("r", BODY_LEG_R)):
        hip, knee, ankle = jv(f"hip_{prefix}"), jv(f"knee_{prefix}"), jv(f"ankle_{prefix}")
        hx, hy, hz = hip
        kx, ky, kz = knee
        ax, ay, az = ankle
        _fill_cylinder(voxels, hx, hy, hz, kx, ky, kz, _rxy_leg(p.thigh_r), leg_kind)
        _fill_cylinder(voxels, kx, ky, kz, ax, ay, az, _rxy_leg(p.calf_r), leg_kind)

    # Pelvis bridge
    hl, hr = jv("hip_l"), jv("hip_r")
    pelvis_cz = (hl[2] + hr[2]) * 0.5 + _m_to_tiles_z(p.pelvis_h * 0.15)
    pelvis_cx = (hl[0] + hr[0]) * 0.5
    _fill_ellipsoid(
        voxels, pelvis_cx, ay0, pelvis_cz,
        _rxy_torso(p.hip_hw * 1.08), _rxy_torso(p.chest_depth * 0.82), _rz(p.pelvis_h * 0.62),
        torso_kind,
    )

    # Torso: tapered chest → waist
    waist = jv("waist")
    chest = jv("chest")
    torso_steps = _cfg().torso_steps
    for i in range(torso_steps):
        t = i / max(torso_steps - 1, 1)
        cx = chest[0] * (1 - t) + waist[0] * t
        cy = chest[1] * (1 - t) + waist[1] * t
        cz = chest[2] * (1 - t) + waist[2] * t
        rx = _rxy_torso(p.shoulder_hw * (1 - t * 0.15) + p.hip_hw * t * 0.15)
        ry = _rxy_torso(p.chest_depth * (1 - t * 0.1) + p.chest_depth * 0.65 * t)
        rz = _rz(p.torso_h / torso_steps * 0.88)
        _fill_ellipsoid(voxels, cx, cy, cz, rx, ry, rz, torso_kind)

    # Shoulder caps (torso bulk at shoulder joint — sized to bridge torso ↔ arm)
    for side in ("shoulder_l", "shoulder_r"):
        sx, sy, sz = jv(side)
        cap_xy = max(p.upper_arm_r * 1.15, p.shoulder_hw * 0.14)
        _fill_ellipsoid(
            voxels, sx, sy, sz,
            _rxy_torso(cap_xy), _rxy_torso(cap_xy * 0.85), _rz(p.upper_arm_r * 1.1),
            torso_kind,
        )

    # Arms: shoulder → elbow → wrist
    for prefix, arm_kind in (("l", BODY_ARM_L), ("r", BODY_ARM_R)):
        r_upper, r_lower = p.upper_arm_r, p.forearm_r
        sh, el, wr = jv(f"shoulder_{prefix}"), jv(f"elbow_{prefix}"), jv(f"wrist_{prefix}")
        _fill_cylinder(voxels, sh[0], sh[1], sh[2], el[0], el[1], el[2], _rxy_arm(r_upper), arm_kind)
        _fill_cylinder(voxels, el[0], el[1], el[2], wr[0], wr[1], wr[2], _rxy_arm(r_lower), arm_kind)
        _fill_ellipsoid(voxels, wr[0], wr[1], wr[2], _rxy_arm(r_lower), _rxy_arm(r_lower), _rz(r_lower * 0.85), arm_kind)

    # Neck
    nb = jv("neck_base")
    hc = jv("head_center")
    _fill_cylinder(voxels, nb[0], nb[1], nb[2], hc[0], hc[1], nb[2] + (hc[2] - nb[2]) * 0.3, _rxy_torso(p.neck_r), torso_kind)

    # Head (no scalp overpaint — hair template covers crown)
    hx, hy, hz = hc
    _fill_ellipsoid(
        voxels, hx, hy, hz,
        _rxy_head(p.head_r), _rxy_head(p.head_r * 0.92), _rz(p.head_h * 0.52),
        BODY_HEAD,
    )

    return voxels


def _finalize_head_voxels(
    voxels: dict[tuple[int, int, int], str],
    morph: CharacterMorphology,
    *,
    ax0: float,
    ay0: float,
) -> None:
    """Re-assert head shell after hair/eyes so face stays visible (H glyph)."""
    if morph.proportions is None:
        return
    p = morph.proportions
    hc = morph.joints.get("head_center")
    if not hc:
        return
    hx = ax0 + _m_to_tiles_xy(hc.x)
    hy = ay0 + _m_to_tiles_xy(hc.y)
    hz = _m_to_tiles_z(hc.z)
    scratch: dict[tuple[int, int, int], str] = {}
    _fill_ellipsoid(
        scratch, hx, hy, hz,
        _rxy_head(p.head_r), _rxy_head(p.head_r * 0.92), _rz(p.head_h * 0.52),
        BODY_HEAD,
    )
    for pos in scratch:
        kind = voxels.get(pos)
        if kind in (VOXEL_HAIR, VOXEL_EYE, VOXEL_FEATURE):
            continue
        voxels[pos] = BODY_HEAD


def _add_hair_template(voxels: dict, morph: CharacterMorphology, *, ax0: float, ay0: float) -> None:
    styles = load_hair_styles()
    race_styles = styles.get(morph.race_id, {})
    template = race_styles.get(morph.hair_style_id, [])
    crown = morph.anchors.get("head_crown")
    if not crown:
        return
    cx = ax0 + _m_to_tiles_xy(crown.x)
    cy = ay0 + _m_to_tiles_xy(crown.y)
    cz = _m_to_tiles_z(crown.z)
    for entry in template:
        dx, dy, dz, kind = int(entry[0]), int(entry[1]), int(entry[2]), str(entry[3])
        pos = (int(round(cx + dx)), int(round(cy + dy)), int(round(cz + dz)))
        voxels[pos] = VOXEL_HAIR if kind == "hair" else VOXEL_FEATURE

    if morph.beard_style_id:
        beard_tpl = styles.get("_beard", {}).get(morph.beard_style_id, [])
        neck = morph.anchors.get("neck_front")
        face_z = _m_to_tiles_z(neck.z) if neck else cz - 2
        for entry in beard_tpl:
            dx, dy, dz, kind = int(entry[0]), int(entry[1]), int(entry[2]), str(entry[3])
            pos = (int(round(cx + dx)), int(round(cy + dy)), int(round(face_z + dz)))
            voxels[pos] = VOXEL_HAIR if kind == "hair" else VOXEL_FEATURE


def _add_ears(voxels: dict, morph: CharacterMorphology, *, ax0: float, ay0: float) -> None:
    if not morph.has_feature("ears_pointed") or morph.proportions is None:
        return
    race = load_race(morph.race_id)
    hc = morph.joints.get("head_center")
    if not hc:
        return
    hx = ax0 + _m_to_tiles_xy(hc.x)
    hy = ay0 + _m_to_tiles_xy(hc.y)
    hz = _m_to_tiles_z(hc.z)
    hr = _m_to_tiles_xy(morph.proportions.head_r)
    ear_len = max(0.5, _m_to_tiles_z(race.ear_length_m))
    for side in (-1, 1):
        _fill_ellipsoid(voxels, hx + side * (hr + 0.3), hy, hz, 0.35, 0.25, ear_len * 0.5, VOXEL_FEATURE)


def _add_eyes(voxels: dict, morph: CharacterMorphology, *, ax0: float, ay0: float) -> None:
    if morph.proportions is None:
        return
    hc = morph.joints.get("head_center")
    if not hc:
        return
    hx = ax0 + _m_to_tiles_xy(hc.x)
    hy = ay0 + _m_to_tiles_xy(hc.y) + _m_to_tiles_xy(morph.proportions.head_r * 0.45)
    hz = _m_to_tiles_z(hc.z) + _m_to_tiles_z(morph.proportions.head_h * 0.08)
    spread = _m_to_tiles_xy(morph.proportions.head_r * 0.38)
    for side in (-1, 1):
        voxels[(int(round(hx + side * spread)), int(round(hy)), int(round(hz)))] = VOXEL_EYE


def _add_race_features(voxels: dict, morph: CharacterMorphology, *, ax0: float, ay0: float) -> None:
    import random

    if morph.proportions is None:
        return
    rng = random.Random(morph.seed)
    chest = morph.joints.get("chest")
    if not chest:
        return
    tx = ax0 + _m_to_tiles_xy(chest.x)
    ty = ay0 + _m_to_tiles_xy(chest.y)
    tz = _m_to_tiles_z(chest.z)
    if morph.has_feature("stone_patch"):
        for _ in range(rng.randint(1, 4)):
            _fill_ellipsoid(
                voxels,
                tx + rng.uniform(-0.8, 0.8),
                ty + rng.uniform(-0.5, 0.5),
                tz + rng.uniform(-1.0, 1.0),
                0.45, 0.35, 0.5,
                VOXEL_FEATURE,
            )
    if morph.has_feature("bark_skin"):
        _fill_ellipsoid(voxels, tx + 0.5, ty, tz, 0.55, 0.45, 0.6, VOXEL_FEATURE)


def morphology_to_voxels(
    morph: CharacterMorphology,
    *,
    anchor_x: int = 0,
    anchor_y: int = 0,
    pose_id: str = "idle_s",
    voxel_config: VoxelBuildConfig | None = None,
) -> TreeVoxelModel:
    global _active_voxel_config
    prev = _active_voxel_config
    if voxel_config is not None:
        _active_voxel_config = voxel_config
    try:
        ax0 = float(anchor_x)
        ay0 = float(anchor_y)
        voxels = _build_body_voxels(morph, ax0=ax0, ay0=ay0, pose_id=pose_id)
        _add_ears(voxels, morph, ax0=ax0, ay0=ay0)
        _add_eyes(voxels, morph, ax0=ax0, ay0=ay0)
        _add_hair_template(voxels, morph, ax0=ax0, ay0=ay0)
        _finalize_head_voxels(voxels, morph, ax0=ax0, ay0=ay0)
        _add_race_features(voxels, morph, ax0=ax0, ay0=ay0)

        height_tiles = max(1, int(round(_m_to_tiles_z(morph.height_m))))
        if voxels:
            height_tiles = max(v[2] for v in voxels) + 1
        return TreeVoxelModel(
            seed=morph.seed,
            height_tiles=height_tiles,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            voxels=voxels,
        )
    finally:
        _active_voxel_config = prev


def spec_to_voxel_model(spec, *, pose_id: str = "idle_s", anchor_x: int = 0, anchor_y: int = 0):
    from src.characters.bake import bake_voxel_model

    return bake_voxel_model(spec, pose_id=pose_id, anchor_x=anchor_x, anchor_y=anchor_y)
