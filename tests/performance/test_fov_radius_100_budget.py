"""Fast FOV-only budget at surface radius (no full walk playthrough)."""
from __future__ import annotations

import os
import time

import pytest

from src.constants import SURFACE_FOV_RADIUS_TILES
from src.overworld.fov import cast_los_fov


@pytest.mark.performance
def test_fov_radius_100_budget(bench_game_iso):
    """LOS at r=100 should stay well under the old ~2s raycast path."""
    game = bench_game_iso
    wm = game.world_map
    layer = "surface"
    px, py = game.overworld.player.tile_pos()
    radius = SURFACE_FOV_RADIUS_TILES
    blocks_fn = lambda x, y: wm.fast_blocks_los(x, y, layer)

    budget_ms = float(os.environ.get("PEPELNY_FOV_LOS_MS", "100"))

    samples: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        visible = cast_los_fov(px, py, radius, blocks_fn)
        samples.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = sum(samples) / len(samples)
    assert len(visible) > 1000
    assert mean_ms < budget_ms, f"fov_los mean {mean_ms:.1f} ms > {budget_ms} ms"
