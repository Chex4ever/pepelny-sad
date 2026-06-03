"""Integration tests for overworld interactions."""
import pytest
import pygame

from tests.conftest import FakeInput


@pytest.mark.integration
def test_open_character_sheet(game):
    game.overworld.handle_input(FakeInput(pressed={pygame.K_TAB}))
    assert game.overworld.sheet.open


@pytest.mark.integration
def test_examine_elion_from_sheet(game, screen_buffer):
    game.overworld.sheet.open = True
    game.overworld.sheet.mode = "equip"
    game.overworld.sheet.handle_input(
        FakeInput(pressed={pygame.K_o}),
        game.profile,
        game.overworld.examine,
    )
    assert not game.overworld.examine.open  # no gear equipped


@pytest.mark.integration
def test_dialogue_trigger_at_npc(game):
    game.overworld.player.x = 20
    game.overworld.player.y = 24
    game.overworld._open_dialogue("elder_intro")
    assert game.overworld.dialogue_open
    assert game.overworld.dialogue.active
    assert game.overworld.dialogue.voice == "elder"


@pytest.mark.integration
def test_fov_computed_after_update(game):
    game.overworld.update()
    assert len(game.overworld.visible) > 0
    assert (game.overworld.player.x, game.overworld.player.y) in game.overworld.visible
