"""Bilateral symmetry helpers for procedural character voxels."""
from __future__ import annotations

VoxelPos = tuple[int, int, int]

LR_KIND_SWAP: dict[str, str] = {
    "body_arm_l": "body_arm_r",
    "body_arm_r": "body_arm_l",
    "body_leg_l": "body_leg_r",
    "body_leg_r": "body_leg_l",
}

CENTER_SAFE_KINDS: frozenset[str] = frozenset(
    {
        "skin",
        "skin_ghost",
        "body_torso",
        "body_head",
        "hair",
        "scalp",
        "eye",
        "feature",
    }
)


def mirror_x(x: int, *, anchor_x: int) -> int:
    """Reflect across the sagittal plane (left ↔ right)."""
    return 2 * anchor_x - x


def mirror_xy(x: int, y: int, *, anchor_x: int, anchor_y: int) -> tuple[int, int]:
    """Left-right mirror; Y (forward) is unchanged."""
    _ = anchor_y
    return mirror_x(x, anchor_x=anchor_x), y


def swap_lr_kind(kind: str) -> str:
    return LR_KIND_SWAP.get(kind, kind)


def count_symmetry_violations(
    voxels: dict[VoxelPos, str],
    *,
    anchor_x: int,
    anchor_y: int,
) -> list[tuple[VoxelPos, str, VoxelPos, str | None, str]]:
    """Return list of (pos, kind, mirror_pos, mirror_kind, expected_kind)."""
    violations: list[tuple[VoxelPos, str, VoxelPos, str | None, str]] = []
    for (x, y, z), kind in voxels.items():
        mx, my = mirror_xy(x, y, anchor_x=anchor_x, anchor_y=anchor_y)
        expected = swap_lr_kind(kind)
        mirror_kind = voxels.get((mx, my, z))
        if mirror_kind != expected:
            violations.append(((x, y, z), kind, (mx, my, z), mirror_kind, expected))
    return violations


def enforce_bilateral_symmetry(
    voxels: dict[VoxelPos, str],
    *,
    anchor_x: int,
    anchor_y: int,
) -> dict[VoxelPos, str]:
    """Mirror left/right body parts; center column never keeps a single-sided limb."""
    out: dict[VoxelPos, str] = {}
    processed: set[VoxelPos] = set()

    for (x, y, z), kind in voxels.items():
        if (x, y, z) in processed:
            continue
        mx, my = mirror_xy(x, y, anchor_x=anchor_x, anchor_y=anchor_y)
        mirror_pos = (mx, my, z)

        if x == anchor_x:
            if kind in LR_KIND_SWAP:
                kind = "body_torso"
            out[(x, y, z)] = kind
            processed.add((x, y, z))
            continue

        left_pos = (x, y, z) if x < anchor_x else mirror_pos
        right_pos = mirror_pos if x < anchor_x else (x, y, z)
        left_kind = voxels.get(left_pos)
        right_kind = voxels.get(right_pos)

        if left_kind is None and right_kind is not None:
            left_kind = swap_lr_kind(right_kind)
        if right_kind is None and left_kind is not None:
            right_kind = swap_lr_kind(left_kind)
        if left_kind is None:
            continue

        if left_kind in LR_KIND_SWAP:
            right_kind = swap_lr_kind(left_kind)
        elif right_kind is None:
            right_kind = swap_lr_kind(left_kind)

        out[left_pos] = left_kind
        out[right_pos] = right_kind
        processed.add(left_pos)
        processed.add(right_pos)

    return out
