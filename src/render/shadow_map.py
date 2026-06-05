"""Directional tile shadows (world-grid, multiplied into light)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShadowCaster:
    vx: int
    vy: int
    height_m: float
    strength: float = 1.0


class ShadowMap:
    """Per-viewport multipliers in [shadow_floor, 1.0]; darkest wins."""

    def __init__(self, width: int, height: int, *, shadow_floor: float = 0.42):
        self.width = width
        self.height = height
        self.shadow_floor = shadow_floor
        self.values = [[1.0] * width for _ in range(height)]

    def get(self, x: int, y: int) -> float:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.values[y][x]
        return 1.0

    def _darken(self, x: int, y: int, factor: float) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            if factor < self.values[y][x]:
                self.values[y][x] = factor

    def cast(
        self,
        caster: ShadowCaster,
        dir_dx: int,
        dir_dy: int,
        *,
        length_scale: float = 0.75,
    ) -> None:
        if dir_dx == 0 and dir_dy == 0:
            return
        max_steps = max(1, min(8, int(caster.height_m * length_scale * 1.15)))
        base = self.shadow_floor + (1.0 - self.shadow_floor) * (1.0 - caster.strength)
        for step in range(1, max_steps + 1):
            t = step / max_steps
            factor = 1.0 - (1.0 - base) * (0.35 + 0.65 * t)
            tx = caster.vx + dir_dx * step
            ty = caster.vy + dir_dy * step
            self._darken(tx, ty, factor)
            if step <= 2:
                self._darken(tx + dir_dy, ty - dir_dx, factor * 0.94)
                self._darken(tx - dir_dy, ty + dir_dx, factor * 0.94)

    def apply_all(
        self,
        casters: list[ShadowCaster],
        dir_dx: int,
        dir_dy: int,
        *,
        length_scale: float,
    ) -> None:
        for c in sorted(casters, key=lambda x: x.height_m):
            self.cast(c, dir_dx, dir_dy, length_scale=length_scale)
