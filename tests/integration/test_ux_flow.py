"""Integration tests for pause, intro, and visibility UX."""
import pygame

import pytest

from src.game import Game
from src.ui.pause_menu import PauseMenu
from src.world.visibility import EXPLORED, filter_tile_char
from tests.conftest import FakeInput, drain_transition


@pytest.mark.integration
def test_pause_menu_save_action(game, save_path, monkeypatch):
    menu = PauseMenu()
    menu.open = True
    menu.cursor = 1
    action = menu.handle_input(FakeInput(pressed={pygame.K_RETURN}))
    assert action == "save"


@pytest.mark.integration
def test_pause_quit_requires_confirm():
    menu = PauseMenu()
    menu.open = True
    menu.cursor = 3
    assert menu.handle_input(FakeInput(pressed={pygame.K_RETURN})) is None
    assert menu.confirm_quit
    action = menu.handle_input(FakeInput(pressed={pygame.K_RETURN}))
    assert action == "quit"


@pytest.mark.integration
def test_intro_skip_to_overworld():
    from src.story.intro import INTRO_LINES

    g = Game()
    g.new_game(seed=99)
    drain_transition(g)
    assert g.scene == "intro"
    g.intro.line_idx = len(INTRO_LINES) - 1
    assert g.intro.handle_input(FakeInput(pressed={pygame.K_RETURN}))
    g._start_transition("overworld")
    drain_transition(g)
    assert g.scene == "overworld"


@pytest.mark.integration
def test_explored_tile_hides_enemy_marker():
    assert filter_tile_char("!", EXPLORED) != "!"
