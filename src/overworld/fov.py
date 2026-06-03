"""Field of view with line-of-sight shadow casting."""
from __future__ import annotations

import math

from src.world.visibility import blocks_los


def cast_los_fov(
    px: int,
    py: int,
    radius: int,
    get_tile_char,
    *,
    min_x: int | None = None,
    max_x: int | None = None,
    min_y: int | None = None,
    max_y: int | None = None,
) -> set[tuple[int, int]]:
    """Shadow-casting via radial rays; returns visible world cells."""
    seen = {(px, py)}
    radius2 = radius * radius
    steps = max(120, radius * 8)

    for i in range(steps):
        ang = (2 * math.pi * i) / steps
        dx = math.cos(ang)
        dy = math.sin(ang)
        for r in range(1, radius + 1):
            x = px + int(round(dx * r))
            y = py + int(round(dy * r))
            if min_x is not None and (x < min_x or x > max_x or y < min_y or y > max_y):
                break
            if (x - px) ** 2 + (y - py) ** 2 > radius2:
                break
            seen.add((x, y))
            ch = get_tile_char(x, y)
            if blocks_los(ch):
                break
    return seen


def compute_fov(px: int, py: int, radius: int, visible_fn) -> set[tuple[int, int]]:
    """Legacy circular FOV (kept for tests)."""
    seen = set()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                x, y = px + dx, py + dy
                if visible_fn(x, y):
                    seen.add((x, y))
    return seen
