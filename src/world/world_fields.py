"""Global continuous world fields (height, moisture, detail)."""
from __future__ import annotations

import math

from src.world.noise import ValueNoise2D

_height_noise: ValueNoise2D | None = None
_moisture_noise: ValueNoise2D | None = None
_detail_noise: ValueNoise2D | None = None
_world_seed: int = 0


def init_world_fields(seed: int) -> None:
    global _height_noise, _moisture_noise, _detail_noise, _world_seed
    _world_seed = seed
    _height_noise = ValueNoise2D(seed)
    _moisture_noise = ValueNoise2D(seed + 7919)
    _detail_noise = ValueNoise2D(seed + 104729)


def height_field(wx: int, wy: int) -> float:
    if _height_noise is None:
        init_world_fields(0)
    return _height_noise.noise(wx * 0.02, wy * 0.02)


def moisture_field(wx: int, wy: int) -> float:
    if _moisture_noise is None:
        init_world_fields(0)
    return _moisture_noise.noise(wx * 0.03 + 50, wy * 0.03 + 50)


def detail_noise(wx: int, wy: int) -> float:
    if _detail_noise is None:
        init_world_fields(0)
    return _detail_noise.noise(wx * 0.11 + 17, wy * 0.11 + 31)


def _gauss(dist: float, spread: float) -> float:
    if spread <= 0:
        return 0.0
    return math.exp(-(dist * dist) / (2.0 * spread * spread))


def biome_weights(h: float, m: float, biomes: dict) -> dict[str, float]:
    raw: dict[str, float] = {}
    for bid, data in biomes.items():
        center = data.get("climate_center", {"h": 0.5, "m": 0.5})
        spread = data.get("climate_spread", 0.18)
        ch = center.get("h", 0.5)
        cm = center.get("m", 0.5)
        dist = math.hypot(h - ch, m - cm)
        raw[bid] = _gauss(dist, spread)
    total = sum(raw.values()) or 1.0
    return {k: v / total for k, v in raw.items()}


def primary_secondary(weights: dict[str, float]) -> tuple[str, str | None, float]:
    ordered = sorted(weights.items(), key=lambda x: -x[1])
    primary = ordered[0][0]
    secondary = ordered[1][0] if len(ordered) > 1 else None
    blend = ordered[1][1] if len(ordered) > 1 else 0.0
    return primary, secondary, blend
