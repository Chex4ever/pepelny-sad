"""Regression tests for startup and DATA_DIR initialization.

These run in isolated subprocesses WITHOUT tests/conftest.py pre-init,
because conftest calls init_paths() at import time and hides the bug where
loaders captured DATA_DIR=None before init_paths().
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_isolated(code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


@pytest.mark.regression
def test_loaders_work_after_init_paths_real_import_order():
    """Regression: art_loader must read DATA_DIR lazily, not at import time."""
    code = f"""
import sys
sys.path.insert(0, {ROOT!r})

from src import constants
from src.data import art_loader

assert constants.DATA_DIR is None, "DATA_DIR must start unset"

from src.constants import init_paths
init_paths({ROOT!r})

biomes = art_loader.load_biomes()
assert "meadow" in biomes
assert art_loader.load_enemies()["whisper"]["name"]
assert art_loader.load_items()["ash_blade"]["fight_damage"] == 12
print("loaders ok")
"""
    result = _run_isolated(code)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.regression
def test_world_map_after_real_import_order():
    """Regression: WorldMap must not crash when init_paths runs after imports."""
    code = f"""
import sys
sys.path.insert(0, {ROOT!r})

from src.data.art_loader import load_biomes  # noqa: F401 — triggers early import
from src.constants import init_paths
init_paths({ROOT!r})

from src.world.world_map import WorldMap
wm = WorldMap(42)
ch, fg, bg = wm.get_tile(0, 0)
assert ch != ""
print("world ok")
"""
    result = _run_isolated(code)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.regression
def test_game_init_matches_main_py_entry_order():
    """Regression: Game() must succeed with the same init order as main.py."""
    code = f"""
import sys
sys.path.insert(0, {ROOT!r})

from src.constants import init_paths
init_paths({ROOT!r})

from src.game import Game
g = Game()
assert g.world_map is not None
g.new_game(seed=1)
assert g.scene == "overworld"
print("game ok")
"""
    result = _run_isolated(code)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.regression
def test_main_module_import_chain():
    """Regression: importing main.py must not leave DATA_DIR unset."""
    code = f"""
import sys
sys.path.insert(0, {ROOT!r})

import main  # noqa: F401 — runs init_paths in main.py
from src import constants
from src.data.art_loader import load_biomes

assert constants.DATA_DIR is not None
assert "ashen_forest" in load_biomes()
print("main ok")
"""
    result = _run_isolated(code)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.regression
def test_landmarks_and_segments_after_init_paths():
    """Regression: landmark/segment loaders must resolve paths after init_paths."""
    code = f"""
import sys
sys.path.insert(0, {ROOT!r})

from src.constants import init_paths
init_paths({ROOT!r})

from src.world.landmark_placer import _load_landmark
from src.world.segment_loader import load_segment

assert _load_landmark("sanctuary_gate"), "sanctuary landmark missing"
lines, meta = load_segment("corridor_01")
assert lines and meta["kind"] == "corridor"
print("assets ok")
"""
    result = _run_isolated(code)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.regression
def test_load_biomes_fails_without_init_paths():
    """Document expected failure when init_paths was never called."""
    code = f"""
import sys
sys.path.insert(0, {ROOT!r})

from src import constants
from src.data.art_loader import load_biomes

constants.DATA_DIR = None
load_biomes.cache_clear()

try:
    load_biomes()
except RuntimeError as e:
    assert "init_paths" in str(e)
    print("guard ok")
else:
    raise SystemExit("expected RuntimeError")
"""
    result = _run_isolated(code)
    assert result.returncode == 0, result.stderr or result.stdout
