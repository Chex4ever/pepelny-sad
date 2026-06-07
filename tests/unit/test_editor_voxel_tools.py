"""Tests for editor voxel tools."""
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
def test_rotate_facing_45(chars_env):
    from src.characters.editor_voxel_tools import rotate_facing

    assert rotate_facing("s", 1) == "sw"
    assert rotate_facing("s", -1) == "se"


@pytest.mark.unit
def test_move_voxel_in_edits(chars_env):
    from src.characters.bake import bake_voxel_model
    from src.characters.editor_voxel_tools import move_voxel_in_edits, voxel_at
    from src.characters.spec import CharacterSpec
    from src.characters.voxel_edits import VoxelEditLayer

    model = bake_voxel_model(CharacterSpec("human", 42, 28))
    edits = VoxelEditLayer()
    pos = next(iter(model.voxels))
    kind = model.voxels[pos]
    new_pos = (pos[0] + 1, pos[1], pos[2])
    assert move_voxel_in_edits(edits, model, pos, new_pos)
    assert pos in edits.removals
    assert edits.additions[new_pos] == kind
    assert voxel_at(model, edits, new_pos) == kind
    assert voxel_at(model, edits, pos) is None


@pytest.mark.unit
def test_arrow_delta(chars_env):
    import pygame
    from src.characters.editor_voxel_tools import arrow_delta

    d = arrow_delta(pygame.K_UP, "s")
    assert d is not None
    assert d[2] == 0
