"""Pose definitions, 8-way facings, and voxel facing transforms."""
from __future__ import annotations

import math
from dataclasses import dataclass

from src.characters.loader import load_poses
from src.characters.morphology import AnchorPoint, CharacterMorphology

FACINGS_8: tuple[str, ...] = ("n", "ne", "e", "se", "s", "sw", "w", "nw")
FACINGS_4: tuple[str, ...] = ("n", "e", "s", "w")
CANONICAL_FACING = "s"

# Diagonal + cardinal unit forward vectors in world XY (character default faces +Y = s).
_FACING_RAW: dict[str, tuple[int, int]] = {
    "n": (0, -1),
    "ne": (1, -1),
    "e": (1, 0),
    "se": (1, 1),
    "s": (0, 1),
    "sw": (-1, 1),
    "w": (-1, 0),
    "nw": (-1, -1),
}


def _all_pose_keys() -> tuple[str, ...]:
    keys: list[str] = []
    for f in FACINGS_8:
        keys.append(f"idle_{f}")
    for f in FACINGS_8:
        for ph in (0, 1, 2):
            keys.append(f"walk_{f}_{ph}")
    return tuple(keys)


POSE_KEYS: tuple[str, ...] = _all_pose_keys()
CANONICAL_POSE_KEYS: tuple[str, ...] = (
    "idle_s",
    "walk_s_0",
    "walk_s_1",
    "walk_s_2",
)

LAYER_ORDER: tuple[str, ...] = ("legs", "chest", "head", "amulet", "hand_l", "hand_r")


@dataclass(frozen=True)
class PoseDelta:
    """Joint offsets in metres (character faces +Y when facing=s before rotation)."""
    leg_l_fwd: float = 0.0
    leg_r_fwd: float = 0.0
    leg_l_lift: float = 0.0
    leg_r_lift: float = 0.0
    leg_l_z: float = 0.0
    leg_r_z: float = 0.0
    arm_l_fwd: float = 0.0
    arm_r_fwd: float = 0.0
    arm_l_z: float = 0.0
    arm_r_z: float = 0.0
    torso_bob: float = 0.0


_WALK_CYCLE: tuple[PoseDelta, ...] = (
    PoseDelta(
        leg_l_fwd=0.14, leg_r_fwd=-0.11,
        leg_l_lift=0.11, leg_r_lift=0.0,
        leg_l_z=0.02, leg_r_z=-0.02,
        arm_l_fwd=-0.10, arm_r_fwd=0.12,
        arm_l_z=-0.03, arm_r_z=0.04,
        torso_bob=0.04,
    ),
    PoseDelta(
        leg_l_fwd=0.03, leg_r_fwd=0.04,
        leg_l_lift=-0.04, leg_r_lift=0.09,
        leg_l_z=0.0, leg_r_z=0.0,
        arm_l_fwd=0.02, arm_r_fwd=-0.02,
        arm_l_z=0.0, arm_r_z=0.0,
        torso_bob=0.07,
    ),
    PoseDelta(
        leg_l_fwd=-0.11, leg_r_fwd=0.14,
        leg_l_lift=0.0, leg_r_lift=0.11,
        leg_l_z=-0.02, leg_r_z=0.02,
        arm_l_fwd=0.12, arm_r_fwd=-0.10,
        arm_l_z=0.04, arm_r_z=-0.03,
        torso_bob=0.04,
    ),
)


def parse_pose_id(pose_id: str) -> tuple[str, bool, int]:
    """Return (facing, walking, phase)."""
    walking = pose_id.startswith("walk_")
    body = pose_id[5:] if walking else pose_id[5:]
    for f in sorted(FACINGS_8, key=len, reverse=True):
        if body == f:
            return f, walking, 0
        if walking and body.startswith(f + "_"):
            phase_s = body[len(f) + 1:]
            phase = int(phase_s) if phase_s.isdigit() else 0
            return f, True, phase
    return CANONICAL_FACING, walking, 0


def facing_from_pose(pose_id: str) -> str:
    return parse_pose_id(pose_id)[0]


def walk_phase_from_pose(pose_id: str) -> int:
    return parse_pose_id(pose_id)[2]


def canonical_pose_id(pose_id: str) -> str:
    facing, walking, phase = parse_pose_id(pose_id)
    if walking:
        return f"walk_{CANONICAL_FACING}_{phase % 3}"
    return f"idle_{CANONICAL_FACING}"


def _walk_delta(phase: int, _facing: str) -> PoseDelta:
    return _WALK_CYCLE[phase % 3]


def load_pose_delta(pose_id: str) -> PoseDelta:
    if pose_id.startswith("walk_"):
        return _walk_delta(walk_phase_from_pose(pose_id), facing_from_pose(pose_id))
    raw = load_poses().get(pose_id, {})
    if not raw and pose_id != canonical_pose_id(pose_id):
        raw = load_poses().get(canonical_pose_id(pose_id), {})
    return PoseDelta(
        leg_l_fwd=float(raw.get("leg_l_fwd", 0)),
        leg_r_fwd=float(raw.get("leg_r_fwd", 0)),
        leg_l_lift=float(raw.get("leg_l_lift", 0)),
        leg_r_lift=float(raw.get("leg_r_lift", 0)),
        leg_l_z=float(raw.get("leg_l_z", 0)),
        leg_r_z=float(raw.get("leg_r_z", 0)),
        arm_l_fwd=float(raw.get("arm_l_fwd", 0)),
        arm_r_fwd=float(raw.get("arm_r_fwd", 0)),
        arm_l_z=float(raw.get("arm_l_z", 0)),
        arm_r_z=float(raw.get("arm_r_z", 0)),
        torso_bob=float(raw.get("torso_bob", 0)),
    )


def facing_vectors(facing: str) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return (forward_xy, right_xy) unit vectors in world space."""
    raw = _FACING_RAW.get(facing, _FACING_RAW[CANONICAL_FACING])
    fx, fy = float(raw[0]), float(raw[1])
    mag = math.hypot(fx, fy) or 1.0
    fx, fy = fx / mag, fy / mag
    return (fx, fy), (fy, -fx)


def facing_rotation_rad(facing: str) -> float:
    """Rotation from canonical facing s (+Y) to target facing."""
    tgt_fwd, _ = facing_vectors(facing)
    canon_fwd = (0.0, 1.0)
    angle_t = math.atan2(tgt_fwd[0], tgt_fwd[1])
    angle_c = math.atan2(canon_fwd[0], canon_fwd[1])
    return angle_t - angle_c


def transform_voxel_xy(
    x: int,
    y: int,
    *,
    anchor_x: int,
    anchor_y: int,
    facing: str,
) -> tuple[int, int]:
    """Rotate voxel XY around anchor from canonical facing s to target facing."""
    if facing == CANONICAL_FACING:
        return x, y
    dx = x - anchor_x
    dy = y - anchor_y
    theta = facing_rotation_rad(facing)
    c, s = math.cos(theta), math.sin(theta)
    rx = dx * c - dy * s
    ry = dx * s + dy * c
    return int(round(anchor_x + rx)), int(round(anchor_y + ry))


def transform_voxels_xy(
    voxels: dict[tuple[int, int, int], str],
    *,
    anchor_x: int,
    anchor_y: int,
    facing: str,
) -> dict[tuple[int, int, int], str]:
    if facing == CANONICAL_FACING:
        return dict(voxels)
    out: dict[tuple[int, int, int], str] = {}
    for (x, y, z), kind in voxels.items():
        nx, ny = transform_voxel_xy(x, y, anchor_x=anchor_x, anchor_y=anchor_y, facing=facing)
        out[(nx, ny, z)] = kind
    return out


def apply_pose_delta_to_point(
    joint_name: str,
    x: float,
    y: float,
    z: float,
    delta: PoseDelta,
    facing: str,
) -> tuple[float, float, float]:
    fwd, right = facing_vectors(facing)

    def _world_offset(fwd_m: float, side_m: float, up_m: float) -> tuple[float, float, float]:
        fx, fy = fwd
        rx, ry = right
        return x + fx * fwd_m + rx * side_m, y + fy * fwd_m + ry * side_m, z + up_m

    upper = {
        "chest", "shoulder_l", "shoulder_r", "elbow_l", "elbow_r",
        "wrist_l", "wrist_r", "neck_base", "head_center", "head_top",
    }
    dz_bob = delta.torso_bob if joint_name in upper else 0.0

    if joint_name == "ankle_l":
        return _world_offset(delta.leg_l_fwd, 0.0, delta.leg_l_lift + delta.leg_l_z + dz_bob)
    if joint_name == "knee_l":
        return _world_offset(delta.leg_l_fwd * 0.55, 0.0, delta.leg_l_lift * 0.65 + delta.leg_l_z * 0.5)
    if joint_name == "hip_l":
        return _world_offset(delta.leg_l_fwd * 0.12, 0.0, delta.leg_l_z * 0.2)
    if joint_name == "ankle_r":
        return _world_offset(delta.leg_r_fwd, 0.0, delta.leg_r_lift + delta.leg_r_z + dz_bob)
    if joint_name == "knee_r":
        return _world_offset(delta.leg_r_fwd * 0.55, 0.0, delta.leg_r_lift * 0.65 + delta.leg_r_z * 0.5)
    if joint_name == "hip_r":
        return _world_offset(delta.leg_r_fwd * 0.12, 0.0, delta.leg_r_z * 0.2)
    if joint_name == "wrist_l":
        return _world_offset(delta.arm_l_fwd, 0.0, delta.arm_l_z + dz_bob)
    if joint_name == "elbow_l":
        return _world_offset(delta.arm_l_fwd * 0.55, 0.0, delta.arm_l_z * 0.6 + dz_bob * 0.5)
    if joint_name == "shoulder_l":
        return _world_offset(delta.arm_l_fwd * 0.15, 0.0, dz_bob)
    if joint_name == "wrist_r":
        return _world_offset(delta.arm_r_fwd, 0.0, delta.arm_r_z + dz_bob)
    if joint_name == "elbow_r":
        return _world_offset(delta.arm_r_fwd * 0.55, 0.0, delta.arm_r_z * 0.6 + dz_bob * 0.5)
    if joint_name == "shoulder_r":
        return _world_offset(delta.arm_r_fwd * 0.15, 0.0, dz_bob)
    if joint_name in upper:
        return x, y, z + dz_bob
    if joint_name == "waist":
        return x, y, z + dz_bob * 0.3
    return x, y, z


def apply_pose(morph: CharacterMorphology, pose_id: str) -> CharacterMorphology:
    delta = load_pose_delta(pose_id)
    facing = facing_from_pose(pose_id)
    new_anchors: dict[str, AnchorPoint] = {}
    for name, pt in morph.anchors.items():
        x, y, z = apply_pose_delta_to_point(name, pt.x, pt.y, pt.z, delta, facing)
        new_anchors[name] = AnchorPoint(x, y, z)
    from dataclasses import replace

    return replace(morph, anchors=new_anchors)


def pose_key(facing: str, *, walking: bool, phase: int) -> str:
    if walking:
        return f"walk_{facing}_{phase % 3}"
    return f"idle_{facing}"


def is_valid_facing(facing: str) -> bool:
    return facing in FACINGS_8
