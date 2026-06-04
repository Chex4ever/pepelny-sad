"""Field of view with line-of-sight shadow casting."""
from __future__ import annotations


def _bresenham(x0: int, y0: int, x1: int, y1: int):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        yield x, y
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def cast_los_fov(
    px: int,
    py: int,
    radius: int,
    blocks_los_fn,
    *,
    min_x: int,
    max_x: int,
    min_y: int,
    max_y: int,
) -> set[tuple[int, int]]:
    """Visible cells in the view rect with LOS from the player."""
    seen: set[tuple[int, int]] = {(px, py)}
    r2 = radius * radius
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if (x - px) ** 2 + (y - py) ** 2 > r2:
                continue
            blocked = False
            for lx, ly in _bresenham(px, py, x, y):
                if (lx, ly) == (px, py):
                    continue
                if blocks_los_fn(lx, ly):
                    blocked = True
                    break
            if not blocked:
                seen.add((x, y))
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
