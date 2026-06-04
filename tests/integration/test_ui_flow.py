"""Integration tests for UI panels."""
import pytest
import pygame

from src.ui.craft_station import CraftStation
from src.ui.examine_panel import ExaminePanel
from tests.conftest import FakeInput


@pytest.mark.integration
def test_examine_panel_open_close(screen_buffer):
    panel = ExaminePanel()
    panel.show("elion")
    panel.draw(screen_buffer)
    assert panel.open
    panel.close()
    assert not panel.open


@pytest.mark.integration
def test_craft_station_craft_recipe(profile, world_state, screen_buffer):
    from src.data.art_loader import load_recipes
    from src.progression.crafting import recipe_visible

    station = CraftStation()
    station.open_station("forge")
    visible = [
        r
        for r in load_recipes()
        if r.get("station") == "forge"
        and recipe_visible(r, world_state.discovered_recipes, world_state.scan_flags)
    ]
    station.cursor = next(i for i, r in enumerate(visible) if r["id"] == "root_staff")
    station.draw(screen_buffer, profile, world_state, ExaminePanel())
    before = profile.inventory.count("root_fiber")
    station.bind(profile, world_state)
    station.handle_content_keys(
        FakeInput(pressed={pygame.K_RETURN}),
        profile,
        world_state,
        ExaminePanel(),
        type("Log", (), {"add": lambda *_: None})(),
    )
    assert profile.inventory.count("root_fiber") < before
    assert profile.inventory.has("root_staff")
