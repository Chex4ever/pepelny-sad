"""Iso pan shows explored tiles and fog outside current FOV."""
from __future__ import annotations

import pytest

from src.render import render_mode
from src.render.screen_buffer import FOG_EXPLORED, FOG_UNEXPLORED
from src.world.visibility import EXPLORED, visibility_state


@pytest.fixture
def iso_scene(game, monkeypatch):
    monkeypatch.setenv("PEPELNY_RENDER", "iso")
    render_mode._MODE = None
    render_mode.render_mode()
    game.world_state.layer = "surface"
    ow = game.overworld
    from src.core.camera import Camera
    from src.render.viewport import map_view_h, map_view_w

    ow.camera = Camera(map_view_w(), map_view_h())
    ow.player.set_tile(50, 50)
    ow.camera.center_on(ow.player.x, ow.player.y)
    game.world_map._ensure_radius(50, 50)
    ow.update(16)
    return ow


def test_draw_queue_includes_explored_off_fov(iso_scene):
    ow = iso_scene
    ptx, pty = ow.player.tile_pos()
    wx, wy = ptx + 3, pty + 2
    ow.game.world_map._ensure_radius(wx, wy)
    ow.game.world_map.mark_explored(wx, wy, "surface")
    ow.visible = {ow.player.tile_pos()}
    assert visibility_state(wx, wy, ow.visible, ow._is_explored) == EXPLORED
    wx0, wy0 = ow.camera.view_origin()
    q = ow.map_renderer.build_iso_draw_queue(wx0, wy0)
    coords = {(t[1], t[2]) for t in q}
    assert (wx, wy) in coords
    fog_by = {(t[1], t[2]): t[8] for t in q}
    assert fog_by[(wx, wy)] == FOG_EXPLORED


def test_unexplored_fog_when_panned(iso_scene, screen_buffer):
    ow = iso_scene
    ow.camera.set_pan(8, 4)
    ow.update(16)
    wx0, wy0 = ow.camera.view_origin()
    ow.draw(screen_buffer, None)
    from src.render.iso_projector import IsoProjector

    p = IsoProjector()
    from src.render.viewport import map_view_h, map_view_w

    vw, vh = map_view_w(), map_view_h()
    focus_wx, focus_wy = p.view_focus(wx0, wy0, vw, vh)
    wx_lo, wx_hi, wy_lo, wy_hi = p.world_bounds_for_focus(focus_wx, focus_wy)
    found_unexplored = False
    for wx in range(wx_lo, wx_hi + 1):
        for wy in range(wy_lo, wy_hi + 1):
            if ow._is_explored(wx, wy):
                continue
            ax, ay = p.world_to_screen(wx, wy, focus_wx=focus_wx, focus_wy=focus_wy)
            if screen_buffer.in_bounds(ax, ay):
                idx = screen_buffer._idx(ax, ay)
                if screen_buffer.fog[idx] == FOG_UNEXPLORED:
                    found_unexplored = True
                    break
        if found_unexplored:
            break
    assert found_unexplored
