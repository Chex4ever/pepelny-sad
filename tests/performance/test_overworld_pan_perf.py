"""Camera pan benchmark (complements walk playthrough in test_overworld_walk_perf)."""
from __future__ import annotations

import math

import pytest

from src.core.perf_benchmark import OverworldBenchConfig, default_budget_ms, run_overworld_playthrough
from src.core.perf_benchmark import WalkInput


class PanInput(WalkInput):
    """No movement; only camera pan changes each frame."""

    def __init__(self, camera, total: int) -> None:
        super().__init__("down")
        self._camera = camera
        self._total = total
        self._frame = 0
        self._limit = camera.pan_limit

    def begin_frame(self) -> None:
        super().begin_frame()
        t = self._frame / max(1, self._total - 1)
        self._camera.set_pan(
            int(math.sin(t * math.pi * 2) * self._limit * 0.85),
            int(math.cos(t * math.pi * 2) * self._limit * 0.85),
        )
        self._frame += 1

    def dir_key(self):
        return None


@pytest.mark.performance
@pytest.mark.slow
def test_overworld_iso_pan_frame_budget(bench_game_iso, bench_config):
    """Pan camera on preloaded world (no walking)."""
    bench_game_iso.world_map._ensure_radius(80, 24)
    cfg = OverworldBenchConfig(
        seed=bench_config.seed,
        warmup_frames=2,
        measure_frames=6,
        bootstrap_new_game=False,
    )
    pan_inp = PanInput(bench_game_iso.overworld.camera, cfg.warmup_frames + cfg.measure_frames)
    report = run_overworld_playthrough(bench_game_iso, cfg, inp=pan_inp)
    mean_budget, p95_budget = default_budget_ms("iso")
    assert report.mean_frame_ms < mean_budget
    assert report.p95_frame_ms < p95_budget
    assert report.counters_mean.get("draw_queue", 0) > 0 or bench_game_iso.perf.count("stamp") > 0
