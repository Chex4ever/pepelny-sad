"""Unit tests for src/characters core."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(scope="module")
def chars_env():
    pass


@pytest.mark.unit
def test_races_catalog_loads_8(chars_env):
    from src.characters.loader import load_races_catalog

    catalog = load_races_catalog()
    assert len(catalog) == 8
    assert "human" in catalog
    assert "stoneheart" in catalog


@pytest.mark.unit
def test_same_seed_same_morphology(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.spec import CharacterSpec

    spec = CharacterSpec(race_id="human", seed=42, age_years=28)
    a = generate_morphology(spec)
    b = generate_morphology(spec)
    assert a.height_m == b.height_m
    assert a.hair_style_id == b.hair_style_id


@pytest.mark.unit
def test_different_races_different_height(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.spec import CharacterSpec

    human = generate_morphology(CharacterSpec("human", 1, 30))
    dwarf = generate_morphology(CharacterSpec("dwarf", 1, 50))
    elf = generate_morphology(CharacterSpec("elf", 1, 120))
    assert dwarf.height_m < human.height_m
    assert human.height_m < elf.height_m


@pytest.mark.unit
def test_age_stage_child_shorter(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.morphology import LifeStage
    from src.characters.spec import CharacterSpec

    child = generate_morphology(CharacterSpec("human", 5, 8))
    adult = generate_morphology(CharacterSpec("human", 5, 30))
    assert child.life_stage == LifeStage.CHILD
    assert adult.life_stage == LifeStage.ADULT
    assert child.height_m < adult.height_m


@pytest.mark.unit
def test_elf_has_pointed_ears(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.spec import CharacterSpec

    morph = generate_morphology(CharacterSpec("elf", 10, 120))
    assert morph.has_feature("ears_pointed")


@pytest.mark.unit
def test_helmet_occludes_hair(chars_env):
    from src.characters.bake import bake_voxel_model
    from src.characters.spec import CharacterSpec

    bare = bake_voxel_model(CharacterSpec("human", 99, 30))
    helm = bake_voxel_model(
        CharacterSpec("human", 99, 30, equipment={"head": "helm_ash"}),
    )
    hair_bare = sum(1 for k in bare.voxels.values() if k == "hair")
    hair_helm = sum(1 for k in helm.voxels.values() if k == "hair")
    armor_helm = sum(1 for k in helm.voxels.values() if k == "armor_head")
    assert hair_bare > 0
    assert hair_helm < hair_bare
    assert armor_helm > 0


@pytest.mark.unit
def test_equip_sword_changes_hand_voxels(chars_env):
    from src.characters.bake import bake_voxel_model
    from src.characters.spec import CharacterSpec

    bare = bake_voxel_model(CharacterSpec("human", 7, 30))
    armed = bake_voxel_model(
        CharacterSpec("human", 7, 30, equipment={"hand_r": "ash_blade"}),
    )
    assert sum(1 for k in bare.voxels.values() if k == "weapon") == 0
    assert sum(1 for k in armed.voxels.values() if k == "weapon") > 0


@pytest.mark.unit
def test_pose_set_count(chars_env):
    from src.characters.bake import bake_pose_set
    from src.characters.poses import CANONICAL_POSE_KEYS, POSE_KEYS
    from src.characters.spec import CharacterSpec

    ps = bake_pose_set(CharacterSpec("human", 3, 25))
    assert len(ps) == len(CANONICAL_POSE_KEYS)
    assert len(CANONICAL_POSE_KEYS) == 4
    for pose_id in POSE_KEYS:
        model = ps.get(pose_id)
        assert model.voxels


@pytest.mark.unit
def test_all_races_generate(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.loader import load_races_catalog
    from src.characters.spec import CharacterSpec

    for rid in load_races_catalog():
        for age in (5, 25, 60, 200):
            morph = generate_morphology(CharacterSpec(rid, 1, age))
            assert morph.height_m > 0.5
            assert morph.segments


@pytest.mark.unit
def test_spec_roundtrip(chars_env):
    from src.characters.spec import CharacterSpec

    spec = CharacterSpec(
        race_id="orc",
        seed=123,
        age_years=20,
        sex="male",
        equipment={"hand_r": "ash_blade"},
    )
    restored = CharacterSpec.from_dict(spec.to_dict())
    assert restored == spec


@pytest.mark.unit
def test_walk_poses_differ_from_idle(chars_env):
    from src.characters.bake import bake_voxel_model
    from src.characters.spec import CharacterSpec

    spec = CharacterSpec("human", 5, 30)
    idle = bake_voxel_model(spec, pose_id="idle_s")
    walk0 = bake_voxel_model(spec, pose_id="walk_s_0")
    walk1 = bake_voxel_model(spec, pose_id="walk_s_1")
    walk2 = bake_voxel_model(spec, pose_id="walk_s_2")
    assert idle.voxels != walk0.voxels
    assert walk0.voxels != walk2.voxels
    assert walk1.voxels != walk0.voxels


@pytest.mark.unit
def test_walk_phases_cycle(chars_env):
    from src.characters.bake import bake_pose_set
    from src.characters.spec import CharacterSpec
    from src.characters.anim import AnimPlayer

    ps = bake_pose_set(CharacterSpec("human", 1, 25))
    anim = AnimPlayer(ps)
    anim.set_walking(True)
    ids = {anim.current_pose_id(now=t) for t in (0.0, 0.12, 0.24, 0.36, 0.48)}
    assert "walk_s_0" in ids
    assert "walk_s_1" in ids
    assert "walk_s_2" in ids


@pytest.mark.unit
def test_body_limb_kinds(chars_env):
    from src.characters.bake import bake_voxel_model
    from src.characters.spec import CharacterSpec

    model = bake_voxel_model(CharacterSpec("human", 3, 25))
    kinds = set(model.voxels.values())
    assert "body_head" in kinds
    assert "body_arm_l" in kinds
    assert "body_leg_r" in kinds
    assert "body_torso" in kinds


@pytest.mark.unit
def test_voxel_model_has_voxels(chars_env):
    from collections import Counter

    from src.characters.adapters.voxel import spec_to_voxel_model
    from src.characters.spec import CharacterSpec

    model = spec_to_voxel_model(CharacterSpec("human", 11, 30), anchor_x=5, anchor_y=5)
    kinds = Counter(model.voxels.values())
    assert len(model.voxels) > 45
    assert kinds.get("body_torso", 0) >= 12
    assert kinds.get("body_head", 0) >= 4
    assert model.max_z() > 10
    xs = [x for x, _y, _z in model.voxels]
    assert max(xs) - min(xs) + 1 >= 3
