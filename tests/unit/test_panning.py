"""Tests for camera pan behavior."""
from __future__ import annotations

import pygame

from src.constants import CELL_W, MAP_VIEW_H
from src.core.camera import Camera
from src.scenes.overworld.input_router import OverworldInputRouter
from tests.conftest import FakeInput


def test_camera_pan_from_total_drag():
    cam = Camera(100, MAP_VIEW_H)
    cam.center_on(50, 50)
    cam.pan_from_drag(100, 0, CELL_W, 16, 0, 0)
    assert cam.pan_x == -10
    assert cam.pan_y == 0


def test_camera_default_pan_limit_is_generous():
    cam = Camera(100, MAP_VIEW_H)
    assert cam.pan_limit >= 30


def test_pan_persists_after_move(game):
    ow = game.overworld
    ow.camera.pan_by(5, -3)
    inp = FakeInput(pressed={pygame.K_w})
    game.input = inp
    ow.input_router.handle_input(inp)
    assert ow.camera.pan_x == 5
    assert ow.camera.pan_y == -3


def test_pan_works_with_log_visible_and_mouse_over_log(game):
    ow = game.overworld
    log = ow.log
    log.show()
    log.add("test")
    router = ow.input_router
    router._panning = True
    router._drag_start = (800, 80)
    router._pan_base = (0, 0)
    inp = FakeInput()
    inp.mouse_down.add(1)
    inp.mouse_pos = (900, 80)
    router._apply_pan_drag(inp)
    assert ow.camera.pan_x != 0


def test_click_on_log_does_not_examine_map(game, monkeypatch):
    ow = game.overworld
    log = ow.log
    log.show()
    log.add("blocked")
    called: list[tuple[int, int]] = []

    def _capture(wx: int, wy: int) -> None:
        called.append((wx, wy))

    monkeypatch.setattr(ow.interaction, "try_examine_world", _capture)
    router = ow.input_router
    inp = FakeInput()
    inp.mouse_pos = (800, 80)
    inp.mouse_pressed.add(1)
    inp.mouse_down.add(1)
    router._handle_map_mouse(inp)
    inp.mouse_pressed.clear()
    inp.mouse_released.add(1)
    inp.mouse_down.discard(1)
    router._handle_map_mouse(inp)
    assert called == []


def test_pan_continues_when_mouse_leaves_map(game):
    ow = game.overworld
    router = ow.input_router
    router._click_pending = True
    router._drag_start = (100, 100)
    router._pan_base = (0, 0)
    router._panning = True
    inp = FakeInput()
    inp.mouse_down.add(1)
    inp.mouse_pos = (200, 100)
    inp._prev_mouse_pos = (150, 100)
    router._apply_pan_drag(inp)
    assert ow.camera.pan_x != 0 or ow.camera.pan_y != 0
