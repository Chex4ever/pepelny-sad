"""Tests for character generator tuning layer."""
from __future__ import annotations

import json
import tempfile

import pytest


@pytest.fixture
def chars_env():
    from src.constants import init_paths
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    init_paths(root)
    return root


@pytest.mark.unit
def test_tuning_override_height_bias(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.spec import CharacterSpec
    from src.characters.tuning import TuningState, build_reference

    spec = CharacterSpec("human", 42, 28)
    ref = build_reference(spec)
    ref_h = ref["morphology.height_m"]

    tuning = TuningState()
    tuning.set("traits.height_bias", 0.99)
    morph = generate_morphology(spec, tuning=tuning)
    assert morph.height_m > ref_h


@pytest.mark.unit
def test_tuning_torso_override_voxels(chars_env):
    from collections import Counter

    from src.characters.bake import bake_voxel_model
    from src.characters.spec import CharacterSpec
    from src.characters.tuning import TuningState, build_reference

    spec = CharacterSpec("human", 3, 25)
    ref = build_reference(spec)
    tuning = TuningState()
    tuning.set("proportions.torso_h", float(ref["proportions.torso_h"]) * 1.35)
    bare = bake_voxel_model(spec)
    tuned = bake_voxel_model(spec, tuning=tuning)
    assert Counter(tuned.voxels.values()).get("body_torso", 0) >= Counter(bare.voxels.values()).get("body_torso", 0)


@pytest.mark.unit
def test_tuning_diff_vs_reference(chars_env):
    from src.characters.spec import CharacterSpec
    from src.characters.tuning import TuningState, build_reference

    spec = CharacterSpec("human", 42, 28)
    ref = build_reference(spec)
    tuning = TuningState()
    tuning.set("race.torso_scale", 1.15)
    diff = tuning.diff_vs(ref)
    assert "race.torso_scale" in diff
    assert diff["race.torso_scale"][0] == 1.15


@pytest.mark.unit
def test_generate_without_tuning_regression(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.spec import CharacterSpec

    spec = CharacterSpec("human", 42, 28)
    a = generate_morphology(spec)
    b = generate_morphology(spec, tuning=None)
    assert a.height_m == b.height_m
    assert a.proportions.torso_h == b.proportions.torso_h


@pytest.mark.unit
def test_export_roundtrip(chars_env):
    from src.characters.spec import CharacterSpec
    from src.characters.tuning import TuningState, build_reference

    spec = CharacterSpec("elf", 7, 120)
    ref = build_reference(spec)
    tuning = TuningState()
    tuning.set("traits.jaw", 0.8)
    data = tuning.to_dict()
    restored = TuningState.from_dict(data)
    assert restored.get("traits.jaw") == 0.8
    assert "traits.jaw" in restored.locked

    with tempfile.TemporaryDirectory() as tmp:
        from src.characters.tuning import save_export_bundle

        path = f"{tmp}/out.json"
        save_export_bundle(path, spec, tuning, ref)
        with open(path, encoding="utf-8") as f:
            bundle = json.load(f)
        assert bundle["meta"]["race_id"] == "elf"
        assert "traits.jaw" in bundle["overrides"]


@pytest.mark.unit
def test_stage_preset_age_elf(chars_env):
    from src.characters.lifecycle import resolve_life_stage, stage_height_multiplier
    from src.characters.loader import load_race
    from src.characters.morphology import LifeStage
    from src.characters.spec import CharacterSpec
    from src.characters.traits import roll_traits
    from src.characters.tuning import build_reference, stage_preset_age

    race = load_race("elf")
    child_age = stage_preset_age(race, LifeStage.CHILD)
    adult_age = stage_preset_age(race, LifeStage.ADULT)
    ref_child = build_reference(CharacterSpec("elf", 1, child_age))
    ref_adult = build_reference(CharacterSpec("elf", 1, adult_age))
    assert ref_child["life_stage"] == "child"
    assert ref_adult["life_stage"] == "adult"
    traits = roll_traits(CharacterSpec("elf", 1, adult_age), race)
    child_mult = stage_height_multiplier(resolve_life_stage(child_age, race), traits.height_bias)
    adult_mult = stage_height_multiplier(resolve_life_stage(adult_age, race), traits.height_bias)
    assert child_mult != adult_mult or child_age != adult_age


@pytest.mark.unit
def test_shoulder_hw_override_moves_joints(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.spec import CharacterSpec
    from src.characters.tuning import TuningState, build_reference

    spec = CharacterSpec("human", 42, 28)
    ref = build_reference(spec)
    base = generate_morphology(spec)
    base_x = abs(base.joints["shoulder_l"].x)

    tuning = TuningState()
    tuning.set("proportions.shoulder_hw", 0.55)
    tuned = generate_morphology(spec, tuning=tuning)
    tuned_x = abs(tuned.joints["shoulder_l"].x)

    assert tuned.proportions.shoulder_hw == 0.55
    assert tuned_x == pytest.approx(0.55, abs=0.01)
    assert tuned_x > base_x
    assert abs(tuned.joints["elbow_l"].x) > abs(base.joints["elbow_l"].x)


@pytest.mark.unit
def test_default_shoulder_hw_increased(chars_env):
    from src.characters.tuning import build_reference
    from src.characters.spec import CharacterSpec

    ref = build_reference(CharacterSpec("human", 42, 28))
    assert ref["proportions.shoulder_hw"] >= 0.28


@pytest.mark.unit
def test_proportion_scale(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.spec import CharacterSpec
    from src.characters.tuning import TuningState

    spec = CharacterSpec("human", 42, 28)
    base = generate_morphology(spec)
    tuning = TuningState()
    tuning.proportion_scale = 1.25
    scaled = generate_morphology(spec, tuning=tuning)
    assert scaled.proportions.torso_h == pytest.approx(base.proportions.torso_h * 1.25, rel=1e-3)
    assert abs(scaled.joints["shoulder_l"].x) > abs(base.joints["shoulder_l"].x)


@pytest.mark.unit
def test_proportion_scale_respects_locked_override(chars_env):
    from src.characters.generate import generate_morphology
    from src.characters.spec import CharacterSpec
    from src.characters.tuning import TuningState, build_reference

    spec = CharacterSpec("human", 42, 28)
    ref = build_reference(spec)
    tuning = TuningState()
    tuning.proportion_scale = 1.3
    tuning.set("proportions.shoulder_hw", float(ref["proportions.shoulder_hw"]))
    morph = generate_morphology(spec, tuning=tuning)
    assert morph.proportions.shoulder_hw == pytest.approx(float(ref["proportions.shoulder_hw"]))


@pytest.mark.unit
def test_race_change_rebuilds_reference(chars_env):
    from src.characters.spec import CharacterSpec
    from src.characters.tuning import build_reference

    human = build_reference(CharacterSpec("human", 42, 28))
    dwarf = build_reference(CharacterSpec("dwarf", 42, 28))
    assert human["race.shoulder_scale"] != dwarf["race.shoulder_scale"]
