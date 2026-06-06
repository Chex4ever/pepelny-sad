"""Tests for iso character view constants and renderer."""
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
def test_yaw_snaps(chars_env):
    from src.render.iso_character_view import YAW_SNAPS_DEG, snap_yaw_deg

    assert len(YAW_SNAPS_DEG) == 8
    assert snap_yaw_deg(22.0) == 0.0
    assert snap_yaw_deg(50.0) == 45.0


@pytest.mark.unit
def test_pitch_constants(chars_env):
    from src.render.iso_character_view import (
        ISO_FLOOR_SLOPE_DEG,
        PITCH_CHARACTER_DEG,
        PITCH_STATIC_DEG,
    )

    assert 20 < ISO_FLOOR_SLOPE_DEG < 30
    assert PITCH_STATIC_DEG > PITCH_CHARACTER_DEG


@pytest.mark.unit
def test_iso_renderer_produces_cells(chars_env):
    import pygame

    pygame.init()
    from src.characters.bake import bake_voxel_model
    from src.characters.spec import CharacterSpec
    from src.prototype.dia_scale.display_scale import PRESET_NORMAL
    from src.prototype.dia_scale.iso_character_renderer import IsoCharacterRenderer

    model = bake_voxel_model(CharacterSpec("human", 42, 28))
    renderer = IsoCharacterRenderer(preset=PRESET_NORMAL, panel_w=400, panel_h=400)
    result = renderer.render(model, title="test")
    assert result.projected
    assert result.surface.get_width() == 400
    pygame.quit()
