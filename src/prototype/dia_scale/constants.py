"""Scale and display constants for test_2x1_dia (prototype only)."""
from __future__ import annotations

from src.constants import (
    STAMP_PREVIEW,
    TILE_XY_M,
    TILE_Z_M,
    TILES_PER_M_XY,
    TILES_PER_M_Z,
)

# Iso-square 2a stamp bbox (chars on floor meadow)
STAMP_CW = 3
STAMP_CH = 2

# Legacy aliases (floor char horizontal size derived from iso-square width)
TILES_PER_M = TILES_PER_M_XY
TILE_WIDTH_M = TILE_XY_M
CHAR_SIZE_M = TILE_WIDTH_M / STAMP_CW

# Voxel tree defaults
TREE_HEIGHT_TILES = 100
TRUNK_BASE_TILES = 4
TRUNK_BASE_RADIUS = TRUNK_BASE_TILES // 2

# Player height in Z tile units (~1.8 m)
PLAYER_HEIGHT_TILES = 18
PLAYER_HEIGHT_CHARS = PLAYER_HEIGHT_TILES
PLAYER_HEIGHT_M = PLAYER_HEIGHT_TILES * TILE_Z_M

# Voxel kind labels
VOXEL_TRUNK = "trunk"
VOXEL_BRANCH = "branch"
VOXEL_LEAF = "leaf"
VOXEL_SKIN = "skin"
VOXEL_HAIR = "hair"
VOXEL_ARMOR = "armor_chest"
VOXEL_WEAPON = "weapon"

# Colors (RGB)
COLOR_BG = (12, 14, 22)
COLOR_FLOOR_FG = (120, 145, 90)
COLOR_FLOOR_BG = (28, 42, 28)
COLOR_FLOOR_ALT_FG = (100, 130, 75)
COLOR_TRUNK_FG = (130, 95, 60)
COLOR_TRUNK_BG = (35, 28, 20)
COLOR_BRANCH_FG = (110, 85, 55)
COLOR_BRANCH_BG = (30, 25, 18)
COLOR_CANOPY_FG = (65, 120, 65)
COLOR_CANOPY_BG = (22, 38, 22)
COLOR_LEAF_FG = (55, 110, 55)
COLOR_LEAF_BG = (18, 32, 18)
COLOR_BUSH_FG = (85, 130, 70)
COLOR_BUSH_BG = (25, 40, 25)
COLOR_PLAYER_FG = (255, 220, 120)
COLOR_PLAYER_BG = (8, 8, 18)
COLOR_HUD = (170, 175, 190)
COLOR_SECTION_BG = (16, 18, 28)
COLOR_SLICE_LINE = (255, 210, 90)

ROTATION_LABELS = ("0° (N)", "90° (E)", "180° (S)", "270° (W)")
