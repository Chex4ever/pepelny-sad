"""Fixed iso-stencil view constants for characters and static objects."""
from __future__ import annotations

import math

from src.constants import ISO_STEP_X, ISO_STEP_Y, TILES_PER_M_XY

# Implicit floor diamond slope from 2:1 iso steps (~26.6° from horizontal).
ISO_FLOOR_SLOPE_DEG = math.degrees(math.atan2(ISO_STEP_Y, ISO_STEP_X))

# Camera pitch (degrees, negative = looking down). Static objects closer to floor plane.
PITCH_STATIC_DEG = -22.0
PITCH_CHARACTER_DEG = -34.0

# Front-on camera for editor (yaw 0 at facing S). Oblique game trees use ~30° in Orbit3D.
YAW_DEFAULT_DEG = 0.0

YAW_FACINGS = 8
ZOOM_FIXED = 1.0

# Editor floor grid extent (5×5 tiles = 1 m at TILES_PER_M_XY=5).
EDITOR_FLOOR_TILES = TILES_PER_M_XY

# Iso game view glyph scale (editor only; 1× = in-game cell size).
EDITOR_VIEW_SCALE_MIN = 1
EDITOR_VIEW_SCALE_MAX = 4
EDITOR_VIEW_SCALES: tuple[int, ...] = (1, 2, 3, 4)

# Max air gap (tile units) under feet before 'a' diagnostic.
AIR_GAP_TILES = 1

# Eight camera yaw snaps (degrees): N, NE, E, SE, S, SW, W, NW viewpoints.
YAW_SNAPS_DEG: tuple[float, ...] = tuple(i * 45.0 for i in range(8))

YAW_SNAP_LABELS: tuple[str, ...] = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def yaw_snap_index(yaw_deg: float) -> int:
    """Nearest yaw snap index for a given yaw in degrees."""
    norm = yaw_deg % 360.0
    best, best_d = 0, 360.0
    for i, snap in enumerate(YAW_SNAPS_DEG):
        d = min(abs(norm - snap), abs(norm - snap - 360), abs(norm - snap + 360))
        if d < best_d:
            best_d = d
            best = i
    return best


def snap_yaw_deg(yaw_deg: float) -> float:
    return YAW_SNAPS_DEG[yaw_snap_index(yaw_deg)]
