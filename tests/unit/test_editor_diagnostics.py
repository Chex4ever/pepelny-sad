"""Tests for editor diagnostics."""
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
def test_compute_floor_z_from_legs(chars_env):
    from src.characters.editor_diagnostics import compute_floor_z

    voxels = {
        (0, 0, 0): "body_leg_l",
        (1, 0, 0): "body_leg_r",
        (0, 0, 5): "body_torso",
    }
    assert compute_floor_z(voxels) == 0


@pytest.mark.unit
def test_below_floor_e_marker(chars_env):
    from src.characters.editor_diagnostics import analyze_voxels

    voxels = {(0, 0, -1): "body_leg_l", (0, 0, 0): "body_leg_l"}
    report = analyze_voxels(voxels, floor_z=0)
    assert report.counts()["e"] >= 1


@pytest.mark.unit
def test_disconnected_kind_s_marker(chars_env):
    from src.characters.editor_diagnostics import analyze_voxels

    voxels = {
        (0, 0, 0): "body_arm_l",
        (5, 5, 5): "body_arm_l",
        (0, 0, 1): "body_torso",
        (0, 0, 2): "body_torso",
    }
    report = analyze_voxels(voxels, floor_z=0)
    assert report.counts()["s"] >= 1


@pytest.mark.unit
def test_air_gap_a_marker(chars_env):
    from src.characters.editor_diagnostics import analyze_voxels

    voxels = {
        (0, 0, 3): "body_leg_l",
        (1, 0, 3): "body_leg_r",
    }
    report = analyze_voxels(voxels, floor_z=0, walking=True)
    assert report.counts()["a"] >= 1
