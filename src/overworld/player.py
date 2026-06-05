"""Overworld player entity (grid tile + smooth render position)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OverworldPlayer:
    tile_x: int = 16
    tile_y: int = 20
    x: float = 16.0
    y: float = 20.0
    symbol: str = "@"
    facing: tuple[int, int] = (0, 1)
    _move_t: float = 1.0
    _move_dx: int = 0
    _move_dy: int = 0

    def tile_pos(self) -> tuple[int, int]:
        return self.tile_x, self.tile_y

    def set_tile(self, tx: int, ty: int) -> None:
        self.tile_x = tx
        self.tile_y = ty
        self.x = float(tx)
        self.y = float(ty)
        self._move_t = 1.0
        self._move_dx = 0
        self._move_dy = 0

    def move(self, dx: int, dy: int) -> None:
        """Instant grid step (save/load, scene transitions)."""
        self.set_tile(self.tile_x + dx, self.tile_y + dy)
        if dx or dy:
            self.facing = (dx, dy)

    def is_moving(self) -> bool:
        return self._move_t < 1.0

    def begin_stride(self, dx: int, dy: int) -> None:
        if dx or dy:
            self.facing = (dx, dy)
        self._move_dx = dx
        self._move_dy = dy
        self._move_t = 0.0

    def update_motion(self, dt_ms: int, *, speed_tps: float) -> bool:
        """Advance interpolation; return True when a grid tile was entered."""
        if self._move_t >= 1.0:
            return False
        step = (dt_ms / 1000.0) * speed_tps
        self._move_t = min(1.0, self._move_t + step)
        self.x = self.tile_x + self._move_dx * self._move_t
        self.y = self.tile_y + self._move_dy * self._move_t
        if self._move_t >= 1.0:
            self.tile_x += self._move_dx
            self.tile_y += self._move_dy
            self.x = float(self.tile_x)
            self.y = float(self.tile_y)
            self._move_dx = 0
            self._move_dy = 0
            return True
        return False
