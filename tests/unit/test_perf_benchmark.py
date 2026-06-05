"""Perf benchmark harness (fast, no GL)."""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from src.core.perf_benchmark import OverworldBenchConfig, WalkInput, run_overworld_playthrough
from src.render.iso_projector import IsoProjector
from src.render.render_mode import init_render_mode_from_env
import pytest


@pytest.fixture(autouse=True)
def _iso_render_mode(monkeypatch):
    monkeypatch.setenv("PEPELNY_RENDER", "iso")
    init_render_mode_from_env()


def test_walk_input_iso_down():
    inp = WalkInput("down")
    inp.begin_frame()
    assert inp.dir_key() == IsoProjector.screen_delta_to_world(0, 1)


def test_playthrough_moves_player():
    from tests.performance.conftest import BenchGame

    game = BenchGame()
    cfg = OverworldBenchConfig(
        bootstrap_new_game=True,
        warmup_frames=2,
        measure_frames=5,
    )
    report = run_overworld_playthrough(game, cfg)
    assert report.player_end != report.player_start
    assert report.frames_measured == 5
    assert report.stages
