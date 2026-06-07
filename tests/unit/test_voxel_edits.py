"""Tests for manual voxel edits."""
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
def test_voxel_edits_roundtrip(chars_env):
    from src.characters.voxel_edits import VoxelEditLayer, apply_edits, load_voxel_edits, save_voxel_edits

    layer = VoxelEditLayer()
    layer.add(1, 2, 3, "body_head")
    layer.remove(0, 0, 0)

    base = {(0, 0, 0): "body_torso", (1, 1, 1): "body_head"}
    merged = apply_edits(base, layer)
    assert (0, 0, 0) not in merged
    assert merged[(1, 2, 3)] == "body_head"
    assert merged[(1, 1, 1)] == "body_head"

    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/edits.json"
        save_voxel_edits(path, layer)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        restored = load_voxel_edits(path)
        assert restored.additions == layer.additions
        assert restored.removals == layer.removals
        assert "additions" in data
