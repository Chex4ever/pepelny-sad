"""Character voxel kind glyphs — shared by 3D renderer and limb legend."""
from __future__ import annotations

CHARACTER_VOXEL_GLYPHS: dict[str, str] = {
    "body_head": "H",
    "body_torso": "T",
    "body_arm_l": "l",
    "body_arm_r": "r",
    "body_leg_l": "L",
    "body_leg_r": "R",
    "hair": "@",
    "scalp": "@",
    "skin": "@",
    "skin_ghost": "@",
    "eye": "o",
    "feature": "*",
    "weapon": "/",
    "armor_chest": "#",
    "armor_legs": "#",
    "armor_head": "#",
    "lantern": "O",
    "amulet": "*",
}


def kind_glyph(kind: str) -> str:
    return CHARACTER_VOXEL_GLYPHS.get(kind, "?")
