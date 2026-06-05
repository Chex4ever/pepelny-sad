"""Integration tests for player click -> sheet."""
from __future__ import annotations


def test_click_player_opens_sheet(game):
    ow = game.overworld
    px, py = ow.player.tile_pos()
    ow.visible.add((px, py))
    ow.sheet.close()
    ow.interaction.try_examine_world(px, py)
    assert ow.sheet.visible


def test_load_art_32_lines():
    from src.data.art_loader import load_art

    entry = load_art("elion_portrait")
    assert len(entry.art) >= 32


def test_tutorial_advances_on_move(game):
    game.world_state.tutorial_step = 0
    game.tutorial.notify_moved()
    assert game.world_state.tutorial_step == 1
