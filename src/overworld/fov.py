"""Field of view with line-of-sight (recursive shadowcasting)."""
from __future__ import annotations

from collections.abc import Callable

Slope = tuple[int, int]  # (y, x) rational slope y/x


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


def _octant_to_world(octant: int, ox: int, oy: int, lx: int, ly: int) -> tuple[int, int]:
    match octant:
        case 0:
            return ox + lx, oy - ly
        case 1:
            return ox + ly, oy - lx
        case 2:
            return ox - ly, oy - lx
        case 3:
            return ox - lx, oy - ly
        case 4:
            return ox - lx, oy + ly
        case 5:
            return ox - ly, oy + lx
        case 6:
            return ox + ly, oy + lx
        case 7:
            return ox + lx, oy + ly
        case _:
            return ox, oy


def _cast_los_fov_raycast(
    px: int,
    py: int,
    radius: int,
    blocks_los_fn: Callable[[int, int], bool],
    *,
    min_x: int,
    max_x: int,
    min_y: int,
    max_y: int,
) -> set[tuple[int, int]]:
    """Brute-force LOS per target cell (O(r³)); kept for regression tests."""
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


def _shadowcast_los_fov(
    px: int,
    py: int,
    radius: int,
    blocks_los_fn: Callable[[int, int], bool],
    *,
    min_x: int,
    max_x: int,
    min_y: int,
    max_y: int,
) -> set[tuple[int, int]]:
    """Recursive shadowcasting (stuffwithstuff / Björn Bergström)."""
    visible: set[tuple[int, int]] = {(px, py)}
    r2 = radius * radius

    def reveal(wx: int, wy: int) -> None:
        if min_x <= wx <= max_x and min_y <= wy <= max_y:
            if (wx - px) ** 2 + (wy - py) ** 2 <= r2:
                visible.add((wx, wy))

    def compute_octant(
        octant: int,
        col: int,
        top: Slope,
        bottom: Slope,
    ) -> None:
        while col <= radius:
            top_y, top_x = top
            bottom_y, bottom_x = bottom
            if top_x == 1:
                y_top = col
            else:
                y_top = ((col * 2 + 1) * top_y + top_x - 1) // (top_x * 2)
            if bottom_y == 0:
                y_bottom = 0
            else:
                y_bottom = ((col * 2 - 1) * bottom_y + bottom_x) // (bottom_x * 2)

            was_opaque = -1
            top_y_r, top_x_r = top
            bottom_y_r, bottom_x_r = bottom
            for ly in range(y_top, y_bottom - 1, -1):
                wx, wy = _octant_to_world(octant, px, py, col, ly)
                in_range = col * col + ly * ly <= r2
                sym_top = ly != y_top or top_y_r * col >= top_x_r * ly
                sym_bottom = ly != y_bottom or bottom_y_r * col <= bottom_x_r * ly
                if in_range and sym_top and sym_bottom:
                    reveal(wx, wy)

                is_opaque = (not in_range) or blocks_los_fn(wx, wy)
                if col != radius:
                    if is_opaque:
                        if was_opaque == 0:
                            new_bottom: Slope = (ly * 2 + 1, col * 2 - 1)
                            if not in_range or ly == y_bottom:
                                bottom = new_bottom
                                break
                            compute_octant(octant, col + 1, top, new_bottom)
                        was_opaque = 1
                    else:
                        if was_opaque > 0:
                            top = (ly * 2 + 1, col * 2 + 1)
                        was_opaque = 0

            if was_opaque != 0:
                break
            col += 1

    for octant in range(8):
        compute_octant(octant, 1, (1, 1), (0, 1))

    return visible


def cast_los_fov(
    px: int,
    py: int,
    radius: int,
    blocks_los_fn,
    *,
    min_x: int | None = None,
    max_x: int | None = None,
    min_y: int | None = None,
    max_y: int | None = None,
) -> set[tuple[int, int]]:
    """Visible cells within radius and LOS from the player."""
    if min_x is None:
        min_x = px - radius
        max_x = px + radius
        min_y = py - radius
        max_y = py + radius
    return _shadowcast_los_fov(
        px, py, radius, blocks_los_fn,
        min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y,
    )


def cast_los_fov_raycast(
    px: int,
    py: int,
    radius: int,
    blocks_los_fn,
    *,
    min_x: int | None = None,
    max_x: int | None = None,
    min_y: int | None = None,
    max_y: int | None = None,
) -> set[tuple[int, int]]:
    """Reference raycast implementation for tests."""
    if min_x is None:
        min_x = px - radius
        max_x = px + radius
        min_y = py - radius
        max_y = py + radius
    return _cast_los_fov_raycast(
        px, py, radius, blocks_los_fn,
        min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y,
    )


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
