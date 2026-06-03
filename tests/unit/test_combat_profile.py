"""Tests for combat profile from equipment."""
from src.progression.combat_profile import build_combat_profile
from src.progression.equipment import Equipment


def test_default_profile():
    profile = build_combat_profile(Equipment())
    assert profile.max_hp == 20
    assert profile.fight_mode == "blade"
    assert profile.box_shape == "normal"


def test_blade_and_wide_greaves():
    eq = Equipment()
    eq.equip("hand_r", "ash_blade")
    eq.equip("legs", "root_greaves")
    profile = build_combat_profile(eq)
    assert profile.fight_mode == "blade"
    assert profile.fight_damage >= 12
    assert profile.box_shape == "wide"


def test_staff_mode():
    eq = Equipment()
    eq.equip("hand_r", "root_staff")
    profile = build_combat_profile(eq)
    assert profile.fight_mode == "staff"
    assert profile.fight_damage >= 6
