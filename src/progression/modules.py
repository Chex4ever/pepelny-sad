"""Overworld module effects."""
from __future__ import annotations


def module_inventory_bonus(installed: list[str]) -> int:
    from src.data.art_loader import load_items

    items = load_items()
    bonus = 0
    for mid in installed:
        data = items.get(mid, {})
        eff = data.get("module_effect", {})
        bonus += eff.get("inventory", 0)
    return bonus


def module_fov_bonus(installed: list[str]) -> int:
    return 0
