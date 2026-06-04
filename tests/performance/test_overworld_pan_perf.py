"""Overworld panning performance benchmark (headless)."""
from __future__ import annotations

import math
import statistics
import time

import pytest

from src.render.render_mode import init_render_mode_from_env


def _smooth_pan(camera, frame: int, total: int, limit: int) -> None:
    t = frame / max(1, total - 1)
    camera.set_pan(
        int(math.sin(t * math.pi * 2) * limit * 0.85),
        int(math.cos(t * math.pi * 2) * limit * 0.85),
    )


def _run_overworld_frames(game, *, frames: int, warmup: int) -> list[float]:
    ow = game.overworld
    assert ow is not None
    ow.game.world_map.perf_stats = game.perf
    limit = ow.camera.pan_limit
    samples: list[float] = []

    for i in range(warmup + frames):
        _smooth_pan(ow.camera, i, warmup + frames, limit)
        t0 = time.perf_counter()
        ow.update(16)
        ow.draw(game.buffer)
        elapsed = (time.perf_counter() - t0) * 1000.0
        if i >= warmup:
            samples.append(elapsed)

    return samples


# Iso surface render is heavy (~4s/frame on dev hardware); thresholds catch regressions.
from src.constants import TARGET_FRAME_MS

_ISO_MEAN_BUDGET_MS = TARGET_FRAME_MS * 1.25
_ISO_P95_BUDGET_MS = TARGET_FRAME_MS * 2.0


@pytest.fixture
def bench_game_iso(monkeypatch):
    monkeypatch.setenv("PEPELNY_RENDER", "iso")
    init_render_mode_from_env()
    from tests.performance.conftest import BenchGame

    return BenchGame()


@pytest.mark.performance
def test_overworld_iso_pan_frame_budget(bench_game_iso):
    """Pan across loaded surface world in iso; records current perf budget."""
    bench_game_iso.world_map._ensure_radius(80, 24)

    samples = _run_overworld_frames(bench_game_iso, frames=6, warmup=2)
    mean_ms = statistics.mean(samples)
    p95_ms = sorted(samples)[int(len(samples) * 0.95)]

    assert mean_ms < _ISO_MEAN_BUDGET_MS, f"iso mean frame {mean_ms:.1f} ms (budget {_ISO_MEAN_BUDGET_MS})"
    assert p95_ms < _ISO_P95_BUDGET_MS, f"iso p95 frame {p95_ms:.1f} ms"
    assert bench_game_iso.perf.count("get_column") > 50
    assert bench_game_iso.perf.count("stamp") > 0
