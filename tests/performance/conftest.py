"""Lightweight fixtures for performance benchmarks (no full Game loop)."""
from __future__ import annotations

import os

os.environ.setdefault("PEPELNY_RENDER", "iso")

import pytest

from src.render.render_mode import init_render_mode_from_env

init_render_mode_from_env()

from src.audio.ambient_controller import AmbientController
from src.audio.audio_manager import AudioManager
from src.constants import SCREEN_H, SCREEN_W
from src.core.perf_stats import PerfStats
from src.progression.player_profile import PlayerProfile
from src.render.screen_buffer import ScreenBuffer
from src.scenes.overworld.overworld_scene import OverworldScene
from src.ui.windows.window_manager import WindowManager
from src.world.world_map import WorldMap
from src.world.world_state import WorldState


class BenchGame:
    """Minimal game shell for overworld draw/update timing."""

    def __init__(self, seed: int = 4242) -> None:
        self.perf = PerfStats()
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


@pytest.fixture
def bench_game() -> BenchGame:
    return BenchGame()
