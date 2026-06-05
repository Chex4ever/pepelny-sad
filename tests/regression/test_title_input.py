"""Regression: title screen input and SDL dummy env must not break gameplay."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run(code: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    full_env = os.environ.copy()
    full_env["SDL_VIDEODRIVER"] = "dummy"
    full_env["SDL_AUDIODRIVER"] = "dummy"
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=full_env,
        capture_output=True,
        text=True,
    )


@pytest.mark.regression
def test_main_py_clears_dummy_sdl_driver():
    code = f"""
import sys
sys.path.insert(0, {ROOT!r})
import main
import os
assert os.environ.get("SDL_VIDEODRIVER") != "dummy"
print("cleared")
"""
    result = _run(code)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.regression
def test_title_starts_game_on_confirm():
    code = f"""
import sys
sys.path.insert(0, {ROOT!r})
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
from src.constants import init_paths
init_paths({ROOT!r})
import pygame
pygame.init()
pygame.display.set_mode((100, 100))

from src.game import Game
from src.input import InputState

g = Game()
g.scene = "title"
seed_before = g.title_seed

inp = InputState()
inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
inp.sync_keyboard()
g.input = inp
g._update_title()

while g.transition.active:
    g.transition.update(300)
while g.loading.active:
    g.loading.tick(g, 500)
while g.transition.active:
    g.transition.update(300)

assert g.scene == "intro", g.scene
assert g.overworld is not None
print("title ok")
"""
    result = _run(code)
    assert result.returncode == 0, result.stderr or result.stdout
