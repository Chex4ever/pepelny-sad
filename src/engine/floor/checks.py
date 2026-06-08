"""Golden validation and rasterization helpers."""

from __future__ import annotations



from src.engine.config import FLOOR_LAYOUT_TILES

from src.engine.floor.draw_map import floor_packed_draw_map

from src.engine.layout.golden import render_packed_test_floor

from src.engine.layout.golden import resolve_tile_slot_view

from src.render.iso_footprint import internal_footprint_holes





def assert_floor_has_no_holes(

    feet_cx: int,

    feet_cy: int,

    *,

    n_tiles: int = FLOOR_LAYOUT_TILES,

) -> None:

    draw = floor_packed_draw_map(feet_cx, feet_cy, n_tiles=n_tiles)

    expected = len(resolve_tile_slot_view(n_tiles=n_tiles))

    if len(draw) != expected:

        raise AssertionError(

            f"floor draw has {len(draw)} cells, expected {expected} stamp slots"

        )

    _ = render_packed_test_floor(n_tiles, feet_cx=feet_cx, feet_cy=feet_cy)





def rasterize_floor_packed_view(

    feet_cx: int,

    feet_cy: int,

    *,

    n_tiles: int = FLOOR_LAYOUT_TILES,

    empty: str = "_",

) -> tuple[str, ...]:

    _ = empty

    return render_packed_test_floor(n_tiles, feet_cx=feet_cx, feet_cy=feet_cy)





def floor_solid_has_internal_holes(

    feet_cx: int,

    feet_cy: int,

    *,

    n_tiles: int = FLOOR_LAYOUT_TILES,

) -> list[tuple[int, int]]:

    draw = floor_packed_draw_map(feet_cx, feet_cy, n_tiles=n_tiles)

    return internal_footprint_holes(set(draw.keys()))

