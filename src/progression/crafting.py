"""Crafting logic."""
from __future__ import annotations

from src.data.art_loader import load_items, load_recipes
from src.progression.inventory import Inventory


def recipe_visible(recipe: dict, discovered: set, scan_flags: set) -> bool:
    discover = recipe.get("discover", "always")
    if discover == "always":
        return True
    if discover.startswith("scan:"):
        act_id = discover.split(":", 1)[1]
        return act_id in scan_flags or f"scan_{act_id}" in discovered
    if discover in discovered:
        return True
    return recipe["id"] in discovered


def can_craft(recipe_id: str, inventory: Inventory, discovered: set, scan_flags: set) -> bool:
    recipes = {r["id"]: r for r in load_recipes()}
    recipe = recipes.get(recipe_id)
    if not recipe or not recipe_visible(recipe, discovered, scan_flags):
        return False
    for ing in recipe["ingredients"]:
        if not inventory.has(ing["id"], ing["count"]):
            return False
    return True


def craft(recipe_id: str, inventory: Inventory, discovered: set, scan_flags: set) -> str | None:
    recipes = {r["id"]: r for r in load_recipes()}
    recipe = recipes.get(recipe_id)
    if not recipe or not can_craft(recipe_id, inventory, discovered, scan_flags):
        return None
    items = load_items()
    for ing in recipe["ingredients"]:
        inventory.remove(ing["id"], ing["count"])
    result = recipe["id"]
    stack_max = items.get(result, {}).get("stack_max", 99)
    leftover = inventory.add(result, 1, stack_max)
    return result if leftover == 0 else None
