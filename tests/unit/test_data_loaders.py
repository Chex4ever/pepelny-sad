"""Tests for data loaders and art."""
from src.data.art_loader import load_art, load_enemies, load_items, load_recipes


def test_load_enemies_has_three_bosses():
    enemies = load_enemies()
    assert set(enemies) >= {"whisper", "sorrow", "warden"}
    assert len(enemies["whisper"]["acts"]) == 3


def test_load_recipes_count():
    recipes = load_recipes()
    assert len(recipes) >= 8


def test_load_art_returns_content():
    entry = load_art("elion")
    assert entry.art
    assert entry.examine_text


def test_load_items_gear_traits():
    items = load_items()
    assert items["ash_blade"]["combat_traits"]["fight_mode"] == "blade"
