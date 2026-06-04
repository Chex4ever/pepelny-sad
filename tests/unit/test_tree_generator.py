"""Parametric tree generation."""
from __future__ import annotations

from src.data.art_loader import load_biomes
from src.world.tree_generator import GLOBAL_HEIGHT_MAX, GLOBAL_HEIGHT_MIN, roll_tree_params, tree_anchor


def test_tree_height_in_range():
    biome = load_biomes()["meadow"]
    for wx in range(1000):
        params = roll_tree_params(biome, 42, wx, wx * 3)
        assert GLOBAL_HEIGHT_MIN <= params["height_m"] <= GLOBAL_HEIGHT_MAX
        assert 4.0 <= params["height_m"] <= 9.0 + 0.01


def test_same_coords_same_tree():
    biome = load_biomes()["meadow"]
    a = roll_tree_params(biome, 7, 10, 20)
    b = roll_tree_params(biome, 7, 10, 20)
    assert a == b


def test_different_coords_usually_different_height():
    biome = load_biomes()["meadow"]
    heights = {roll_tree_params(biome, 3, i, i)["height_m"] for i in range(50)}
    assert len(heights) > 3


def test_tree_anchor_has_params():
    anchor = tree_anchor(5, 5, load_biomes()["ashen_forest"], 1)
    assert anchor.structure_id == "tree"
    assert "height_m" in anchor.params
