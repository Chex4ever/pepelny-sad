"""Day/night cycle and torch flicker."""
from __future__ import annotations

import math

from src.constants import DAY_CYCLE_TURNS


def ambient_for_time(time_s: float, layer: str = "surface", weather_dim: float = 0.0) -> float:
    """Day/night from continuous world time (1 s ≈ 1 legacy turn)."""
    return ambient_for_turn(int(time_s), layer, weather_dim)


def ambient_for_turn(turn: int, layer: str = "surface", weather_dim: float = 0.0) -> float:
    if layer == "dungeon":
        return max(0.15, 0.25 - weather_dim)
    phase = (turn % DAY_CYCLE_TURNS) / DAY_CYCLE_TURNS
    if phase < 0.25:
        t = phase / 0.25
        base = 0.35 + 0.65 * t
    elif phase < 0.65:
        base = 1.0
    elif phase < 0.85:
        t = (phase - 0.65) / 0.2
        base = 1.0 - 0.45 * t
    else:
        t = (phase - 0.85) / 0.15
        base = 0.55 - 0.2 * t
    return max(0.2, base * (1.0 - weather_dim))


def torch_flicker(frame: int, seed: int = 0) -> float:
    return 0.85 + 0.15 * math.sin(frame * 0.15 + seed * 1.7)


def torch_char(frame: int) -> str:
    return "i" if (frame // 4) % 2 else "l"


def sun_shadow_vector(turn: int, layer: str = "surface") -> tuple[int, int, float]:
    """World (dx, dy) shadow falls toward, and length scale (shorter at noon)."""
    if layer == "dungeon":
        return 1, 1, 0.55
    phase = (turn % DAY_CYCLE_TURNS) / DAY_CYCLE_TURNS
    # Isometric sun from upper-left; shadow toward south-east in world (+1,+1).
    if phase < 0.2:
        t = phase / 0.2
        length_scale = 0.85 - 0.35 * t
        return 1, 1, length_scale
    if phase < 0.65:
        return 1, 1, 0.4
    if phase < 0.85:
        t = (phase - 0.65) / 0.2
        return 1, 1, 0.4 + 0.5 * t
    t = (phase - 0.85) / 0.15
    return 1, 0 if t < 0.5 else 1, 0.9 - 0.25 * t


def sky_char(turn: int) -> str:
    phase = (turn % DAY_CYCLE_TURNS) / DAY_CYCLE_TURNS
    if phase < 0.2 or phase > 0.85:
        return "*"
    if phase < 0.35:
        return "+"
    return "·"
