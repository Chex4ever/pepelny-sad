"""GPU overworld walk benchmark (skipped without GL)."""
from __future__ import annotations

import pytest

from src.core.perf_benchmark import OverworldBenchConfig, default_budget_ms, run_overworld_playthrough
from src.render.gpu.context import gl_available
from src.render.render_mode import init_render_mode_from_env


@pytest.fixture
def bench_game_gpu(monkeypatch):
    """OpenGL bench; teardown restores render mode for later tests."""
    if not gl_available():
        pytest.skip("No OpenGL context")
    import pygame

    from src.constants import CELL_H, CELL_W, SCREEN_H, SCREEN_W
    from src.render.gpu.presenter import GpuPresenter
    from src.render.renderer import AsciiRenderer

    monkeypatch.setenv("PEPELNY_RENDER", "gpu")
    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    monkeypatch.delenv("SDL_AUDIODRIVER", raising=False)
    if pygame.get_init():
        pygame.display.quit()
        pygame.quit()
    init_render_mode_from_env()
    pygame.init()
    pixel_w, pixel_h = SCREEN_W * CELL_W, SCREEN_H * CELL_H
    screen = pygame.display.set_mode((pixel_w, pixel_h), pygame.OPENGL | pygame.DOUBLEBUF)
    from tests.performance.conftest import BenchGame

    g = BenchGame()
    g.gpu_presenter = GpuPresenter(screen, AsciiRenderer(screen))
    if not g.gpu_presenter.available:
        pytest.skip("GPU presenter unavailable")
    try:
        yield g
    finally:
        if pygame.get_init():
            pygame.display.quit()
            pygame.quit()
        init_render_mode_from_env()


@pytest.mark.performance
@pytest.mark.slow
def test_overworld_gpu_walk_frame_budget(bench_game_gpu):
    """GPU map path budget (flip/vsync excluded — varies by driver)."""
    cfg = OverworldBenchConfig(warmup_frames=8, measure_frames=16)
    report = run_overworld_playthrough(bench_game_gpu, cfg, gpu_present=True)
    map_stage = next((s for s in report.stages if s.key == "map_draw"), None)
    assert map_stage is not None, report.text_lines()[:8]
    map_budget = float(
        __import__("os").environ.get("PEPELNY_GPU_MAP_MS", "25")
    )
    assert map_stage.mean_ms < map_budget, (
        f"gpu map mean {map_stage.mean_ms:.1f} ms > {map_budget}\n"
        + "\n".join(report.text_lines()[:12])
    )
    stage_keys = {s.key for s in report.stages}
    assert "present" in stage_keys or "gpu_map" in stage_keys
