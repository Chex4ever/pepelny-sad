"""Shared fixtures for unit and integration tests."""
from __future__ import annotations

import os
import sys

import pytest

# Headless pygame before any game imports.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PEPELNY_RENDER", "classic")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# NOTE: init_paths here hides startup-order bugs (DATA_DIR captured at import).
# See tests/regression/test_startup_data_dir.py for subprocess tests that mimic
# `python main.py` without this early initialization.
from src.constants import init_paths
from src.data.art_init import ensure_art_files

init_paths(ROOT)
from src.i18n import init_locale_from_env

init_locale_from_env()
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
    from src.overworld.overworld_scene import OverworldScene
    from src.progression.player_profile import PlayerProfile
    from src.world.world_map import WorldMap
    from src.world.world_state import WorldState

    g = Game()
    g.world_state = WorldState(world_seed=4242)
    g.profile = PlayerProfile()
    g.profile.inventory.add("grey_herb", 3, 20)
    g.profile.inventory.add("root_fiber", 2, 20)
    g.world_map = WorldMap(4242)
    g.world_map.perf_stats = g.perf
    g.overworld = OverworldScene(g)
    g.scene = "overworld"
    g.transition.active = False
    return g


def drain_transition(game, step_ms: int = 300):
    """Advance TransitionManager until idle (for tests)."""
    while game.transition.active:
        game.transition.update(step_ms)


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
        self.mouse_down: set[int] = set()
        self.mouse_pressed: set[int] = set()
        self.mouse_released: set[int] = set()

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

    def any_key_pressed(self) -> bool:
        return bool(self._pressed)

    def pressed_escape(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_ESCAPE)

    def pressed_f1(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_F1)

    def pressed_f4(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_F4)

    def pressed_tab(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_TAB)

    def pressed_e(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_e)

    def pressed_f5(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_F5)

    def pressed_f9(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_F9)

    def nav_up_pressed(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_UP, pygame.K_w)

    def nav_down_pressed(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_DOWN, pygame.K_s)

    def nav_left_pressed(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_LEFT, pygame.K_a)

    def nav_right_pressed(self) -> bool:
        import pygame
        return self.any_pressed(pygame.K_RIGHT, pygame.K_d)

    def nav_up_held(self) -> bool:
        return self.nav_up_pressed()

    def nav_down_held(self) -> bool:
        return self.nav_down_pressed()

    def nav_left_held(self) -> bool:
        return self.nav_left_pressed()

    def nav_right_held(self) -> bool:
        return self.nav_right_pressed()

    def mouse_left_clicked(self) -> bool:
        return 1 in self.mouse_pressed

    def mouse_left_down(self) -> bool:
        return 1 in self.mouse_pressed

    def mouse_left_held(self) -> bool:
        return 1 in self.mouse_down

    def mouse_left_released(self) -> bool:
        return 1 in self.mouse_released

    def mouse_middle_down(self) -> bool:
        return 2 in self.mouse_pressed

    def mouse_middle_held(self) -> bool:
        return 2 in self.mouse_down

    def mouse_middle_released(self) -> bool:
        return 2 in self.mouse_released

    def mouse_dragging(self, threshold: int = 4) -> bool:
        return False

    def mouse_on_map(self, map_origin_y: int = 0) -> bool:
        return False

    def mouse_delta(self) -> tuple[int, int]:
        return (0, 0)

    def mouse_grid(self, char_w=16, char_h=16) -> tuple[int, int]:
        return (0, 0)

    def mouse_world(self, camera, camera_y=None, map_origin_y=None):
        return None

    def handle_event(self, event):
        pass

    def sync_keyboard(self):
        pass

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
