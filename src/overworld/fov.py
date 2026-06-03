"""Field of view."""
from __future__ import annotations

import math


def compute_fov(px: int, py: int, radius: int, visible_fn) -> set[tuple[int, int]]:
    seen = set()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                x, y = px + dx, py + dy
                if visible_fn(x, y):
                    seen.add((x, y))
    return seen


def cast_shadows(px: int, py: int, radius: int, blocks_fn) -> set[tuple[int, int]]:
    seen = {(px, py)}
    for angle in range(360):
        rad = math.radians(angle)
        for r in range(1, radius + 1):
            x = px + int(round(math.cos(rad) * r))
            y = py + int(round(math.sin(rad) * r))
            seen.add((x, y))
            if blocks_fn(x, y):
                break
    return seen
