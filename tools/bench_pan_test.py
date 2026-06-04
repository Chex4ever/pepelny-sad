import math
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["PEPELNY_RENDER"] = "classic"

from src.constants import init_paths
from src.render.render_mode import init_render_mode_from_env, render_mode

init_paths(ROOT)
init_render_mode_from_env()
print("mode", render_mode())

from tests.performance.conftest import BenchGame

g = BenchGame()
g.world_map._ensure_radius(80, 24)
ow = g.overworld
limit = ow.camera.pan_limit
samples = []
for i in range(10):
    t = i / 9
    ow.camera.set_pan(
        int(math.sin(t * 6.28) * limit * 0.85),
        int(math.cos(t * 6.28) * limit * 0.85),
    )
    g.perf.begin_frame()
    t0 = time.perf_counter()
    ow.update(16)
    ow.draw(g.buffer)
    ms = (time.perf_counter() - t0) * 1000
    samples.append(ms)
    print(f"{i}: {ms:.0f}ms cols={g.perf.count('get_column')}")
print("mean", statistics.mean(samples))
