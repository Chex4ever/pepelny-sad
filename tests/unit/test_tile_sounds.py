"""Unit tests for footstep surface resolution."""
from src.audio.tile_sounds import resolve_footstep
from src.world.world_map import WorldMap


def test_footstep_grass_meadow(world_map):
    wx, wy = 0, 0
    assert resolve_footstep(wx, wy, "surface", world_map) == "grass"


def test_footstep_dungeon_stone(world_map):
    assert resolve_footstep(2, 2, "dungeon", world_map) == "stone"


def test_footstep_road_tile(world_map):
    cx, cy, lx, ly = world_map.world_to_chunk(10, 10)
    chunk = world_map.chunks[(cx, cy)]
    chunk.set(lx, ly, "=")
    assert resolve_footstep(10, 10, "surface", world_map) == "road"
