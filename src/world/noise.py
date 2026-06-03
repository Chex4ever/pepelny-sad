"""Simple value noise for terrain."""
from __future__ import annotations

import random


def _fade(t: float) -> float:
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class ValueNoise2D:
    def __init__(self, seed: int):
        rng = random.Random(seed)
        self.grid = [[rng.random() for _ in range(256)] for _ in range(256)]

    def _val(self, x: int, y: int) -> float:
        return self.grid[x & 255][y & 255]

    def noise(self, x: float, y: float) -> float:
        x0, y0 = int(x) & 255, int(y) & 255
        x1, y1 = (x0 + 1) & 255, (y0 + 1) & 255
        sx = _fade(x - int(x))
        sy = _fade(y - int(y))
        n0 = _lerp(self._val(x0, y0), self._val(x1, y0), sx)
        n1 = _lerp(self._val(x0, y1), self._val(x1, y1), sx)
        return _lerp(n0, n1, sy)
