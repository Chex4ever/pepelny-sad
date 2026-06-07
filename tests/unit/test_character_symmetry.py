"""Base character generation must be bilaterally symmetric (idle + walk cycle balance)."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(scope="module")
def chars_env():
    from src.constants import init_paths

    init_paths(ROOT)


def _violations(model) -> list:
    from src.characters.symmetry import count_symmetry_violations

    return count_symmetry_violations(
        model.voxels,
        anchor_x=model.anchor_x,
        anchor_y=model.anchor_y,
    )


@pytest.mark.unit
@pytest.mark.parametrize("race_id", [
    "human", "elf", "dwarf", "orc", "ashkin", "rootbound", "whisper", "stoneheart",
])
def test_idle_pose_symmetric_all_races(chars_env, race_id: str):
    from src.characters.bake import bake_voxel_model
    from src.characters.spec import CharacterSpec

    spec = CharacterSpec(race_id=race_id, seed=42, age_years=30, sex="neutral")
    model = bake_voxel_model(spec, pose_id="idle_s", anchor_x=0, anchor_y=0)
    bad = _violations(model)
    assert bad == [], f"{race_id} idle_s: {bad[:5]}"


@pytest.mark.unit
def test_default_traits_have_zero_asymmetry(chars_env):
    from src.characters.loader import load_race
    from src.characters.spec import CharacterSpec
    from src.characters.traits import roll_traits

    spec = CharacterSpec("human", 99, 28)
    traits = roll_traits(spec, load_race("human"))
    assert traits.asymmetry == 0.0


@pytest.mark.unit
def test_walk_cycle_phases_mirror_each_other(chars_env):
    from src.characters.poses import PoseDelta, _WALK_CYCLE

    p0, p1, p2 = _WALK_CYCLE

    def swapped(delta: PoseDelta) -> PoseDelta:
        return PoseDelta(
            leg_l_fwd=delta.leg_r_fwd,
            leg_r_fwd=delta.leg_l_fwd,
            leg_l_lift=delta.leg_r_lift,
            leg_r_lift=delta.leg_l_lift,
            leg_l_z=delta.leg_r_z,
            leg_r_z=delta.leg_l_z,
            arm_l_fwd=delta.arm_r_fwd,
            arm_r_fwd=delta.arm_l_fwd,
            arm_l_z=delta.arm_r_z,
            arm_r_z=delta.arm_l_z,
            torso_bob=delta.torso_bob,
        )

    assert swapped(p0) == p2
    assert p1.leg_l_fwd == p1.leg_r_fwd
    assert p1.leg_l_lift == -p1.leg_r_lift
    assert p1.arm_l_fwd == p1.arm_r_fwd == 0.0


@pytest.mark.unit
def test_all_races_multiple_seeds_symmetric(chars_env):
    from src.characters.bake import bake_voxel_model
    from src.characters.loader import load_races_catalog
    from src.characters.spec import CharacterSpec

    for race_id in load_races_catalog():
        for seed in (1, 7, 42, 1337):
            spec = CharacterSpec(race_id=race_id, seed=seed, age_years=30)
            model = bake_voxel_model(spec, pose_id="idle_s")
            bad = _violations(model)
            assert not bad, f"{race_id} seed={seed}: {bad[:3]}"


@pytest.mark.unit
def test_walk_poses_not_forced_symmetric(chars_env):
    from src.characters.bake import bake_voxel_model
    from src.characters.spec import CharacterSpec
    from src.characters.symmetry import count_symmetry_violations

    spec = CharacterSpec("human", 5, 30)
    walk0 = bake_voxel_model(spec, pose_id="walk_s_0")
    walk1 = bake_voxel_model(spec, pose_id="walk_s_1")
    assert walk0.voxels != walk1.voxels
    # Walk breaks left-right mirror by design (stride).
    assert count_symmetry_violations(walk0.voxels, anchor_x=0, anchor_y=0)


@pytest.mark.unit
def test_hair_templates_bilateral_when_possible(chars_env):
    import json
    from pathlib import Path

    path = Path(ROOT) / "src" / "characters" / "data" / "hair_styles.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for race_id, styles in data.items():
        if race_id.startswith("_"):
            continue
        for style_id, cells in styles.items():
            if not cells:
                continue
            keyed = {(int(c[0]), int(c[1]), int(c[2])): str(c[3]) for c in cells}
            for (dx, dy, dz), kind in keyed.items():
                mirror = (-dx, dy, dz)
                if dx == 0:
                    continue
                assert mirror in keyed, f"{race_id}/{style_id}: missing mirror for ({dx},{dy},{dz})"
                assert keyed[mirror] == kind
