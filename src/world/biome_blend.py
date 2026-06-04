"""Biome blending from climate fields."""
from __future__ import annotations

from src.data.art_loader import load_biomes
from src.world.world_fields import biome_weights, height_field, moisture_field, primary_secondary


def _lerp_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def sample_climate(wx: int, wy: int) -> tuple[str, str | None, float, dict[str, float]]:
    h = height_field(wx, wy)
    m = moisture_field(wx, wy)
    weights = biome_weights(h, m, load_biomes())
    primary, secondary, blend = primary_secondary(weights)
    return primary, secondary, blend, weights


def blended_floor(primary: str, secondary: str | None, blend: float) -> tuple[str, tuple, tuple, str]:
    biomes = load_biomes()
    p = biomes[primary]
    fg = tuple(p["fg"])
    bg = tuple(p["bg"])
    floor = p["floor"]
    stencil = p.get("stencil_id", "grass")
    if secondary and blend > 0.15:
        s = biomes[secondary]
        t = min(0.65, blend / (p.get("weight", 0.5) + blend + 0.01))
        fg = _lerp_rgb(fg, tuple(s["fg"]), t)
        bg = _lerp_rgb(bg, tuple(s["bg"]), t)
        if blend > 0.35 and s.get("transition_stencil_id"):
            stencil = s["transition_stencil_id"]
    return floor, fg, bg, stencil


def blended_chance(primary: str, secondary: str | None, blend: float, key: str) -> float:
    biomes = load_biomes()
    pval = biomes[primary].get(key, 0.0)
    if not secondary or blend < 0.1:
        return pval
    sval = biomes[secondary].get(key, 0.0)
    return pval * (1.0 - blend * 0.5) + sval * (blend * 0.5)
