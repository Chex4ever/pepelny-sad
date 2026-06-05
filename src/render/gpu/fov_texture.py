"""Optional GPU FOV (polar ray-march). Disabled by default — CPU shadowcast at VISIBLE_LOS_RADIUS is faster to ship.

Enable future work with PEPELNY_GPU_FOV=1 once occluder atlas + fog pass are wired.
"""
from __future__ import annotations

import os


def gpu_fov_enabled() -> bool:
    return os.environ.get("PEPELNY_GPU_FOV", "0").strip().lower() in ("1", "true", "yes")
