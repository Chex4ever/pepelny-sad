"""New game loading flow."""
from __future__ import annotations

from src.core.new_game_loader import iter_build_new_game


def test_iter_build_new_game_steps(game):
    steps = list(iter_build_new_game(game, 4242))
    assert len(steps) >= 5
    assert game.overworld is not None
    assert game.world_map.chunks
    assert game.world_state.world_seed == 4242


def test_flush_pressed_clears_enter(game):
    import pygame

    from src.input import SCAN_RETURN

    inp = game.input
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, scancode=SCAN_RETURN))
    assert inp.confirm_pressed()
    inp.flush_pressed()
    assert not inp.confirm_pressed()
    assert not inp.scancodes_pressed
