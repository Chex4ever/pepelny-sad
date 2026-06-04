"""Surface detail variants."""
from src.data.art_loader import load_biomes
from src.world.surface_detail import pick_floor_stencil


def test_floor_variant_count_per_biome():
    seed = 12345
    for biome_id in load_biomes():
        seen: set[str] = set()
        for wx in range(50):
            for wy in range(50):
                seen.add(pick_floor_stencil(biome_id, wx, wy, seed))
        assert len(seen) >= 3, f"{biome_id} only {seen}"
