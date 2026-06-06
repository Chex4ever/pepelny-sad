"""GPU overworld walk — full frame must stay under 16 ms (gameplay path)."""
from __future__ import annotations

import os

import pytest

from src.core.perf_benchmark import (
    OverworldBenchConfig,
    default_frame_budget_ms,
    default_gpu_batch_budget,
    default_gpu_map_budget_ms,
    run_overworld_playthrough,
)
from src.render.gpu.context import gl_available
from src.render.render_mode import init_render_mode_from_env


@pytest.fixture
def bench_game_gpu(monkeypatch):
    """OpenGL bench; teardown restores render mode for later tests."""
    if not gl_available():
        pytest.fail(
            "OpenGL required for gameplay perf gate (PEPELNY_RENDER=gpu). "
            "Install GPU drivers or set PEPELNY_SKIP_GPU_PERF=1 only in local debug."
        )
    if os.environ.get("PEPELNY_SKIP_GPU_PERF", "").strip().lower() in ("1", "true", "yes"):
        pytest.skip("PEPELNY_SKIP_GPU_PERF=1")
    import pygame

    from src.constants import CELL_H, CELL_W, SCREEN_H, SCREEN_W
    from src.render.gpu.presenter import GpuPresenter
    from src.render.renderer import AsciiRenderer

    monkeypatch.setenv("PEPELNY_RENDER", "gpu")
    monkeypatch.setenv("PEPELNY_BENCH", "1")
    monkeypatch.setenv("PEPELNY_GPU_SPLAT", "1")
    monkeypatch.setenv("PEPELNY_VISIBLE_LOS", "24")
    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    monkeypatch.delenv("SDL_AUDIODRIVER", raising=False)
    if pygame.get_init():
        pygame.display.quit()
        pygame.quit()
    init_render_mode_from_env()
    pygame.init()
    from src.render.gpu.context import configure_bench_gl_attributes

    configure_bench_gl_attributes()
    pixel_w, pixel_h = SCREEN_W * CELL_W, SCREEN_H * CELL_H
    screen = pygame.display.set_mode((pixel_w, pixel_h), pygame.OPENGL | pygame.DOUBLEBUF)
    from tests.performance.conftest import BenchGame

    g = BenchGame()
    g.gpu_presenter = GpuPresenter(screen, AsciiRenderer(screen))
    if not g.gpu_presenter.available:
        pytest.fail("GPU presenter unavailable — gameplay path cannot meet 16 ms budget")
    try:
        yield g
    finally:
        if pygame.get_init():
            pygame.display.quit()
            pygame.quit()
        init_render_mode_from_env()


def _stage(report, key: str):
    return next((s for s in report.stages if s.key == key), None)


@pytest.mark.performance
@pytest.mark.slow
def test_overworld_gpu_full_frame_under_16ms(bench_game_gpu):
    """Full overworld frame with GPU present — same path as in-game PEPELNY_RENDER=gpu."""
    cfg = OverworldBenchConfig(
        warmup_frames=10,
        measure_frames=40,
        measure_burn_in=2,
        warmup_stand_frames=6,
        dt_ms=16,
        stand_still_measure=True,
    )
    report = run_overworld_playthrough(bench_game_gpu, cfg, gpu_present=True)

    mean_b, p95_b = default_frame_budget_ms()
    map_b = default_gpu_map_budget_ms()
    batch_b = default_gpu_batch_budget()

    gpu_map = _stage(report, "gpu_map")
    gpu_batch = report.counters_mean.get("gpu_batch", 0)

    lines = "\n".join(report.text_lines()[:16])
    assert report.mean_frame_ms < mean_b, (
        f"full frame mean {report.mean_frame_ms:.1f} ms > {mean_b} ms (60 FPS gate)\n{lines}"
    )
    assert report.p95_frame_ms < p95_b, (
        f"full frame p95 {report.p95_frame_ms:.1f} ms > {p95_b} ms\n{lines}"
    )
    assert gpu_map is not None, f"gpu_map stage missing\n{lines}"
    assert gpu_map.mean_ms < map_b, (
        f"gpu_map mean {gpu_map.mean_ms:.1f} ms > {map_b} ms "
        f"(gpu_batch≈{gpu_batch:.0f})\n{lines}"
    )
    assert gpu_batch <= batch_b, (
        f"gpu_batch mean {gpu_batch:.0f} > {batch_b} quads/frame\n{lines}"
    )
