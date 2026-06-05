#!/usr/bin/env python3
"""Run overworld walk benchmark and print/write JSON report.

Examples:
  python scripts/run_perf_benchmark.py
  PEPELNY_RENDER=gpu python scripts/run_perf_benchmark.py
  PEPELNY_PERF_REPORT=benchmark.json PEPELNY_PERF=1 python scripts/run_perf_benchmark.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.constants import init_paths
from src.core.perf_benchmark import (
    OverworldBenchConfig,
    default_budget_ms,
    default_fov_los_budget_ms,
    default_frame_budget_ms,
    default_gpu_batch_budget,
    default_gpu_map_budget_ms,
    maybe_write_report,
    run_overworld_playthrough,
)
from src.render.render_mode import init_render_mode_from_env, render_mode


def main() -> int:
    init_paths(ROOT)
    init_render_mode_from_env()
    mode = render_mode()

    from tests.performance.conftest import BenchGame

    game = BenchGame()
    gpu = mode == "gpu"

    if gpu:
        import pygame

        from src.constants import CELL_H, CELL_W, SCREEN_H, SCREEN_W
        from src.render.gpu.presenter import GpuPresenter
        from src.render.renderer import AsciiRenderer

        os.environ.pop("SDL_VIDEODRIVER", None)
        os.environ.pop("SDL_AUDIODRIVER", None)
        if pygame.get_init():
            pygame.display.quit()
            pygame.quit()
        pygame.init()
        screen = pygame.display.set_mode(
            (SCREEN_W * CELL_W, SCREEN_H * CELL_H),
            pygame.OPENGL | pygame.DOUBLEBUF,
        )
        game.gpu_presenter = GpuPresenter(screen, AsciiRenderer(screen))
        if not game.gpu_presenter.available:
            print("GPU unavailable, falling back to buffer-only timing")
            gpu = False

    cfg = OverworldBenchConfig(
        warmup_frames=int(os.environ.get("PEPELNY_BENCH_WARMUP", "15")),
        measure_frames=int(os.environ.get("PEPELNY_BENCH_FRAMES", "40")),
    )
    report = run_overworld_playthrough(game, cfg, gpu_present=gpu)
    path = maybe_write_report(report)
    mean_b, p95_b = (
        default_frame_budget_ms() if gpu else default_budget_ms(mode)
    )

    for line in report.text_lines():
        print(line)
    print(f"Budget ({mode}): mean < {mean_b:.0f} ms, p95 < {p95_b:.0f} ms")
    if report.stages:
        print("--- top stages ---")
        for s in report.stages[:3]:
            print(f"  {s.label:<22} {s.mean_ms:7.2f} ms  ({s.share_pct:4.1f}%)")
    fov_budget = default_fov_los_budget_ms()
    fov_stage = next((s for s in report.stages if s.key == "fov_los"), None)
    if fov_stage is not None:
        print(f"fov_los: mean {fov_stage.mean_ms:.1f} ms (budget < {fov_budget:.0f} ms)")
    if gpu:
        gpu_map = next((s for s in report.stages if s.key == "gpu_map"), None)
        batch = report.counters_mean.get("gpu_batch", 0)
        print(
            f"gpu_map: mean {gpu_map.mean_ms:.1f} ms (budget < {default_gpu_map_budget_ms():.0f} ms)"
            if gpu_map
            else "gpu_map: (missing)"
        )
        print(f"gpu_batch: mean {batch:.0f} (budget <= {default_gpu_batch_budget()})")
    if path:
        print(f"Wrote {path}")
    if gpu and report.mean_frame_ms >= mean_b:
        return 1
    if gpu:
        gpu_map = next((s for s in report.stages if s.key == "gpu_map"), None)
        if gpu_map is not None and gpu_map.mean_ms >= default_gpu_map_budget_ms():
            return 1
        if report.counters_mean.get("gpu_batch", 0) > default_gpu_batch_budget():
            return 1
    if not gpu and report.mean_frame_ms >= mean_b:
        return 1
    if fov_stage is not None and fov_stage.mean_ms >= fov_budget:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
