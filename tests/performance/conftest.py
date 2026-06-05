"""Fixtures for performance benchmarks (playthrough-style)."""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from src.audio.ambient_controller import AmbientController
from src.audio.audio_manager import AudioManager
from src.constants import SCREEN_H, SCREEN_W
from src.core.perf_benchmark import OverworldBenchConfig
from src.core.perf_stats import PerfStats
from src.progression.player_profile import PlayerProfile
from src.render.render_mode import init_render_mode_from_env
from src.render.screen_buffer import ScreenBuffer
from src.scenes.overworld.overworld_scene import OverworldScene
from src.ui.windows.window_manager import WindowManager
from src.world.world_map import WorldMap
from src.world.world_state import WorldState

class BenchGame:
    """Minimal game shell; use bootstrap_bench_world() for new-game parity."""

    def __init__(self, seed: int = 4242) -> None:
        self.perf = PerfStats(history=256)
        self.world_state = WorldState(world_seed=seed)
        self.world_state.layer = "surface"
        self.profile = PlayerProfile()
        self.world_map = WorldMap(seed)
        self.world_map.perf_stats = self.perf
        self.buffer = ScreenBuffer(SCREEN_W, SCREEN_H)
        self.windows = WindowManager()
        self.audio = AudioManager()
        self.ambient = AmbientController(self.audio)
        self.overworld = OverworldScene(self)
        self.gpu_presenter = None

    def serialize_state(self) -> dict:
        return {"seed": self.world_state.world_seed}


@pytest.fixture
def bench_game() -> BenchGame:
    return BenchGame()


@pytest.fixture
def bench_config() -> OverworldBenchConfig:
    return OverworldBenchConfig(
        warmup_frames=int(os.environ.get("PEPELNY_BENCH_WARMUP", "10")),
        measure_frames=int(os.environ.get("PEPELNY_BENCH_FRAMES", "30")),
    )


@pytest.fixture
def bench_game_iso(monkeypatch) -> BenchGame:
    monkeypatch.setenv("PEPELNY_RENDER", "iso")
    init_render_mode_from_env()
    return BenchGame()
