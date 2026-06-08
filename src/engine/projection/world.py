"""World tile coordinates → iso screen (game overworld path)."""
from __future__ import annotations

from src.render.iso_projector import IsoProjector


def world_to_screen(
    wx: int,
    wy: int,
    *,
    focus_wx: int,
    focus_wy: int,
    origin_x: int | None = None,
    origin_y: int | None = None,
) -> tuple[int, int]:
    """World tile center in screen pixels (via IsoProjector)."""
    p = IsoProjector(
        origin_x=origin_x if origin_x is not None else 0,
        origin_y=origin_y if origin_y is not None else 0,
    )
    return p.world_to_screen(wx, wy, focus_wx=focus_wx, focus_wy=focus_wy)


def screen_to_world(
    sx: int,
    sy: int,
    *,
    focus_wx: int,
    focus_wy: int,
    origin_x: int = 0,
    origin_y: int = 0,
) -> tuple[int, int]:
    p = IsoProjector(origin_x=origin_x, origin_y=origin_y)
    return p.screen_to_world(sx, sy, focus_wx=focus_wx, focus_wy=focus_wy)
