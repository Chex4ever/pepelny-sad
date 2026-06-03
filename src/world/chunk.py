"""Chunk tile storage."""
from __future__ import annotations

from src.constants import CHUNK_SIZE


class Chunk:
    def __init__(self, cx: int, cy: int):
        self.cx = cx
        self.cy = cy
        n = CHUNK_SIZE * CHUNK_SIZE
        self.tiles = ["." ] * n
        self.fg = [(100, 130, 90)] * n
        self.bg = [(30, 45, 30)] * n
        self.explored = [False] * n
        self.biome = "meadow"

    def idx(self, lx: int, ly: int) -> int:
        return ly * CHUNK_SIZE + lx

    def in_bounds(self, lx: int, ly: int) -> bool:
        return 0 <= lx < CHUNK_SIZE and 0 <= ly < CHUNK_SIZE

    def get(self, lx: int, ly: int) -> str:
        if not self.in_bounds(lx, ly):
            return "#"
        return self.tiles[self.idx(lx, ly)]

    def set(self, lx: int, ly: int, ch: str, fg=None, bg=None):
        if not self.in_bounds(lx, ly):
            return
        i = self.idx(lx, ly)
        self.tiles[i] = ch
        if fg:
            self.fg[i] = fg
        if bg:
            self.bg[i] = bg

    def mark_explored(self, lx: int, ly: int):
        if self.in_bounds(lx, ly):
            self.explored[self.idx(lx, ly)] = True
