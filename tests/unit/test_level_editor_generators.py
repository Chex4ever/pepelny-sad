"""Level editor generators smoke tests."""
from __future__ import annotations

import pytest

from src.world.editor.editable_world import EditableWorld
from src.world.editor.generators import fill_biome, make_clearing, paint_road, scatter_trees


@pytest.mark.unit
def test_fill_biome_and_clearing():
    world = EditableWorld(seed=1, width=8, height=8)
    world.fill_blank_grass()
    fill_biome(world, "meadow", trees=False)
    chunk, lx, ly = world.chunk_for_world(world.bounds.wx0, world.bounds.wy0)
    assert chunk.floor_stencils[chunk.idx(lx, ly)] != ""
    make_clearing(world, world.bounds.wx0, world.bounds.wy0, 2, 2)
    assert chunk.get(lx, ly) == "."


@pytest.mark.unit
def test_paint_road():
    world = EditableWorld(seed=2, width=10, height=10)
    world.fill_blank_grass()
    paint_road(world, [(0, 0), (5, 5)], width=0)
    chunk, lx, ly = world.chunk_for_world(3, 3)
    assert chunk.get(lx, ly) == "="


@pytest.mark.unit
def test_scatter_trees():
    world = EditableWorld(seed=3, width=12, height=12)
    world.fill_blank_grass()
    fill_biome(world, "meadow", trees=False)
    scatter_trees(world, density=0.5)
    total_anchors = sum(len(c.structure_anchors) for c in world.doc.chunks.values())
    assert total_anchors > 0
