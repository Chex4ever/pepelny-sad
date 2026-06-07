"""Tests for 8-way facing transforms and animation pause."""
from __future__ import annotations

import pytest


@pytest.fixture
def chars_env():
    from src.constants import init_paths
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    init_paths(root)
    return root


@pytest.mark.unit
def test_facing_transform_preserves_count(chars_env):
    from src.characters.bake import bake_voxel_model, transform_model_facing
    from src.characters.spec import CharacterSpec

    base = bake_voxel_model(CharacterSpec("human", 42, 28), pose_id="idle_s")
    for facing in ("e", "ne", "w"):
        rotated = transform_model_facing(base, facing)
        assert len(rotated.voxels) > 40
        assert rotated.voxels != base.voxels


@pytest.mark.unit
def test_lazy_pose_set_facing(chars_env):
    from src.characters.bake import bake_pose_set
    from src.characters.spec import CharacterSpec

    ps = bake_pose_set(CharacterSpec("human", 42, 28))
    idle_e = ps.get("idle_e")
    idle_s = ps.get("idle_s")
    assert idle_e.voxels != idle_s.voxels


@pytest.mark.unit
def test_anim_pause_manual_phase(chars_env):
    from src.characters.anim import AnimPlayer
    from src.characters.bake import bake_pose_set
    from src.characters.spec import CharacterSpec

    ps = bake_pose_set(CharacterSpec("human", 1, 25))
    anim = AnimPlayer(ps)
    anim.set_walking(True)
    anim.set_manual_phase(2)
    anim.paused = True
    assert anim.walk_phase() == 2
    assert anim.current_pose_id() == "walk_s_2"


@pytest.mark.unit
def test_eight_facings_valid(chars_env):
    from src.characters.poses import FACINGS_8, POSE_KEYS, is_valid_facing, parse_pose_id

    assert len(FACINGS_8) == 8
    assert len(POSE_KEYS) == 32
    for f in FACINGS_8:
        assert is_valid_facing(f)
        facing, walking, phase = parse_pose_id(f"walk_{f}_1")
        assert facing == f
        assert walking
        assert phase == 1
