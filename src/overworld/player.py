"""Overworld player entity."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OverworldPlayer:
    x: int = 16
    y: int = 20
    symbol: str = "@"
    facing: tuple[int, int] = (0, 1)

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy
        if dx or dy:
            self.facing = (dx, dy)
