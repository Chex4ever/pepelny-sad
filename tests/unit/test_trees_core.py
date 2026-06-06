"""Unit tests for src/trees core (species, lifecycle, forest patches)."""
from __future__ import annotations

import pytest

ROOT = None


@pytest.fixture(scope="module")
def trees_env():
    import os
    import sys

    global ROOT
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)


@pytest.mark.unit
def test_species_catalog_loads_12(trees_env):
    from src.trees.loader import load_species_catalog

    catalog = load_species_catalog()
    assert len(catalog) >= 12
    assert "oak" in catalog
    assert "birch" in catalog
    assert "baobab" in catalog


@pytest.mark.unit
def test_morphology_deterministic(trees_env):
    from src.trees.generate import generate_morphology
    from src.trees.instance import TreeInstanceSpec

    spec = TreeInstanceSpec(species_id="pine", seed=42, age_years=80, wx=1, wy=2)
    a = generate_morphology(spec)
    b = generate_morphology(spec)
    assert a.height_m == b.height_m
    assert len(a.branches) == len(b.branches)


@pytest.mark.unit
def test_seedling_stage(trees_env):
    from src.trees.generate import generate_morphology
    from src.trees.instance import TreeInstanceSpec
    from src.trees.morphology import TreeLifeStage

    spec = TreeInstanceSpec(species_id="oak", seed=1, age_years=0.5)
    morph = generate_morphology(spec)
    assert morph.stage == TreeLifeStage.SEEDLING
    assert morph.height_m < 2.0


@pytest.mark.unit
def test_mature_height_in_range(trees_env):
    from src.trees.generate import generate_morphology
    from src.trees.instance import TreeInstanceSpec
    from src.trees.loader import load_species

    species = load_species("oak")
    spec = TreeInstanceSpec(species_id="oak", seed=5, age_years=species.max_age_years * 0.6)
    morph = generate_morphology(spec)
    assert species.height_m[0] * 0.5 <= morph.height_m <= species.height_m[1] * 1.05


@pytest.mark.unit
def test_dead_tree_no_foliage(trees_env):
    from src.trees.generate import generate_morphology
    from src.trees.instance import TreeInstanceSpec
    from src.trees.morphology import TreeLifeStage

    spec = TreeInstanceSpec(
        species_id="birch", seed=9, age_years=50, health=0.0, force_dead=True
    )
    morph = generate_morphology(spec)
    assert morph.stage == TreeLifeStage.DEAD_STANDING
    assert not morph.has_foliage()


@pytest.mark.unit
def test_stump_low(trees_env):
    from src.trees.generate import generate_morphology
    from src.trees.instance import TreeInstanceSpec
    from src.trees.loader import load_species
    from src.trees.morphology import TreeLifeStage

    species = load_species("oak")
    spec = TreeInstanceSpec(
        species_id="oak", seed=3, age_years=100, force_stump=True
    )
    morph = generate_morphology(spec)
    assert morph.stage == TreeLifeStage.STUMP
    assert morph.height_m < species.height_m[1] * 0.2
    assert not morph.branches


@pytest.mark.unit
def test_birch_grove_mostly_birch(trees_env):
    from src.trees.forest_placer import place_forest_multi

    placements = place_forest_multi("birch_grove", nx=20, ny=20, world_seed=12345)
    assert len(placements) > 5
    birch = sum(1 for p in placements if p.instance.species_id == "birch")
    assert birch / len(placements) >= 0.5


@pytest.mark.unit
def test_burned_clearing_dead_or_stump(trees_env):
    from src.trees.forest_placer import place_forest_multi
    from src.trees.morphology import TreeLifeStage
    from src.trees.generate import generate_morphology

    placements = place_forest_multi("burned_clearing", nx=12, ny=12, world_seed=99)
    assert len(placements) > 0
    for p in placements:
        morph = generate_morphology(p.instance)
        assert morph.stage in (
            TreeLifeStage.DEAD_STANDING,
            TreeLifeStage.STUMP,
            TreeLifeStage.DECAYED,
        )


@pytest.mark.unit
def test_voxel_from_spec_has_voxels(trees_env):
    from src.trees.adapters.voxel import spec_to_voxel_model
    from src.trees.instance import TreeInstanceSpec

    spec = TreeInstanceSpec(species_id="pine", seed=11, age_years=60)
    model = spec_to_voxel_model(spec, anchor_x=10, anchor_y=10)
    assert len(model.voxels) > 50
    assert model.max_z() > 20


@pytest.mark.unit
def test_instance_roundtrip_dict(trees_env):
    from src.trees.instance import TreeInstanceSpec

    spec = TreeInstanceSpec(species_id="maple", seed=7, age_years=30, wx=3, wy=4)
    restored = TreeInstanceSpec.from_dict(spec.to_dict())
    assert restored == spec


@pytest.mark.unit
def test_forest_patches_load(trees_env):
    from src.trees.loader import load_forest_patches

    patches = load_forest_patches()
    assert "birch_grove" in patches
    assert "burned_clearing" in patches
    assert patches["burned_clearing"].dead_ratio == 1.0
