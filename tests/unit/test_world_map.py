"""Tests for world generation."""
from src.constants import CHUNK_SIZE
from src.world.surface_gen import generate_chunk_isolated
from src.world.world_map import WorldMap


def test_same_seed_same_chunk():
    a = generate_chunk_isolated(1, 2, seed=999)
    b = generate_chunk_isolated(1, 2, seed=999)
    assert a.tiles == b.tiles


def test_different_seed_different_chunk():
    a = generate_chunk_isolated(0, 0, seed=1)
    b = generate_chunk_isolated(0, 0, seed=2)
    assert a.tiles != b.tiles


def test_world_to_chunk_negative_coords():
    wm = WorldMap(42)
    cx, cy, lx, ly = wm.world_to_chunk(-5, -33)
    assert 0 <= lx < CHUNK_SIZE
    assert 0 <= ly < CHUNK_SIZE
    assert wm.get_tile(-5, -33)[0] != ""


def test_out_of_radius_is_fog():
    wm = WorldMap(42)
    ch, _, _ = wm.get_tile(9999, 9999)
    assert ch == "░"


def test_landmarks_stamped_in_start_chunk():
    wm = WorldMap(42)
    wm._ensure_radius(0, 0)
    chunk = wm.chunks[(0, 0)]
    tiles = set(chunk.tiles)
    assert "&" in tiles or "@" in tiles or "l" in tiles
