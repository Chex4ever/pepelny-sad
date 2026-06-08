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


@pytest.mark.unit
@pytest.mark.parametrize("race_id", [
    "human", "elf", "dwarf", "orc", "ashkin", "rootbound", "whisper", "stoneheart",
])
def test_idle_s_arms_same_screen_height(chars_env, race_id: str):
    """Bilateral voxels must project to equal sv for L/R arms (front-on camera)."""
    import pygame

    pygame.init()
    from src.characters.bake import bake_voxel_model
    from src.characters.loader import load_races_catalog
    from src.characters.spec import CharacterSpec
    from src.prototype.dia_scale.display_scale import PRESET_NORMAL
    from src.prototype.dia_scale.iso_character_renderer import IsoCharacterRenderer

    assert race_id in load_races_catalog()
    model = bake_voxel_model(CharacterSpec(race_id, 42, 30), pose_id="idle_s")
    renderer = IsoCharacterRenderer(preset=PRESET_NORMAL, panel_w=320, panel_h=320)
    result = renderer.render(model, show_floor=False, show_shading=False, show_diagnostics=False)
    sv_l = sorted(row[3] for row in result.projected if row[7] == "body_arm_l")
    sv_r = sorted(row[3] for row in result.projected if row[7] == "body_arm_r")
    assert sv_l, f"{race_id}: no left arm voxels projected"
    assert sv_r, f"{race_id}: no right arm voxels projected"
    assert sv_l == sv_r, f"{race_id}: arm screen heights differ L={sv_l} R={sv_r}"
    pygame.quit()


@pytest.mark.unit
def test_editor_floor_has_diag_iso_tiles(chars_env):
    """Character editor floor: 1 m (5×5) diag iso tiles centered on feet."""
    from src.characters.editor_floor import (
        build_floor_patch,
        floor_screen_offset,
        floor_tile_anchors,
    )
    from src.render.iso_character_view import EDITOR_FLOOR_TILES

    n = EDITOR_FLOOR_TILES
    patch = build_floor_patch(0, 0, seed=2)
    assert len(floor_tile_anchors(0, 0, n_tiles=n)) == n ** 2
    assert len(patch) == 60
    anchors_iso = {
        floor_screen_offset(ax, ay, ref_cx=0, ref_cy=0)
        for _tx, _ty, ax, ay in floor_tile_anchors(0, 0, n_tiles=n)
    }
    assert len(anchors_iso) == n ** 2


@pytest.mark.unit
def test_facing_rotates_character_not_floor(chars_env):
    """World facing is bake-only (45°/step); camera must not add a second yaw."""
    import math
    import pygame

    pygame.init()
    from src.characters.bake import bake_voxel_model
    from src.characters.editor_diagnostics import compute_floor_z
    from src.characters.spec import CharacterSpec
    from src.prototype.dia_scale.display_scale import PRESET_NORMAL
    from src.prototype.dia_scale.iso_character_renderer import IsoCharacterRenderer

    spec = CharacterSpec("human", 42, 30)
    model_s = bake_voxel_model(spec, pose_id="idle_s")
    model_sw = bake_voxel_model(spec, pose_id="idle_sw")
    renderer = IsoCharacterRenderer(preset=PRESET_NORMAL, panel_w=320, panel_h=320)
    orbit = renderer._orbit_like()
    zoom = renderer.camera.zoom

    def proj(model, x, y, z):
        floor_z = compute_floor_z(model.voxels)
        cx0, cy0 = float(model.anchor_x), float(model.anchor_y)
        return renderer._project_point(
            x, y, z, cx0=cx0, cy0=cy0, cz0=float(floor_z), orbit=orbit, zoom=zoom,
        )

    floor_z = compute_floor_z(model_s.voxels)
    feet = (model_s.anchor_x, model_s.anchor_y, floor_z)
    _, su_fs, sv_fs = proj(model_s, *feet)
    _, su_fsw, sv_fsw = proj(model_sw, *feet)
    assert (su_fs, sv_fs) == (su_fsw, sv_fsw)

    from src.characters.editor_floor import floor_screen_offset

    su_ff, sv_ff = floor_screen_offset(feet[0], feet[1], ref_cx=feet[0], ref_cy=feet[1])
    assert (su_ff, sv_ff) == (0, 0)

    arm_s = next(p for p, k in model_s.voxels.items() if k == "body_arm_r")
    arm_sw = next(p for p, k in model_sw.voxels.items() if k == "body_arm_r")
    _, su_hs, sv_hs = proj(model_s, *arm_s)
    _, su_hsw, sv_hsw = proj(model_sw, *arm_sw)
    assert (su_hs, sv_hs) != (su_hsw, sv_hsw)

    delta = math.degrees(math.atan2(su_hsw - su_hs, sv_hsw - sv_hs))
    assert abs(abs(delta) - 45.0) < 6.0
    pygame.quit()
