"""Tests for crafting."""
from src.progression.crafting import can_craft, craft, recipe_visible
from src.progression.inventory import Inventory


def test_recipe_visible_always():
    recipe = {"id": "root_staff", "discover": "always"}
    assert recipe_visible(recipe, set(), set())


def test_recipe_visible_after_scan():
    recipe = {"id": "grey_tincture", "discover": "scan:listen"}
    assert not recipe_visible(recipe, set(), set())
    assert recipe_visible(recipe, set(), {"listen"})


def test_craft_consumes_ingredients(profile, world_state):
    world_state.discovered_recipes.add("root_staff")
    before = profile.inventory.count("root_fiber")
    result = craft("root_staff", profile.inventory, world_state.discovered_recipes, world_state.scan_flags)
    assert result == "root_staff"
    assert profile.inventory.count("root_fiber") < before
    assert profile.inventory.has("root_staff")


def test_craft_fails_without_materials(world_state):
    inv = Inventory(4)
    assert craft("ash_blade", inv, world_state.discovered_recipes, world_state.scan_flags) is None


def test_can_craft_respects_scan_gate(profile, world_state):
    profile.inventory.add("grey_herb", 10, 20)
    assert not can_craft("grey_tincture", profile.inventory, world_state.discovered_recipes, world_state.scan_flags)
    world_state.scan_flags.add("listen")
    assert can_craft("grey_tincture", profile.inventory, world_state.discovered_recipes, world_state.scan_flags)
