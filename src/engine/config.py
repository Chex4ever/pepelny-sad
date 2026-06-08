"""Engine-wide constants for floor layout and world patch sizing."""
from __future__ import annotations

import os

from src.constants import TILES_PER_M_XY

# One packed-diamond layout unit: 5×5 diag tiles = 1 m.
FLOOR_LAYOUT_TILES = TILES_PER_M_XY

# Legacy alias used across editors.
EDITOR_FLOOR_TILES = FLOOR_LAYOUT_TILES

DEFAULT_EDITOR_FLOOR_METERS = 5.0


def editor_floor_meters() -> float:
    raw = os.environ.get("PEPELNY_EDITOR_FLOOR_METERS", "").strip()
    if raw:
        return max(1.0, float(raw))
    return DEFAULT_EDITOR_FLOOR_METERS


def editor_floor_patch_tiles() -> int:
    """World-editor patch side in tiles (level editor default)."""
    return max(
        FLOOR_LAYOUT_TILES,
        int(round(editor_floor_meters() * TILES_PER_M_XY)),
    )
