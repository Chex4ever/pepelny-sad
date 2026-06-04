"""Global world fields and biome blending."""
from __future__ import annotations

from src.constants import CHUNK_SIZE
from src.data.art_loader import load_biomes
from src.world.biome_blend import sample_climate
from src.world.world_fields import (
    biome_weights,
    height_field,
    init_world_fields,
    moisture_field,
)


def test_noise_continuous_across_chunk_boundary():
    init_world_fields(4242)
    seam_x = CHUNK_SIZE
    diffs = []
    for wy in range(0, 64, 4):
        h0 = height_field(seam_x - 1, wy)
        h1 = height_field(seam_x, wy)
        m0 = moisture_field(seam_x - 1, wy)
        m1 = moisture_field(seam_x, wy)
        diffs.append(abs(h1 - h0))
        diffs.append(abs(m1 - m0))
    assert max(diffs) < 0.35


def test_biome_weights_sum_to_one():
    init_world_fields(1)
    biomes = load_biomes()
    for wx in range(0, 100, 7):
        for wy in range(0, 100, 11):
            h = height_field(wx, wy)
            m = moisture_field(wx, wy)
            w = biome_weights(h, m, biomes)
            assert abs(sum(w.values()) - 1.0) < 1e-6


def test_transition_band_has_two_biomes():
    init_world_fields(555)
    biomes = load_biomes()
    found = False
    for wx in range(200):
        for wy in range(200):
            h = height_field(wx, wy)
            m = moisture_field(wx, wy)
            weights = biome_weights(h, m, biomes)
            ordered = sorted(weights.values(), reverse=True)
            if len(ordered) > 1 and ordered[0] > 0.1 and ordered[1] > 0.1:
                found = True
                break
        if found:
            break
    assert found


def test_sample_climate_returns_primary():
    init_world_fields(99)
    primary, secondary, blend, weights = sample_climate(50, 50)
    assert primary in load_biomes()
    assert primary in weights
    assert blend >= 0.0
    if secondary:
        assert secondary in weights
