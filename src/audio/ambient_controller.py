"""Environmental ambient loop volumes from overworld state."""
from __future__ import annotations

from src.world.lighting import ambient_for_turn


def nearest_torch_volume(
    visible: set[tuple[int, int]],
    player_pos: tuple[int, int],
    tile_ch,
    max_dist: float = 8.0,
) -> float:
    px, py = player_pos
    max_dist2 = max_dist * max_dist
    best = 0.0
    for wx, wy in visible:
        d2 = (wx - px) ** 2 + (wy - py) ** 2
        if d2 > max_dist2:
            continue
        if tile_ch(wx, wy) not in "li":
            continue
        dist = d2**0.5
        vol = max(0.0, 1.0 - dist / max_dist)
        best = max(best, vol)
        if best >= 1.0:
            break
    return min(1.0, best)


class AmbientController:
    def __init__(self, audio):
        self.audio = audio

    def update(
        self,
        *,
        layer: str,
        weather_active: bool,
        in_shelter: bool,
        visible: set[tuple[int, int]],
        player_pos: tuple[int, int],
        turn_count: int,
        tile_ch,
    ):
        if not self.audio.enabled:
            return

        if layer == "dungeon":
            self.audio.set_loop("wind_soft", False)
            self.audio.set_loop("wind_gust", False)
            self.audio.set_loop("ember", False)
            self.audio.set_loop("cave", True, volume=0.55)
            torch = nearest_torch_volume(visible, player_pos, tile_ch) * 0.7
            self.audio.set_loop("torch", torch > 0.05, volume=torch)
            return

        self.audio.set_loop("cave", False)
        ambient = ambient_for_turn(turn_count, "surface", 0.2 if weather_active else 0.0)
        night_boost = max(0.0, 0.55 - ambient)

        if in_shelter:
            self.audio.set_loop("wind_soft", False)
            self.audio.set_loop("wind_gust", False)
            self.audio.set_loop("ember", False)
        elif weather_active:
            self.audio.set_loop("wind_soft", True, volume=0.15 + night_boost * 0.2)
            self.audio.set_loop("wind_gust", True, volume=0.45 + night_boost * 0.25)
            self.audio.set_loop("ember", True, volume=0.25)
        else:
            self.audio.set_loop("wind_gust", False)
            self.audio.set_loop("ember", False)
            wind = 0.12 + night_boost * 0.35
            self.audio.set_loop("wind_soft", True, volume=wind)

        torch = nearest_torch_volume(visible, player_pos, tile_ch)
        self.audio.set_loop("torch", torch > 0.05, volume=torch * 0.65)
