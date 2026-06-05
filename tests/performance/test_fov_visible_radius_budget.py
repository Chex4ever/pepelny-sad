"""FOV at gameplay visible radius (not legacy r=100)."""
from __future__ import annotations

import os
import time

import pytest

from src.constants import VISIBLE_LOS_RADIUS_SURFACE
from src.overworld.fov import cast_los_fov


@pytest.mark.performance
def test_fov_visible_los_radius_budget(bench_game_iso):
    game = bench_game_iso
    wm = game.world_map
    layer = "surface"
    px, py = game.overworld.player.tile_pos()
    radius = VISIBLE_LOS_RADIUS_SURFACE
    blocks_fn = lambda x, y: wm.fast_blocks_los(x, y, layer)

    budget_ms = float(os.environ.get("PEPELNY_FOV_LOS_MS", "8"))

    samples: list[float] = []
    for _ in range(8):
        t0 = time.perf_counter()
        visible = cast_los_fov(px, py, radius, blocks_fn)
        samples.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = sum(samples) / len(samples)
    assert len(visible) > 50
    assert mean_ms < budget_ms, f"fov_los mean {mean_ms:.2f} ms > {budget_ms} ms at r={radius}"
