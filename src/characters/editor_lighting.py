"""Editor sun lighting state and shading helpers."""
from __future__ import annotations

import math
from dataclasses import dataclass

# Default ≈ former (light_x, light_y, light_z) = (0.4, -0.6, 0.7)
_DEFAULT_AZIMUTH = math.atan2(0.4, -0.6)
_DEFAULT_ELEVATION = math.asin(0.7)


@dataclass
class EditorLighting:
    """Sun in spherical coords: elevation 0=horizon, π/2=zenith; azimuth orbit in XY."""

    sun_azimuth: float = _DEFAULT_AZIMUTH
    sun_elevation: float = _DEFAULT_ELEVATION
    ambient: float = 0.38
    light: float = 0.62

    def nudge_elevation(self, delta_deg: float) -> None:
        """W/S — raise or lower the sun (zenith ↔ horizon)."""
        lo = math.radians(2.0)
        hi = math.radians(88.0)
        self.sun_elevation = max(lo, min(hi, self.sun_elevation + math.radians(delta_deg)))

    def nudge_azimuth(self, delta_deg: float) -> None:
        """A/D — orbit the sun around the character (+Y = canonical forward)."""
        self.sun_azimuth = (self.sun_azimuth + math.radians(delta_deg)) % (2.0 * math.pi)

    def nudge_ambient(self, delta: float) -> None:
        self.ambient = max(0.0, min(1.0, self.ambient + delta))

    def nudge_light(self, delta: float) -> None:
        self.light = max(0.0, min(1.0, self.light + delta))

    def normalized_dir(self) -> tuple[float, float, float]:
        """Unit vector from character toward the sun."""
        cos_e = math.cos(self.sun_elevation)
        lx = cos_e * math.sin(self.sun_azimuth)
        ly = cos_e * math.cos(self.sun_azimuth)
        lz = math.sin(self.sun_elevation)
        return lx, ly, lz

    @property
    def elevation_deg(self) -> float:
        return math.degrees(self.sun_elevation)

    @property
    def azimuth_deg(self) -> float:
        return math.degrees(self.sun_azimuth) % 360.0

    def sun_label(self) -> str:
        return f"elev {self.elevation_deg:.0f}°  orbit {self.azimuth_deg:.0f}°"


def brightness_at(
    x: float,
    y: float,
    z: float,
    *,
    lighting: EditorLighting,
    up_bias: float = 1.0,
) -> float:
    """Return 0..1 brightness factor for a world-space point."""
    lx, ly, lz = lighting.normalized_dir()
    # Direction from point toward sun (sun above +Z when at zenith).
    horiz = (x * lx + y * ly) * 0.12 + 0.5
    vert = max(0.0, lz) * up_bias
    lit = horiz * 0.45 + vert * 0.55
    return max(0.0, min(1.0, lighting.ambient + lighting.light * lit))


def shade_from_brightness(
    fg: tuple[int, int, int],
    bg: tuple[int, int, int],
    brightness: float,
) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Map brightness 0..1 to fg/bg (0=dark, 1=full)."""
    from src.characters.editor_shading import shade_color

    factor = 1.0 - brightness
    return shade_color(fg, bg, factor * 0.85)
