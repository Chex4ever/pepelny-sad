"""Surface FOV radius and exploration."""
from __future__ import annotations

from src.constants import VISIBLE_LOS_RADIUS_SURFACE
from src.scenes.overworld.fov_controller import FovController


def test_surface_fov_radius(game):
    ow = game.overworld
    ow.game.world_state.layer = "surface"
    assert ow.fov.fov_radius() >= VISIBLE_LOS_RADIUS_SURFACE - 4


def test_fov_marks_player_tile_explored(game):
    ow = game.overworld
    ow.game.world_state.layer = "surface"
    px, py = ow.player.tile_pos()
    wm = ow.game.world_map
    cx, cy, lx, ly = wm.world_to_chunk(px, py)
    wm._ensure_chunk(cx, cy)
    chunk = wm.chunks[(cx, cy)]
    chunk.explored[chunk.idx(lx, ly)] = False
    ow.update(16)
    assert wm.is_explored(px, py, "surface")
