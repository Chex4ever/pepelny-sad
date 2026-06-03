"""Emotional palette overlay for dungeon."""
from __future__ import annotations


def reskin_char(ch: str, spare_count: int, kill_count: int) -> tuple[str, tuple | None]:
    if spare_count > kill_count and ch in "░▒":
        return "*", (180, 160, 120)
    if kill_count > spare_count and ch in "░▒":
        return "▓", (60, 50, 55)
    return ch, None


def bullet_speed_mult(kill_count: int, spare_count: int, in_dungeon: bool) -> float:
    if not in_dungeon:
        return 1.0
    if kill_count > spare_count:
        return 1.1
    return 1.0
