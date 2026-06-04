"""Craft window input via WindowManager."""
from __future__ import annotations

import pygame

from src.ui.windows.craft_window import CraftWindow
from src.ui.windows.window_manager import WindowManager
from tests.conftest import FakeInput


def test_craft_window_manager_does_not_crash(game):
    wm = WindowManager()
    craft = CraftWindow()
    wm.register(craft)
    craft.open_station("forge")
    craft.bind(game.profile, game.world_state)
    assert wm.handle_input(FakeInput()) is False

    craft.handle_keys(FakeInput(pressed={pygame.K_ESCAPE}))
    assert not craft.visible
