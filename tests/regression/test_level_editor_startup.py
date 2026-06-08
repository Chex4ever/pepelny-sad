"""Regression: level_editor startup and first frame."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.regression
def test_level_editor_smoke_cli_exits_zero():
    """Regression: level_editor must init window and draw one frame without crash."""
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    env["PEPELNY_RENDER"] = "iso"
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "level_editor.py"), "--smoke", "--size", "10"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


@pytest.mark.regression
def test_level_editor_run_smoke_frame_import():
    """Same smoke path via import (catches import/init errors in-process)."""
    import sys

    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("PEPELNY_RENDER", "iso")

    from src.characters import editor_fonts

    editor_fonts._UI_CACHE.clear()
    editor_fonts._MONO_CACHE.clear()
    editor_fonts._ICON_CACHE.clear()

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "level_editor",
        os.path.join(ROOT, "scripts", "level_editor.py"),
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.run_smoke_frame(seed=1, size=10) == 0
