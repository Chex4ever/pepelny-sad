"""Tests for save/load."""
from src.world.save import load_game, save_game


def test_save_and_load_roundtrip(save_path):
    payload = {"world_seed": 7, "hp": 15, "layer": "surface"}
    save_game(payload)
    loaded = load_game()
    assert loaded == payload


def test_load_missing_returns_none(save_path):
    assert load_game() is None
