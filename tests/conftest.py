"""Shared fixtures for unit and integration tests."""
from __future__ import annotations

import os
import sys

import pytest

# Headless pygame before any game imports.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# NOTE: init_paths here hides startup-order bugs (DATA_DIR captured at import).
# See tests/regression/test_startup_data_dir.py for subprocess tests that mimic
# `python main.py` without this early initialization.
from src.constants import init_paths
from src.data.art_init import ensure_art_files

init_paths(ROOT)
ensure_art_files()


@pytest.fixture(scope="session", autouse=True)
def _paths_ready():
    """Ensure paths stay initialized for the whole session."""
    yield


@pytest.fixture
def world_state():
    from src.world.world_state import WorldState

    return WorldState(world_seed=12345)


@pytest.fixture
def profile():
    from src.progression.player_profile import PlayerProfile

    p = PlayerProfile()
    p.inventory.add("grey_herb", 5, 20)
    p.inventory.add("root_fiber", 5, 20)
    p.inventory.add("ash_clump", 10, 30)
    return p


@pytest.fixture
def world_map(world_state):
    from src.world.world_map import WorldMap

    return WorldMap(world_state.world_seed)


@pytest.fixture
def screen_buffer():
    from src.constants import SCREEN_H, SCREEN_W
    from src.render.screen_buffer import ScreenBuffer

    return ScreenBuffer(SCREEN_W, SCREEN_H)


@pytest.fixture
def game():
    from src.game import Game

    g = Game()
    g.new_game(seed=4242)
    return g


@pytest.fixture
def save_path(tmp_path, monkeypatch):
    path = tmp_path / "save.pkl"
    monkeypatch.setattr("src.world.save.SAVE_PATH", str(path))
    return path


class FakeInput:
    """Minimal input stub for scene tests."""

    def __init__(self, pressed: set | None = None, held: set | None = None):
        self._pressed = pressed or set()
        self._held = held or set()

    def begin_frame(self):
        pass

    def pressed(self, key) -> bool:
        return key in self._pressed

    def held(self, key) -> bool:
        return key in self._held

    def any_pressed(self, *keys) -> bool:
        return any(k in self._pressed for k in keys)

    def action_pressed(self) -> bool:
        import pygame

        return self.any_pressed(pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)

    def confirm_pressed(self) -> bool:
        return self.action_pressed()

    def dir_key(self):
        import pygame

        if self.any_pressed(pygame.K_UP, pygame.K_w):
            return (0, -1)
        if self.any_pressed(pygame.K_DOWN, pygame.K_s):
            return (0, 1)
        if self.any_pressed(pygame.K_LEFT, pygame.K_a):
            return (-1, 0)
        if self.any_pressed(pygame.K_RIGHT, pygame.K_d):
            return (1, 0)
        return None


@pytest.fixture
def fake_input_factory():
    return FakeInput
