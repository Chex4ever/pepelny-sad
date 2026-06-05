"""Shadowcast FOV vs raycast reference and basic regressions."""
from __future__ import annotations

import random

from src.overworld.fov import cast_los_fov, cast_los_fov_raycast


def _agreement_ratio(
    shadow: set[tuple[int, int]],
    raycast: set[tuple[int, int]],
) -> float:
    if not raycast:
        return 1.0
    return len(shadow & raycast) / len(raycast)


def test_shadowcast_matches_raycast_open_field():
    w, h = 20, 20

    def blocks(_x: int, _y: int) -> bool:
        return False

    for px, py, radius in ((10, 10, 8), (5, 5, 12), (1, 1, 6)):
        shadow = cast_los_fov(
            px, py, radius, blocks, min_x=0, max_x=w - 1, min_y=0, max_y=h - 1
        )
        raycast = cast_los_fov_raycast(
            px, py, radius, blocks, min_x=0, max_x=w - 1, min_y=0, max_y=h - 1
        )
        assert shadow == raycast


def test_shadowcast_agrees_with_raycast_vertical_wall():
    """Structured map: shadowcast and Bresenham raycast should match closely."""
    w, h = 20, 20
    walls = {(10, y) for y in range(h)}

    def blocks(x: int, y: int) -> bool:
        return (x, y) in walls

    shadow = cast_los_fov(5, 10, 10, blocks, min_x=0, max_x=w - 1, min_y=0, max_y=h - 1)
    raycast = cast_los_fov_raycast(5, 10, 10, blocks, min_x=0, max_x=w - 1, min_y=0, max_y=h - 1)
    assert _agreement_ratio(shadow, raycast) >= 0.95


def test_shadowcast_agrees_with_raycast_on_random_walls():
    w, h = 20, 20
    walls: set[tuple[int, int]] = set()
    random.seed(42)
    for _ in range(35):
        walls.add((random.randint(0, w - 1), random.randint(0, h - 1)))

    def blocks(x: int, y: int) -> bool:
        return (x, y) in walls or x < 0 or y < 0 or x >= w or y >= h

    ratios = []
    for px, py, radius in ((10, 10, 8), (5, 5, 12)):
        shadow = cast_los_fov(
            px, py, radius, blocks, min_x=0, max_x=w - 1, min_y=0, max_y=h - 1
        )
        raycast = cast_los_fov_raycast(
            px, py, radius, blocks, min_x=0, max_x=w - 1, min_y=0, max_y=h - 1
        )
        ratios.append(_agreement_ratio(shadow, raycast))
    assert min(ratios) >= 0.87
    assert sum(ratios) / len(ratios) >= 0.90


def test_player_tile_always_visible():
    walls = {(5, 5), (5, 6), (6, 5)}

    def blocks(x: int, y: int) -> bool:
        return (x, y) in walls

    visible = cast_los_fov(3, 3, 6, blocks, min_x=0, max_x=15, min_y=0, max_y=15)
    assert (3, 3) in visible


def test_behind_wall_not_visible():
    def blocks(x: int, y: int) -> bool:
        return x == 5 and 0 <= y <= 10

    visible = cast_los_fov(3, 5, 8, blocks, min_x=0, max_x=15, min_y=0, max_y=15)
    assert (3, 5) in visible
    assert (10, 5) not in visible


def test_radius_limit():
    def blocks(_x: int, _y: int) -> bool:
        return False

    visible = cast_los_fov(0, 0, 4, blocks)
    for x, y in visible:
        assert x * x + y * y <= 16
