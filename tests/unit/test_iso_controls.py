"""Isometric screen-aligned movement."""
from __future__ import annotations

import pygame

from src.input import InputState, SCAN_S, SCAN_W
from src.render import render_mode
from src.render.iso_projector import IsoProjector


def test_screen_delta_to_world_up():
    assert IsoProjector.screen_delta_to_world(0, -1) == (-1, -1)
    assert IsoProjector.screen_delta_to_world(0, 1) == (1, 1)
    assert IsoProjector.screen_delta_to_world(-1, 0) == (-1, 1)
    assert IsoProjector.screen_delta_to_world(1, 0) == (1, -1)


def test_dir_key_iso_w(monkeypatch):
    monkeypatch.setenv("PEPELNY_RENDER", "iso")
    render_mode._MODE = None
    render_mode.render_mode()
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w, scancode=SCAN_W))
    assert inp.dir_key() == (-1, -1)


def test_dir_key_iso_s(monkeypatch):
    monkeypatch.setenv("PEPELNY_RENDER", "iso")
    render_mode._MODE = None
    render_mode.render_mode()
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, scancode=SCAN_S))
    assert inp.dir_key() == (1, 1)
