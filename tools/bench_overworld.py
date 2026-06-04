#!/usr/bin/env python3
"""Quick overworld frame benchmark."""
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PEPELNY_RENDER", "iso")

from src.constants import init_paths
from src.render.render_mode import init_render_mode_from_env

init_paths(ROOT)
init_render_mode_from_env()

import sys

sys.path.insert(0, os.path.join(ROOT, "tests", "performance"))
from conftest import BenchGame

g = BenchGame()
g.world_map._ensure_radius(80, 24)
ow = g.overworld
limit = ow.camera.pan_limit
for i in range(8):
    t = time.perf_counter()
    ow.camera.set_pan(int(math.sin(i) * limit * 0.8), int(math.cos(i) * limit * 0.8))
    g.perf.begin_frame()
    ow.update(16)
    ow.draw(g.buffer)
    g.perf.end_frame()
    print(
        f"frame {i}: {g.perf.last_frame_ms:.0f} ms "
        f"cols={g.perf.count('get_column')} stamps={g.perf.count('stamp')}"
    )
